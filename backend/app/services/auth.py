from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from uuid import UUID, uuid4

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import select

from app.core.config import get_settings
from app.db import RefreshTokenModel, UserModel, SessionLocal
from app.repositories.users import UserRepository
from app.schemas.auth import (
    EmailVerificationConfirm,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
settings = get_settings()
user_repository = UserRepository()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _unauthorized(message: str = "Invalid or expired token") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message, headers={"WWW-Authenticate": "Bearer"})


def _access_token(user: UserModel) -> tuple[str, int]:
    now = _now()
    expires_at = now + timedelta(seconds=settings.access_token_ttl_seconds)
    payload = {
        "sub": user.id,
        "typ": "access",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": expires_at,
        "ver": user.token_version,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256"), settings.access_token_ttl_seconds


def _issue_tokens(user: UserModel, session, *, user_agent: str | None = None, ip_address: str | None = None) -> TokenResponse:
    access_token, expires_in = _access_token(user)
    refresh_token = secrets.token_urlsafe(48)
    now = _now()
    session.add(
        RefreshTokenModel(
            id=str(uuid4()),
            user_id=user.id,
            token_hash=_hash_token(refresh_token),
            expires_at=now + timedelta(seconds=settings.refresh_token_ttl_seconds),
            created_at=now,
            updated_at=now,
            user_agent=user_agent,
            ip_address=ip_address,
        )
    )
    session.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, expires_in=expires_in, user=user_repository._user(user))


def register(payload: RegisterRequest) -> UserResponse:
    try:
        user = user_repository.create(payload, password_hash.hash(payload.password))
        session = SessionLocal()
        try:
            row = session.get(UserModel, str(user.id))
            if row:
                verification_token = secrets.token_urlsafe(48)
                row.verification_token_hash = _hash_token(verification_token)
                row.verification_expires_at = _now() + timedelta(hours=24)
                row.updated_at = _now()
                session.commit()
        finally:
            session.close()
        # Email delivery is intentionally deferred to the configured provider integration.
        return user
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


def login(payload: LoginRequest, *, user_agent: str | None = None, ip_address: str | None = None) -> TokenResponse:
    session = SessionLocal()
    try:
        user = session.scalar(select(UserModel).where(UserModel.email == str(payload.email).lower()))
        if not user or not password_hash.verify(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
        return _issue_tokens(user, session, user_agent=user_agent, ip_address=ip_address)
    finally:
        session.close()


def _decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "typ", "iss", "aud", "iat", "exp", "ver"]},
        )
        if payload.get("typ") != "access":
            raise _unauthorized()
        return payload
    except (jwt.PyJWTError, KeyError, ValueError, TypeError) as exc:
        raise _unauthorized() from exc


def current_user_from_token(token: str) -> UserResponse:
    payload = _decode_access_token(token)
    try:
        user_id = UUID(payload["sub"])
        token_version = int(payload["ver"])
    except (KeyError, ValueError, TypeError) as exc:
        raise _unauthorized() from exc
    user = user_repository.get_model(user_id)
    if not user or not user.is_active or user.token_version != token_version:
        raise _unauthorized("User account is not authorized")
    return user_repository._user(user)


def current_user(credentials: HTTPAuthorizationCredentials | None) -> UserResponse:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Bearer token required")
    return current_user_from_token(credentials.credentials)


def refresh(refresh_token: str, *, user_agent: str | None = None, ip_address: str | None = None) -> TokenResponse:
    session = SessionLocal()
    try:
        now = _now()
        row = session.scalar(select(RefreshTokenModel).where(RefreshTokenModel.token_hash == _hash_token(refresh_token)))
        if not row or row.revoked_at is not None or _utc(row.expires_at) <= now:
            raise _unauthorized("Invalid or expired refresh token")
        user = session.get(UserModel, row.user_id)
        if not user or not user.is_active:
            raise _unauthorized("User account is not authorized")
        row.revoked_at = now
        row.updated_at = now
        return _issue_tokens(user, session, user_agent=user_agent, ip_address=ip_address)
    finally:
        session.close()


def logout(refresh_token: str, user_id: UUID) -> None:
    session = SessionLocal()
    try:
        now = _now()
        row = session.scalar(
            select(RefreshTokenModel).where(
                RefreshTokenModel.token_hash == _hash_token(refresh_token),
                RefreshTokenModel.user_id == str(user_id),
            )
        )
        user = session.get(UserModel, str(user_id))
        if user:
            user.token_version += 1
            user.updated_at = now
        if row and row.revoked_at is None:
            row.revoked_at = now
            row.updated_at = now
        session.commit()
    finally:
        session.close()


def request_password_reset(payload: PasswordResetRequest) -> None:
    session = SessionLocal()
    try:
        user = session.scalar(select(UserModel).where(UserModel.email == str(payload.email).lower()))
        if user and user.is_active:
            token = secrets.token_urlsafe(48)
            now = _now()
            user.password_reset_token_hash = _hash_token(token)
            user.password_reset_expires_at = now + timedelta(minutes=30)
            user.updated_at = now
            # Delivery is intentionally deferred to the email provider integration.
            session.commit()
    finally:
        session.close()


def confirm_password_reset(payload: PasswordResetConfirm) -> bool:
    session = SessionLocal()
    try:
        now = _now()
        user = session.scalar(select(UserModel).where(UserModel.password_reset_token_hash == _hash_token(payload.token)))
        if not user or not user.password_reset_expires_at or _utc(user.password_reset_expires_at) <= now:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired password reset token")
        user.password_hash = password_hash.hash(payload.new_password)
        user.password_reset_token_hash = None
        user.password_reset_expires_at = None
        user.token_version += 1
        user.updated_at = now
        session.commit()
        return True
    finally:
        session.close()


def confirm_email_verification(payload: EmailVerificationConfirm) -> bool:
    session = SessionLocal()
    try:
        now = _now()
        user = session.scalar(select(UserModel).where(UserModel.verification_token_hash == _hash_token(payload.token)))
        if not user or not user.verification_expires_at or _utc(user.verification_expires_at) <= now:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")
        user.is_verified = True
        user.verification_token_hash = None
        user.verification_expires_at = None
        user.updated_at = now
        session.commit()
        return True
    finally:
        session.close()

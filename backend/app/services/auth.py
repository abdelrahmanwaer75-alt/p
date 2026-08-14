from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
settings = get_settings()
user_repository = UserRepository(settings.download_db_path)
TOKEN_TTL_SECONDS = 3600


def register(payload: RegisterRequest) -> UserResponse:
    try:
        return user_repository.create(payload, password_hash.hash(payload.password))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


def login(payload: LoginRequest) -> TokenResponse:
    found = user_repository.get_by_email(str(payload.email))
    if not found or not password_hash.verify(payload.password, found[1]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    user = found[0]
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=TOKEN_TTL_SECONDS)
    token = jwt.encode({"sub": str(user.id), "exp": expires_at}, settings.jwt_secret, algorithm="HS256")
    return TokenResponse(access_token=token, expires_in=TOKEN_TTL_SECONDS, user=user)


def current_user(credentials: HTTPAuthorizationCredentials | None) -> UserResponse:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user_id = UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc
    user = user_repository.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found")
    return user

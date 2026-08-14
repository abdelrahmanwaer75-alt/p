from collections.abc import Iterator
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import UserModel, get_session
from app.schemas.auth import RegisterRequest, UserResponse


class UserRepository:
    def _session(self) -> Iterator[Session]:
        return get_session()

    def create(self, payload: RegisterRequest, password_hash: str) -> UserResponse:
        now = datetime.now(timezone.utc)
        user = UserModel(
            id=str(uuid4()),
            email=str(payload.email).lower(),
            password_hash=password_hash,
            created_at=now,
            updated_at=now,
            is_active=True,
            is_verified=False,
            token_version=0,
        )
        session = next(self._session())
        try:
            session.add(user)
            session.commit()
            session.refresh(user)
            return self._user(user)
        except IntegrityError as exc:
            session.rollback()
            raise ValueError("An account with this email already exists") from exc
        finally:
            session.close()

    def get_model_by_email(self, email: str) -> UserModel | None:
        session = next(self._session())
        try:
            return session.scalar(select(UserModel).where(UserModel.email == email.lower()))
        finally:
            session.close()

    def get_by_email(self, email: str) -> tuple[UserResponse, str] | None:
        row = self.get_model_by_email(email)
        return (self._user(row), row.password_hash) if row else None

    def get_model(self, user_id: UUID | str) -> UserModel | None:
        session = next(self._session())
        try:
            return session.get(UserModel, str(user_id))
        finally:
            session.close()

    def get(self, user_id: UUID | str) -> UserResponse | None:
        row = self.get_model(user_id)
        return self._user(row) if row else None

    def set_password(self, user_id: UUID | str, password_hash: str) -> bool:
        session = next(self._session())
        try:
            row = session.get(UserModel, str(user_id))
            if not row:
                return False
            row.password_hash = password_hash
            row.updated_at = datetime.now(timezone.utc)
            row.token_version += 1
            session.commit()
            return True
        finally:
            session.close()

    def increment_token_version(self, user_id: UUID | str) -> bool:
        session = next(self._session())
        try:
            row = session.get(UserModel, str(user_id))
            if not row:
                return False
            row.token_version += 1
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
            return True
        finally:
            session.close()

    @staticmethod
    def _user(row: UserModel) -> UserResponse:
        return UserResponse(
            id=UUID(row.id),
            email=row.email,
            created_at=row.created_at,
            updated_at=row.updated_at,
            is_active=row.is_active,
            is_verified=row.is_verified,
        )

import sqlite3
from datetime import datetime
from pathlib import Path
from threading import Lock
from uuid import UUID, uuid4

from app.schemas.auth import RegisterRequest, UserResponse


class UserRepository:
    def __init__(self, database_path: str) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def create(self, payload: RegisterRequest, password_hash: str) -> UserResponse:
        user = UserResponse(id=uuid4(), email=payload.email, created_at=datetime.now().astimezone())
        try:
            with self._lock, self._connect() as connection:
                connection.execute(
                    "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                    (str(user.id), str(user.email).lower(), password_hash, user.created_at.isoformat()),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("An account with this email already exists") from exc
        return user

    def get_by_email(self, email: str) -> tuple[UserResponse, str] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
        if not row:
            return None
        user = UserResponse(id=UUID(row["id"]), email=row["email"], created_at=datetime.fromisoformat(row["created_at"]))
        return user, row["password_hash"]

    def get(self, user_id: UUID) -> UserResponse | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM users WHERE id = ?", (str(user_id),)).fetchone()
        if not row:
            return None
        return UserResponse(id=UUID(row["id"]), email=row["email"], created_at=datetime.fromisoformat(row["created_at"]))

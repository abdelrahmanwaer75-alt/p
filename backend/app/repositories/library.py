import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import UUID, uuid4

from app.schemas.library import LibraryItem, LibraryItemCreate


class LibraryRepository:
    def __init__(self, database_path: str) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS library_items (
                    id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    media_path TEXT,
                    media_type TEXT NOT NULL,
                    is_favorite INTEGER NOT NULL DEFAULT 0,
                    viewed_at TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def create(self, owner_id: UUID, payload: LibraryItemCreate) -> LibraryItem:
        item = LibraryItem(
            id=uuid4(), owner_id=owner_id, title=payload.title, source_url=payload.source_url,
            media_path=payload.media_path, media_type=payload.media_type, is_favorite=False,
            viewed_at=None, created_at=datetime.now(timezone.utc),
        )
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO library_items (id, owner_id, title, source_url, media_path, media_type, is_favorite, viewed_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (str(item.id), str(item.owner_id), item.title, str(item.source_url), item.media_path, item.media_type, 0, None, item.created_at.isoformat()),
            )
        return item

    def list(self, owner_id: UUID, *, favorites_only: bool = False, history_only: bool = False, files_only: bool = False) -> list[LibraryItem]:
        query = "SELECT * FROM library_items WHERE owner_id = ?"
        params: list[object] = [str(owner_id)]
        if favorites_only:
            query += " AND is_favorite = 1"
        if history_only:
            query += " AND viewed_at IS NOT NULL"
        if files_only:
            query += " AND media_path IS NOT NULL"
        query += " ORDER BY COALESCE(viewed_at, created_at) DESC"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._from_row(row) for row in rows]

    def get(self, owner_id: UUID, item_id: UUID) -> LibraryItem | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM library_items WHERE owner_id = ? AND id = ?", (str(owner_id), str(item_id))).fetchone()
        return self._from_row(row) if row else None

    def set_favorite(self, owner_id: UUID, item_id: UUID, favorite: bool) -> LibraryItem | None:
        with self._lock, self._connect() as connection:
            connection.execute("UPDATE library_items SET is_favorite = ? WHERE owner_id = ? AND id = ?", (int(favorite), str(owner_id), str(item_id)))
        return self.get(owner_id, item_id)

    def mark_viewed(self, owner_id: UUID, item_id: UUID) -> LibraryItem | None:
        with self._lock, self._connect() as connection:
            connection.execute("UPDATE library_items SET viewed_at = ? WHERE owner_id = ? AND id = ?", (datetime.now(timezone.utc).isoformat(), str(owner_id), str(item_id)))
        return self.get(owner_id, item_id)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> LibraryItem:
        return LibraryItem(
            id=UUID(row["id"]), owner_id=UUID(row["owner_id"]), title=row["title"], source_url=row["source_url"],
            media_path=row["media_path"], media_type=row["media_type"], is_favorite=bool(row["is_favorite"]),
            viewed_at=datetime.fromisoformat(row["viewed_at"]) if row["viewed_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
        )

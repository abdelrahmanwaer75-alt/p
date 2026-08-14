import sqlite3
from datetime import datetime
from pathlib import Path
from threading import Lock
from uuid import UUID, uuid4

from app.schemas.downloads import DownloadStatus, DownloadTask, DownloadTaskCreate


class DownloadRepository:
    def __init__(self, database_path: str) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS download_tasks (
                    id TEXT PRIMARY KEY,
                    source_url TEXT NOT NULL,
                    format_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress_percent REAL,
                    progress_known INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, payload: DownloadTaskCreate) -> DownloadTask:
        now = datetime.now().astimezone()
        task = DownloadTask(
            id=uuid4(),
            source_url=payload.source_url,
            format_id=payload.format_id,
            status=DownloadStatus.QUEUED,
            created_at=now,
            updated_at=now,
        )
        self.save(task)
        return task

    def save(self, task: DownloadTask) -> DownloadTask:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO download_tasks
                (id, source_url, format_id, status, progress_percent, progress_known,
                 error_message, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(task.id),
                    str(task.source_url),
                    task.format_id,
                    task.status.value,
                    task.progress_percent,
                    int(task.progress_known),
                    task.error_message,
                    task.created_at.isoformat(),
                    task.updated_at.isoformat(),
                ),
            )
        return task

    def get(self, task_id: UUID) -> DownloadTask | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM download_tasks WHERE id = ?", (str(task_id),)).fetchone()
        return self._from_row(row) if row else None

    def list(self) -> list[DownloadTask]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM download_tasks ORDER BY created_at DESC").fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> DownloadTask:
        return DownloadTask(
            id=UUID(row["id"]),
            source_url=row["source_url"],
            format_id=row["format_id"],
            status=DownloadStatus(row["status"]),
            progress_percent=row["progress_percent"],
            progress_known=bool(row["progress_known"]),
            error_message=row["error_message"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

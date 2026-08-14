from sqlalchemy import text
from typing import Literal, TypedDict

from sqlalchemy.exc import SQLAlchemyError

from app.db import engine
from app.queue import DownloadQueue


class ReadinessState(TypedDict):
    status: Literal["ready", "not_ready"]
    database: Literal["ok", "error"]
    redis: Literal["ok", "error"]


class ReadinessService:
    def __init__(self, queue: DownloadQueue | None = None) -> None:
        self.queue = queue or DownloadQueue()

    def check_database(self) -> bool:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    def check_redis(self) -> bool:
        return self.queue.ping()

    def check(self) -> ReadinessState:
        database: Literal["ok", "error"] = "ok" if self.check_database() else "error"
        redis: Literal["ok", "error"] = "ok" if self.check_redis() else "error"
        return {
            "status": "ready" if database == "ok" and redis == "ok" else "not_ready",
            "database": database,
            "redis": redis,
        }

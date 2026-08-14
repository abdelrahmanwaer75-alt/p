import asyncio

from typing import cast

from fastapi import HTTPException, WebSocket, WebSocketDisconnect

from app.queue import DownloadQueue
from app.repositories.downloads import DownloadRepository
from app.services.auth import current_user_from_token
from app.core.config import get_settings
from uuid import UUID


class NotificationService:
    def __init__(self, queue: DownloadQueue | None = None, repository: DownloadRepository | None = None) -> None:
        self.queue = queue or DownloadQueue(get_settings().redis_url)
        self.repository = repository or DownloadRepository()

    async def stream_downloads(self, websocket: WebSocket) -> None:
        authorization = websocket.headers.get("authorization", "")
        if not authorization.lower().startswith("bearer "):
            await websocket.close(code=4401)
            return
        try:
            user = current_user_from_token(authorization[7:].strip())
        except HTTPException:
            await websocket.close(code=4401)
            return
        await websocket.accept()
        last_id = "$"
        try:
            while True:
                response = cast(
                    list[tuple[str, list[tuple[str, dict[str, str]]]]],
                    await asyncio.to_thread(
                        self.queue.redis.xread,
                        {self.queue.event_stream: last_id},
                        count=50,
                        block=25_000,
                    ),
                )
                if not response:
                    await websocket.send_json({"event": "heartbeat"})
                    continue
                _, messages = response[0]
                for message_id, fields in messages:
                    last_id = message_id
                    task_id = fields.get("task_id")
                    if not task_id:
                        continue
                    task = self.repository.get_any(UUID(task_id))
                    if task is None or task.owner_id != user.id:
                        continue
                    payload = {"task_id": task_id, "event": fields.get("event", "download.updated")}
                    payload.update(
                        {key: value for key, value in fields.items() if key not in {"task_id", "event", "published_at"}}
                    )
                    await websocket.send_json(payload)
        except WebSocketDisconnect:
            return
        except Exception:
            await websocket.close(code=1011)

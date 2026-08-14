from fastapi import APIRouter, WebSocket

from app.services.notification_service import NotificationService

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/downloads")
async def download_events(websocket: WebSocket) -> None:
    await NotificationService().stream_downloads(websocket)

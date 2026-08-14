from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.typing import as_http_url
from app.db import DownloadTaskModel, get_session
from app.schemas.downloads import DownloadStatus, DownloadTask, DownloadTaskCreate
from app.services.download_state_machine import require_transition


class DownloadRepository:
    def _session(self) -> Session:
        return next(get_session())

    def create(self, payload: DownloadTaskCreate, owner_id: UUID) -> DownloadTask:
        now = datetime.now(timezone.utc)
        task = DownloadTask(
            id=uuid4(),
            owner_id=owner_id,
            source_url=payload.source_url,
            platform=payload.platform,
            title=payload.title,
            format_id=payload.format_id,
            format_type=payload.format_type,
            extension=payload.extension,
            mime_type=payload.mime_type,
            quality=payload.quality,
            status=DownloadStatus.QUEUED,
            progress_percent=None,
            progress_known=False,
            bytes_downloaded=0,
            retry_count=0,
            created_at=now,
            updated_at=now,
        )
        return self.save(task, idempotency_key=None)

    def create_with_idempotency(self, payload: DownloadTaskCreate, owner_id: UUID, idempotency_key: str | None) -> DownloadTask:
        if idempotency_key:
            existing = self.get_by_idempotency(idempotency_key, owner_id)
            if existing:
                return existing
        now = datetime.now(timezone.utc)
        task = DownloadTask(
            id=uuid4(), owner_id=owner_id, source_url=payload.source_url, platform=payload.platform,
            title=payload.title, format_id=payload.format_id, format_type=payload.format_type,
            extension=payload.extension, mime_type=payload.mime_type, quality=payload.quality,
            status=DownloadStatus.QUEUED, progress_percent=0, progress_known=False,
            bytes_downloaded=0, retry_count=0, created_at=now, updated_at=now,
        )
        try:
            return self.save(task, idempotency_key=idempotency_key)
        except IntegrityError:
            existing = self.get_by_idempotency(idempotency_key, owner_id) if idempotency_key else None
            if existing:
                return existing
            raise

    def save(self, task: DownloadTask, idempotency_key: str | None = None) -> DownloadTask:
        session = self._session()
        try:
            model = session.get(DownloadTaskModel, str(task.id))
            values = {
                "id": str(task.id), "user_id": str(task.owner_id), "source_url": str(task.source_url),
                "platform": task.platform, "title": task.title, "format_id": task.format_id,
                "format_type": task.format_type, "extension": task.extension, "mime_type": task.mime_type,
                "quality": task.quality, "status": task.status.value, "progress_percent": task.progress_percent,
                "bytes_downloaded": task.bytes_downloaded, "total_bytes": task.total_bytes, "speed": task.speed,
                "eta": task.eta, "progress_known": task.progress_known, "output_path": task.output_path,
                "output_filename": task.output_filename, "error_code": task.error_code,
                "error_message": task.error_message, "created_at": task.created_at, "started_at": task.started_at,
                "completed_at": task.completed_at, "cancelled_at": task.cancelled_at,
                "updated_at": task.updated_at, "retry_count": task.retry_count,
            }
            if model is None:
                values["idempotency_key"] = idempotency_key
                session.add(DownloadTaskModel(**values))
            else:
                for key, value in values.items():
                    setattr(model, key, value)
                if idempotency_key is not None:
                    model.idempotency_key = idempotency_key
            session.commit()
            return task
        finally:
            session.close()

    def get_by_idempotency(self, idempotency_key: str, owner_id: UUID) -> DownloadTask | None:
        session = self._session()
        try:
            model = session.scalar(select(DownloadTaskModel).where(DownloadTaskModel.user_id == str(owner_id), DownloadTaskModel.idempotency_key == idempotency_key))
            return self._from_model(model) if model else None
        finally:
            session.close()

    def get(self, task_id: UUID, owner_id: UUID) -> DownloadTask | None:
        session = self._session()
        try:
            model = session.scalar(select(DownloadTaskModel).where(DownloadTaskModel.id == str(task_id), DownloadTaskModel.user_id == str(owner_id)))
            return self._from_model(model) if model else None
        finally:
            session.close()

    def get_any(self, task_id: UUID) -> DownloadTask | None:
        session = self._session()
        try:
            model = session.get(DownloadTaskModel, str(task_id))
            return self._from_model(model) if model else None
        finally:
            session.close()

    def list(self, owner_id: UUID) -> list[DownloadTask]:
        session = self._session()
        try:
            models = session.scalars(select(DownloadTaskModel).where(DownloadTaskModel.user_id == str(owner_id)).order_by(DownloadTaskModel.created_at.desc())).all()
            return [self._from_model(model) for model in models]
        finally:
            session.close()

    def update(self, task_id: UUID, **values) -> DownloadTask | None:
        session = self._session()
        try:
            model = session.get(DownloadTaskModel, str(task_id))
            if model is None:
                return None
            for key, value in values.items():
                setattr(model, key, value)
            model.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(model)
            return self._from_model(model)
        finally:
            session.close()

    def delete(self, task_id: UUID, owner_id: UUID) -> DownloadTask | None:
        session = self._session()
        try:
            model = session.scalar(select(DownloadTaskModel).where(DownloadTaskModel.id == str(task_id), DownloadTaskModel.user_id == str(owner_id)))
            if model is None:
                return None
            result = self._from_model(model)
            session.delete(model)
            session.commit()
            return result
        finally:
            session.close()

    def transition(self, task_id: UUID, target: DownloadStatus, **values) -> DownloadTask | None:
        session = self._session()
        try:
            model = session.get(DownloadTaskModel, str(task_id))
            if model is None:
                return None
            current = DownloadStatus(model.status)
            require_transition(current, target)
            model.status = target.value
            for key, value in values.items():
                setattr(model, key, value)
            model.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(model)
            return self._from_model(model)
        finally:
            session.close()

    def request_cancel(self, task_id: UUID, owner_id: UUID) -> DownloadTask | None:
        session = self._session()
        try:
            model = session.scalar(select(DownloadTaskModel).where(DownloadTaskModel.id == str(task_id), DownloadTaskModel.user_id == str(owner_id)))
            if model is None:
                return None
            now = datetime.now(timezone.utc)
            status = DownloadStatus(model.status)
            if status == DownloadStatus.QUEUED:
                target = DownloadStatus.CANCELLED
                values = {"cancelled_at": now}
            elif status in {DownloadStatus.STARTING, DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED}:
                target = DownloadStatus.CANCELLING
                values = {}
            else:
                return self._from_model(model)
            require_transition(status, target)
            model.status = target.value
            for key, value in values.items():
                setattr(model, key, value)
            model.updated_at = now
            session.commit()
            session.refresh(model)
            return self._from_model(model)
        finally:
            session.close()

    @staticmethod
    def _from_model(model: DownloadTaskModel) -> DownloadTask:
        return DownloadTask(
            id=UUID(model.id), owner_id=UUID(model.user_id),             source_url=as_http_url(model.source_url),

            platform=model.platform, title=model.title, format_id=model.format_id,
            format_type=model.format_type, extension=model.extension, mime_type=model.mime_type,
            quality=model.quality, status=DownloadStatus(model.status), progress_percent=model.progress_percent,
            bytes_downloaded=model.bytes_downloaded or 0, total_bytes=model.total_bytes, speed=model.speed,
            eta=model.eta, progress_known=model.progress_known, output_path=model.output_path,
            output_filename=model.output_filename, error_code=model.error_code, error_message=model.error_message,
            created_at=model.created_at, started_at=model.started_at, completed_at=model.completed_at,
            cancelled_at=model.cancelled_at, updated_at=model.updated_at, retry_count=model.retry_count or 0,
        )

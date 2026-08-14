from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.typing import as_http_url
from app.db import FavoriteModel, HistoryItemModel, LibraryItemModel, get_session
from app.schemas.library import LibraryItem, LibraryItemCreate


class LibraryRepository:
    def _session(self) -> Session:
        return next(get_session())

    def create(self, owner_id: UUID, payload: LibraryItemCreate) -> LibraryItem:
        now = datetime.now(timezone.utc)
        item = LibraryItem(
            id=uuid4(),
            owner_id=owner_id,
            title=payload.title,
            source_url=payload.source_url,
            media_path=payload.media_path,
            media_type=payload.media_type,
            filename=payload.filename,
            mime_type=payload.mime_type,
            file_size=payload.file_size,
            duration=payload.duration,
            thumbnail=payload.thumbnail,
            downloaded_at=now if payload.media_path else None,
            is_favorite=False,
            viewed_at=None,
            created_at=now,
        )
        session = self._session()
        try:
            session.add(
                LibraryItemModel(
                    id=str(item.id),
                    owner_id=str(item.owner_id),
                    title=item.title,
                    source_url=str(item.source_url),
                    media_path=item.media_path,
                    media_type=item.media_type,
                    filename=item.filename,
                    mime_type=item.mime_type,
                    file_size=item.file_size,
                    duration=item.duration,
                    thumbnail=item.thumbnail,
                    downloaded_at=item.downloaded_at,
                    is_favorite=False,
                    viewed_at=None,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.commit()
            return item
        finally:
            session.close()

    def list(self, owner_id: UUID, *, favorites_only: bool = False, history_only: bool = False, files_only: bool = False, search: str | None = None, sort: str = "date", descending: bool = True) -> list[LibraryItem]:
        session = self._session()
        try:
            query = select(LibraryItemModel).where(LibraryItemModel.owner_id == str(owner_id))
            if favorites_only:
                query = query.join(FavoriteModel, FavoriteModel.library_item_id == LibraryItemModel.id).where(FavoriteModel.user_id == str(owner_id))
            if history_only:
                query = query.join(HistoryItemModel, HistoryItemModel.library_item_id == LibraryItemModel.id).where(HistoryItemModel.user_id == str(owner_id))
            if files_only:
                query = query.where(LibraryItemModel.media_path.is_not(None))
            if search:
                pattern = f"%{search.strip()}%"
                query = query.where(or_(LibraryItemModel.title.ilike(pattern), LibraryItemModel.filename.ilike(pattern), LibraryItemModel.source_url.ilike(pattern)))
            sort_column = {"name": LibraryItemModel.filename, "size": LibraryItemModel.file_size, "type": LibraryItemModel.media_type, "date": LibraryItemModel.created_at}.get(sort, LibraryItemModel.created_at)
            models = session.scalars(query.order_by(sort_column.desc() if descending else sort_column.asc())).unique().all()
            favorite_ids = {
                row.library_item_id
                for row in session.scalars(select(FavoriteModel).where(FavoriteModel.user_id == str(owner_id))).all()
            }
            history_rows = session.scalars(select(HistoryItemModel).where(HistoryItemModel.user_id == str(owner_id))).all()
            history_by_item = {row.library_item_id: row.viewed_at for row in history_rows}
            return [self._from_model(model, model.id in favorite_ids, history_by_item.get(model.id)) for model in models]
        finally:
            session.close()

    def get(self, owner_id: UUID, item_id: UUID) -> LibraryItem | None:
        session = self._session()
        try:
            model = session.scalar(select(LibraryItemModel).where(LibraryItemModel.owner_id == str(owner_id), LibraryItemModel.id == str(item_id)))
            if model is None:
                return None
            favorite = session.scalar(select(FavoriteModel).where(FavoriteModel.user_id == str(owner_id), FavoriteModel.library_item_id == str(item_id)))
            history = session.scalar(select(HistoryItemModel.viewed_at).where(HistoryItemModel.user_id == str(owner_id), HistoryItemModel.library_item_id == str(item_id)))
            return self._from_model(model, favorite is not None, history)
        finally:
            session.close()

    def update_file(self, owner_id: UUID, item_id: UUID, *, media_path: str, filename: str, file_size: int, mime_type: str | None) -> LibraryItem | None:
        session = self._session()
        try:
            model = session.scalar(select(LibraryItemModel).where(LibraryItemModel.owner_id == str(owner_id), LibraryItemModel.id == str(item_id)))
            if model is None:
                return None
            model.media_path = media_path
            model.filename = filename
            model.file_size = file_size
            model.mime_type = mime_type
            model.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(model)
            return self._from_model(model)
        finally:
            session.close()

    def delete(self, owner_id: UUID, item_id: UUID) -> LibraryItem | None:
        session = self._session()
        try:
            model = session.scalar(select(LibraryItemModel).where(LibraryItemModel.owner_id == str(owner_id), LibraryItemModel.id == str(item_id)))
            if model is None:
                return None
            result = self._from_model(model)
            session.delete(model)
            session.commit()
            return result
        finally:
            session.close()

    def set_favorite(self, owner_id: UUID, item_id: UUID, favorite: bool) -> LibraryItem | None:
        session = self._session()
        try:
            model = session.scalar(select(LibraryItemModel).where(LibraryItemModel.owner_id == str(owner_id), LibraryItemModel.id == str(item_id)))
            if model is None:
                return None
            now = datetime.now(timezone.utc)
            model.is_favorite = favorite
            model.updated_at = now
            existing = session.scalar(
                select(FavoriteModel).where(FavoriteModel.user_id == str(owner_id), FavoriteModel.library_item_id == str(item_id))
            )
            if favorite and existing is None:
                session.add(FavoriteModel(id=str(uuid4()), user_id=str(owner_id), library_item_id=str(item_id), created_at=now, updated_at=now))
            elif favorite and existing is not None:
                existing.updated_at = now
            elif not favorite and existing is not None:
                session.delete(existing)
            session.commit()
            viewed = session.scalar(
                select(HistoryItemModel.viewed_at).where(HistoryItemModel.user_id == str(owner_id), HistoryItemModel.library_item_id == str(item_id))
            )
            return self._from_model(model, favorite, viewed)
        finally:
            session.close()

    def mark_viewed(self, owner_id: UUID, item_id: UUID) -> LibraryItem | None:
        session = self._session()
        try:
            model = session.scalar(select(LibraryItemModel).where(LibraryItemModel.owner_id == str(owner_id), LibraryItemModel.id == str(item_id)))
            if model is None:
                return None
            now = datetime.now(timezone.utc)
            model.viewed_at = now
            model.updated_at = now
            history = session.scalar(
                select(HistoryItemModel).where(HistoryItemModel.user_id == str(owner_id), HistoryItemModel.library_item_id == str(item_id))
            )
            if history is None:
                session.add(HistoryItemModel(id=str(uuid4()), user_id=str(owner_id), library_item_id=str(item_id), viewed_at=now, created_at=now, updated_at=now))
            else:
                history.viewed_at = now
                history.updated_at = now
            favorite = session.scalar(
                select(FavoriteModel).where(FavoriteModel.user_id == str(owner_id), FavoriteModel.library_item_id == str(item_id))
            )
            session.commit()
            return self._from_model(model, favorite is not None, now)
        finally:
            session.close()

    @staticmethod
    def _from_model(model: LibraryItemModel, is_favorite: bool = False, viewed_at: datetime | None = None) -> LibraryItem:
        return LibraryItem(
            id=UUID(model.id),
            owner_id=UUID(model.owner_id),
            title=model.title,
            source_url=as_http_url(model.source_url),
            media_path=model.media_path,
            media_type=model.media_type,
            filename=model.filename,
            mime_type=model.mime_type,
            file_size=model.file_size,
            duration=model.duration,
            thumbnail=model.thumbnail,
            downloaded_at=model.downloaded_at,
            is_favorite=is_favorite,
            viewed_at=viewed_at,
            created_at=model.created_at,
        )

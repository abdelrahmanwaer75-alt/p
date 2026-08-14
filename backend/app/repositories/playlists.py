from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import LibraryItemModel, PlaylistItemModel, PlaylistModel, get_session
from app.schemas.playlists import Playlist, PlaylistItem, PlaylistCreate, PlaylistItemCreate, PlaylistUpdate


class PlaylistRepository:
    def _session(self) -> Session:
        return next(get_session())

    def list(self, user_id: UUID) -> list[Playlist]:
        session = self._session()
        try:
            models = session.scalars(select(PlaylistModel).where(PlaylistModel.user_id == str(user_id)).order_by(PlaylistModel.updated_at.desc())).all()
            return [self._playlist(session, model) for model in models]
        finally:
            session.close()

    def get(self, user_id: UUID, playlist_id: UUID) -> Playlist | None:
        session = self._session()
        try:
            model = session.scalar(select(PlaylistModel).where(PlaylistModel.id == str(playlist_id), PlaylistModel.user_id == str(user_id)))
            return self._playlist(session, model) if model else None
        finally:
            session.close()

    def create(self, user_id: UUID, payload: PlaylistCreate) -> Playlist:
        now = datetime.now(timezone.utc)
        model = PlaylistModel(id=str(uuid4()), user_id=str(user_id), name=payload.name.strip(), description=payload.description, created_at=now, updated_at=now)
        session = self._session()
        try:
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._playlist(session, model)
        finally:
            session.close()

    def update(self, user_id: UUID, playlist_id: UUID, payload: PlaylistUpdate) -> Playlist | None:
        session = self._session()
        try:
            model = session.scalar(select(PlaylistModel).where(PlaylistModel.id == str(playlist_id), PlaylistModel.user_id == str(user_id)))
            if not model:
                return None
            if payload.name is not None:
                model.name = payload.name.strip()
            if payload.description is not None:
                model.description = payload.description
            model.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(model)
            return self._playlist(session, model)
        finally:
            session.close()

    def delete(self, user_id: UUID, playlist_id: UUID) -> Playlist | None:
        session = self._session()
        try:
            model = session.scalar(select(PlaylistModel).where(PlaylistModel.id == str(playlist_id), PlaylistModel.user_id == str(user_id)))
            if not model:
                return None
            result = self._playlist(session, model)
            session.delete(model)
            session.commit()
            return result
        finally:
            session.close()

    def add_item(self, user_id: UUID, playlist_id: UUID, payload: PlaylistItemCreate) -> Playlist | None:
        session = self._session()
        try:
            playlist = session.scalar(select(PlaylistModel).where(PlaylistModel.id == str(playlist_id), PlaylistModel.user_id == str(user_id)))
            library = session.scalar(select(LibraryItemModel).where(LibraryItemModel.id == str(payload.library_item_id), LibraryItemModel.owner_id == str(user_id)))
            if not playlist or not library:
                return None
            existing = session.scalar(select(PlaylistItemModel).where(PlaylistItemModel.playlist_id == playlist.id, PlaylistItemModel.library_item_id == library.id))
            if existing:
                return self._playlist(session, playlist)
            max_position = session.scalar(select(PlaylistItemModel.position).where(PlaylistItemModel.playlist_id == playlist.id).order_by(PlaylistItemModel.position.desc()).limit(1))
            position = payload.position if payload.position is not None else ((max_position or -1) + 1)
            if payload.position is not None:
                session.query(PlaylistItemModel).filter(PlaylistItemModel.playlist_id == playlist.id, PlaylistItemModel.position >= position).update({PlaylistItemModel.position: PlaylistItemModel.position + 1}, synchronize_session=False)
            now = datetime.now(timezone.utc)
            session.add(PlaylistItemModel(id=str(uuid4()), playlist_id=playlist.id, library_item_id=library.id, position=position, created_at=now, updated_at=now))
            playlist.updated_at = now
            session.commit()
            return self._playlist(session, playlist)
        finally:
            session.close()

    def remove_item(self, user_id: UUID, playlist_id: UUID, item_id: UUID) -> Playlist | None:
        session = self._session()
        try:
            playlist = session.scalar(select(PlaylistModel).where(PlaylistModel.id == str(playlist_id), PlaylistModel.user_id == str(user_id)))
            item = session.scalar(select(PlaylistItemModel).where(PlaylistItemModel.id == str(item_id), PlaylistItemModel.playlist_id == str(playlist_id)))
            if not playlist or not item:
                return None
            removed_position = item.position
            session.delete(item)
            session.query(PlaylistItemModel).filter(PlaylistItemModel.playlist_id == str(playlist_id), PlaylistItemModel.position > removed_position).update({PlaylistItemModel.position: PlaylistItemModel.position - 1}, synchronize_session=False)
            playlist.updated_at = datetime.now(timezone.utc)
            session.commit()
            return self._playlist(session, playlist)
        finally:
            session.close()

    def reorder(self, user_id: UUID, playlist_id: UUID, item_ids: list[UUID]) -> Playlist | None:
        session = self._session()
        try:
            playlist = session.scalar(select(PlaylistModel).where(PlaylistModel.id == str(playlist_id), PlaylistModel.user_id == str(user_id)))
            items = session.scalars(select(PlaylistItemModel).where(PlaylistItemModel.playlist_id == str(playlist_id)).order_by(PlaylistItemModel.position.asc())).all()
            if not playlist or {UUID(item.id) for item in items} != set(item_ids) or len(item_ids) != len(items):
                return None
            by_id = {item.id: item for item in items}
            for position, item_id in enumerate(item_ids):
                by_id[str(item_id)].position = position
                by_id[str(item_id)].updated_at = datetime.now(timezone.utc)
            playlist.updated_at = datetime.now(timezone.utc)
            session.commit()
            return self._playlist(session, playlist)
        finally:
            session.close()

    def _playlist(self, session: Session, model: PlaylistModel) -> Playlist:
        rows = session.execute(select(PlaylistItemModel, LibraryItemModel).join(LibraryItemModel, LibraryItemModel.id == PlaylistItemModel.library_item_id).where(PlaylistItemModel.playlist_id == model.id).order_by(PlaylistItemModel.position.asc())).all()
        return Playlist(id=UUID(model.id), user_id=UUID(model.user_id), name=model.name, description=model.description, items=[self._item(item, library) for item, library in rows], created_at=model.created_at, updated_at=model.updated_at)

    @staticmethod
    def _item(item: PlaylistItemModel, library: LibraryItemModel) -> PlaylistItem:
        return PlaylistItem(id=UUID(item.id), playlist_id=UUID(item.playlist_id), library_item_id=UUID(item.library_item_id), position=item.position, title=library.title, filename=library.filename, media_path=library.media_path, media_type=library.media_type, mime_type=library.mime_type, duration=library.duration, thumbnail=library.thumbnail, created_at=item.created_at)

from collections.abc import Generator

from sqlalchemy.orm import Session

from .session import get_session


def get_db() -> Generator[Session, None, None]:
    yield from get_session()


__all__ = ["get_db"]

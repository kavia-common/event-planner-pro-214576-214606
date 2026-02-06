from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.core.config import get_settings


def _normalize_postgres_url(url: str) -> str:
    """Ensure POSTGRES_URL is SQLAlchemy-psycopg compatible."""
    if url.startswith("postgresql+psycopg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    # Allow users to provide full SQLAlchemy URL; otherwise it will fail loudly.
    return url


def get_engine() -> Engine:
    """Create the SQLAlchemy Engine (singleton-ish; module-level call site uses caching)."""
    settings = get_settings()
    if not settings.postgres_url:
        raise RuntimeError(
            "POSTGRES_URL env var is required. "
            "It should match event_database/db_connection.txt (converted to SQLAlchemy form)."
        )
    return create_engine(_normalize_postgres_url(settings.postgres_url), pool_pre_ping=True)


_ENGINE = None
_SessionLocal = None


def _init_once() -> None:
    global _ENGINE, _SessionLocal
    if _ENGINE is None:
        _ENGINE = get_engine()
        _SessionLocal = sessionmaker(bind=_ENGINE, autocommit=False, autoflush=False)


# PUBLIC_INTERFACE
@contextmanager
def db_session() -> Session:
    """Provide a transactional scope around a series of operations."""
    _init_once()
    assert _SessionLocal is not None
    db: Session = _SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

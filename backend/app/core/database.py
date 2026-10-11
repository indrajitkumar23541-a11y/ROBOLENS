import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def init_engine():
    """
    Initialize primary database engine with automatic fallback
    to SQLite in local development if PostgreSQL is unreachable.
    """
    db_url = settings.DATABASE_URL
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    try:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            connect_args=connect_args
        )
        # Attempt lightweight probe
        with engine.connect():
            pass
        return engine
    except Exception as e:
        logger.warning(
            f"Could not connect to configured database ({db_url}). "
            f"Falling back to local SQLite './robolens.db' for development: {e}"
        )
        return create_engine(
            "sqlite:///./robolens.db",
            pool_pre_ping=True,
            connect_args={"check_same_thread": False}
        )


engine = init_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """Dependency for providing database sessions per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

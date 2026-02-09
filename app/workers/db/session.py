# app/workers/db/session.py
import os
from typing import AsyncGenerator, Tuple

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ==================================================
# Internal helpers
# ==================================================

def _get_database_url() -> str:
    """
    Read DATABASE_URL at runtime (Lambda-safe).
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")
    return db_url


# ==================================================
# API / FastAPI (GLOBAL, REUSED)
# ==================================================

_engine = None
_SessionLocal = None


def get_api_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """
    Lazily initialize ONE engine + sessionmaker.
    Reused across requests (correct for FastAPI + Lambda).
    """
    global _engine, _SessionLocal

    if _engine is None:
        _engine = create_async_engine(
            _get_database_url(),
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=0,
            future=True,
        )

        _SessionLocal = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _SessionLocal


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency.
    """
    SessionLocal = get_api_sessionmaker()
    async with SessionLocal() as session:
        yield session


# ==================================================
# Workers / SQS / Jobs (PER INVOCATION)
# ==================================================

def create_worker_session_factory() -> Tuple:
    """
    Create a NEW engine + sessionmaker for a worker invocation.
    Worker Lambdas MUST close engines.
    """
    engine = create_async_engine(
        _get_database_url(),
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=0,
        future=True,
    )

    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    return engine, SessionLocal

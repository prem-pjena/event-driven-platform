# app/workers/db/session.py
import os
from typing import Tuple

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)


# ==================================================
# INTERNAL: read env ONLY when called
# ==================================================
def _get_database_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")
    return db_url


# ==================================================
# API / FastAPI (lazy, safe)
# ==================================================
def get_api_sessionmaker():
    """
    Lazily creates engine + sessionmaker.
    SAFE for Lambda import phase.
    """
    DATABASE_URL = _get_database_url()

    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=0,
        future=True,
    )

    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


# ==================================================
# Workers / SQS / Jobs (PER INVOCATION)
# ==================================================
def create_session_factory() -> Tuple:
    """
    Creates a NEW async engine + sessionmaker
    bound to the CURRENT invocation.
    """
    DATABASE_URL = _get_database_url()

    engine = create_async_engine(
        DATABASE_URL,
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

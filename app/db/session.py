import os
from typing import Tuple

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

# --------------------------------------------------
# Database URL
# --------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# ==================================================
# API / FastAPI (GLOBAL ENGINE — SAFE)
# ==================================================
_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=0,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ==================================================
# Lambda / Workers (PER INVOCATION)
# ==================================================
def create_session_factory() -> Tuple:
    """
    Creates a NEW async engine + sessionmaker
    bound to the CURRENT asyncio event loop.
    """

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

# app/db/session.py
import os
import ssl
from typing import AsyncGenerator, Tuple

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ==================================================
# SSL CONTEXT (RDS / AURORA)
# ==================================================
_ssl_context = ssl.create_default_context()
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE


def _get_database_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")
    return db_url


# ==================================================
# API ENGINE (GLOBAL, REUSED ACROSS INVOCATIONS)
# ==================================================
_engine = None
_SessionLocal = None


def _get_api_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _engine, _SessionLocal

    if _engine is None:
        _engine = create_async_engine(
            _get_database_url(),
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=0,
            connect_args={"ssl": _ssl_context},
        )

        _SessionLocal = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _SessionLocal


# ==================================================
# ✅ FASTAPI DEPENDENCY (ONLY THING API IMPORTS)
# ==================================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    SessionLocal = _get_api_sessionmaker()
    async with SessionLocal() as session:
        yield session


# ==================================================
# WORKER SESSION FACTORY (PER INVOCATION)
# ==================================================
def create_worker_session_factory() -> Tuple:
    engine = create_async_engine(
        _get_database_url(),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=0,
        connect_args={"ssl": _ssl_context},
    )

    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    return engine, SessionLocal

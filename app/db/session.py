import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# --------------------------------------------------
# Database URL (from env / Secrets Manager)
# --------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# --------------------------------------------------
# Async SQLAlchemy Engine (Lambda-safe)
# --------------------------------------------------
engine = create_async_engine(
    DATABASE_URL,
    echo=False,                  # NEVER echo SQL in production
    pool_pre_ping=True,          # detects stale connections
    pool_size=5,                 # conservative for Lambda
    max_overflow=0,              # prevents connection storms
    future=True,
)

# --------------------------------------------------
# Async Session Factory
# --------------------------------------------------
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

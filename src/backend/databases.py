from fastapi import HTTPException 
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Text, DateTime, inspect
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL Async Engine Configuration
DATABASE_URL = os.getenv("PostgreSQL_URL")

# Monkeypatch asyncpg to use unnamed prepared statements
# This is required for transaction pooling with pgbouncer
def _get_unique_id(self, prefix):
    return ""

asyncpg.connection.Connection._get_unique_id = _get_unique_id

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
    connect_args={
        "statement_cache_size": 0
    }
)

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Create the tables
async def create_tables():
    async with engine.begin() as conn:
        result = await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table('users'))
        if not result:
            await conn.run_sync(lambda sync_conn: Base.metadata.create_all(bind=sync_conn))

# Dependency to get DB session
async def get_db():
    try:
        async with AsyncSessionLocal() as session:
            yield session
    except asyncpg.InvalidPasswordError:
        raise HTTPException(status_code=500, detail="Database authentication failed. Please check credentials.")
    except asyncpg.CannotConnectNowError:
        raise HTTPException(status_code=503, detail="Database server is down. Try again later.")
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

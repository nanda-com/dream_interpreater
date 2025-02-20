from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL Async Engine Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True
)

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

class DreamEntry(Base):
    __tablename__ = 'dream_entries'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    interpretation = Column(Text)
    emotion_tags = Column(String)
    image_url = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

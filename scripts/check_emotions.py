"""
Check emotion tags on dreams
"""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.backend.models.dreamentry import DreamEntry
from src.backend.models.dream_vector import DreamVector  # Import to resolve relationship
import os
from dotenv import load_dotenv

load_dotenv()

async def check_emotions():
    engine = create_async_engine(os.getenv('PostgreSQL_URL'))
    async_session = sessionmaker(engine, class_=AsyncSession)
    async with async_session() as db:
        result = await db.execute(select(DreamEntry).where(DreamEntry.user_id == 1))
        print("Dream Emotion Tags:")
        print("=" * 60)
        for d in result.scalars():
            print(f'\nDream {d.id}: {d.title}')
            print(f'  Description: {d.description[:50]}')
            print(f'  Emotion tags: {d.emotion_tags if d.emotion_tags else "(none)"}')
    await engine.dispose()

asyncio.run(check_emotions())

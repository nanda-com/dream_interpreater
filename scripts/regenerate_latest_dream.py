"""
Regenerate embedding for the latest dream to test 6x emotion weighting
"""
import asyncio
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from src.backend.models.dreamentry import DreamEntry
from src.backend.models.dream_vector import DreamVector
from src.backend.services.dream_embedding_service import get_embedding_service

load_dotenv()


async def regenerate_latest(user_id: int):
    """Regenerate embedding for latest dream"""

    database_url = os.getenv("PostgreSQL_URL")
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Get latest dream
        result = await db.execute(
            select(DreamEntry)
            .where(DreamEntry.user_id == user_id)
            .order_by(DreamEntry.id.desc())
            .limit(1)
        )
        dream = result.scalar_one_or_none()

        if not dream:
            print("No dreams found!")
            return

        print(f"Regenerating embedding for Dream {dream.id}: '{dream.title}'")
        print(f"Emotion tags: {dream.emotion_tags}")

        # Regenerate embedding
        embedding_service = get_embedding_service()
        await embedding_service.embed_dream_entry(db, dream)

        print(f"✓ Embedding regenerated with 6x emotion weighting!")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python regenerate_latest_dream.py <user_id>")
        sys.exit(1)

    user_id = int(sys.argv[1])
    asyncio.run(regenerate_latest(user_id))

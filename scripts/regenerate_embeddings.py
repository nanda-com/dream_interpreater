"""
Regenerate all dream embeddings with the new weighted strategy
"""
import asyncio
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from src.backend.models.dreamentry import DreamEntry
from src.backend.services.dream_embedding_service import get_embedding_service

load_dotenv()


async def regenerate_all_embeddings(user_id: int = None):
    """Regenerate embeddings for all dreams (or specific user)"""

    database_url = os.getenv("PostgreSQL_URL")
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("=" * 60)
        print("REGENERATING EMBEDDINGS WITH NEW WEIGHTED STRATEGY")
        print("=" * 60)

        # Build query
        query = select(DreamEntry)
        if user_id:
            query = query.where(DreamEntry.user_id == user_id)

        result = await db.execute(query)
        dreams = result.scalars().all()

        print(f"\nFound {len(dreams)} dreams to process")

        embedding_service = get_embedding_service()

        success_count = 0
        error_count = 0

        for i, dream in enumerate(dreams, 1):
            try:
                print(f"\n[{i}/{len(dreams)}] Dream {dream.id}: '{dream.title}'")
                print(f"  Description: {dream.description[:50]}...")

                # Generate new embedding with weighted strategy
                await embedding_service.embed_dream_entry(db, dream)

                print(f"  ✓ Embedding regenerated successfully")
                success_count += 1

            except Exception as e:
                print(f"  ✗ Error: {e}")
                error_count += 1

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"✓ Successfully regenerated: {success_count}")
        print(f"✗ Errors: {error_count}")
        print(f"Total processed: {len(dreams)}")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    user_id = None
    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
        print(f"Regenerating embeddings for user {user_id} only")
    else:
        print("Regenerating embeddings for ALL users")

    asyncio.run(regenerate_all_embeddings(user_id))

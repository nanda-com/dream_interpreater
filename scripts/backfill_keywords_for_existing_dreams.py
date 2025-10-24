"""
Backfill keywords for existing dreams that don't have them
"""
import asyncio
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from loguru import logger

from src.backend.models.dreamentry import DreamEntry
from src.backend.models.dream_vector import DreamVector
from src.backend.ai_interpreters.gemini_interpreter import GeminiDreamInterpreter
from src.backend.services.dream_embedding_service import get_embedding_service

load_dotenv()


async def backfill_keywords(user_id: int = None):
    """Extract and store keywords for existing dreams"""

    database_url = os.getenv("PostgreSQL_URL")
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("=" * 60)
        print("BACKFILLING KEYWORDS FOR EXISTING DREAMS")
        print("=" * 60)

        # Build query for dreams without keywords
        query = select(DreamEntry).where(
            (DreamEntry.keywords == None) | (DreamEntry.keywords == [])
        )
        if user_id:
            query = query.where(DreamEntry.user_id == user_id)

        result = await db.execute(query)
        dreams = result.scalars().all()

        if not dreams:
            print("\n✓ All dreams already have keywords!")
            return

        print(f"\nFound {len(dreams)} dreams without keywords")

        # Initialize services
        interpreter = GeminiDreamInterpreter()
        embedding_service = get_embedding_service()

        success_count = 0
        error_count = 0

        for i, dream in enumerate(dreams, 1):
            try:
                print(f"\n[{i}/{len(dreams)}] Processing Dream {dream.id}: '{dream.title}'")
                print(f"  Description: {dream.description[:50]}...")

                # Use the interpreter to extract keywords
                _, _, _, keywords = interpreter.interpret_dream(
                    description=dream.description,
                    title=dream.title
                )

                if keywords:
                    # Update dream with keywords
                    dream.keywords = keywords
                    await db.commit()
                    await db.refresh(dream)

                    print(f"  ✓ Extracted keywords: {keywords}")

                    # Regenerate embedding with keywords
                    try:
                        await embedding_service.embed_dream_entry(db, dream, keywords=keywords)
                        print(f"  ✓ Updated embedding")
                    except Exception as embed_error:
                        logger.error(f"Failed to update embedding: {embed_error}")
                        print(f"  ⚠ Warning: Embedding update failed (dream saved with keywords)")

                    success_count += 1
                else:
                    print(f"  ⚠ No keywords extracted")
                    error_count += 1

            except Exception as e:
                print(f"  ✗ Error: {e}")
                logger.error(f"Error processing dream {dream.id}: {e}")
                error_count += 1

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"✓ Successfully processed: {success_count}")
        print(f"✗ Errors/Skipped: {error_count}")
        print(f"Total: {len(dreams)}")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    user_id = None
    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
        print(f"Backfilling keywords for user {user_id} only\n")
    else:
        print("Backfilling keywords for ALL users\n")

    asyncio.run(backfill_keywords(user_id))

"""
Diagnostic script to debug Dream Explorer issues
Checks if embeddings exist and tests similarity scores
"""
import asyncio
import os
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from src.backend.models.dreamentry import DreamEntry
from src.backend.models.dream_vector import DreamVector
from src.backend.services.dream_embedding_service import get_embedding_service
from src.backend.services.dream_retrieval_service import get_retrieval_service

load_dotenv()


async def diagnose_dream_explorer(user_id: int):
    """Run diagnostics for dream explorer functionality"""

    # Create database connection
    database_url = os.getenv("PostgreSQL_URL")
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("=" * 60)
        print("DREAM EXPLORER DIAGNOSTICS")
        print("=" * 60)

        # 1. Check if user has dreams
        result = await db.execute(
            select(DreamEntry).where(DreamEntry.user_id == user_id)
        )
        dreams = result.scalars().all()
        print(f"\n✓ Found {len(dreams)} dream entries for user {user_id}")

        if dreams:
            for i, dream in enumerate(dreams, 1):
                print(f"  {i}. Dream ID {dream.id}: '{dream.title}' ({len(dream.description)} chars)")

        # 2. Check if embeddings exist
        result = await db.execute(
            select(DreamVector).where(DreamVector.user_id == user_id)
        )
        vectors = result.scalars().all()
        print(f"\n✓ Found {len(vectors)} embeddings for user {user_id}")

        if len(dreams) != len(vectors):
            print(f"  ⚠️  WARNING: {len(dreams)} dreams but only {len(vectors)} embeddings!")
            print("  Missing embeddings for dreams:")
            dream_ids_with_embeddings = {v.dream_id for v in vectors}
            for dream in dreams:
                if dream.id not in dream_ids_with_embeddings:
                    print(f"    - Dream ID {dream.id}: '{dream.title}'")

        # 3. Check pgvector extension
        try:
            result = await db.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            extension = result.fetchone()
            if extension:
                print("\n✓ pgvector extension is installed")
            else:
                print("\n✗ pgvector extension is NOT installed!")
        except Exception as e:
            print(f"\n✗ Error checking pgvector: {e}")

        # 4. Test semantic search with different thresholds
        if vectors:
            print("\n" + "=" * 60)
            print("TESTING SEMANTIC SEARCH")
            print("=" * 60)

            test_query = "What emotions appear most in my dreams?"
            print(f"\nQuery: '{test_query}'")

            retrieval_service = get_retrieval_service()

            # Test with very low threshold
            for threshold in [0.0, 0.3, 0.6]:
                print(f"\n--- Testing with threshold={threshold} ---")
                try:
                    results = await retrieval_service.search_similar_dreams(
                        db=db,
                        user_id=user_id,
                        query=test_query,
                        top_k=10,
                        min_similarity=threshold
                    )
                    print(f"Found {len(results)} dreams:")
                    for dream, score in results:
                        print(f"  - Score {score:.3f}: Dream {dream.id} - '{dream.title}'")
                except Exception as e:
                    print(f"  Error: {e}")

        # 5. Generate missing embeddings
        if len(dreams) > len(vectors):
            print("\n" + "=" * 60)
            print("FIXING MISSING EMBEDDINGS")
            print("=" * 60)

            embedding_service = get_embedding_service()
            dream_ids_with_embeddings = {v.dream_id for v in vectors}

            for dream in dreams:
                if dream.id not in dream_ids_with_embeddings:
                    try:
                        print(f"\nGenerating embedding for Dream {dream.id}: '{dream.title}'...")
                        await embedding_service.embed_dream_entry(db, dream)
                        print(f"  ✓ Success!")
                    except Exception as e:
                        print(f"  ✗ Failed: {e}")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python debug_dream_explorer.py <user_id>")
        print("Example: python debug_dream_explorer.py 1")
        sys.exit(1)

    user_id = int(sys.argv[1])
    asyncio.run(diagnose_dream_explorer(user_id))

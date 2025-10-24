"""
Test script for the 3-level fallback search system
"""
import asyncio
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from loguru import logger

from src.backend.models.dreamentry import DreamEntry
from src.backend.services.dream_retrieval_service import get_retrieval_service

load_dotenv()


async def test_text_search():
    """Test the text search fallback functionality"""

    database_url = os.getenv("PostgreSQL_URL")
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("=" * 60)
        print("TESTING TEXT SEARCH FALLBACK")
        print("=" * 60)

        # Get a user with dreams
        result = await db.execute(
            select(DreamEntry)
            .limit(1)
        )
        sample_dream = result.scalar_one_or_none()

        if not sample_dream:
            print("\n✗ No dreams found in database. Please add some dreams first.")
            return

        user_id = sample_dream.user_id
        print(f"\nTesting with user_id: {user_id}")

        # Get the retrieval service
        retrieval_service = get_retrieval_service()

        # Test 1: Text search with a common word that should be in descriptions
        print("\n" + "-" * 60)
        print("TEST 1: Text search for common word")
        print("-" * 60)

        # Use a word from the sample dream's description
        test_word = sample_dream.description.split()[0] if sample_dream.description else "dream"
        print(f"Query: 'Did I {test_word}?'")

        try:
            results = await retrieval_service.search_by_text(
                db=db,
                user_id=user_id,
                query=f"Did I {test_word}?",
                top_k=5,
                semantic_rerank=True
            )

            print(f"\n✓ Found {len(results)} dreams")
            for i, (dream, score) in enumerate(results, 1):
                print(f"\n  Dream {i}:")
                print(f"    Title: {dream.title}")
                print(f"    Score: {score:.4f}")
                print(f"    Description: {dream.description[:100]}...")

        except Exception as e:
            print(f"\n✗ Error: {e}")

        # Test 2: Text search without semantic re-ranking
        print("\n" + "-" * 60)
        print("TEST 2: Text search without semantic re-ranking")
        print("-" * 60)

        try:
            results = await retrieval_service.search_by_text(
                db=db,
                user_id=user_id,
                query=f"Did I {test_word}?",
                top_k=5,
                semantic_rerank=False
            )

            print(f"\n✓ Found {len(results)} dreams (text scores only)")
            for i, (dream, score) in enumerate(results, 1):
                print(f"  {i}. {dream.title} - Score: {score:.4f}")

        except Exception as e:
            print(f"\n✗ Error: {e}")

        # Test 3: Test with a query that should trigger fallbacks
        print("\n" + "-" * 60)
        print("TEST 3: Testing fallback chain")
        print("-" * 60)
        print("Query: 'xyz123nonexistent'")

        try:
            # Try semantic search
            semantic_results = await retrieval_service.search_similar_dreams(
                db=db,
                user_id=user_id,
                query="xyz123nonexistent",
                top_k=5,
                min_similarity=0.5
            )
            print(f"  Semantic search: {len(semantic_results)} results")

            # Try keyword search
            keyword_results = await retrieval_service.search_by_keywords(
                db=db,
                user_id=user_id,
                query="xyz123nonexistent",
                top_k=5
            )
            print(f"  Keyword search: {len(keyword_results)} results")

            # Try text search
            text_results = await retrieval_service.search_by_text(
                db=db,
                user_id=user_id,
                query="xyz123nonexistent",
                top_k=5
            )
            print(f"  Text search: {len(text_results)} results")

        except Exception as e:
            print(f"\n✗ Error: {e}")

        print("\n" + "=" * 60)
        print("TESTS COMPLETE")
        print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_text_search())

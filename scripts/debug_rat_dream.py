"""
Targeted diagnostic for the rat dream issue
"""
import asyncio
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import numpy as np

from src.backend.models.dreamentry import DreamEntry
from src.backend.models.dream_vector import DreamVector
from src.backend.services.dream_embedding_service import get_embedding_service

load_dotenv()


async def diagnose_rat_dream(user_id: int):
    """Check why 'rat' dream isn't found by 'rats' query"""

    database_url = os.getenv("PostgreSQL_URL")
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("=" * 60)
        print("RAT DREAM DIAGNOSTIC")
        print("=" * 60)

        # Find all dreams for this user
        result = await db.execute(
            select(DreamEntry).where(DreamEntry.user_id == user_id)
        )
        dreams = result.scalars().all()

        # Find the rat dream
        rat_dream = None
        for dream in dreams:
            if 'rat' in dream.description.lower():
                rat_dream = dream
                break

        if not rat_dream:
            print("\n✗ No dream with 'rat' in description found!")
            print("\nAll dreams:")
            for d in dreams:
                print(f"  Dream {d.id}: '{d.title}'")
                print(f"    Description: {d.description[:100]}")
            return

        print(f"\n✓ Found rat dream:")
        print(f"  Dream ID: {rat_dream.id}")
        print(f"  Title: {rat_dream.title}")
        print(f"  Description: {rat_dream.description}")
        print(f"  Interpretation: {rat_dream.interpretation}")

        # Check if it has an embedding
        result = await db.execute(
            select(DreamVector).where(DreamVector.dream_id == rat_dream.id)
        )
        dream_vector = result.scalar_one_or_none()

        if not dream_vector:
            print("\n✗ NO EMBEDDING EXISTS FOR THIS DREAM!")
            print("  This is why it's not being found in semantic search.")
            print("\n  Generating embedding now...")

            embedding_service = get_embedding_service()
            try:
                await embedding_service.embed_dream_entry(db, rat_dream)
                print("  ✓ Embedding generated successfully!")

                # Fetch the newly created embedding
                result = await db.execute(
                    select(DreamVector).where(DreamVector.dream_id == rat_dream.id)
                )
                dream_vector = result.scalar_one_or_none()
            except Exception as e:
                print(f"  ✗ Failed to generate embedding: {e}")
                return
        else:
            print(f"\n✓ Embedding exists (ID: {dream_vector.id})")

        # Now test semantic similarity with different queries
        print("\n" + "=" * 60)
        print("SEMANTIC SIMILARITY TESTS")
        print("=" * 60)

        embedding_service = get_embedding_service()

        # Get the dream's embedding
        dream_embedding = np.array(dream_vector.embedding)

        test_queries = [
            "did i dream about rats?",
            "rat",
            "rats",
            "rodent",
            "mouse",
            "i saw rat",
            "emotions",
            "flying"
        ]

        print(f"\nDream text for embedding:")
        dream_text = embedding_service.prepare_dream_text(
            rat_dream.title,
            rat_dream.description,
            rat_dream.interpretation
        )
        print(f"  {dream_text[:200]}...")

        for query in test_queries:
            query_embedding = np.array(embedding_service.generate_embedding(query))

            # Calculate cosine similarity manually
            cosine_sim = np.dot(dream_embedding, query_embedding) / (
                np.linalg.norm(dream_embedding) * np.linalg.norm(query_embedding)
            )

            # Also calculate distance (1 - similarity)
            distance = 1 - cosine_sim

            print(f"\nQuery: '{query}'")
            print(f"  Cosine Similarity: {cosine_sim:.4f}")
            print(f"  Distance: {distance:.4f}")
            print(f"  Above threshold 0.6? {cosine_sim >= 0.6}")
            print(f"  Above threshold 0.3? {cosine_sim >= 0.3}")

        # Test the actual retrieval service
        print("\n" + "=" * 60)
        print("ACTUAL RETRIEVAL SERVICE TEST")
        print("=" * 60)

        from src.backend.services.dream_retrieval_service import get_retrieval_service

        retrieval_service = get_retrieval_service()

        for threshold in [0.0, 0.3, 0.6]:
            print(f"\n--- Searching with threshold={threshold} ---")
            results = await retrieval_service.search_similar_dreams(
                db=db,
                user_id=user_id,
                query="did i dream about rats?",
                top_k=10,
                min_similarity=threshold
            )

            print(f"Found {len(results)} dreams")
            for dream, score in results:
                rat_marker = " ← RAT DREAM!" if dream.id == rat_dream.id else ""
                print(f"  Score {score:.4f}: Dream {dream.id} - '{dream.title}'{rat_marker}")

            if rat_dream.id not in [d.id for d, _ in results]:
                print(f"  ✗ Rat dream (ID {rat_dream.id}) NOT in results!")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python debug_rat_dream.py <user_id>")
        sys.exit(1)

    user_id = int(sys.argv[1])
    asyncio.run(diagnose_rat_dream(user_id))

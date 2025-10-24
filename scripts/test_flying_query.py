"""
Test why "flying" query doesn't find the flying dream
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
from src.backend.services.dream_retrieval_service import get_retrieval_service

load_dotenv()


async def test_flying_query(user_id: int):
    """Test flying query similarity"""

    database_url = os.getenv("PostgreSQL_URL")
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("=" * 60)
        print("TESTING FLYING QUERY")
        print("=" * 60)

        # Get all dreams for this user
        result = await db.execute(
            select(DreamEntry)
            .where(DreamEntry.user_id == user_id)
            .order_by(DreamEntry.id.desc())
        )
        dreams = result.scalars().all()

        print(f"\nUser has {len(dreams)} dreams:")
        for dream in dreams:
            print(f"  Dream {dream.id}: '{dream.title}' - {dream.description[:50]}")

        # Find the flying dream
        flying_dream = None
        for dream in dreams:
            if 'flying' in dream.description.lower():
                flying_dream = dream
                break

        if not flying_dream:
            print("\n✗ No dream with 'flying' found!")
            return

        print(f"\n✓ Found flying dream:")
        print(f"  ID: {flying_dream.id}")
        print(f"  Title: {flying_dream.title}")
        print(f"  Description: {flying_dream.description}")
        print(f"  Emotions: {flying_dream.emotion_tags}")

        # Test similarity
        embedding_service = get_embedding_service()

        # Get dream embedding
        result = await db.execute(
            select(DreamVector).where(DreamVector.dream_id == flying_dream.id)
        )
        dream_vector = result.scalar_one_or_none()

        if not dream_vector:
            print("\n✗ No embedding found!")
            return

        dream_embedding = np.array(dream_vector.embedding)

        # Test queries
        test_queries = [
            "did i dream about flying",
            "flying",
            "flying over mountains",
            "flight dreams",
            "soaring through the sky"
        ]

        print("\n" + "=" * 60)
        print("SEMANTIC SIMILARITY SCORES")
        print("=" * 60)

        for query in test_queries:
            query_embedding = np.array(embedding_service.generate_embedding(query))

            cosine_sim = np.dot(dream_embedding, query_embedding) / (
                np.linalg.norm(dream_embedding) * np.linalg.norm(query_embedding)
            )

            print(f"\nQuery: '{query}'")
            print(f"  Similarity: {cosine_sim:.4f}")
            print(f"  Above 0.5 threshold? {cosine_sim >= 0.5}")

        # Test actual retrieval service
        print("\n" + "=" * 60)
        print("ACTUAL RETRIEVAL SERVICE TEST")
        print("=" * 60)

        retrieval_service = get_retrieval_service()

        for query in ["did i dream about flying", "flying"]:
            print(f"\nQuery: '{query}'")
            results = await retrieval_service.search_similar_dreams(
                db=db,
                user_id=user_id,
                query=query,
                top_k=10,
                min_similarity=0.5
            )

            print(f"Found {len(results)} dreams")
            for dream, score in results:
                marker = " ← FLYING DREAM!" if dream.id == flying_dream.id else ""
                print(f"  Score {score:.4f}: Dream {dream.id} - '{dream.title}'{marker}")

            if not any(d.id == flying_dream.id for d, _ in results):
                print(f"  ✗ Flying dream (ID {flying_dream.id}) NOT in results!")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_flying_query.py <user_id>")
        sys.exit(1)

    user_id = int(sys.argv[1])
    asyncio.run(test_flying_query(user_id))

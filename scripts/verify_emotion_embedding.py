"""
Verify that dream embeddings include emotion tags
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


async def verify_emotion_embeddings(user_id: int):
    """Check if emotion tags are included in embeddings"""

    database_url = os.getenv("PostgreSQL_URL")
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("=" * 60)
        print("VERIFYING EMOTION TAGS IN EMBEDDINGS")
        print("=" * 60)

        # Get the latest dream (should be the flying one)
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

        print(f"\nLatest Dream:")
        print(f"  ID: {dream.id}")
        print(f"  Title: {dream.title}")
        print(f"  Description: {dream.description}")
        print(f"  Emotion Tags: {dream.emotion_tags}")

        # Check what text was used for embedding
        embedding_service = get_embedding_service()

        embedding_text = embedding_service.prepare_dream_text(
            title=dream.title,
            description=dream.description,
            interpretation=dream.interpretation,
            emotion_tags=dream.emotion_tags
        )

        print(f"\n--- Text Used for Embedding ---")
        print(f"Length: {len(embedding_text)} characters")
        print(f"\nFirst 500 chars:")
        print(embedding_text[:500])
        print("\n...")

        # Check if emotions appear in the text
        if dream.emotion_tags:
            emotion_count = embedding_text.count(f"Emotions: {dream.emotion_tags}")
            print(f"\n'Emotions: {dream.emotion_tags}' appears {emotion_count} times")

        # Test similarity with emotion query
        print("\n" + "=" * 60)
        print("TESTING SEMANTIC SIMILARITY")
        print("=" * 60)

        test_queries = [
            "What emotions appear most in my dreams?",
            "emotions",
            "joyful",
            "happy dreams",
            "feelings in dreams"
        ]

        import numpy as np

        # Get dream embedding from database
        result = await db.execute(
            select(DreamVector).where(DreamVector.dream_id == dream.id)
        )
        dream_vector = result.scalar_one_or_none()

        if dream_vector:
            dream_embedding = np.array(dream_vector.embedding)

            for query in test_queries:
                query_embedding = np.array(embedding_service.generate_embedding(query))

                # Calculate cosine similarity
                cosine_sim = np.dot(dream_embedding, query_embedding) / (
                    np.linalg.norm(dream_embedding) * np.linalg.norm(query_embedding)
                )

                print(f"\nQuery: '{query}'")
                print(f"  Similarity: {cosine_sim:.4f}")
                print(f"  Above 0.5 threshold? {cosine_sim >= 0.5}")
        else:
            print("\n✗ No embedding found for this dream!")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python verify_emotion_embedding.py <user_id>")
        sys.exit(1)

    user_id = int(sys.argv[1])
    asyncio.run(verify_emotion_embeddings(user_id))

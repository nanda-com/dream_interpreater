"""
Debug pgvector distance calculations
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

load_dotenv()


async def debug_pgvector(user_id: int):
    """Debug pgvector calculations"""

    database_url = os.getenv("PostgreSQL_URL")
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("=" * 60)
        print("PGVECTOR DISTANCE DEBUG")
        print("=" * 60)

        # Get test query embedding
        embedding_service = get_embedding_service()
        query = "did i dream about rats?"
        query_embedding = embedding_service.generate_embedding(query)

        print(f"\nQuery: '{query}'")
        print(f"Query embedding dimensions: {len(query_embedding)}")

        # Raw SQL query to see what pgvector returns
        print("\n--- Raw pgvector query ---")

        raw_query = text("""
            SELECT
                de.id,
                de.title,
                dv.embedding <=> CAST(:query_embedding AS vector) as distance,
                1 - (dv.embedding <=> CAST(:query_embedding AS vector)) as similarity
            FROM dream_entries de
            JOIN dream_vectors dv ON de.id = dv.dream_id
            WHERE de.user_id = :user_id
            ORDER BY distance
            LIMIT 10
        """)

        result = await db.execute(
            raw_query,
            {
                "query_embedding": str(query_embedding),
                "user_id": user_id
            }
        )
        rows = result.fetchall()

        print(f"\nFound {len(rows)} rows from raw query:")
        for row in rows:
            dream_id, title, distance, similarity = row
            print(f"  Dream {dream_id}: '{title}'")
            print(f"    Distance: {distance}")
            print(f"    Similarity: {similarity}")
            print(f"    Distance type: {type(distance)}")
            print(f"    Similarity >= 0.0? {similarity >= 0.0}")
            print(f"    Similarity >= 0.6? {similarity >= 0.6}")

        # Now test with SQLAlchemy ORM query (same as retrieval service)
        print("\n--- SQLAlchemy ORM query ---")

        query_stmt = (
            select(
                DreamEntry,
                DreamVector.embedding.cosine_distance(query_embedding).label('distance')
            )
            .join(DreamVector, DreamEntry.id == DreamVector.dream_id)
            .where(DreamEntry.user_id == user_id)
            .order_by('distance')
            .limit(10)
        )

        result = await db.execute(query_stmt)
        rows = result.all()

        print(f"\nFound {len(rows)} rows from ORM query:")
        for dream, distance in rows:
            similarity = float(1 - distance)
            print(f"  Dream {dream.id}: '{dream.title}'")
            print(f"    Distance: {distance} (type: {type(distance)})")
            print(f"    Similarity: {similarity}")
            print(f"    Similarity >= 0.0? {similarity >= 0.0}")
            print(f"    Similarity >= 0.6? {similarity >= 0.6}")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python debug_pgvector.py <user_id>")
        sys.exit(1)

    user_id = int(sys.argv[1])
    asyncio.run(debug_pgvector(user_id))

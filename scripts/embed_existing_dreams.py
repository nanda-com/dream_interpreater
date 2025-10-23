"""
Script to generate embeddings for existing dreams.
Run this script to backfill embeddings for dreams created before the Dream Explorer feature.

Usage:
    python scripts/embed_existing_dreams.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.backend.databases import AsyncSessionLocal, engine
from src.backend.models.dreamentry import DreamEntry
from src.backend.models.dream_vector import DreamVector
from src.backend.services.dream_embedding_service import get_embedding_service


async def embed_existing_dreams():
    """
    Process all existing dreams and generate embeddings for those without them.
    """
    logger.info("Starting embedding generation for existing dreams...")

    async with AsyncSessionLocal() as db:
        try:
            # Get all dreams
            result = await db.execute(select(DreamEntry))
            all_dreams = result.scalars().all()
            total_dreams = len(all_dreams)
            logger.info(f"Found {total_dreams} total dreams")

            # Get dreams that already have embeddings
            result = await db.execute(select(DreamVector.dream_id))
            existing_embeddings = {row[0] for row in result.all()}
            logger.info(f"Found {len(existing_embeddings)} existing embeddings")

            # Filter dreams that need embeddings
            dreams_to_embed = [
                dream for dream in all_dreams
                if dream.id not in existing_embeddings
            ]
            dreams_to_embed_count = len(dreams_to_embed)

            if dreams_to_embed_count == 0:
                logger.info("All dreams already have embeddings. Nothing to do.")
                return

            logger.info(f"Need to generate embeddings for {dreams_to_embed_count} dreams")

            # Initialize embedding service
            embedding_service = get_embedding_service()

            # Process each dream
            success_count = 0
            error_count = 0

            for i, dream in enumerate(dreams_to_embed, 1):
                try:
                    logger.info(f"Processing dream {i}/{dreams_to_embed_count} (ID: {dream.id})")

                    # Generate and store embedding
                    await embedding_service.embed_dream_entry(db, dream)

                    success_count += 1
                    logger.info(f"Successfully embedded dream {dream.id}")

                except Exception as e:
                    error_count += 1
                    logger.error(f"Failed to embed dream {dream.id}: {str(e)}")
                    continue

            # Summary
            logger.info("=" * 50)
            logger.info("Embedding generation completed!")
            logger.info(f"Total dreams processed: {dreams_to_embed_count}")
            logger.info(f"Successfully embedded: {success_count}")
            logger.info(f"Errors: {error_count}")
            logger.info("=" * 50)

        except Exception as e:
            logger.error(f"Fatal error during embedding generation: {str(e)}")
            raise
        finally:
            await db.close()


async def verify_embeddings():
    """
    Verify that all dreams have embeddings.
    """
    async with AsyncSessionLocal() as db:
        try:
            # Get count of dreams
            result = await db.execute(select(DreamEntry))
            dream_count = len(result.scalars().all())

            # Get count of embeddings
            result = await db.execute(select(DreamVector))
            embedding_count = len(result.scalars().all())

            logger.info("=" * 50)
            logger.info("Verification Results:")
            logger.info(f"Total dreams: {dream_count}")
            logger.info(f"Total embeddings: {embedding_count}")

            if dream_count == embedding_count:
                logger.info("✓ All dreams have embeddings!")
            else:
                logger.warning(f"✗ Missing embeddings for {dream_count - embedding_count} dreams")
            logger.info("=" * 50)

        finally:
            await db.close()


async def main():
    """Main function to run the embedding script."""
    logger.info("Dream Embedding Script")
    logger.info("=" * 50)

    # Run embedding generation
    await embed_existing_dreams()

    # Verify results
    await verify_embeddings()


if __name__ == "__main__":
    asyncio.run(main())

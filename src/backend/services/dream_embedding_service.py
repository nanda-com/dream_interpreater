"""
Dream Embedding Service
Generates and stores vector embeddings for dreams using sentence-transformers.
"""
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
from loguru import logger

from src.backend.models.dream_vector import DreamVector
from src.backend.models.dreamentry import DreamEntry


class DreamEmbeddingService:
    """Service for generating and managing dream embeddings."""

    def __init__(self):
        """Initialize the embedding model."""
        # Use all-MiniLM-L6-v2 model (384 dimensions, fast and efficient)
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dimension = 384

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector from text.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    def prepare_dream_text(
        self,
        title: Optional[str],
        description: str,
        interpretation: Optional[str]
    ) -> str:
        """
        Prepare comprehensive text from dream components for embedding.

        Args:
            title: Dream title
            description: Dream description
            interpretation: Dream interpretation

        Returns:
            Combined text for embedding
        """
        parts = []

        if title:
            parts.append(f"Title: {title}")

        if description:
            parts.append(f"Description: {description}")

        if interpretation:
            parts.append(f"Interpretation: {interpretation}")

        return " ".join(parts)

    async def store_dream_embedding(
        self,
        db: AsyncSession,
        dream_id: int,
        user_id: int,
        text: str
    ) -> DreamVector:
        """
        Generate and store embedding for a dream.

        Args:
            db: Database session
            dream_id: ID of the dream entry
            user_id: ID of the user
            text: Text to embed (combined title + description + interpretation)

        Returns:
            The created DreamVector object
        """
        try:
            # Generate embedding
            embedding = self.generate_embedding(text)

            # Check if embedding already exists
            result = await db.execute(
                select(DreamVector).where(DreamVector.dream_id == dream_id)
            )
            existing_vector = result.scalar_one_or_none()

            if existing_vector:
                # Update existing embedding
                existing_vector.embedding = embedding
                logger.info(f"Updated embedding for dream_id: {dream_id}")
                await db.commit()
                await db.refresh(existing_vector)
                return existing_vector
            else:
                # Create new embedding
                dream_vector = DreamVector(
                    dream_id=dream_id,
                    user_id=user_id,
                    embedding=embedding
                )
                db.add(dream_vector)
                await db.commit()
                await db.refresh(dream_vector)
                logger.info(f"Created new embedding for dream_id: {dream_id}")
                return dream_vector

        except Exception as e:
            await db.rollback()
            logger.error(f"Error storing dream embedding: {str(e)}")
            raise

    async def embed_dream_entry(
        self,
        db: AsyncSession,
        dream_entry: DreamEntry
    ) -> DreamVector:
        """
        Generate and store embedding for a complete dream entry.

        Args:
            db: Database session
            dream_entry: The DreamEntry object to embed

        Returns:
            The created DreamVector object
        """
        # Prepare text from dream components
        text = self.prepare_dream_text(
            title=dream_entry.title,
            description=dream_entry.description,
            interpretation=dream_entry.interpretation
        )

        # Store the embedding
        return await self.store_dream_embedding(
            db=db,
            dream_id=dream_entry.id,
            user_id=dream_entry.user_id,
            text=text
        )

    async def delete_dream_embedding(
        self,
        db: AsyncSession,
        dream_id: int
    ) -> bool:
        """
        Delete embedding for a dream.

        Args:
            db: Database session
            dream_id: ID of the dream entry

        Returns:
            True if deleted, False if not found
        """
        try:
            result = await db.execute(
                select(DreamVector).where(DreamVector.dream_id == dream_id)
            )
            dream_vector = result.scalar_one_or_none()

            if dream_vector:
                await db.delete(dream_vector)
                await db.commit()
                logger.info(f"Deleted embedding for dream_id: {dream_id}")
                return True
            else:
                logger.warning(f"No embedding found for dream_id: {dream_id}")
                return False

        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting dream embedding: {str(e)}")
            raise


# Singleton instance
_embedding_service: Optional[DreamEmbeddingService] = None


def get_embedding_service() -> DreamEmbeddingService:
    """
    Get or create singleton embedding service instance.

    Returns:
        DreamEmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = DreamEmbeddingService()
    return _embedding_service

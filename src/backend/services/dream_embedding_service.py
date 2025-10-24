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
        interpretation: Optional[str],
        emotion_tags: Optional[str] = None,
        keywords: Optional[list[str]] = None
    ) -> str:
        """
        Prepare comprehensive text from dream components for embedding.

        Weights AI-extracted keywords 10x higher for maximum search accuracy,
        while keeping full description 2x for context.

        Args:
            title: Dream title
            description: Dream description
            interpretation: Dream interpretation
            emotion_tags: Comma-separated emotion tags
            keywords: AI-extracted key content words (nouns, verbs, adjectives)

        Returns:
            Combined text for embedding with weighted keywords
        """
        parts = []

        # Add each keyword individually 10 times for maximum weight
        # Each keyword gets its own 10x boost for stronger single-word matching
        # E.g., "flying" × 10, "mountains" × 10, "soaring" × 10
        if keywords and len(keywords) > 0:
            for keyword in keywords:
                for _ in range(10):
                    parts.append(keyword)

        # Add full description 2 times for context
        # This preserves meaning while letting keywords dominate
        if description:
            parts.append(description)
            parts.append(description)

        # Add emotion tags 3 times for emotion-based queries (half weight of description)
        # This balances content queries (flying) with emotion queries (what emotions)
        # Meta-questions about emotions will use the special handler, not semantic search
        if emotion_tags:
            emotion_text = f"Emotions: {emotion_tags}"
            parts.append(emotion_text)
            parts.append(emotion_text)
            parts.append(emotion_text)

        if title:
            parts.append(f"Title: {title}")

        if description:
            parts.append(f"Description: {description}")

        # Only include a short excerpt of interpretation to avoid dilution
        # Limit to first 100 characters
        if interpretation:
            interpretation_excerpt = interpretation[:50] if len(interpretation) > 50 else interpretation
            parts.append(f"Interpretation: {interpretation_excerpt}")

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
        dream_entry: DreamEntry,
        keywords: Optional[list[str]] = None
    ) -> DreamVector:
        """
        Generate and store embedding for a complete dream entry.

        Args:
            db: Database session
            dream_entry: The DreamEntry object to embed
            keywords: Optional AI-extracted keywords for weighted embedding

        Returns:
            The created DreamVector object
        """
        # Prepare text from dream components including emotion tags and keywords
        text = self.prepare_dream_text(
            title=dream_entry.title,
            description=dream_entry.description,
            interpretation=dream_entry.interpretation,
            emotion_tags=dream_entry.emotion_tags,
            keywords=keywords
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

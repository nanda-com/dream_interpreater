"""
Dream Retrieval Service
Performs semantic search on dream entries using vector similarity.
"""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import os

from src.backend.models.dreamentry import DreamEntry
from src.backend.models.dream_vector import DreamVector
from src.backend.services.dream_embedding_service import get_embedding_service


class DreamRetrievalService:
    """Service for retrieving dreams using semantic similarity search."""

    def __init__(self):
        """Initialize the retrieval service."""
        self.embedding_service = get_embedding_service()
        self.default_top_k = int(os.getenv("MAX_RETRIEVED_DREAMS", "5"))
        self.default_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.6"))

    async def search_similar_dreams(
        self,
        db: AsyncSession,
        user_id: int,
        query: str,
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        emotion_tags: Optional[List[str]] = None
    ) -> List[Tuple[DreamEntry, float]]:
        """
        Search for dreams similar to the query using vector similarity.

        Args:
            db: Database session
            user_id: ID of the user whose dreams to search
            query: Natural language query
            top_k: Number of results to return (default from env)
            min_similarity: Minimum similarity threshold (default from env)
            start_date: Filter dreams after this date
            end_date: Filter dreams before this date
            emotion_tags: Filter by emotion tags

        Returns:
            List of tuples (DreamEntry, similarity_score) ordered by relevance
        """
        try:
            # Use defaults if not provided
            # Note: Use 'is None' check to allow 0.0 as a valid threshold
            top_k = top_k or self.default_top_k
            min_similarity = self.default_threshold if min_similarity is None else min_similarity

            # Generate embedding for the query
            query_embedding = self.embedding_service.generate_embedding(query)

            # Build the query with filters
            # Using pgvector's cosine distance operator (<=>)
            # Note: cosine distance is 1 - cosine similarity
            # So we need to convert: similarity = 1 - distance
            query_stmt = (
                select(
                    DreamEntry,
                    DreamVector.embedding.cosine_distance(query_embedding).label('distance')
                )
                .join(DreamVector, DreamEntry.id == DreamVector.dream_id)
                .where(DreamEntry.user_id == user_id)
            )

            # Apply date filters
            if start_date:
                query_stmt = query_stmt.where(DreamEntry.timestamp >= start_date)
            if end_date:
                query_stmt = query_stmt.where(DreamEntry.timestamp <= end_date)

            # Apply emotion tag filters
            if emotion_tags:
                emotion_filters = [
                    DreamEntry.emotion_tags.like(f"%{tag}%")
                    for tag in emotion_tags
                ]
                query_stmt = query_stmt.where(or_(*emotion_filters))

            # Order by similarity (ascending distance = higher similarity)
            # and limit results
            query_stmt = query_stmt.order_by('distance').limit(top_k)

            # Execute query
            result = await db.execute(query_stmt)
            rows = result.all()

            # Convert distance to similarity and filter by threshold
            # similarity = 1 - distance
            results = []
            for dream, distance in rows:
                similarity = float(1 - distance)
                if similarity >= min_similarity:
                    results.append((dream, similarity))

            logger.info(
                f"Found {len(results)} similar dreams for user {user_id} "
                f"(query: '{query[:50]}...')"
            )

            return results

        except Exception as e:
            logger.error(f"Error searching similar dreams: {str(e)}")
            raise

    async def find_similar_to_dream(
        self,
        db: AsyncSession,
        dream_id: int,
        user_id: int,
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None
    ) -> List[Tuple[DreamEntry, float]]:
        """
        Find dreams similar to a specific dream.

        Args:
            db: Database session
            dream_id: ID of the reference dream
            user_id: ID of the user
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of tuples (DreamEntry, similarity_score) ordered by relevance
        """
        try:
            # Get the reference dream's embedding
            result = await db.execute(
                select(DreamVector.embedding)
                .where(DreamVector.dream_id == dream_id)
            )
            reference_embedding = result.scalar_one_or_none()

            if reference_embedding is None:
                logger.warning(f"No embedding found for dream_id: {dream_id}")
                return []

            # Use defaults if not provided
            # Note: Use 'is None' check to allow 0.0 as a valid threshold
            top_k = top_k or self.default_top_k
            min_similarity = self.default_threshold if min_similarity is None else min_similarity

            # Find similar dreams (excluding the reference dream itself)
            query_stmt = (
                select(
                    DreamEntry,
                    DreamVector.embedding.cosine_distance(reference_embedding).label('distance')
                )
                .join(DreamVector, DreamEntry.id == DreamVector.dream_id)
                .where(
                    and_(
                        DreamEntry.user_id == user_id,
                        DreamEntry.id != dream_id  # Exclude the reference dream
                    )
                )
                .order_by('distance')
                .limit(top_k)
            )

            # Execute query
            result = await db.execute(query_stmt)
            rows = result.all()

            # Convert distance to similarity and filter by threshold
            results = []
            for dream, distance in rows:
                similarity = float(1 - distance)
                if similarity >= min_similarity:
                    results.append((dream, similarity))

            logger.info(
                f"Found {len(results)} dreams similar to dream_id {dream_id}"
            )

            return results

        except Exception as e:
            logger.error(f"Error finding similar dreams: {str(e)}")
            raise

    async def get_dream_clusters(
        self,
        db: AsyncSession,
        user_id: int,
        min_cluster_size: int = 3
    ) -> List[List[DreamEntry]]:
        """
        Group dreams into clusters based on semantic similarity.
        This is a simple clustering approach - could be enhanced with proper clustering algorithms.

        Args:
            db: Database session
            user_id: ID of the user
            min_cluster_size: Minimum number of dreams to form a cluster

        Returns:
            List of dream clusters
        """
        # TODO: Implement clustering algorithm (e.g., DBSCAN, K-means)
        # This is a placeholder for future enhancement
        logger.info("Dream clustering feature coming soon...")
        return []

    async def search_by_keywords(
        self,
        db: AsyncSession,
        user_id: int,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Tuple[DreamEntry, float]]:
        """
        Search dreams by keyword matching in the keywords array field.
        This is a fallback when semantic search returns no results.

        Args:
            db: Database session
            user_id: ID of the user
            query: Query string (will extract keywords from this)
            top_k: Number of results to return

        Returns:
            List of tuples (DreamEntry, match_score) ordered by relevance
        """
        try:
            from sqlalchemy import func, or_, and_

            # Extract keywords from query (split by spaces, remove common words and punctuation)
            import string
            stop_words = {'i', 'did', 'have', 'dream', 'about', 'of', 'the', 'a', 'an', 'my', 'me', 'was', 'were', 'is', 'are'}
            query_keywords = [
                word.strip().lower().strip(string.punctuation)  # Remove punctuation like ? ! . ,
                for word in query.split()
                if word.strip().lower().strip(string.punctuation) not in stop_words and len(word.strip()) > 0
            ]

            if not query_keywords:
                return []

            logger.info(f"Searching by keywords: {query_keywords}")

            # Build query to match any keyword in the array
            # Using PostgreSQL array overlap operator &&
            query_stmt = (
                select(DreamEntry)
                .where(
                    and_(
                        DreamEntry.user_id == user_id,
                        DreamEntry.keywords.overlap(query_keywords)  # PostgreSQL array overlap
                    )
                )
                .order_by(DreamEntry.timestamp.desc())
                .limit(top_k or self.default_top_k)
            )

            # Execute query
            result = await db.execute(query_stmt)
            dreams = result.scalars().all()

            # Calculate match score based on number of matching keywords
            results = []
            for dream in dreams:
                if dream.keywords:
                    matches = len(set(dream.keywords) & set(query_keywords))
                    total = len(query_keywords)
                    score = matches / total if total > 0 else 0.0
                    results.append((dream, score))

            # Sort by score descending
            results.sort(key=lambda x: x[1], reverse=True)

            logger.info(
                f"Found {len(results)} dreams by keyword matching for user {user_id}"
            )

            return results

        except Exception as e:
            logger.error(f"Error in keyword search: {str(e)}")
            raise


# Singleton instance
_retrieval_service: Optional[DreamRetrievalService] = None


def get_retrieval_service() -> DreamRetrievalService:
    """
    Get or create singleton retrieval service instance.

    Returns:
        DreamRetrievalService instance
    """
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = DreamRetrievalService()
    return _retrieval_service

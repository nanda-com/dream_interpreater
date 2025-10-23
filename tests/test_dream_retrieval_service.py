"""
Unit tests for Dream Retrieval Service
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.services.dream_retrieval_service import DreamRetrievalService, get_retrieval_service
from src.backend.models.dreamentry import DreamEntry
from src.backend.models.dream_vector import DreamVector


@pytest.fixture
def retrieval_service():
    """Create retrieval service instance for testing."""
    return DreamRetrievalService()


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_dreams_with_scores():
    """Create sample dreams with similarity scores."""
    dreams = [
        (
            DreamEntry(
                id=1,
                user_id=123,
                title="Flying Dream",
                description="I was flying over mountains",
                interpretation="Represents freedom",
                emotion_tags="happy,excited",
                timestamp=datetime(2024, 1, 15)
            ),
            0.92
        ),
        (
            DreamEntry(
                id=2,
                user_id=123,
                title="Ocean Dream",
                description="I was swimming in the ocean",
                interpretation="Represents emotions",
                emotion_tags="calm,peaceful",
                timestamp=datetime(2024, 1, 10)
            ),
            0.85
        ),
        (
            DreamEntry(
                id=3,
                user_id=123,
                title="Chase Dream",
                description="I was being chased",
                interpretation="Represents anxiety",
                emotion_tags="anxious,scared",
                timestamp=datetime(2024, 1, 5)
            ),
            0.78
        )
    ]
    return dreams


class TestDreamRetrievalService:
    """Test suite for Dream Retrieval Service."""

    def test_service_initialization(self, retrieval_service):
        """Test that the service initializes correctly."""
        assert retrieval_service is not None
        assert retrieval_service.embedding_service is not None
        assert retrieval_service.default_top_k > 0
        assert retrieval_service.default_threshold >= 0.0

    @pytest.mark.asyncio
    async def test_search_similar_dreams_basic(self, retrieval_service, mock_db):
        """Test basic similarity search."""
        # Mock embedding service
        with patch.object(retrieval_service.embedding_service, 'generate_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 384

            # Mock database results
            dream1 = DreamEntry(id=1, user_id=123, title="Test", description="Test", timestamp=datetime.now())
            mock_result = Mock()
            mock_result.all.return_value = [(dream1, 0.2)]  # distance = 0.2, so similarity = 0.8
            mock_db.execute.return_value = mock_result

            # Execute search
            results = await retrieval_service.search_similar_dreams(
                db=mock_db,
                user_id=123,
                query="flying dreams"
            )

            # Verify results
            assert len(results) == 1
            assert results[0][0].id == 1
            assert results[0][1] == 0.8  # similarity = 1 - 0.2

    @pytest.mark.asyncio
    async def test_search_similar_dreams_with_threshold(self, retrieval_service, mock_db):
        """Test similarity search with threshold filtering."""
        with patch.object(retrieval_service.embedding_service, 'generate_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 384

            # Mock dreams with different similarities
            dream1 = DreamEntry(id=1, user_id=123, title="High", description="High", timestamp=datetime.now())
            dream2 = DreamEntry(id=2, user_id=123, title="Low", description="Low", timestamp=datetime.now())

            mock_result = Mock()
            # distance 0.1 = similarity 0.9 (above threshold)
            # distance 0.5 = similarity 0.5 (below threshold of 0.6)
            mock_result.all.return_value = [(dream1, 0.1), (dream2, 0.5)]
            mock_db.execute.return_value = mock_result

            # Execute search with threshold
            results = await retrieval_service.search_similar_dreams(
                db=mock_db,
                user_id=123,
                query="test",
                min_similarity=0.6
            )

            # Only high similarity dream should be returned
            assert len(results) == 1
            assert results[0][0].id == 1

    @pytest.mark.asyncio
    async def test_search_similar_dreams_with_date_filter(self, retrieval_service, mock_db):
        """Test similarity search with date filtering."""
        with patch.object(retrieval_service.embedding_service, 'generate_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 384

            mock_result = Mock()
            mock_result.all.return_value = []
            mock_db.execute.return_value = mock_result

            # Execute search with date filters
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 12, 31)

            results = await retrieval_service.search_similar_dreams(
                db=mock_db,
                user_id=123,
                query="test",
                start_date=start_date,
                end_date=end_date
            )

            # Verify execute was called
            assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_search_similar_dreams_with_emotion_tags(self, retrieval_service, mock_db):
        """Test similarity search with emotion tag filtering."""
        with patch.object(retrieval_service.embedding_service, 'generate_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 384

            mock_result = Mock()
            mock_result.all.return_value = []
            mock_db.execute.return_value = mock_result

            # Execute search with emotion tags
            results = await retrieval_service.search_similar_dreams(
                db=mock_db,
                user_id=123,
                query="test",
                emotion_tags=["happy", "excited"]
            )

            # Verify execute was called
            assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_find_similar_to_dream_found(self, retrieval_service, mock_db):
        """Test finding similar dreams to a specific dream."""
        reference_embedding = [0.1] * 384

        # Mock getting reference embedding
        mock_result1 = Mock()
        mock_result1.scalar_one_or_none.return_value = reference_embedding

        # Mock similar dreams
        dream1 = DreamEntry(id=2, user_id=123, title="Similar", description="Similar", timestamp=datetime.now())
        mock_result2 = Mock()
        mock_result2.all.return_value = [(dream1, 0.15)]  # similarity = 0.85

        mock_db.execute.side_effect = [mock_result1, mock_result2]

        # Execute
        results = await retrieval_service.find_similar_to_dream(
            db=mock_db,
            dream_id=1,
            user_id=123
        )

        # Verify
        assert len(results) == 1
        assert results[0][0].id == 2
        assert results[0][1] == 0.85

    @pytest.mark.asyncio
    async def test_find_similar_to_dream_not_found(self, retrieval_service, mock_db):
        """Test finding similar dreams when reference dream has no embedding."""
        # Mock no embedding found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Execute
        results = await retrieval_service.find_similar_to_dream(
            db=mock_db,
            dream_id=999,
            user_id=123
        )

        # Should return empty list
        assert results == []

    @pytest.mark.asyncio
    async def test_search_by_keywords(self, retrieval_service, mock_db):
        """Test keyword-based search."""
        with patch.object(retrieval_service, 'search_similar_dreams') as mock_search:
            mock_search.return_value = []

            # Execute
            await retrieval_service.search_by_keywords(
                db=mock_db,
                user_id=123,
                keywords=["flying", "sky", "freedom"]
            )

            # Verify search was called with combined query
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert "flying sky freedom" in call_args[1]['query']

    def test_get_retrieval_service_singleton(self):
        """Test that get_retrieval_service returns singleton instance."""
        service1 = get_retrieval_service()
        service2 = get_retrieval_service()

        assert service1 is service2

    @pytest.mark.asyncio
    async def test_search_similar_dreams_custom_top_k(self, retrieval_service, mock_db):
        """Test similarity search with custom top_k parameter."""
        with patch.object(retrieval_service.embedding_service, 'generate_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 384

            mock_result = Mock()
            mock_result.all.return_value = []
            mock_db.execute.return_value = mock_result

            # Execute with custom top_k
            await retrieval_service.search_similar_dreams(
                db=mock_db,
                user_id=123,
                query="test",
                top_k=10
            )

            # Verify execute was called
            assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_search_similar_dreams_empty_results(self, retrieval_service, mock_db):
        """Test similarity search returning no results."""
        with patch.object(retrieval_service.embedding_service, 'generate_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 384

            mock_result = Mock()
            mock_result.all.return_value = []
            mock_db.execute.return_value = mock_result

            # Execute
            results = await retrieval_service.search_similar_dreams(
                db=mock_db,
                user_id=123,
                query="nonexistent"
            )

            # Should return empty list
            assert results == []

    @pytest.mark.asyncio
    async def test_get_dream_clusters_placeholder(self, retrieval_service, mock_db):
        """Test that clustering returns empty list (placeholder)."""
        results = await retrieval_service.get_dream_clusters(
            db=mock_db,
            user_id=123
        )

        # Currently returns empty as it's a placeholder
        assert results == []

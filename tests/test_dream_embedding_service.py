"""
Unit tests for Dream Embedding Service
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.backend.services.dream_embedding_service import DreamEmbeddingService, get_embedding_service
from src.backend.models.dream_vector import DreamVector
from src.backend.models.dreamentry import DreamEntry


@pytest.fixture
def embedding_service():
    """Create embedding service instance for testing."""
    return DreamEmbeddingService()


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_dream_entry():
    """Create sample dream entry for testing."""
    return DreamEntry(
        id=1,
        user_id=123,
        title="Flying Dream",
        description="I was flying over mountains and feeling free",
        interpretation="This dream represents freedom and aspiration",
        timestamp=None
    )


class TestDreamEmbeddingService:
    """Test suite for Dream Embedding Service."""

    def test_service_initialization(self, embedding_service):
        """Test that the service initializes correctly."""
        assert embedding_service is not None
        assert embedding_service.model is not None
        assert embedding_service.embedding_dimension == 384

    def test_generate_embedding(self, embedding_service):
        """Test embedding generation from text."""
        text = "I had a dream about flying over mountains"
        embedding = embedding_service.generate_embedding(text)

        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)

    def test_generate_embedding_empty_text(self, embedding_service):
        """Test embedding generation with empty text."""
        text = ""
        embedding = embedding_service.generate_embedding(text)

        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) == 384

    def test_prepare_dream_text_all_fields(self, embedding_service):
        """Test preparing dream text with all fields present."""
        text = embedding_service.prepare_dream_text(
            title="Flying Dream",
            description="I was flying over mountains",
            interpretation="Represents freedom"
        )

        assert "Title: Flying Dream" in text
        assert "Description: I was flying over mountains" in text
        assert "Interpretation: Represents freedom" in text

    def test_prepare_dream_text_partial_fields(self, embedding_service):
        """Test preparing dream text with only some fields."""
        text = embedding_service.prepare_dream_text(
            title=None,
            description="I was flying over mountains",
            interpretation=None
        )

        assert "Title:" not in text
        assert "Description: I was flying over mountains" in text
        assert "Interpretation:" not in text

    @pytest.mark.asyncio
    async def test_store_dream_embedding_new(self, embedding_service, mock_db):
        """Test storing a new dream embedding."""
        # Mock database query to return None (no existing embedding)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Call the method
        result = await embedding_service.store_dream_embedding(
            db=mock_db,
            dream_id=1,
            user_id=123,
            text="Test dream text"
        )

        # Verify database operations
        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called

    @pytest.mark.asyncio
    async def test_store_dream_embedding_update_existing(self, embedding_service, mock_db):
        """Test updating an existing dream embedding."""
        # Mock existing embedding
        existing_vector = DreamVector(
            id=1,
            dream_id=1,
            user_id=123,
            embedding=[0.1] * 384
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_vector
        mock_db.execute.return_value = mock_result

        # Call the method
        result = await embedding_service.store_dream_embedding(
            db=mock_db,
            dream_id=1,
            user_id=123,
            text="Updated dream text"
        )

        # Verify update happened
        assert existing_vector.embedding is not None
        assert mock_db.commit.called
        assert mock_db.refresh.called

    @pytest.mark.asyncio
    async def test_embed_dream_entry(self, embedding_service, mock_db, sample_dream_entry):
        """Test embedding a complete dream entry."""
        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Call the method
        result = await embedding_service.embed_dream_entry(
            db=mock_db,
            dream_entry=sample_dream_entry
        )

        # Verify database operations
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_delete_dream_embedding_exists(self, embedding_service, mock_db):
        """Test deleting an existing dream embedding."""
        # Mock existing embedding
        existing_vector = DreamVector(
            id=1,
            dream_id=1,
            user_id=123,
            embedding=[0.1] * 384
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_vector
        mock_db.execute.return_value = mock_result

        # Call the method
        result = await embedding_service.delete_dream_embedding(
            db=mock_db,
            dream_id=1
        )

        # Verify deletion
        assert result is True
        assert mock_db.delete.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_delete_dream_embedding_not_found(self, embedding_service, mock_db):
        """Test deleting a non-existent dream embedding."""
        # Mock no embedding found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Call the method
        result = await embedding_service.delete_dream_embedding(
            db=mock_db,
            dream_id=999
        )

        # Verify no deletion occurred
        assert result is False
        assert not mock_db.delete.called

    def test_get_embedding_service_singleton(self):
        """Test that get_embedding_service returns singleton instance."""
        service1 = get_embedding_service()
        service2 = get_embedding_service()

        assert service1 is service2

    def test_embedding_consistency(self, embedding_service):
        """Test that same text generates consistent embeddings."""
        text = "I had a dream about flying"

        embedding1 = embedding_service.generate_embedding(text)
        embedding2 = embedding_service.generate_embedding(text)

        # Embeddings should be identical for same input
        assert embedding1 == embedding2

    @pytest.mark.asyncio
    async def test_store_dream_embedding_rollback_on_error(self, embedding_service, mock_db):
        """Test that errors trigger rollback."""
        # Mock database to raise error on commit
        mock_db.commit.side_effect = Exception("Database error")
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Call should raise exception
        with pytest.raises(Exception):
            await embedding_service.store_dream_embedding(
                db=mock_db,
                dream_id=1,
                user_id=123,
                text="Test dream"
            )

        # Verify rollback was called
        assert mock_db.rollback.called

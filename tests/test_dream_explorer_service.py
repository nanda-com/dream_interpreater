"""
Unit tests for Dream Explorer Service
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.backend.services.dream_explorer_service import DreamExplorerService, get_explorer_service
from src.backend.models.dreamentry import DreamEntry


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def sample_dreams():
    """Create sample dreams for testing."""
    return [
        (
            DreamEntry(
                id=1,
                user_id=123,
                title="Flying Dream",
                description="I was flying over mountains and feeling free",
                interpretation="Represents freedom and aspiration",
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
                description="Swimming in deep blue ocean",
                interpretation="Represents emotional depth",
                emotion_tags="calm,peaceful",
                timestamp=datetime(2024, 1, 10)
            ),
            0.85
        )
    ]


class TestDreamExplorerService:
    """Test suite for Dream Explorer Service."""

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test that the service initializes correctly."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            service = DreamExplorerService()
            assert service is not None
            assert service.llm is not None
            assert service.chain is not None
            assert service.retrieval_service is not None

    def test_format_dream_context_with_dreams(self, sample_dreams):
        """Test formatting dreams into context."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            service = DreamExplorerService()
            context = service.format_dream_context(sample_dreams)

            assert "Flying Dream" in context
            assert "Ocean Dream" in context
            assert "2024-01-15" in context
            assert "happy,excited" in context
            assert "0.92" in context

    def test_format_dream_context_empty(self):
        """Test formatting with no dreams."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            service = DreamExplorerService()
            context = service.format_dream_context([])

            assert "No relevant dreams found" in context

    def test_format_chat_history_with_messages(self):
        """Test formatting chat history."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            service = DreamExplorerService()
            history = [
                {"role": "user", "content": "What are my flying dreams about?"},
                {"role": "assistant", "content": "Your flying dreams represent freedom."}
            ]

            formatted = service.format_chat_history(history)

            assert "User: What are my flying dreams about?" in formatted
            assert "Assistant: Your flying dreams represent freedom." in formatted

    def test_format_chat_history_empty(self):
        """Test formatting empty chat history."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            service = DreamExplorerService()
            formatted = service.format_chat_history([])

            assert "No previous conversation" in formatted

    @pytest.mark.asyncio
    async def test_ask_question_basic(self, mock_db, sample_dreams):
        """Test asking a question with no chat history."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            # Mock the LLM before service initialization
            mock_llm = Mock()
            mock_llm_instance = Mock()

            with patch('src.backend.services.dream_explorer_service.ChatGoogleGenerativeAI', return_value=mock_llm_instance):
                with patch('src.backend.services.dream_explorer_service.LLMChain') as mock_chain_class:
                    # Create a mock chain instance
                    mock_chain_instance = Mock()
                    mock_chain_instance.arun = AsyncMock(return_value="Your flying dreams represent freedom and personal growth.")
                    mock_chain_class.return_value = mock_chain_instance

                    service = DreamExplorerService()

                    # Mock retrieval service
                    with patch.object(service.retrieval_service, 'search_similar_dreams', new_callable=AsyncMock) as mock_search:
                        mock_search.return_value = sample_dreams

                        # Execute
                        result = await service.ask_question(
                            db=mock_db,
                            user_id=123,
                            question="What do my flying dreams mean?"
                        )

                        # Verify result structure
                        assert "answer" in result
                        assert "relevant_dreams" in result
                        assert "chat_history" in result
                    assert len(result["relevant_dreams"]) == 2
                    assert len(result["chat_history"]) == 2  # user + assistant

    @pytest.mark.asyncio
    async def test_ask_question_with_chat_history(self, mock_db, sample_dreams):
        """Test asking a follow-up question with existing chat history."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            mock_llm_instance = Mock()

            with patch('src.backend.services.dream_explorer_service.ChatGoogleGenerativeAI', return_value=mock_llm_instance):
                with patch('src.backend.services.dream_explorer_service.LLMChain') as mock_chain_class:
                    mock_chain_instance = Mock()
                    mock_chain_instance.arun = AsyncMock(return_value="Based on your previous dreams...")
                    mock_chain_class.return_value = mock_chain_instance

                    service = DreamExplorerService()

                    existing_history = [
                        {"role": "user", "content": "Tell me about my dreams"},
                        {"role": "assistant", "content": "You have many flying dreams"}
                    ]

                    with patch.object(service.retrieval_service, 'search_similar_dreams', new_callable=AsyncMock) as mock_search:
                        mock_search.return_value = sample_dreams

                        result = await service.ask_question(
                            db=mock_db,
                            user_id=123,
                            question="What about ocean dreams?",
                            chat_history=existing_history
                        )

                        # Chat history should be extended
                        assert len(result["chat_history"]) == 4  # 2 existing + 2 new

    @pytest.mark.asyncio
    async def test_ask_question_custom_top_k(self, mock_db, sample_dreams):
        """Test asking a question with custom top_k."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            mock_llm_instance = Mock()

            with patch('src.backend.services.dream_explorer_service.ChatGoogleGenerativeAI', return_value=mock_llm_instance):
                with patch('src.backend.services.dream_explorer_service.LLMChain') as mock_chain_class:
                    mock_chain_instance = Mock()
                    mock_chain_instance.arun = AsyncMock(return_value="Test response")
                    mock_chain_class.return_value = mock_chain_instance

                    service = DreamExplorerService()

                    with patch.object(service.retrieval_service, 'search_similar_dreams', new_callable=AsyncMock) as mock_search:
                        mock_search.return_value = sample_dreams

                        await service.ask_question(
                            db=mock_db,
                            user_id=123,
                            question="Test question",
                            top_k=10
                        )

                        # Verify top_k was passed
                        mock_search.assert_called_once()
                        assert mock_search.call_args[1]['top_k'] == 10

    @pytest.mark.asyncio
    async def test_find_patterns(self, mock_db, sample_dreams):
        """Test finding patterns in dream history."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            mock_llm_instance = Mock()
            mock_llm_instance.apredict = AsyncMock(return_value="Pattern analysis: You often dream about flying...")

            with patch('src.backend.services.dream_explorer_service.ChatGoogleGenerativeAI', return_value=mock_llm_instance):
                with patch('src.backend.services.dream_explorer_service.LLMChain') as mock_chain_class:
                    mock_chain_instance = Mock()
                    mock_chain_instance.arun = AsyncMock(return_value="Mock response")
                    mock_chain_class.return_value = mock_chain_instance

                    service = DreamExplorerService()

                    with patch.object(service.retrieval_service, 'search_similar_dreams', new_callable=AsyncMock) as mock_search:
                        mock_search.return_value = sample_dreams

                        result = await service.find_patterns(
                            db=mock_db,
                            user_id=123,
                            pattern_query="flying dreams"
                        )

                        # Verify result structure
                        assert "pattern_analysis" in result
                        assert "relevant_dreams" in result
                        assert len(result["relevant_dreams"]) == 2

    @pytest.mark.asyncio
    async def test_find_patterns_custom_top_k(self, mock_db, sample_dreams):
        """Test finding patterns with custom top_k."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            mock_llm_instance = Mock()
            mock_llm_instance.apredict = AsyncMock(return_value="Pattern analysis...")

            with patch('src.backend.services.dream_explorer_service.ChatGoogleGenerativeAI', return_value=mock_llm_instance):
                with patch('src.backend.services.dream_explorer_service.LLMChain') as mock_chain_class:
                    mock_chain_instance = Mock()
                    mock_chain_instance.arun = AsyncMock(return_value="Mock response")
                    mock_chain_class.return_value = mock_chain_instance

                    service = DreamExplorerService()

                    with patch.object(service.retrieval_service, 'search_similar_dreams', new_callable=AsyncMock) as mock_search:
                        mock_search.return_value = sample_dreams

                        await service.find_patterns(
                            db=mock_db,
                            user_id=123,
                            pattern_query="test",
                            top_k=15
                        )

                        # Verify top_k was used
                        mock_search.assert_called_once()
                        assert mock_search.call_args[1]['top_k'] == 15

    @pytest.mark.asyncio
    async def test_compare_dreams(self, mock_db):
        """Test comparing two dreams."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            mock_llm_instance = Mock()
            mock_llm_instance.apredict = AsyncMock(return_value="Comparison: Both dreams involve movement...")

            with patch('src.backend.services.dream_explorer_service.ChatGoogleGenerativeAI', return_value=mock_llm_instance):
                with patch('src.backend.services.dream_explorer_service.LLMChain') as mock_chain_class:
                    mock_chain_instance = Mock()
                    mock_chain_instance.arun = AsyncMock(return_value="Mock response")
                    mock_chain_class.return_value = mock_chain_instance

                    service = DreamExplorerService()

                    # Create two dreams
                    dream1 = DreamEntry(
                        id=1, user_id=123, title="Dream 1", description="Flying",
                        interpretation="Freedom", timestamp=datetime(2024, 1, 1)
                    )
                    dream2 = DreamEntry(
                        id=2, user_id=123, title="Dream 2", description="Swimming",
                        interpretation="Emotions", timestamp=datetime(2024, 1, 2)
                    )

                    # Mock database query
                    mock_result = Mock()
                    mock_result.scalars.return_value.all.return_value = [dream1, dream2]
                    mock_db.execute.return_value = mock_result

                    result = await service.compare_dreams(
                        db=mock_db,
                        dream_id_1=1,
                        dream_id_2=2,
                        user_id=123
                    )

                    # Verify result
                    assert "Comparison" in result
                    assert mock_llm_instance.apredict.called

    @pytest.mark.asyncio
    async def test_compare_dreams_not_found(self, mock_db):
        """Test comparing dreams when one is not found."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            service = DreamExplorerService()

            # Mock only one dream found
            dream1 = DreamEntry(
                id=1, user_id=123, title="Dream 1", description="Test",
                interpretation="Test", timestamp=datetime.now()
            )

            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = [dream1]
            mock_db.execute.return_value = mock_result

            # Should raise ValueError
            with pytest.raises(ValueError, match="Could not find both dreams"):
                await service.compare_dreams(
                    db=mock_db,
                    dream_id_1=1,
                    dream_id_2=999,
                    user_id=123
                )

    def test_get_explorer_service_singleton(self):
        """Test that get_explorer_service returns singleton instance."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            service1 = get_explorer_service()
            service2 = get_explorer_service()

            assert service1 is service2

    @pytest.mark.asyncio
    async def test_ask_question_no_results(self, mock_db):
        """Test asking a question when no relevant dreams are found."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            mock_llm_instance = Mock()

            with patch('src.backend.services.dream_explorer_service.ChatGoogleGenerativeAI', return_value=mock_llm_instance):
                with patch('src.backend.services.dream_explorer_service.LLMChain') as mock_chain_class:
                    mock_chain_instance = Mock()
                    mock_chain_instance.arun = AsyncMock(return_value="I couldn't find relevant dreams...")
                    mock_chain_class.return_value = mock_chain_instance

                    service = DreamExplorerService()

                    with patch.object(service.retrieval_service, 'search_similar_dreams', new_callable=AsyncMock) as mock_search:
                        mock_search.return_value = []

                        result = await service.ask_question(
                            db=mock_db,
                            user_id=123,
                            question="Test question"
                        )

                        # Should still return valid response
                        assert "answer" in result
                        assert len(result["relevant_dreams"]) == 0

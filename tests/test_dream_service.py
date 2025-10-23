# tests/test_dream_service.py
from src.backend.ai_services import DreamAIService
import pytest


@pytest.mark.skip(reason="Legacy test - DreamAIService uses deprecated OpenAI integration")
def test_dream_interpretation():
    ai_service = DreamAIService()
    dream_description = "I was flying over a city..."

    interpretation = ai_service.generate_interpretation(dream_description)
    assert len(interpretation) > 50
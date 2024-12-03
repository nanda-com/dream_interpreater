# tests/test_dream_service.py
from backend.ai_services import DreamAIService


def test_dream_interpretation():
    ai_service = DreamAIService()
    dream_description = "I was flying over a city..."
    
    interpretation = ai_service.generate_interpretation(dream_description)
    assert len(interpretation) > 50
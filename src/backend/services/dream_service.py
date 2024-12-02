from typing import List, Optional
from uuid import uuid4
from datetime import datetime

from src.backend.models.schemas import DreamInterpretationResponse
from src.backend.ai_interpreters.gemini_interpreter import GeminiDreamInterpreter

class DreamService:
    def __init__(self, ai_interpreter: Optional[GeminiDreamInterpreter] = None):
        # Allow optional AI interpreter
        self.dreams: List[DreamInterpretationResponse] = []
        self.ai_interpreter = ai_interpreter or GeminiDreamInterpreter()

    def create_dream(
        self, 
        description: str, 
        interpretation: Optional[str] = None,
        emotions: Optional[List[str]] = None
    ) -> DreamInterpretationResponse:
        # Generate interpretation if not provided
        if not interpretation:
            interpretation = self.ai_interpreter.interpret_dream(description)
        
        # Generate title
        title = self.ai_interpreter.generate_dream_title(description)

        # Create dream response
        dream = DreamInterpretationResponse(
            id=str(uuid4()),
            description=description,
            interpretation=interpretation,
            title=title,
            date=datetime.now(),
            emotions=emotions or []
        )
        
        self.dreams.append(dream)
        return dream

    def list_dreams(self) -> List[DreamInterpretationResponse]:
        return self.dreams
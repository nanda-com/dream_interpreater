from typing import List
from uuid import uuid4
from datetime import datetime

from src.backend.models.schemas import DreamInterpretationResponse

class DreamService:
    def __init__(self):
        # In-memory storage (replace with database in production)
        self.dreams: List[DreamInterpretationResponse] = []

    def create_dream(
        self, 
        description: str, 
        interpretation: str,
        emotions: List[str] = None
    ) -> DreamInterpretationResponse:
        dream = DreamInterpretationResponse(
            id=str(uuid4()),
            description=description,
            interpretation=interpretation,
            date=datetime.now(),
            emotions=emotions
        )
        
        self.dreams.append(dream)
        return dream

    def list_dreams(self) -> List[DreamInterpretationResponse]:
        return self.dreams
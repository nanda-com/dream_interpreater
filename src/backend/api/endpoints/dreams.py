from fastapi import APIRouter, Depends, HTTPException
from typing import List

# Import your schemas and services
from src.backend.models.schemas import (
    DreamCreateRequest, 
    DreamInterpretationResponse
)
from src.backend.services.dream_service import DreamService
from src.backend.ai_interpreters.gemini_interpreter import GeminiDreamInterpreter

# Create the router with a specific name
dream_router = APIRouter(prefix="/dreams", tags=["dreams"])

# Dependency to get DreamService
def get_dream_service():
    ai_interpreter = GeminiDreamInterpreter()
    return DreamService(ai_interpreter)

@dream_router.post(
    "/", 
    response_model=DreamInterpretationResponse,
    status_code=201
)
async def create_dream_entry(
    dream_data: DreamCreateRequest,
    dream_service: DreamService = Depends(get_dream_service)
) -> DreamInterpretationResponse:
    """
    Create a new dream entry with AI interpretation
    """
    try:
        # Use the service to create and interpret the dream
        dream = dream_service.create_dream(
            description=dream_data.description,
            emotions=dream_data.emotions
        )
        return dream
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@dream_router.get(
    "/", 
    response_model=List[DreamInterpretationResponse]
)
async def list_dreams(
    dream_service: DreamService = Depends(get_dream_service)
) -> List[DreamInterpretationResponse]:
    """
    Retrieve all dream entries
    """
    return dream_service.list_dreams()
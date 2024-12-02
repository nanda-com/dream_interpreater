from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status
)
from typing import List

from src.backend.models.schemas import (
    DreamCreateRequest, 
    DreamInterpretationResponse
)
from src.backend.services.dream_service import DreamService
from src.backend.ai_interpreters.gemini_interpreter import GeminiDreamInterpreter

dream_router = APIRouter(
    prefix="/dreams",
    tags=["dreams"]
)

@dream_router.post(
    "/",
    response_model=DreamInterpretationResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_dream_entry(
    dream_request: DreamCreateRequest,
    dream_service: DreamService = Depends(),
    ai_interpreter: GeminiDreamInterpreter = Depends()
):
    try:
        interpretation = ai_interpreter.interpret_dream(
            dream_request.description
        )

        dream_response = dream_service.create_dream(
            description=dream_request.description,
            interpretation=interpretation,
            emotions=dream_request.emotions
        )

        return dream_response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@dream_router.get(
    "/",
    response_model=List[DreamInterpretationResponse]
)
async def list_dreams(
    dream_service: DreamService = Depends()
):
    return dream_service.list_dreams()
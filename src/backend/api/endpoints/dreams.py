from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.backend.databases import get_db
from src.backend.services.dream_service import DreamService
from src.backend.models.schemas import DreamCreateRequest, DreamInterpretationResponse, DreamUpdateRequest
from src.backend.utils.auth import verify_token
from src.backend.ai_interpreters.gemini_interpreter import GeminiDreamInterpreter
from typing import List

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

dream_router = APIRouter(
    prefix="/dreams",
    tags=["dreams"]
)
dream_service = DreamService()

@dream_router.post(
    "/", 
    response_model=DreamInterpretationResponse,
    status_code=201,
    responses={
        201: {"description": "Successfully created dream entry"},
        401: {"description": "Unauthorized"},
        422: {"description": "Validation Error"}
    }
)
async def create_dream_entry(
    dream_data: DreamCreateRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> DreamInterpretationResponse:
    """
    Create a new dream entry with AI interpretation
    """
    # Verify token and get user_id
    payload = verify_token(token)
    user_id = int(payload.get("sub"))
    print(user_id)
    try:
        dream_entry = await dream_service.create_dream(
            db=db,
            user_id=user_id,
            description=dream_data.description,
            title=dream_data.title,
            emotions=dream_data.emotions
        )
        print(dream_entry)
        return dream_entry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@dream_router.get(
    "/", 
    response_model=List[DreamInterpretationResponse],
    responses={
        200: {"description": "List of user's dreams"},
        401: {"description": "Authentication failed"}
    }
)
async def list_dreams(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    payload = verify_token(token)
    user_id = int(payload.get("sub"))
    
    dreams = await dream_service.list_user_dreams(db, user_id)
    return dreams

@dream_router.delete(
    "/{dream_id}",
    responses={
        200: {"description": "Dream deleted successfully"},
        404: {"description": "Dream not found"},
        401: {"description": "Unauthorized"}
    }
)
async def delete_dream(
    dream_id: int,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    Delete a dream entry by ID
    """
    payload = verify_token(token)
    user_id = int(payload.get("sub"))
    
    success = await dream_service.delete_dream(
        db=db, 
        dream_id=dream_id, 
        user_id=user_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Dream entry not found")
    
    return {"message": "Dream deleted successfully"}

@dream_router.put(
    "/{dream_id}",
    response_model=DreamInterpretationResponse,
    responses={
        200: {"description": "Dream updated successfully"},
        404: {"description": "Dream not found"},
        401: {"description": "Unauthorized"},
        422: {"description": "Validation Error"}
    }
)
async def update_dream(
    dream_id: int,
    dream_data: DreamUpdateRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> DreamInterpretationResponse:
    """
    Update a dream entry by ID
    """
    payload = verify_token(token)
    user_id = int(payload.get("sub"))
    
    updated_dream = await dream_service.update_dream(
        db=db,
        dream_id=dream_id,
        user_id=user_id,
        title=dream_data.title,
        description=dream_data.description,
        emotions=dream_data.emotions
    )
    
    if not updated_dream:
        raise HTTPException(status_code=404, detail="Dream entry not found")
    
    return updated_dream
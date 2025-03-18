from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.backend.databases import get_db
from src.backend.services.feedback_service import FeedbackService
from src.backend.models.schemas import FeedbackCreateRequest, FeedbackResponse
from src.backend.utils.auth import verify_token
from typing import List

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

feedback_router = APIRouter(
    prefix="/feedback",
    tags=["feedback"]
)
feedback_service = FeedbackService()

@feedback_router.post(
    "/", 
    response_model=FeedbackResponse,
    status_code=201,
    responses={
        201: {"description": "Successfully submitted feedback"},
        401: {"description": "Unauthorized"},
        422: {"description": "Validation Error"}
    }
)
async def submit_feedback(
    feedback_data: FeedbackCreateRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> FeedbackResponse:
    """
    Submit user feedback
    """
    try:
        # Verify the token and get user information
        payload = verify_token(token)
        user_id = int(payload.get("sub"))
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Create the feedback entry
        feedback = await feedback_service.create_feedback(
            db=db,
            user_id=user_id,
            feedback_data=feedback_data
        )

        # Return feedback response
        return FeedbackResponse(
            id=feedback.id,
            content=feedback.content,
            rating=feedback.rating,
            timestamp=feedback.timestamp
        )
    except Exception as e:
        print(e)
        # Handle any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


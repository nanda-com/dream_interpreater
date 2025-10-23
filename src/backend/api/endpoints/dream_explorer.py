"""
Dream Explorer API Endpoints
Provides conversational interface to explore dream history.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from typing import List

from src.backend.databases import get_db
from src.backend.utils.auth import verify_token
from src.backend.models.schemas import (
    DreamExplorerQuery,
    DreamExplorerResponse,
    PatternSearchRequest,
    PatternSearchResponse,
    SimilarDreamsRequest,
    SimilarDreamsResponse,
    CompareDreamsRequest,
    CompareDreamsResponse,
    DreamSummary
)
from src.backend.services.dream_explorer_service import get_explorer_service
from src.backend.services.dream_retrieval_service import get_retrieval_service


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

dream_explorer_router = APIRouter(
    prefix="/dream-explorer",
    tags=["Dream Explorer"]
)


@dream_explorer_router.post(
    "/ask",
    response_model=DreamExplorerResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Successfully generated response"},
        401: {"description": "Unauthorized"},
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"}
    }
)
async def ask_question(
    query: DreamExplorerQuery,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> DreamExplorerResponse:
    """
    Ask a question about your dream history.

    This endpoint allows you to have a conversation with your dream journal.
    Ask questions like:
    - "What do my dreams about flying usually mean?"
    - "Have I ever dreamt about my childhood friend before?"
    - "I felt really anxious in my dream last night. Is that common in my dreams?"

    The AI will retrieve relevant dreams from your history and provide
    personalized insights based on your specific dream experiences.
    """
    # Verify token and get user_id
    payload = verify_token(token)
    user_id = int(payload.get("sub"))

    try:
        logger.info(f"Processing dream explorer query for user {user_id}")

        # Get explorer service
        explorer_service = get_explorer_service()

        # Process the question
        result = await explorer_service.ask_question(
            db=db,
            user_id=user_id,
            question=query.question,
            chat_history=query.chat_history,
            top_k=query.top_k
        )

        return DreamExplorerResponse(**result)

    except Exception as e:
        logger.error(f"Error in ask_question endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process question: {str(e)}"
        )


@dream_explorer_router.post(
    "/search",
    response_model=SimilarDreamsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Successfully retrieved similar dreams"},
        401: {"description": "Unauthorized"},
        422: {"description": "Validation Error"}
    }
)
async def search_similar_dreams(
    request: SimilarDreamsRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> SimilarDreamsResponse:
    """
    Search for dreams using natural language query.

    Performs semantic search across your dream history to find dreams
    that are similar to your search query. You can filter by date range
    and emotion tags.

    Example queries:
    - "dreams about water and oceans"
    - "anxiety-filled nightmares"
    - "flying and freedom"
    """
    # Verify token and get user_id
    payload = verify_token(token)
    user_id = int(payload.get("sub"))

    if not request.query:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query is required for search"
        )

    try:
        logger.info(f"Searching similar dreams for user {user_id}")

        # Get retrieval service
        retrieval_service = get_retrieval_service()

        # Search for similar dreams
        similar_dreams = await retrieval_service.search_similar_dreams(
            db=db,
            user_id=user_id,
            query=request.query,
            top_k=request.top_k,
            start_date=request.start_date,
            end_date=request.end_date,
            emotion_tags=request.emotion_tags
        )

        # Format response
        dream_summaries = [
            DreamSummary(
                dream_id=dream.id,
                title=dream.title or "Untitled",
                date=dream.timestamp.isoformat() if dream.timestamp else None,
                relevance_score=float(score)
            )
            for dream, score in similar_dreams
        ]

        return SimilarDreamsResponse(
            dreams=dream_summaries,
            total_found=len(dream_summaries)
        )

    except Exception as e:
        logger.error(f"Error in search_similar_dreams endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search dreams: {str(e)}"
        )


@dream_explorer_router.get(
    "/similar/{dream_id}",
    response_model=SimilarDreamsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Successfully retrieved similar dreams"},
        401: {"description": "Unauthorized"},
        404: {"description": "Dream not found"}
    }
)
async def find_similar_to_dream(
    dream_id: int,
    top_k: int = 5,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> SimilarDreamsResponse:
    """
    Find dreams that are similar to a specific dream.

    Given a dream ID, this endpoint finds other dreams in your history
    that share similar themes, symbols, or content.

    Useful for:
    - Discovering patterns in your dreams
    - Finding related dreams
    - Exploring dream themes over time
    """
    # Verify token and get user_id
    payload = verify_token(token)
    user_id = int(payload.get("sub"))

    try:
        logger.info(f"Finding dreams similar to {dream_id} for user {user_id}")

        # Get retrieval service
        retrieval_service = get_retrieval_service()

        # Find similar dreams
        similar_dreams = await retrieval_service.find_similar_to_dream(
            db=db,
            dream_id=dream_id,
            user_id=user_id,
            top_k=top_k
        )

        # Format response
        dream_summaries = [
            DreamSummary(
                dream_id=dream.id,
                title=dream.title or "Untitled",
                date=dream.timestamp.isoformat() if dream.timestamp else None,
                relevance_score=float(score)
            )
            for dream, score in similar_dreams
        ]

        return SimilarDreamsResponse(
            dreams=dream_summaries,
            total_found=len(dream_summaries)
        )

    except Exception as e:
        logger.error(f"Error in find_similar_to_dream endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar dreams: {str(e)}"
        )


@dream_explorer_router.post(
    "/patterns",
    response_model=PatternSearchResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Successfully analyzed patterns"},
        401: {"description": "Unauthorized"},
        422: {"description": "Validation Error"}
    }
)
async def find_patterns(
    request: PatternSearchRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> PatternSearchResponse:
    """
    Find patterns in your dream history.

    Analyzes your dreams to identify:
    - Recurring themes and symbols
    - Common emotions or situations
    - Evolution of patterns over time
    - Psychological insights

    Example pattern queries:
    - "recurring nightmares"
    - "water and ocean imagery"
    - "anxiety dreams"
    - "dreams about family"
    """
    # Verify token and get user_id
    payload = verify_token(token)
    user_id = int(payload.get("sub"))

    try:
        logger.info(f"Finding patterns for user {user_id}")

        # Get explorer service
        explorer_service = get_explorer_service()

        # Find patterns
        result = await explorer_service.find_patterns(
            db=db,
            user_id=user_id,
            pattern_query=request.pattern_query,
            top_k=request.top_k
        )

        return PatternSearchResponse(**result)

    except Exception as e:
        logger.error(f"Error in find_patterns endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find patterns: {str(e)}"
        )


@dream_explorer_router.post(
    "/compare",
    response_model=CompareDreamsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Successfully compared dreams"},
        401: {"description": "Unauthorized"},
        404: {"description": "One or both dreams not found"},
        422: {"description": "Validation Error"}
    }
)
async def compare_dreams(
    request: CompareDreamsRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> CompareDreamsResponse:
    """
    Compare two dreams and get insights about their connections.

    This endpoint analyzes two dreams side-by-side and identifies:
    - Similarities in themes, symbols, or emotions
    - Key differences
    - Possible connections or evolution between the dreams
    - Insights about what these dreams might reveal together

    Useful for understanding how your dreams evolve over time
    or finding connections between seemingly unrelated dreams.
    """
    # Verify token and get user_id
    payload = verify_token(token)
    user_id = int(payload.get("sub"))

    try:
        logger.info(
            f"Comparing dreams {request.dream_id_1} and {request.dream_id_2} "
            f"for user {user_id}"
        )

        # Get explorer service
        explorer_service = get_explorer_service()

        # Compare dreams
        comparison = await explorer_service.compare_dreams(
            db=db,
            dream_id_1=request.dream_id_1,
            dream_id_2=request.dream_id_2,
            user_id=user_id
        )

        return CompareDreamsResponse(comparison=comparison)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in compare_dreams endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare dreams: {str(e)}"
        )


@dream_explorer_router.get(
    "/health",
    status_code=status.HTTP_200_OK
)
async def health_check():
    """
    Check if Dream Explorer service is operational.
    """
    try:
        # Try to initialize the services
        get_explorer_service()
        get_retrieval_service()

        return {
            "status": "healthy",
            "service": "Dream Explorer",
            "message": "All systems operational"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

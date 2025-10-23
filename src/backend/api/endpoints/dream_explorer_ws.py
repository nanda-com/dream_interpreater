"""
Dream Explorer WebSocket Endpoints
Provides real-time streaming responses for dream exploration.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from typing import Optional
import json

from src.backend.databases import get_db
from src.backend.utils.auth import verify_token
from src.backend.services.dream_explorer_service import get_explorer_service
from src.backend.services.dream_retrieval_service import get_retrieval_service


dream_explorer_ws_router = APIRouter(
    prefix="/dream-explorer/ws",
    tags=["Dream Explorer WebSocket"]
)


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """Accept and store a WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")

    def disconnect(self, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")

    async def send_message(self, session_id: str, message: dict):
        """Send a message to a specific connection."""
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

    async def send_text(self, session_id: str, text: str):
        """Send text to a specific connection."""
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(text)


# Global connection manager
manager = ConnectionManager()


@dream_explorer_ws_router.websocket("/ask/{session_id}")
async def websocket_ask_question(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for asking questions with streaming responses.

    The client sends:
    {
        "question": "What do my flying dreams mean?",
        "chat_history": [...],
        "top_k": 5
    }

    The server streams back:
    {
        "type": "status",
        "message": "Retrieving relevant dreams..."
    }
    {
        "type": "dreams_found",
        "count": 3,
        "dreams": [...]
    }
    {
        "type": "answer_chunk",
        "chunk": "Your flying dreams..."
    }
    {
        "type": "complete",
        "answer": "Full answer...",
        "relevant_dreams": [...],
        "chat_history": [...]
    }
    """
    await manager.connect(session_id, websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Validate token if provided
            user_id = None
            if token:
                try:
                    payload = verify_token(token)
                    user_id = int(payload.get("sub"))
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Authentication failed"
                    })
                    continue

            # Extract request data
            question = data.get("question")
            chat_history = data.get("chat_history", [])
            top_k = data.get("top_k")

            if not question:
                await websocket.send_json({
                    "type": "error",
                    "message": "Question is required"
                })
                continue

            # Get database session
            async for db in get_db():
                try:
                    # Send status update
                    await websocket.send_json({
                        "type": "status",
                        "message": "Retrieving relevant dreams..."
                    })

                    # Get services
                    explorer_service = get_explorer_service()
                    retrieval_service = get_retrieval_service()

                    # Retrieve relevant dreams
                    similar_dreams = await retrieval_service.search_similar_dreams(
                        db=db,
                        user_id=user_id or 1,  # Default user if not authenticated
                        query=question,
                        top_k=top_k
                    )

                    # Send dreams found
                    dream_summaries = [
                        {
                            "dream_id": dream.id,
                            "title": dream.title or "Untitled",
                            "date": dream.timestamp.isoformat() if dream.timestamp else None,
                            "relevance_score": float(score)
                        }
                        for dream, score in similar_dreams
                    ]

                    await websocket.send_json({
                        "type": "dreams_found",
                        "count": len(dream_summaries),
                        "dreams": dream_summaries
                    })

                    # Send status update
                    await websocket.send_json({
                        "type": "status",
                        "message": "Generating response..."
                    })

                    # Generate response
                    result = await explorer_service.ask_question(
                        db=db,
                        user_id=user_id or 1,
                        question=question,
                        chat_history=chat_history,
                        top_k=top_k
                    )

                    # Stream answer in chunks (simulated streaming)
                    answer = result["answer"]
                    chunk_size = 50  # Characters per chunk

                    for i in range(0, len(answer), chunk_size):
                        chunk = answer[i:i + chunk_size]
                        await websocket.send_json({
                            "type": "answer_chunk",
                            "chunk": chunk
                        })

                    # Send complete response
                    await websocket.send_json({
                        "type": "complete",
                        "answer": answer,
                        "relevant_dreams": dream_summaries,
                        "chat_history": result["chat_history"]
                    })

                except Exception as e:
                    logger.error(f"Error in WebSocket handler: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Error processing request: {str(e)}"
                    })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(session_id)


@dream_explorer_ws_router.websocket("/search/{session_id}")
async def websocket_search(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for searching dreams with real-time updates.

    The client sends:
    {
        "query": "flying dreams",
        "top_k": 5,
        "start_date": null,
        "end_date": null,
        "emotion_tags": []
    }

    The server streams back:
    {
        "type": "searching",
        "message": "Searching your dream history..."
    }
    {
        "type": "result",
        "dream": {...}
    }
    {
        "type": "complete",
        "total_found": 5
    }
    """
    await manager.connect(session_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()

            # Validate token if provided
            user_id = None
            if token:
                try:
                    payload = verify_token(token)
                    user_id = int(payload.get("sub"))
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Authentication failed"
                    })
                    continue

            # Extract request data
            query = data.get("query")
            top_k = data.get("top_k")
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            emotion_tags = data.get("emotion_tags")

            if not query:
                await websocket.send_json({
                    "type": "error",
                    "message": "Query is required"
                })
                continue

            # Get database session
            async for db in get_db():
                try:
                    # Send searching status
                    await websocket.send_json({
                        "type": "searching",
                        "message": "Searching your dream history..."
                    })

                    # Get retrieval service
                    retrieval_service = get_retrieval_service()

                    # Search for similar dreams
                    similar_dreams = await retrieval_service.search_similar_dreams(
                        db=db,
                        user_id=user_id or 1,
                        query=query,
                        top_k=top_k,
                        start_date=start_date,
                        end_date=end_date,
                        emotion_tags=emotion_tags
                    )

                    # Stream results one by one
                    for dream, score in similar_dreams:
                        await websocket.send_json({
                            "type": "result",
                            "dream": {
                                "dream_id": dream.id,
                                "title": dream.title or "Untitled",
                                "date": dream.timestamp.isoformat() if dream.timestamp else None,
                                "relevance_score": float(score),
                                "description": dream.description[:200] + "..." if len(dream.description) > 200 else dream.description
                            }
                        })

                    # Send completion
                    await websocket.send_json({
                        "type": "complete",
                        "total_found": len(similar_dreams)
                    })

                except Exception as e:
                    logger.error(f"Error in WebSocket search: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Error searching dreams: {str(e)}"
                    })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"Search client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket search error: {str(e)}")
        manager.disconnect(session_id)

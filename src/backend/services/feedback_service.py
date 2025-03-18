from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from src.backend.models.feedback import Feedback
from src.backend.models.schemas import FeedbackCreateRequest, FeedbackResponse
from datetime import datetime

class FeedbackService:
    async def create_feedback(
        self, 
        db: AsyncSession, 
        user_id: int, 
        feedback_data: FeedbackCreateRequest
    ) -> Feedback:
        """Create a new feedback entry"""
        new_feedback = Feedback(
            user_id=user_id,
            content=feedback_data.content,
            rating=feedback_data.rating,
            timestamp=datetime.utcnow()
        )
        db.add(new_feedback)
        await db.commit()
        await db.refresh(new_feedback)
        
        return new_feedback
    
    async def get_user_feedback(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> List[Feedback]:
        """Get all feedback entries for a specific user"""
        result = await db.execute(
            select(Feedback)
            .where(Feedback.user_id == user_id)
            .order_by(Feedback.timestamp.desc())
        )
        
        return result.scalars().all()
    
    async def get_all_feedback(
        self, 
        db: AsyncSession
    ) -> List[Feedback]:
        """Get all feedback entries (admin function)"""
        result = await db.execute(
            select(Feedback)
            .order_by(Feedback.timestamp.desc())
        )
        
        return result.scalars().all() 
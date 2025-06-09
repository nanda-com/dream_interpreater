from typing import List, Optional
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.models.schemas import DreamInterpretationResponse
from src.backend.ai_interpreters.gemini_interpreter import GeminiDreamInterpreter
from src.backend.models.dreamentry import DreamEntry
from src.backend.models.reported_dream import ReportedDream

class DreamService:
    def __init__(self, ai_interpreter: Optional[GeminiDreamInterpreter] = None):
        # Allow optional AI interpreter
        self.ai_interpreter = ai_interpreter or GeminiDreamInterpreter()

    async def create_dream(
        self,
        db: AsyncSession,
        user_id: int,
        description: str,
        title: Optional[str] = None,
        emotions: Optional[List[str]] = None,
        timestamp: Optional[datetime] = None
    ) -> DreamEntry:
   
        # Get AI interpretation
        # The updated interpret_dream method returns a tuple (interpretation, title)
        interpretation, ai_title = self.ai_interpreter.interpret_dream(description, title)
        
        # Use provided title if available, otherwise use AI-generated title
        final_title = title or ai_title
        
        # If still no title, generate one as fallback
        if not final_title:
            final_title = self.ai_interpreter.generate_dream_title(description) or "Untitled Dream"
            
        # Ensure title isn't too long
        if final_title:
            final_title = final_title[:35]  

        # Create dream entry
        dream_entry = DreamEntry(
            user_id=user_id,
            title=final_title,
            description=description,
            interpretation=interpretation,
            emotion_tags=",".join(emotions) if emotions else None,
            timestamp=timestamp or datetime.utcnow()
        )

        
        try:
            db.add(dream_entry)
            await db.commit()
            await db.refresh(dream_entry)
            
        except Exception as e:
            print("debug: error adding dream to db: ", e)
            raise HTTPException(status_code=500, detail=str(e))
        
        # print(dream_entry.interpretation)
        return dream_entry

    async def list_user_dreams(
        self,
        db: AsyncSession,
        user_id: int
    ) -> List[DreamEntry]:
        result = await db.execute(
            select(DreamEntry)
            .where(DreamEntry.user_id == user_id)
            .order_by(DreamEntry.timestamp.desc())
        )
        return result.scalars().all()

    async def delete_dream(
        self,
        db: AsyncSession,
        dream_id: int,
        user_id: int
    ) -> bool:
        """
        Delete a dream entry by ID. Ensures the dream belongs to the user.
        Also deletes any associated reports to maintain referential integrity.
        Returns True if deletion was successful, False if dream was not found.
        """
        # First verify the dream exists and belongs to the user
        result = await db.execute(
            select(DreamEntry)
            .where(DreamEntry.id == dream_id)
            .where(DreamEntry.user_id == user_id)
        )
        dream = result.scalars().first()
        
        if not dream:
            return False
            
        try:
            # First delete any associated reports
            await db.execute(
                delete(ReportedDream)
                .where(ReportedDream.dream_id == dream_id)
            )
            
            # Then delete the dream entry
            await db.delete(dream)
            await db.commit()
            return True
            
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        
    async def update_dream(
        self,
        db: AsyncSession,
        dream_id: int,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        emotions: Optional[List[str]] = None,
        timestamp: Optional[datetime] = None
    ) -> Optional[DreamEntry]:
        """
        Update a dream entry. If description is changed, re-interpret the dream.
        Returns updated dream entry if found, None otherwise.
        """
        result = await db.execute(
            select(DreamEntry)
            .where(DreamEntry.id == dream_id)
            .where(DreamEntry.user_id == user_id)
        )
        dream = result.scalars().first()
        
        if not dream:
            return None
            
        # Update fields if provided
        if title is not None:
            dream.title = title
            
        # If description changed, re-interpret the dream
        if description is not None and description != dream.description:
            dream.description = description
            new_interpretation, new_title = self.ai_interpreter.interpret_dream(description, title)
            dream.interpretation = new_interpretation
            # Only update title if not explicitly provided
            if title is None:
                dream.title = new_title[:35] if new_title else dream.title
            
        # Update emotions if provided
        if emotions is not None:
            dream.emotion_tags = ",".join(emotions) if emotions else None
            
        # Update timestamp if provided
        if timestamp is not None:
            dream.timestamp = timestamp
            
        await db.commit()
        await db.refresh(dream)
        return dream

    async def report_dream(
        self,
        db: AsyncSession,
        dream_id: int,
        user_id: int,
        reason: Optional[str] = None
    ) -> ReportedDream:
        """
        Report a dream entry. Creates a new entry in the reported_dreams table.
        Returns the created report entry.
        """
        # First verify the dream exists
        result = await db.execute(
            select(DreamEntry)
            .where(DreamEntry.id == dream_id)
        )
        dream = result.scalars().first()
        
        if not dream:
            raise HTTPException(status_code=404, detail="Dream not found")
            
        # Create report entry
        report_entry = ReportedDream(
            dream_id=dream_id,
            user_id=user_id,
            reason=reason,
            timestamp=datetime.utcnow()
        )
        
        try:
            db.add(report_entry)
            await db.commit()
            await db.refresh(report_entry)
            return report_entry
            
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

def get_dream_service() -> DreamService:
    """
    Dependency function to get DreamService instance
    """
    return DreamService()
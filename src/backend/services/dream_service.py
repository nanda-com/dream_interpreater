from typing import List, Optional
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.models.schemas import DreamInterpretationResponse
from src.backend.ai_interpreters.gemini_interpreter import GeminiDreamInterpreter
from src.backend.models.dreamentry import DreamEntry

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
        interpretation = self.ai_interpreter.interpret_dream(description)
        
        # Generate title if not provided
        if not title:
            title = self.ai_interpreter.generate_dream_title(description)
            title = title[:35]  

        # Create dream entry
        dream_entry = DreamEntry(
            user_id=user_id,
            title=title,
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
        Returns True if deletion was successful, False if dream was not found.
        """
        result = await db.execute(
            select(DreamEntry)
            .where(DreamEntry.id == dream_id)
            .where(DreamEntry.user_id == user_id)
        )
        dream = result.scalars().first()
        
        if not dream:
            return False
            
        await db.delete(dream)
        await db.commit()
        return True
        
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
            dream.interpretation = self.ai_interpreter.interpret_dream(description)
            
        # Update emotions if provided
        if emotions is not None:
            dream.emotion_tags = ",".join(emotions) if emotions else None
            
        # Update timestamp if provided
        if timestamp is not None:
            dream.timestamp = timestamp
            
        await db.commit()
        await db.refresh(dream)
        return dream
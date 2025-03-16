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
        emotions: Optional[List[str]] = None
    ) -> DreamEntry:
   
        # Get AI interpretation
        interpretation = self.ai_interpreter.interpret_dream(description)
        
        # Generate title if not provided
        if not title:
            title = self.ai_interpreter.generate_dream_title(description)

        # Create dream entry
        dream_entry = DreamEntry(
            user_id=user_id,
            title=title,
            description=description,
            interpretation=interpretation,
            emotion_tags=",".join(emotions) if emotions else None,
            timestamp=datetime.utcnow()
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
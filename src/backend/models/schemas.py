from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional

class DreamCreateRequest(BaseModel):
    description: str = Field(
        ..., 
        min_length=10, 
        max_length=2000, 
        description="Detailed dream description"
    )
    date: Optional[datetime] = Field(default_factory=datetime.now)
    emotions: Optional[List[str]] = None
    tags: Optional[List[str]] = None

    @validator('description')
    def validate_description(cls, description):
        if len(description.split()) < 5:
            raise ValueError("Dream description is too short")
        return description

class DreamInterpretationResponse(BaseModel):
    id: Optional[str] = None
    description: str
    interpretation: str
    date: datetime
    emotions: Optional[List[str]] = None
from pydantic import BaseModel, Field, field_validator, constr
from datetime import datetime
from typing import List, Optional

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username for the user")
    password: str = Field(..., min_length=6, description="Password for the user")

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

    @field_validator('description')
    @classmethod
    def validate_description(cls, description):
        if len(description.split()) < 2:
            raise ValueError("Dream description is too short")
        return description

class UserLogin(BaseModel):
    username: str = Field(..., description="Username for login")
    password: str = Field(..., description="Password for login")

class DreamInterpretationResponse(BaseModel):
    id: Optional[str] = None
    description: str
    interpretation: str
    title: Optional[str] = None
    date: datetime
    emotions: Optional[List[str]] = None

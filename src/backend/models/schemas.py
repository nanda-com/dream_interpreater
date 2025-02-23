from pydantic import BaseModel, Field, field_validator, constr
from datetime import datetime
from typing import List, Optional

class UserCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=20, description="Name for the user")
    email: str = Field(..., max_length=30, description="Email address for the user") 
    password: str = Field(..., min_length=6,max_length=60, description="Password for the user")

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
    email: str = Field(..., description="Email address for login")
    email: str = Field(..., description="Email address for login")  # Optional: Allow login via email
    password: str = Field(..., description="Password for login")

class DreamInterpretationResponse(BaseModel):
    id: Optional[str] = None
    description: str
    interpretation: str
    title: Optional[str] = None
    date: datetime
    emotions: Optional[List[str]] = None

from pydantic import BaseModel, Field, field_validator, constr
from datetime import datetime
from typing import List, Optional

class UserCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=20, description="Name for the user")
    email: str = Field(..., max_length=30, description="Email address for the user") 
    password: str = Field(..., min_length=6,max_length=60, description="Password for the user")
    isGuest: bool = Field(default=False, description="Flag indicating if the user is a guest")

class DreamCreateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
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
    password: str = Field(..., description="Password for login")

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    isGuest: bool

class DreamInterpretationResponse(BaseModel):
    id: Optional[int] = None
    description: str
    interpretation: str
    title: Optional[str] = None
    timestamp: datetime
    emotions: Optional[List[str]] = None

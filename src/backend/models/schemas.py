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
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    emotions: Optional[List[str]] = None
    tags: Optional[List[str]] = None

    @field_validator('description')
    @classmethod
    def validate_description(cls, description):
        if len(description.split()) < 2:
            raise ValueError("Dream description is too short")
        return description

class DreamUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(
        None, 
        min_length=10, 
        max_length=2000, 
        description="Updated dream description"
    )
    timestamp: Optional[datetime] = None
    emotions: Optional[List[str]] = None

    @field_validator('description')
    @classmethod
    def validate_description(cls, description):
        if description is not None and len(description.split()) < 2:
            raise ValueError("Dream description is too short")
        return description

class FeedbackCreateRequest(BaseModel):
    content: str = Field(
        ..., 
        min_length=1, 
        max_length=1000, 
        description="Feedback content from the user"
    )
    rating: Optional[int] = Field(
        None, 
        ge=1, 
        le=5, 
        description="Optional rating from 1-5"
    )

class FeedbackResponse(BaseModel):
    id: int
    content: str
    rating: Optional[int] = None
    timestamp: datetime

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
    date_created: datetime

class DreamInterpretationResponse(BaseModel):
    id: Optional[int] = None
    description: str
    interpretation: str
    title: Optional[str] = None
    timestamp: datetime
    emotions: Optional[List[str]] = None

class GuestToRegularConversion(BaseModel):
    name: str = Field(..., min_length=3, max_length=20, description="New name for the user")
    email: str = Field(..., max_length=30, description="New email address for the user") 
    password: str = Field(..., min_length=6, max_length=60, description="New password for the user")

class GoogleAuthRequest(BaseModel):
    """Schema for Google authentication token data"""
    token: str = Field(..., description="Google authentication token")
    token_type: str = Field(default="id_token", description="Type of token provided. Can be 'id_token' or 'access_token'")

class GoogleUserInfo(BaseModel):
    """Schema for Google user information"""
    id: str
    email: str
    name: str
    picture: Optional[str] = None

class UserUpdateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=20, description="Updated name for the user")

class ReportedDreamCreateRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=200, description="Reason for reporting the dream")

class ReportedDreamResponse(BaseModel):
    id: int
    dream_id: int
    user_id: int
    reason: Optional[str] = None
    timestamp: datetime

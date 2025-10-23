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

# Dream Explorer Schemas
class DreamExplorerQuery(BaseModel):
    """Schema for asking questions about dream history."""
    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Question about dream history"
    )
    chat_history: Optional[List[dict]] = Field(
        default=[],
        description="Previous conversation messages"
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Number of relevant dreams to retrieve"
    )

class DreamSummary(BaseModel):
    """Summary of a dream for response."""
    dream_id: int
    title: str
    date: Optional[str] = None
    relevance_score: float = Field(..., ge=0.0, le=1.0)

class DreamExplorerResponse(BaseModel):
    """Response from Dream Explorer."""
    answer: str
    relevant_dreams: List[DreamSummary]
    chat_history: List[dict]

class PatternSearchRequest(BaseModel):
    """Request to find patterns in dream history."""
    pattern_query: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Description of the pattern to find"
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=50,
        description="Number of dreams to analyze"
    )

class PatternSearchResponse(BaseModel):
    """Response with pattern analysis."""
    pattern_analysis: str
    relevant_dreams: List[DreamSummary]

class SimilarDreamsRequest(BaseModel):
    """Request to find similar dreams."""
    query: Optional[str] = Field(
        None,
        min_length=3,
        max_length=500,
        description="Search query"
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Number of similar dreams to return"
    )
    start_date: Optional[datetime] = Field(
        None,
        description="Filter dreams after this date"
    )
    end_date: Optional[datetime] = Field(
        None,
        description="Filter dreams before this date"
    )
    emotion_tags: Optional[List[str]] = Field(
        None,
        description="Filter by emotion tags"
    )

class SimilarDreamsResponse(BaseModel):
    """Response with similar dreams."""
    dreams: List[DreamSummary]
    total_found: int

class CompareDreamsRequest(BaseModel):
    """Request to compare two dreams."""
    dream_id_1: int = Field(..., description="ID of first dream")
    dream_id_2: int = Field(..., description="ID of second dream")

class CompareDreamsResponse(BaseModel):
    """Response with dream comparison."""
    comparison: str

from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime
from datetime import datetime
from src.backend.databases import Base

class Feedback(Base):
    __tablename__ = 'user_feedback'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # Optional rating (e.g., 1-5 stars)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<Feedback(id={self.id}, user_id={self.user_id}, timestamp={self.timestamp})>" 
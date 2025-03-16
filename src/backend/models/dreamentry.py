from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime
from datetime import datetime
from src.backend.databases import Base

class DreamEntry(Base):
    __tablename__ = 'dream_entries'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=True)  # Add title field
    description = Column(Text, nullable=False)
    interpretation = Column(Text)
    email = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    emotion_tags = Column(String(100))
    image_url = Column(String(200))
    video_url = Column(String(200))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<DreamEntry(id={self.id}, user_id={self.user_id}, timestamp={self.timestamp})>"

from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from src.backend.databases import Base

class DreamEntry(Base):
    __tablename__ = 'dream_entries'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    interpretation = Column(Text)
    emotion_tags = Column(String(100))
    image_url = Column(String(200))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<DreamEntry(id={self.id}, user_id={self.user_id}, timestamp={self.timestamp})>"

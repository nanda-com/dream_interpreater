from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from datetime import datetime
from src.backend.databases import Base

class ReportedDream(Base):
    __tablename__ = 'reported_dreams'
    
    id = Column(Integer, primary_key=True, index=True)
    dream_id = Column(Integer, ForeignKey('dream_entries.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reason = Column(String(200), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<ReportedDream(id={self.id}, dream_id={self.dream_id}, user_id={self.user_id})>" 
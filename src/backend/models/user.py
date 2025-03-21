from sqlalchemy import Column, Integer, String, Boolean, DateTime
from src.backend.databases import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), nullable=False)
    password = Column(String(60), nullable=False)
    email = Column(String(30), unique=True, nullable=False)  # New email field
    isGuest = Column(Boolean, default=False, nullable=False)  # New isGuest field
    google_id = Column(String(100), unique=True, nullable=True)  # Google ID for OAuth
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)  # Date when user was created

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, email={self.email}, isGuest={self.isGuest})>"

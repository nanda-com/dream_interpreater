# src/backend/database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# SQL Alchemy Setup
Base = declarative_base()
engine = create_engine('sqlite:///dream_journal.db')
SessionLocal = sessionmaker(bind=engine)

class DreamEntry(Base):
    __tablename__ = 'dream_entries'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    interpretation = Column(Text)
    emotion_tags = Column(String)
    image_url = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)
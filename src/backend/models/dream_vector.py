from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from pgvector.sqlalchemy import Vector
from src.backend.databases import Base


class DreamVector(Base):
    """
    Model to store dream embeddings for semantic search.
    Uses pgvector extension for efficient similarity search.
    """
    __tablename__ = 'dream_vectors'

    id = Column(Integer, primary_key=True, index=True)
    dream_id = Column(Integer, ForeignKey('dream_entries.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    embedding = Column(Vector(384), nullable=False)  # 384 dimensions for all-MiniLM-L6-v2
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Ensure one embedding per dream
    __table_args__ = (
        UniqueConstraint('dream_id', name='uq_dream_vector_dream_id'),
    )

    def __repr__(self):
        return f"<DreamVector(id={self.id}, dream_id={self.dream_id}, user_id={self.user_id})>"

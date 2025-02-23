from sqlalchemy import Column, Integer, String
from src.backend.databases import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)  # New email field

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

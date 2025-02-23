from sqlalchemy import Column, Integer, String
from src.backend.databases import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), nullable=False)
    password = Column(String(30), nullable=False)
    email = Column(String(30), unique=True, nullable=False)  # New email field

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, email={self.email})>"

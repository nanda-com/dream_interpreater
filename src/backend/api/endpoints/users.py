from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.backend.databases import get_db
from sqlalchemy.future import select
from src.backend.models.schemas import UserCreate, UserLogin
from src.backend.utils.auth import hash_password, create_jwt_token, verify_password
from src.backend.models import User

user_router = APIRouter(prefix="/users", tags=["users"])

@user_router.post("/register")
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if the user already exists
    existing_user = await db.execute(select(User).where(User.username == user.username))
    if existing_user.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")

    # Hash the password and create the user
    hashed_password = hash_password(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    return {"message": "User registered successfully"}

@user_router.post("/login")
async def login_user(user: UserLogin, db: AsyncSession = Depends(get_db)):
    # Verify user credentials
    existing_user = await db.execute(select(User).where(User.username == user.username))
    user_record = existing_user.scalars().first()
    if not user_record or not verify_password(user.password, user_record.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # Create JWT token
    token = create_jwt_token(user_record.id)
    return {"access_token": token, "token_type": "bearer"}

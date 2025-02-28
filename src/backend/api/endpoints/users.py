from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from src.backend.databases import get_db
from sqlalchemy.future import select
from src.backend.models.schemas import UserCreate, UserLogin
from src.backend.utils.auth import hash_password, create_jwt_token, verify_password, verify_token
from src.backend.models import User

user_router = APIRouter(prefix="/users", tags=["users"])

@user_router.post("/register")
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if the user already exists
    existing_email = await db.execute(select(User).where(User.email == user.email))
    if existing_email.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password and create the user
    hashed_password = hash_password(user.password)
    new_user = User(name=user.name, email=user.email, password=hashed_password)
    db.add(new_user)
    await db.commit()
    return {"message": "User registered successfully"}

@user_router.post("/login")
async def login_user(user: UserLogin, db: AsyncSession = Depends(get_db)):
    # Verify user credentials
    existing_user = await db.execute(select(User).where(User.email == user.email))
    user_record = existing_user.scalars().first()
    if not user_record or not verify_password(user.password, user_record.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # Create access and refresh tokens
    access_token = create_jwt_token(user_record.id)
    refresh_token = create_jwt_token(user_record.id, is_refresh_token=True)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@user_router.post("/refresh")
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    try:
        payload = verify_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user_id = int(payload.get("sub"))
        new_access_token = create_jwt_token(user_id)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@user_router.get("/test_DB")
async def test_database_connection(db: AsyncSession = Depends(get_db)):
    try:
        print("excecute query")
        result = await db.execute(text("SELECT version()"))
        print("excecuted query")
        print(result)
        version = result.scalar()
        return {"database_version": version}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from src.backend.databases import get_db
from sqlalchemy.future import select
from src.backend.models.schemas import UserCreate, UserLogin, Token, UserResponse, GuestToRegularConversion, GoogleAuthRequest, GoogleUserInfo
from src.backend.utils.auth import hash_password, create_jwt_token, verify_password, verify_token
from src.backend.utils.oauth.google import verify_google_token
from src.backend.models import User
import uuid
import random
import string

user_router = APIRouter(prefix="/users", tags=["users"])

@user_router.post("/register")
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if the user already exists
    existing_email = await db.execute(select(User).where(User.email == user.email))
    if existing_email.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password and create the user
    hashed_password = hash_password(user.password)
    new_user = User(name=user.name, email=user.email, password=hashed_password, isGuest=user.isGuest)
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
        "token_type": "bearer",
        "user": {
            "id": user_record.id,
            "name": user_record.name,
            "email": user_record.email,
            "isGuest": user_record.isGuest
        }
    }

# Add a new endpoint that works with OAuth2 password flow for Swagger UI
@user_router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Verify user credentials
    existing_user = await db.execute(select(User).where(User.email == form_data.username))
    user_record = existing_user.scalars().first()
    if not user_record or not verify_password(form_data.password, user_record.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_jwt_token(user_record.id)
    
    return {
        "access_token": access_token,
        "refresh_token": "",  # OAuth2 form doesn't need refresh token
        "token_type": "bearer",
        "user": {
            "id": user_record.id,
            "name": user_record.name,
            "email": user_record.email,
            "isGuest": user_record.isGuest
        }
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

@user_router.post("/guest")
async def create_guest_user(db: AsyncSession = Depends(get_db)):
    # Generate a random name, email, and password for the guest user
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    guest_name = f"Guest_{random_suffix}"
    guest_email = f"guest_{random_suffix}@guest.com"
    guest_password = str(uuid.uuid4())
    
    # Hash the password and create the guest user
    hashed_password = hash_password(guest_password)
    guest_user = User(name=guest_name, email=guest_email, password=hashed_password, isGuest=True)
    db.add(guest_user)
    await db.commit()
    
    # Create access and refresh tokens
    access_token = create_jwt_token(guest_user.id)
    refresh_token = create_jwt_token(guest_user.id, is_refresh_token=True)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": guest_user.id,
            "name": guest_user.name,
            "email": guest_user.email,
            "isGuest": guest_user.isGuest
        }
    }

# Add a function to get the current user
async def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/users/token")), db: AsyncSession = Depends(get_db)):
    try:
        payload = verify_token(token)
        user_id = int(payload.get("sub"))
        user_query = await db.execute(select(User).where(User.id == user_id))
        user = user_query.scalars().first()
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

@user_router.get("/me", response_model=UserResponse)
async def get_user_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "isGuest": current_user.isGuest
    }

@user_router.post("/convert-guest")
async def convert_guest_to_regular(
    user_data: GuestToRegularConversion, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if the current user is a guest
    if not current_user.isGuest:
        raise HTTPException(status_code=400, detail="Only guest users can be converted")
    
    # Check if the email is already registered by another user
    existing_email = await db.execute(
        select(User).where(
            (User.email == user_data.email) & 
            (User.id != current_user.id)
        )
    )
    if existing_email.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Update the user information
    current_user.name = user_data.name
    current_user.email = user_data.email
    current_user.password = hash_password(user_data.password)
    current_user.isGuest = False
    
    await db.commit()
    
    # Create new tokens
    access_token = create_jwt_token(current_user.id)
    refresh_token = create_jwt_token(current_user.id, is_refresh_token=True)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "isGuest": current_user.isGuest
        }
    }

@user_router.post("/auth/google")
async def login_with_google(google_data: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """
    Handle Google OAuth login with support for both ID tokens and access tokens
    """
    try:
        # Verify the Google token using the specified token type
        user_info = await verify_google_token(google_data.token, google_data.token_type)
        
        # Check if user with this Google ID exists
        user_by_google_id = await db.execute(select(User).where(User.google_id == user_info["id"]))
        user_record = user_by_google_id.scalars().first()
        
        # If not found by Google ID, try to find by email
        if not user_record:
            user_by_email = await db.execute(select(User).where(User.email == user_info["email"]))
            user_record = user_by_email.scalars().first()
            
            # If user exists with this email but no Google ID, update the user with Google ID
            if user_record:
                user_record.google_id = user_info["id"]
                await db.commit()
        
        # If user doesn't exist, create a new one
        if not user_record:
            # Generate a random password (user won't use it)
            random_password = str(uuid.uuid4())
            hashed_password = hash_password(random_password)
            
            # Create user
            new_user = User(
                name=user_info["name"], 
                email=user_info["email"],
                password=hashed_password,
                google_id=user_info["id"],
                isGuest=False
            )
            db.add(new_user)
            await db.commit()
            
            # Refresh to get the ID
            await db.refresh(new_user)
            user_record = new_user
        
        # Create tokens
        access_token = create_jwt_token(user_record.id)
        refresh_token = create_jwt_token(user_record.id, is_refresh_token=True)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user_record.id,
                "name": user_record.name,
                "email": user_record.email,
                "isGuest": user_record.isGuest
            }
        }
        
    except ValueError as e:
        if "GOOGLE_CLIENT_ID is not set" in str(e):
            raise HTTPException(
                status_code=500,
                detail="Server configuration error: Google Client ID is not configured. Please add GOOGLE_CLIENT_ID to your .env file."
            )
        raise HTTPException(status_code=401, detail=f"Invalid Google authentication: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google authentication: {str(e)}")

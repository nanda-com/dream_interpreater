import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from src.backend.utils.config import get_settings
from fastapi import HTTPException

settings = get_settings()

async def verify_google_token(token: str):
    """
    Verify a Google OAuth ID token and return the user's information
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID is not set in .env file")
        
    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        
        # Check if token is from Google
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Invalid issuer')
            
        # Extract user information
        user_info = {
            "id": idinfo['sub'],
            "email": idinfo['email'],
            "name": idinfo.get('name', ''),
            "picture": idinfo.get('picture', None)
        }
        
        return user_info
    except ValueError as e:
        # Invalid token
        raise ValueError(f"Invalid token: {str(e)}") 
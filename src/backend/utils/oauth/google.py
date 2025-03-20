import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from src.backend.utils.config import get_settings
from fastapi import HTTPException

settings = get_settings()

async def verify_google_token(token: str, token_type: str = "id_token"):
    """
    Verify a Google OAuth token and return the user's information
    
    Args:
        token: The token from Google OAuth
        token_type: The type of token, either "id_token" or "access_token"
    
    Returns:
        dict: User information from Google
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID is not set in .env file")
        
    try:
        if token_type == "id_token":
            # Verify the ID token using Google's libraries
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
        elif token_type == "access_token":
            # For access token, make a request to Google's userinfo endpoint
            response = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Check if the request was successful
            if response.status_code != 200:
                raise ValueError(f"Failed to get user info: {response.text}")
                
            # Parse the user information from the response
            user_data = response.json()
            user_info = {
                "id": user_data['sub'],
                "email": user_data['email'],
                "name": user_data.get('name', ''),
                "picture": user_data.get('picture', None)
            }
        else:
            raise ValueError(f"Invalid token_type: {token_type}. Must be 'id_token' or 'access_token'")
        
        return user_info
    except ValueError as e:
        # Invalid token
        raise ValueError(f"Invalid token: {str(e)}") 
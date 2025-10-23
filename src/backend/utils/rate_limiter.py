"""
Rate Limiting Utilities
Provides rate limiting for API endpoints to prevent abuse.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
import os


def get_user_identifier(request: Request) -> str:
    """
    Get user identifier for rate limiting.
    Uses user_id from token if available, otherwise uses IP address.
    """
    # Try to get user_id from request state (set by auth middleware)
    if hasattr(request.state, 'user_id'):
        return f"user:{request.state.user_id}"

    # Try to get from authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            from src.backend.utils.auth import verify_token
            token = auth_header.replace("Bearer ", "")
            payload = verify_token(token)
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except:
            pass

    # Fallback to IP address
    return get_remote_address(request)


# Check if we're in testing mode
IS_TESTING = os.getenv("TESTING", "0") == "1"

# Initialize rate limiter
# In testing mode, set enabled=False to disable rate limiting
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=[os.getenv("DEFAULT_RATE_LIMIT", "100/hour")],
    enabled=not IS_TESTING
)


# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    "dream_explorer_ask": "10/minute",  # Conversational queries (more expensive)
    "dream_explorer_search": "20/minute",  # Search queries
    "dream_explorer_patterns": "5/minute",  # Pattern analysis (very expensive)
    "dream_explorer_compare": "15/minute",  # Dream comparison
    "dream_explorer_similar": "30/minute",  # Finding similar dreams
}


def get_rate_limit(endpoint_type: str) -> str:
    """
    Get rate limit for a specific endpoint type.

    Args:
        endpoint_type: Type of endpoint

    Returns:
        Rate limit string (e.g., "10/minute")
    """
    return RATE_LIMITS.get(endpoint_type, "20/minute")

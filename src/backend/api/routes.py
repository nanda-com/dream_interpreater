from fastapi import APIRouter

# Import the specific router from dreams endpoint
from src.backend.api.endpoints.dreams import dream_router

# Create the main router
router = APIRouter()

# Include the dream router
router.include_router(dream_router)

# You can add more routers for other endpoints here
# For example:
# from src.backend.api.endpoints.users import user_router
# router.include_router(user_router)
from fastapi import APIRouter

# Import the specific router from dreams endpoint
from src.backend.api.endpoints.dreams import dream_router
from src.backend.api.endpoints.users import user_router
from src.backend.api.endpoints.feedback import feedback_router
from src.backend.api.endpoints.dream_explorer import dream_explorer_router
from src.backend.api.endpoints.dream_explorer_ws import dream_explorer_ws_router

# Create the main router
router = APIRouter()

# Include the dream router and user router
router.include_router(dream_router)
router.include_router(user_router)
router.include_router(feedback_router)
router.include_router(dream_explorer_router)
router.include_router(dream_explorer_ws_router)

# You can add more routers for other endpoints here
# For example:
# from src.backend.api.endpoints.users import user_router
# router.include_router(user_router)

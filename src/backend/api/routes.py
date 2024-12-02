from fastapi import APIRouter
from src.backend.api.endpoints.dreams import dream_router

router = APIRouter()

# Include endpoint routers
router.include_router(dream_router)
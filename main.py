import uvicorn
from fastapi import FastAPI, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.backend.databases import create_tables
from fastapi.middleware.cors import CORSMiddleware
from src.backend.api.routes import router
from src.backend.utils.config import get_settings
from src.backend.utils.rate_limiter import limiter
from src.backend.utils.error_handlers import (
    DreamExplorerException,
    dream_explorer_exception_handler,
    generic_exception_handler,
    validation_exception_handler
)
from fastapi.openapi.utils import get_openapi
from slowapi.errors import RateLimitExceeded

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_application() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI-powered Dream Interpretation API",
        version="1.0.0",
        swagger_ui_parameters={"persistAuthorization": True},
        redirect_slashes=False
    )

    # Add rate limiter state to app
    app.state.limiter = limiter

    # Add rate limit exception handler
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "detail": "Too many requests. Please try again later.",
                "retry_after": exc.detail
            }
        )

    # Add custom exception handlers
    app.add_exception_handler(DreamExplorerException, dream_explorer_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
            
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # Preserve existing components if they exist
        components = openapi_schema.get("components", {})
        
        # Update security schemes
        components["securitySchemes"] = {
            "OAuth2PasswordBearer": {
                "type": "oauth2",
                "flows": {
                    "password": {
                        "tokenUrl": "token",
                        "scopes": {}
                    }
                }
            }
        }
        
        # Update the components in the schema
        openapi_schema["components"] = components
        
        # Apply security globally
        openapi_schema["security"] = [
            {
                "OAuth2PasswordBearer": []
            }
        ]
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
    
    # Include router after OpenAPI setup
    app.include_router(router)
    return app

# Create app instance
app = create_application()

# Startup event
@app.on_event("startup")
async def startup_event():
    await create_tables()  # Call the create_tables function
    print(f"Starting {app.title} API")

# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )

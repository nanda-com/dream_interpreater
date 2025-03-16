import uvicorn
from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from src.backend.databases import create_tables
from fastapi.middleware.cors import CORSMiddleware
from src.backend.api.routes import router
from src.backend.utils.config import get_settings
from fastapi.openapi.utils import get_openapi

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_application() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI-powered Dream Interpretation API",
        version="1.0.0",
        swagger_ui_parameters={"persistAuthorization": True}
    )

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

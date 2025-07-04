from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import os
from dotenv import load_dotenv

# Import core API modules
from app.api.core import auth as core_auth
from app.api.core import calls as core_calls
from app.api.core import privacy as core_privacy

# Import enterprise API modules
from app.api.enterprise import admin as enterprise_admin
from app.api.enterprise import analytics as enterprise_analytics

# Load environment variables
load_dotenv()

app = FastAPI(
    title="SIP Call API", 
    version="1.0.0",
    description="Modular SIP calling API with core and enterprise features"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Include core API routers
app.include_router(core_auth.router, prefix="/api/v1/auth", tags=["Core - Authentication"])
app.include_router(core_calls.router, prefix="/api/v1/calls", tags=["Core - Calls"])
app.include_router(core_privacy.router, prefix="/api/v1/privacy", tags=["Core - Privacy"])

# Include enterprise API routers
app.include_router(enterprise_admin.router, prefix="/api/v1/admin", tags=["Enterprise - Administration"])
app.include_router(enterprise_analytics.router, prefix="/api/v1/analytics", tags=["Enterprise - Analytics"])

@app.get("/")
async def root():
    return {
        "message": "SIP Call API is running",
        "version": "1.0.0",
        "modules": {
            "core": ["auth", "calls", "privacy"],
            "enterprise": ["admin", "analytics"]
        }
    }

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/features")
async def get_available_features():
    """Return available features based on deployment type"""
    return {
        "core_features": [
            "authentication",
            "basic_calling",
            "call_history",
            "privacy_controls"
        ],
        "enterprise_features": [
            "admin_dashboard",
            "user_management", 
            "system_analytics",
            "cost_tracking",
            "quality_analytics",
            "advanced_reporting"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
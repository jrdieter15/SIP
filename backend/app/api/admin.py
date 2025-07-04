from fastapi import APIRouter, Depends, HTTPException
from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/status")
async def get_system_status(current_user: dict = Depends(get_current_user)):
    return {
        "system": "operational",
        "database": "connected",
        "freeswitch": "connected"
    }

@router.get("/users")
async def list_users(current_user: dict = Depends(get_current_user)):
    # Placeholder implementation
    return {"users": ["admin"]}
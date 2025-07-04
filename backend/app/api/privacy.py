from fastapi import APIRouter, Depends
from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/privacy", tags=["privacy"])

@router.get("/policy")
async def get_privacy_policy():
    return {
        "policy": "Privacy policy content here",
        "last_updated": "2024-01-01"
    }

@router.delete("/user-data")
async def delete_user_data(current_user: dict = Depends(get_current_user)):
    # Placeholder implementation for GDPR compliance
    return {"message": "User data deletion requested"}
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from ...auth.dependencies import get_current_user

router = APIRouter(tags=["admin"])

class SystemMetrics(BaseModel):
    active_calls: int
    total_users: int
    system_health: str
    database_status: str
    freeswitch_status: str

class UserSummary(BaseModel):
    user_id: str
    username: str
    email: str
    total_calls: int
    last_call: str = None
    is_active: bool

class UsersResponse(BaseModel):
    users: List[UserSummary]
    total_count: int

def check_admin_permissions(current_user: dict = Depends(get_current_user)):
    # In a real implementation, check if user has admin role
    # For now, allow all authenticated users
    return current_user

@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics(current_user: dict = Depends(check_admin_permissions)):
    return SystemMetrics(
        active_calls=5,
        total_users=150,
        system_health="healthy",
        database_status="connected",
        freeswitch_status="connected"
    )

@router.get("/users", response_model=UsersResponse)
async def list_users(current_user: dict = Depends(check_admin_permissions)):
    # Placeholder implementation
    users = [
        UserSummary(
            user_id="1",
            username="admin",
            email="admin@example.com",
            total_calls=25,
            last_call="2024-01-01T10:30:00Z",
            is_active=True
        ),
        UserSummary(
            user_id="2",
            username="user1",
            email="user1@example.com",
            total_calls=10,
            last_call="2024-01-01T09:15:00Z",
            is_active=True
        )
    ]
    
    return UsersResponse(users=users, total_count=len(users))

@router.put("/users/{user_id}/permissions")
async def update_user_permissions(
    user_id: str, 
    permissions: Dict[str, Any],
    current_user: dict = Depends(check_admin_permissions)
):
    # Update user permissions
    return {
        "message": f"Permissions updated for user {user_id}",
        "permissions": permissions
    }

@router.get("/system-config")
async def get_system_config(current_user: dict = Depends(check_admin_permissions)):
    return {
        "sip_provider": {
            "name": "Telnyx",
            "status": "connected",
            "balance_cents": 50000
        },
        "rate_limits": {
            "calls_per_minute": 10,
            "calls_per_day": 100
        },
        "security": {
            "encryption_enabled": True,
            "audit_logging": True
        }
    }

@router.post("/system-config")
async def update_system_config(
    config: Dict[str, Any],
    current_user: dict = Depends(check_admin_permissions)
):
    # Update system configuration
    return {
        "message": "System configuration updated",
        "config": config
    }
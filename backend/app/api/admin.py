"""
Admin API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog

from app.database import get_session, User, Call, CallEvent
from app.auth.dependencies import get_admin_user
from app.services.encryption import encryption_service

logger = structlog.get_logger()
router = APIRouter()

class SystemMetrics(BaseModel):
    """System metrics response"""
    system_health: Dict[str, Any]
    call_statistics: Dict[str, Any]

class UserSummary(BaseModel):
    """User summary for admin"""
    user_id: str
    display_name: str
    email: str
    total_calls: int
    last_call: Optional[datetime] = None
    permissions: Dict[str, Any]

class UsersResponse(BaseModel):
    """Users list response"""
    users: List[UserSummary]
    total_count: int

@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics(
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get system metrics and analytics"""
    
    try:
        # System health checks
        total_users = session.exec(select(func.count(User.id))).one()
        
        # Active calls (calls in progress)
        active_calls = session.exec(
            select(func.count(Call.id)).where(
                Call.status.in_(["initiated", "ringing", "answered"])
            )
        ).one()
        
        # Today's statistics
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_calls = session.exec(
            select(func.count(Call.id)).where(
                Call.initiated_at >= today_start
            )
        ).one()
        
        completed_today = session.exec(
            select(func.count(Call.id)).where(
                Call.initiated_at >= today_start,
                Call.status == "completed"
            )
        ).one()
        
        failed_today = session.exec(
            select(func.count(Call.id)).where(
                Call.initiated_at >= today_start,
                Call.status == "failed"
            )
        ).one()
        
        # This month's statistics
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_calls = session.exec(
            select(func.count(Call.id)).where(
                Call.initiated_at >= month_start
            )
        ).one()
        
        # Average duration and cost
        avg_duration = session.exec(
            select(func.avg(Call.duration_seconds)).where(
                Call.initiated_at >= month_start,
                Call.duration_seconds.isnot(None)
            )
        ).one() or 0
        
        total_cost = session.exec(
            select(func.sum(Call.cost_cents)).where(
                Call.initiated_at >= month_start,
                Call.cost_cents.isnot(None)
            )
        ).one() or 0
        
        avg_quality = session.exec(
            select(func.avg(Call.quality_score)).where(
                Call.initiated_at >= month_start,
                Call.quality_score.isnot(None)
            )
        ).one() or 0
        
        system_metrics = SystemMetrics(
            system_health={
                "freeswitch_status": "healthy",  # TODO: Implement actual health check
                "database_status": "healthy",
                "active_calls": active_calls,
                "total_users": total_users
            },
            call_statistics={
                "today": {
                    "total_calls": today_calls,
                    "completed_calls": completed_today,
                    "failed_calls": failed_today,
                    "total_duration_minutes": 0  # TODO: Calculate from duration_seconds
                },
                "this_month": {
                    "total_calls": month_calls,
                    "total_cost_cents": int(total_cost),
                    "avg_duration_seconds": int(avg_duration),
                    "avg_quality_score": round(float(avg_quality), 2) if avg_quality else 0
                }
            }
        )
        
        logger.info("System metrics retrieved", admin_user=admin_user.nextcloud_user_id)
        return system_metrics
        
    except Exception as e:
        logger.error("Failed to get system metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system metrics"
        )

@router.get("/users", response_model=UsersResponse)
async def get_users(
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session),
    limit: int = 50,
    offset: int = 0,
    search: str = None
):
    """Get list of all users"""
    
    try:
        # Build query
        statement = select(User)
        
        if search:
            statement = statement.where(
                User.display_name.ilike(f"%{search}%") |
                User.email.ilike(f"%{search}%")
            )
        
        # Get total count
        total_count = len(session.exec(statement).all())
        
        # Apply pagination
        statement = statement.offset(offset).limit(limit)
        users = session.exec(statement).all()
        
        # Get call statistics for each user
        user_summaries = []
        for user in users:
            # Get call count and last call
            call_count = session.exec(
                select(func.count(Call.id)).where(Call.user_id == user.id)
            ).one()
            
            last_call = session.exec(
                select(func.max(Call.initiated_at)).where(Call.user_id == user.id)
            ).one()
            
            user_summaries.append(UserSummary(
                user_id=str(user.id),
                display_name=user.display_name or "Unknown",
                email=user.email or "No email",
                total_calls=call_count,
                last_call=last_call,
                permissions=user.permissions
            ))
        
        logger.info("Users list retrieved", 
                   admin_user=admin_user.nextcloud_user_id,
                   count=len(user_summaries))
        
        return UsersResponse(
            users=user_summaries,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error("Failed to get users list", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users list"
        )

@router.put("/users/{user_id}/permissions")
async def update_user_permissions(
    user_id: str,
    permissions: Dict[str, Any],
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update user permissions"""
    
    try:
        # Get user
        statement = select(User).where(User.id == user_id)
        user = session.exec(statement).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update permissions
        user.permissions.update(permissions)
        user.updated_at = datetime.utcnow()
        
        session.add(user)
        session.commit()
        
        logger.info("User permissions updated",
                   admin_user=admin_user.nextcloud_user_id,
                   target_user=user.nextcloud_user_id,
                   permissions=permissions)
        
        return {"message": "Permissions updated successfully"}
        
    except Exception as e:
        logger.error("Failed to update user permissions", 
                    user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user permissions"
        )

@router.get("/system-config")
async def get_system_config(
    admin_user: User = Depends(get_admin_user)
):
    """Get system configuration"""
    
    try:
        # Return system configuration (non-sensitive data only)
        config = {
            "sip_provider": {
                "name": "Telnyx",  # TODO: Get from actual config
                "status": "connected",  # TODO: Implement actual status check
                "balance_cents": 50000  # TODO: Get from provider API
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
        
        logger.info("System config retrieved", admin_user=admin_user.nextcloud_user_id)
        return config
        
    except Exception as e:
        logger.error("Failed to get system config", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system configuration"
        )
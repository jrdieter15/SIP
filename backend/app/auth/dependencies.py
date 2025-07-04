"""
Authentication dependencies for FastAPI
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from typing import Optional
import structlog

from app.database import get_session, User
from app.auth.jwt_handler import jwt_handler

logger = structlog.get_logger()

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    """Get current authenticated user"""
    
    # Verify JWT token
    payload = jwt_handler.verify_token(credentials.credentials)
    
    # Extract user ID from token
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Get user from database
    statement = select(User).where(User.nextcloud_user_id == user_id)
    user = session.exec(statement).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    session.add(user)
    session.commit()
    
    return user

async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify admin permissions"""
    
    if not current_user.permissions.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user

async def check_call_permission(
    current_user: User = Depends(get_current_user)
) -> User:
    """Check if user has permission to make calls"""
    
    if not current_user.permissions.get("can_call", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Call permission required"
        )
    
    return current_user
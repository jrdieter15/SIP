"""
Authentication API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
import structlog
import httpx
from datetime import datetime

from app.database import get_session, User
from app.auth.jwt_handler import jwt_handler
from app.config import settings

logger = structlog.get_logger()
router = APIRouter()

class AuthRequest(BaseModel):
    """Authentication request model"""
    code: str
    redirect_uri: str

class RefreshRequest(BaseModel):
    """Token refresh request model"""
    refresh_token: str

class AuthResponse(BaseModel):
    """Authentication response model"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

@router.post("/auth", response_model=AuthResponse)
async def authenticate(
    auth_request: AuthRequest,
    session: Session = Depends(get_session)
):
    """Authenticate user with Nextcloud OAuth2 code"""
    
    try:
        # Exchange OAuth2 code for user info
        # In production, this would call Nextcloud OAuth2 endpoint
        # For now, simulate successful authentication
        
        logger.info("Processing authentication request")
        
        # Mock user data - in production, get from Nextcloud OAuth2
        mock_user_data = {
            "nextcloud_user_id": "demo_user",
            "email": "demo@example.com",
            "display_name": "Demo User"
        }
        
        # Check if user exists
        statement = select(User).where(
            User.nextcloud_user_id == mock_user_data["nextcloud_user_id"]
        )
        user = session.exec(statement).first()
        
        if not user:
            # Create new user
            user = User(
                nextcloud_user_id=mock_user_data["nextcloud_user_id"],
                email=mock_user_data["email"],
                display_name=mock_user_data["display_name"],
                permissions={"can_call": True, "is_admin": False}
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            
            logger.info("Created new user", user_id=user.nextcloud_user_id)
        else:
            # Update existing user
            user.email = mock_user_data["email"]
            user.display_name = mock_user_data["display_name"]
            user.last_login = datetime.utcnow()
            session.add(user)
            session.commit()
            
            logger.info("Updated existing user", user_id=user.nextcloud_user_id)
        
        # Create JWT tokens
        token_data = {
            "sub": user.nextcloud_user_id,
            "user_id": str(user.id),
            "email": user.email,
            "permissions": user.permissions
        }
        
        tokens = jwt_handler.create_tokens(token_data)
        
        logger.info("Authentication successful", user_id=user.nextcloud_user_id)
        
        return AuthResponse(**tokens)
        
    except Exception as e:
        logger.error("Authentication failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

@router.post("/auth/refresh", response_model=AuthResponse)
async def refresh_token(
    refresh_request: RefreshRequest,
    session: Session = Depends(get_session)
):
    """Refresh expired access token"""
    
    try:
        # Verify refresh token
        payload = jwt_handler.verify_token(refresh_request.refresh_token, "refresh")
        
        # Get user from database
        user_id = payload.get("sub")
        statement = select(User).where(User.nextcloud_user_id == user_id)
        user = session.exec(statement).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new tokens
        token_data = {
            "sub": user.nextcloud_user_id,
            "user_id": str(user.id),
            "email": user.email,
            "permissions": user.permissions
        }
        
        tokens = jwt_handler.create_tokens(token_data)
        
        logger.info("Token refreshed successfully", user_id=user.nextcloud_user_id)
        
        return AuthResponse(**tokens)
        
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )
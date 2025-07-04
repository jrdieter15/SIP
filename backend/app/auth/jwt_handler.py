"""
JWT token handling for authentication
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, status
import structlog

from app.config import settings

logger = structlog.get_logger()

class JWTHandler:
    """Handle JWT token creation and validation"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_EXPIRY_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_EXPIRY_DAYS
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    def create_tokens(self, user_data: Dict[str, Any]) -> Dict[str, str]:
        """Create both access and refresh tokens"""
        access_token = self.create_access_token(user_data)
        refresh_token = self.create_refresh_token(user_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }

# Global JWT handler instance
jwt_handler = JWTHandler()
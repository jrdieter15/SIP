"""
Middleware configuration for FastAPI
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
import structlog

from app.config import settings

logger = structlog.get_logger()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

def setup_middleware(app: FastAPI):
    """Setup all middleware for the FastAPI app"""
    
    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware for production
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )
    
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Add security headers to all responses"""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
    
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all HTTP requests"""
        start_time = time.time()
        
        # Log request
        logger.info(
            "HTTP request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            "HTTP request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=round(process_time, 4)
        )
        
        return response
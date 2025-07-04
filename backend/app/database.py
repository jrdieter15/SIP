"""
Database configuration and models for SIPCall
"""

from sqlmodel import SQLModel, create_engine, Session, Field
from typing import Optional, List
import uuid
from datetime import datetime
from sqlalchemy import Column, LargeBinary, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
import os

from app.config import settings

# Database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG_MODE,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session

async def init_db():
    """Initialize database tables"""
    SQLModel.metadata.create_all(engine)

# Base models
class TimestampMixin(SQLModel):
    """Mixin for timestamp fields"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class User(SQLModel, table=True):
    """User model"""
    __tablename__ = "users"
    
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column=Column(UUID(as_uuid=True))
    )
    nextcloud_user_id: str = Field(unique=True, index=True)
    email: Optional[str] = Field(default=None, index=True)
    display_name: Optional[str] = Field(default=None)
    permissions: dict = Field(
        default={"can_call": True, "is_admin": False},
        sa_column=Column(JSONB)
    )
    privacy_consent: bool = Field(default=False)
    privacy_consent_date: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)

class Call(SQLModel, table=True):
    """Call model with encrypted sensitive data"""
    __tablename__ = "calls"
    
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column=Column(UUID(as_uuid=True))
    )
    user_id: uuid.UUID = Field(
        foreign_key="users.id",
        sa_column=Column(UUID(as_uuid=True))
    )
    
    # Encrypted sensitive data
    destination_number_enc: bytes = Field(sa_column=Column(LargeBinary))
    caller_id_enc: Optional[bytes] = Field(default=None, sa_column=Column(LargeBinary))
    
    # Call metadata
    call_uuid: Optional[str] = Field(default=None, unique=True, index=True)
    status: str = Field(default="initiated", index=True)
    direction: str = Field(default="outbound")
    
    # Timing information
    initiated_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    answered_at: Optional[datetime] = Field(default=None)
    ended_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[int] = Field(default=None)
    
    # Cost and billing
    cost_cents: Optional[int] = Field(default=None)
    currency: str = Field(default="USD")
    
    # Technical details
    codec: Optional[str] = Field(default=None)
    quality_score: Optional[float] = Field(default=None)
    disconnect_reason: Optional[str] = Field(default=None)
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CallEvent(SQLModel, table=True):
    """Call events for detailed logging"""
    __tablename__ = "call_events"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    call_id: uuid.UUID = Field(
        foreign_key="calls.id",
        sa_column=Column(UUID(as_uuid=True))
    )
    event_type: str = Field(index=True)
    event_data: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)

class SystemConfig(SQLModel, table=True):
    """System configuration"""
    __tablename__ = "system_config"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    config_key: str = Field(unique=True, index=True)
    config_value: dict = Field(sa_column=Column(JSONB))
    description: Optional[str] = Field(default=None)
    is_encrypted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AuditLog(SQLModel, table=True):
    """Audit logging for compliance"""
    __tablename__ = "audit_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="users.id",
        sa_column=Column(UUID(as_uuid=True))
    )
    action: str = Field(index=True)
    resource_type: Optional[str] = Field(default=None)
    resource_id: Optional[str] = Field(default=None)
    details: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)

class RateLimit(SQLModel, table=True):
    """Rate limiting tracking"""
    __tablename__ = "rate_limits"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="users.id",
        sa_column=Column(UUID(as_uuid=True))
    )
    endpoint: str = Field()
    request_count: int = Field(default=0)
    window_start: datetime = Field(default_factory=datetime.utcnow)
    window_duration_minutes: int = Field(default=60)
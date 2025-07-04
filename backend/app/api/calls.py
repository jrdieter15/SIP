"""
Call management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import structlog
import uuid

from app.database import get_session, User, Call, CallEvent
from app.auth.dependencies import get_current_user, check_call_permission
from app.services.freeswitch import freeswitch_service
from app.services.encryption import encryption_service

logger = structlog.get_logger()
router = APIRouter()

class CallRequest(BaseModel):
    """Call initiation request"""
    destination_number: str = Field(..., min_length=7, max_length=20)
    caller_id: Optional[str] = Field(None, max_length=20)
    privacy_mode: bool = Field(default=False)

class CallResponse(BaseModel):
    """Call response model"""
    call_id: str
    call_uuid: str
    status: str
    destination_number: str
    initiated_at: datetime

class CallStatusResponse(BaseModel):
    """Call status response"""
    call_id: str
    status: str
    duration_seconds: Optional[int] = None
    quality_score: Optional[float] = None
    last_updated: datetime

class CallHistoryItem(BaseModel):
    """Call history item"""
    call_id: str
    destination_number: str
    status: str
    initiated_at: datetime
    duration_seconds: Optional[int] = None
    cost_cents: Optional[int] = None
    quality_score: Optional[float] = None

class CallHistoryResponse(BaseModel):
    """Call history response"""
    calls: List[CallHistoryItem]
    total_count: int
    has_more: bool

@router.post("/call", response_model=CallResponse)
async def initiate_call(
    call_request: CallRequest,
    current_user: User = Depends(check_call_permission),
    session: Session = Depends(get_session)
):
    """Initiate a new outbound call"""
    
    try:
        logger.info("Initiating call", 
                   user_id=current_user.nextcloud_user_id,
                   destination=call_request.destination_number[:5] + "***")
        
        # Validate phone number format
        cleaned_number = ''.join(filter(str.isdigit, call_request.destination_number.replace('+', '')))
        if len(cleaned_number) < 7 or len(cleaned_number) > 15:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number format"
            )
        
        # Check rate limits (simplified)
        # In production, implement proper rate limiting with Redis
        recent_calls = session.exec(
            select(Call).where(
                Call.user_id == current_user.id,
                Call.initiated_at > datetime.utcnow() - timedelta(minutes=1)
            )
        ).all()
        
        if len(recent_calls) >= 5:  # Max 5 calls per minute
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Originate call via FreeSWITCH
        fs_result = await freeswitch_service.originate_call(
            destination=call_request.destination_number,
            caller_id=call_request.caller_id
        )
        
        if not fs_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Call initiation failed: {fs_result.get('error', 'Unknown error')}"
            )
        
        # Create call record
        call = Call(
            user_id=current_user.id,
            destination_number_enc=encryption_service.encrypt_phone_number(call_request.destination_number),
            caller_id_enc=encryption_service.encrypt(call_request.caller_id) if call_request.caller_id else None,
            call_uuid=fs_result["call_uuid"],
            status="initiated",
            direction="outbound"
        )
        
        session.add(call)
        session.commit()
        session.refresh(call)
        
        # Log call event
        call_event = CallEvent(
            call_id=call.id,
            event_type="call_initiated",
            event_data={
                "privacy_mode": call_request.privacy_mode,
                "freeswitch_response": fs_result
            }
        )
        session.add(call_event)
        session.commit()
        
        logger.info("Call initiated successfully", 
                   call_id=str(call.id),
                   call_uuid=call.call_uuid)
        
        return CallResponse(
            call_id=str(call.id),
            call_uuid=call.call_uuid,
            status=call.status,
            destination_number=call_request.destination_number,
            initiated_at=call.initiated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Call initiation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/call-status/{call_id}", response_model=CallStatusResponse)
async def get_call_status(
    call_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get current status of a specific call"""
    
    try:
        # Get call from database
        statement = select(Call).where(
            Call.id == uuid.UUID(call_id),
            Call.user_id == current_user.id
        )
        call = session.exec(statement).first()
        
        if not call:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )
        
        # Get status from FreeSWITCH if call is active
        if call.status in ["initiated", "ringing", "answered"] and call.call_uuid:
            fs_status = await freeswitch_service.get_call_status(call.call_uuid)
            
            # Update call status if changed
            if fs_status["status"] != call.status:
                call.status = fs_status["status"]
                call.updated_at = datetime.utcnow()
                
                if fs_status["status"] == "completed":
                    call.ended_at = datetime.utcnow()
                    call.duration_seconds = fs_status.get("duration", 0)
                    call.quality_score = fs_status.get("quality_score")
                
                session.add(call)
                session.commit()
        
        return CallStatusResponse(
            call_id=str(call.id),
            status=call.status,
            duration_seconds=call.duration_seconds,
            quality_score=call.quality_score,
            last_updated=call.updated_at
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid call ID format"
        )
    except Exception as e:
        logger.error("Failed to get call status", call_id=call_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/call/{call_id}/hangup")
async def hangup_call(
    call_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Terminate an active call"""
    
    try:
        # Get call from database
        statement = select(Call).where(
            Call.id == uuid.UUID(call_id),
            Call.user_id == current_user.id
        )
        call = session.exec(statement).first()
        
        if not call:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )
        
        if call.status in ["completed", "failed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Call is already terminated"
            )
        
        # Hangup call via FreeSWITCH
        if call.call_uuid:
            fs_result = await freeswitch_service.hangup_call(call.call_uuid)
            
            if fs_result["success"]:
                call.status = "terminated"
                call.ended_at = datetime.utcnow()
                call.updated_at = datetime.utcnow()
                
                session.add(call)
                session.commit()
                
                logger.info("Call terminated successfully", call_id=call_id)
                
                return {
                    "call_id": call_id,
                    "status": "terminated",
                    "ended_at": call.ended_at
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to terminate call"
                )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid call ID format"
        )
    except Exception as e:
        logger.error("Failed to hangup call", call_id=call_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/call-history", response_model=CallHistoryResponse)
async def get_call_history(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None)
):
    """Retrieve user's call history"""
    
    try:
        # Build query
        statement = select(Call).where(Call.user_id == current_user.id)
        
        if from_date:
            statement = statement.where(Call.initiated_at >= from_date)
        if to_date:
            statement = statement.where(Call.initiated_at <= to_date)
        
        # Get total count
        total_count = len(session.exec(statement).all())
        
        # Apply pagination and ordering
        statement = statement.order_by(Call.initiated_at.desc()).offset(offset).limit(limit)
        calls = session.exec(statement).all()
        
        # Decrypt and format call history
        call_history = []
        for call in calls:
            try:
                destination_number = encryption_service.decrypt_phone_number(call.destination_number_enc)
                call_history.append(CallHistoryItem(
                    call_id=str(call.id),
                    destination_number=destination_number,
                    status=call.status,
                    initiated_at=call.initiated_at,
                    duration_seconds=call.duration_seconds,
                    cost_cents=call.cost_cents,
                    quality_score=call.quality_score
                ))
            except Exception as e:
                logger.error("Failed to decrypt call data", call_id=str(call.id), error=str(e))
                # Skip corrupted records
                continue
        
        has_more = (offset + limit) < total_count
        
        return CallHistoryResponse(
            calls=call_history,
            total_count=total_count,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error("Failed to get call history", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
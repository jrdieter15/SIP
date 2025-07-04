"""
Privacy and GDPR compliance API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime
import structlog
import uuid

from app.database import get_session, User, Call, CallEvent, AuditLog
from app.auth.dependencies import get_current_user
from app.services.encryption import encryption_service

logger = structlog.get_logger()
router = APIRouter()

class DataExportResponse(BaseModel):
    """Data export response for GDPR compliance"""
    user: Dict[str, Any]
    calls: List[Dict[str, Any]]
    export_date: datetime

class DeleteAccountResponse(BaseModel):
    """Account deletion response"""
    message: str
    deletion_id: str
    estimated_completion: datetime

@router.get("/data-export", response_model=DataExportResponse)
async def export_user_data(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Export all user data for GDPR compliance"""
    
    try:
        logger.info("Data export requested", user_id=current_user.nextcloud_user_id)
        
        # Export user data
        user_data = {
            "user_id": str(current_user.id),
            "nextcloud_user_id": current_user.nextcloud_user_id,
            "display_name": current_user.display_name,
            "email": current_user.email,
            "permissions": current_user.permissions,
            "privacy_consent": current_user.privacy_consent,
            "privacy_consent_date": current_user.privacy_consent_date,
            "created_at": current_user.created_at,
            "last_login": current_user.last_login
        }
        
        # Export call data with decryption
        statement = select(Call).where(Call.user_id == current_user.id)
        calls = session.exec(statement).all()
        
        call_data = []
        for call in calls:
            try:
                # Decrypt sensitive data
                destination_number = encryption_service.decrypt_phone_number(call.destination_number_enc)
                caller_id = encryption_service.decrypt(call.caller_id_enc) if call.caller_id_enc else None
                
                call_data.append({
                    "call_id": str(call.id),
                    "destination_number": destination_number,
                    "caller_id": caller_id,
                    "status": call.status,
                    "direction": call.direction,
                    "initiated_at": call.initiated_at,
                    "answered_at": call.answered_at,
                    "ended_at": call.ended_at,
                    "duration_seconds": call.duration_seconds,
                    "cost_cents": call.cost_cents,
                    "currency": call.currency,
                    "quality_score": call.quality_score,
                    "disconnect_reason": call.disconnect_reason
                })
            except Exception as e:
                logger.error("Failed to decrypt call data", 
                           call_id=str(call.id), error=str(e))
                # Include encrypted data with error note
                call_data.append({
                    "call_id": str(call.id),
                    "error": "Failed to decrypt call data",
                    "status": call.status,
                    "initiated_at": call.initiated_at
                })
        
        # Log the export request
        audit_log = AuditLog(
            user_id=current_user.id,
            action="data_export",
            resource_type="user_data",
            resource_id=str(current_user.id),
            details={"export_type": "gdpr_compliance"}
        )
        session.add(audit_log)
        session.commit()
        
        export_response = DataExportResponse(
            user=user_data,
            calls=call_data,
            export_date=datetime.utcnow()
        )
        
        logger.info("Data export completed", 
                   user_id=current_user.nextcloud_user_id,
                   calls_count=len(call_data))
        
        return export_response
        
    except Exception as e:
        logger.error("Data export failed", 
                    user_id=current_user.nextcloud_user_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export user data"
        )

@router.post("/delete-account", response_model=DeleteAccountResponse)
async def delete_user_account(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete all user data (GDPR right to be forgotten)"""
    
    try:
        deletion_id = f"del_{uuid.uuid4()}"
        
        logger.info("Account deletion requested", 
                   user_id=current_user.nextcloud_user_id,
                   deletion_id=deletion_id)
        
        # Log the deletion request before deleting
        audit_log = AuditLog(
            user_id=current_user.id,
            action="account_deletion_requested",
            resource_type="user_account",
            resource_id=str(current_user.id),
            details={
                "deletion_id": deletion_id,
                "gdpr_compliance": True
            }
        )
        session.add(audit_log)
        session.commit()
        
        # Delete call events first (foreign key constraint)
        call_ids = session.exec(
            select(Call.id).where(Call.user_id == current_user.id)
        ).all()
        
        for call_id in call_ids:
            session.exec(
                select(CallEvent).where(CallEvent.call_id == call_id)
            ).all()
            # Delete call events
            statement = select(CallEvent).where(CallEvent.call_id == call_id)
            events = session.exec(statement).all()
            for event in events:
                session.delete(event)
        
        # Delete calls
        statement = select(Call).where(Call.user_id == current_user.id)
        calls = session.exec(statement).all()
        for call in calls:
            session.delete(call)
        
        # Anonymize audit logs (don't delete for compliance)
        statement = select(AuditLog).where(AuditLog.user_id == current_user.id)
        audit_logs = session.exec(statement).all()
        for log in audit_logs:
            log.user_id = None
            log.details = {"anonymized": True, "deletion_id": deletion_id}
            session.add(log)
        
        # Delete user record
        session.delete(current_user)
        session.commit()
        
        estimated_completion = datetime.utcnow()
        
        logger.info("Account deletion completed", 
                   deletion_id=deletion_id,
                   calls_deleted=len(calls))
        
        return DeleteAccountResponse(
            message="User data deletion initiated",
            deletion_id=deletion_id,
            estimated_completion=estimated_completion
        )
        
    except Exception as e:
        session.rollback()
        logger.error("Account deletion failed", 
                    user_id=current_user.nextcloud_user_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user account"
        )

@router.post("/consent")
async def update_privacy_consent(
    consent: bool,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update user's privacy consent"""
    
    try:
        current_user.privacy_consent = consent
        current_user.privacy_consent_date = datetime.utcnow()
        current_user.updated_at = datetime.utcnow()
        
        session.add(current_user)
        session.commit()
        
        # Log consent change
        audit_log = AuditLog(
            user_id=current_user.id,
            action="privacy_consent_updated",
            resource_type="user_consent",
            resource_id=str(current_user.id),
            details={"consent": consent}
        )
        session.add(audit_log)
        session.commit()
        
        logger.info("Privacy consent updated", 
                   user_id=current_user.nextcloud_user_id,
                   consent=consent)
        
        return {
            "message": "Privacy consent updated successfully",
            "consent": consent,
            "updated_at": current_user.privacy_consent_date
        }
        
    except Exception as e:
        logger.error("Failed to update privacy consent", 
                    user_id=current_user.nextcloud_user_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update privacy consent"
        )
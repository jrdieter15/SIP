from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from ...auth.dependencies import get_current_user
from ...services.freeswitch import FreeSwitchService

router = APIRouter(tags=["calls"])

class CallRequest(BaseModel):
    from_number: str
    to_number: str

class CallResponse(BaseModel):
    call_id: str
    status: str
    from_number: str
    to_number: str

freeswitch_service = FreeSwitchService()

@router.post("/make", response_model=CallResponse)
async def make_call(request: CallRequest, current_user: dict = Depends(get_current_user)):
    try:
        result = await freeswitch_service.make_call(request.from_number, request.to_number)
        return CallResponse(
            call_id=result["call_id"],
            status=result["status"],
            from_number=result["from"],
            to_number=result["to"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hangup/{call_id}")
async def hangup_call(call_id: str, current_user: dict = Depends(get_current_user)):
    try:
        result = await freeswitch_service.hangup_call(call_id)
        return {"message": f"Call {call_id} terminated", "status": result["status"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_call_history(current_user: dict = Depends(get_current_user)):
    # Placeholder implementation
    return {
        "calls": [
            {
                "call_id": "call-123",
                "from_number": "+1234567890",
                "to_number": "+0987654321",
                "status": "completed",
                "duration": 120
            }
        ]
    }
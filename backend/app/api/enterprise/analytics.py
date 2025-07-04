from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ...auth.dependencies import get_current_user

router = APIRouter(tags=["analytics"])

class CallAnalytics(BaseModel):
    total_calls: int
    successful_calls: int
    failed_calls: int
    average_duration: float
    total_cost: float
    peak_hours: List[int]

class UserAnalytics(BaseModel):
    user_id: str
    username: str
    total_calls: int
    total_duration: int
    total_cost: float
    most_called_numbers: List[str]

class CostAnalytics(BaseModel):
    daily_cost: List[Dict[str, Any]]
    monthly_cost: float
    cost_by_destination: List[Dict[str, Any]]
    cost_trends: List[Dict[str, Any]]

def check_admin_permissions(current_user: dict = Depends(get_current_user)):
    # Check admin permissions
    return current_user

@router.get("/calls", response_model=CallAnalytics)
async def get_call_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(check_admin_permissions)
):
    # Placeholder analytics data
    return CallAnalytics(
        total_calls=1250,
        successful_calls=1180,
        failed_calls=70,
        average_duration=125.5,
        total_cost=2450.75,
        peak_hours=[9, 10, 11, 14, 15, 16]
    )

@router.get("/users", response_model=List[UserAnalytics])
async def get_user_analytics(
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(check_admin_permissions)
):
    # Placeholder user analytics
    return [
        UserAnalytics(
            user_id="1",
            username="admin",
            total_calls=125,
            total_duration=15600,
            total_cost=245.50,
            most_called_numbers=["+1234567890", "+0987654321"]
        ),
        UserAnalytics(
            user_id="2",
            username="user1",
            total_calls=85,
            total_duration=10200,
            total_cost=156.75,
            most_called_numbers=["+1111111111", "+2222222222"]
        )
    ]

@router.get("/costs", response_model=CostAnalytics)
async def get_cost_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(check_admin_permissions)
):
    # Placeholder cost analytics
    return CostAnalytics(
        daily_cost=[
            {"date": "2024-01-01", "cost": 45.50},
            {"date": "2024-01-02", "cost": 52.25},
            {"date": "2024-01-03", "cost": 38.75}
        ],
        monthly_cost=1250.00,
        cost_by_destination=[
            {"country": "US", "cost": 450.00},
            {"country": "UK", "cost": 320.00},
            {"country": "DE", "cost": 280.00}
        ],
        cost_trends=[
            {"month": "2023-12", "cost": 1180.00},
            {"month": "2024-01", "cost": 1250.00}
        ]
    )

@router.get("/quality")
async def get_quality_analytics(current_user: dict = Depends(check_admin_permissions)):
    return {
        "average_quality_score": 4.2,
        "quality_distribution": {
            "excellent": 45,
            "good": 35,
            "fair": 15,
            "poor": 5
        },
        "quality_trends": [
            {"date": "2024-01-01", "score": 4.1},
            {"date": "2024-01-02", "score": 4.3},
            {"date": "2024-01-03", "score": 4.2}
        ]
    }
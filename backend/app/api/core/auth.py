from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from ...auth.jwt_handler import create_access_token, verify_password, get_password_hash

router = APIRouter(tags=["authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    # Placeholder authentication logic
    # In a real implementation, you would verify against a database
    if request.username == "admin" and request.password == "password":
        access_token = create_access_token(data={"sub": request.username})
        return LoginResponse(access_token=access_token, token_type="bearer")
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password"
    )
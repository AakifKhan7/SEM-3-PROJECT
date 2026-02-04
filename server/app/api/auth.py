from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.user_auth import UserLogin, UserLoginResponse, RefreshRequest
from app.services.auth_service import signup, login, refresh_access_token
from app.services.user_service import list as list_user
from app.middleware.auth import JWTBearer, get_current_user_id

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup", response_model=UserLoginResponse, status_code=status.HTTP_201_CREATED)
async def signup_endpoint(user_data: UserCreate, db: Session = Depends(get_db)):
    token_response = signup(db, user_data)
    print(f"DEBUG: signup_endpoint token_response: {token_response}")
    return UserLoginResponse(**token_response)

@router.post("/login", response_model=UserLoginResponse)
async def login_endpoint(login_data: UserLogin, db: Session = Depends(get_db)):
    token_response = login(db, login_data)
    return UserLoginResponse(**token_response)


@router.post("/refresh", response_model=UserLoginResponse)
async def refresh_endpoint(body: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access token (and new refresh token)."""
    token_response = refresh_access_token(db, body.refresh_token)
    return UserLoginResponse(**token_response)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token_data: dict = Depends(JWTBearer())
):
    user_id = get_current_user_id(request)
    users = list_user(db, user_id=user_id)
    if not users:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(users[0])


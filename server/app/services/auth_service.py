from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional
from app.models import User, UserAuth
from app.schemas.user import UserCreate
from app.schemas.user_auth import UserLogin
from app.utils.security import verify_password, create_access_token
from datetime import timedelta
from app.config import settings
from app.services.user_service import add as add_user
from app.services.user_auth_service import add as add_user_auth

def signup(db: Session, user_data: UserCreate) -> dict:
    ADMIN_USER_ID = 1
    new_user = add_user(db, user_data, ADMIN_USER_ID)
    
    from app.schemas.user_auth import UserAuthCreate
    auth_data = UserAuthCreate(
        user_id=new_user.id,
        email=user_data.email,
        password=user_data.password
    )
    user_auth = add_user_auth(db, auth_data, ADMIN_USER_ID)
    
    token_response = generate_token_response(user_auth)
    return token_response

def login(db: Session, login_data: UserLogin) -> dict:
    user_auth = db.query(UserAuth).filter(UserAuth.email == login_data.email).first()
    
    if not user_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if user_auth.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deleted"
        )
    
    user = db.query(User).filter(User.id == user_auth.user_id).first()
    if not user or not user.is_active or user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    if not verify_password(login_data.password, user_auth.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    token_response = generate_token_response(user_auth)
    return token_response

def generate_token_response(user_auth: UserAuth) -> dict:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user_auth.user_id), "email": user_auth.email},
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_auth.user_id,
        "email": user_auth.email
    }

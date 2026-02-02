from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional
from datetime import datetime, timedelta

from app.config import settings
from app.models import User, UserAuth
from app.models.refresh_token import RefreshToken
from app.schemas.user import UserCreate
from app.schemas.user_auth import UserLogin
from app.utils.security import verify_password, create_access_token, create_refresh_token_string
from app.services.user_service import add as add_user
from app.services.user_auth_service import add as add_user_auth

def signup(db: Session, user_data: UserCreate) -> dict:
    # Use None for created_by so the first user (and any user) can sign up without needing an existing admin
    new_user = add_user(db, user_data, created_by=None)
    
    from app.schemas.user_auth import UserAuthCreate
    auth_data = UserAuthCreate(
        user_id=new_user.id,
        email=user_data.email,
        password=user_data.password
    )
    user_auth = add_user_auth(db, auth_data, created_by=None)
    
    token_response = generate_token_response(db, user_auth)
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
    
    token_response = generate_token_response(db, user_auth)
    return token_response

def generate_token_response(db: Session, user_auth: UserAuth) -> dict:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user_auth.user_id), "email": user_auth.email},
        expires_delta=access_token_expires
    )
    refresh_token_str = create_refresh_token_string()
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_row = RefreshToken(
        user_id=user_auth.user_id,
        token=refresh_token_str,
        expires_at=expires_at,
    )
    db.add(refresh_row)
    db.commit()
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token_str,
        "user_id": user_auth.user_id,
        "email": user_auth.email,
    }


def refresh_access_token(db: Session, refresh_token_str: str) -> dict:
    """Validate refresh token and return new access token (and new refresh token)."""
    row = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token_str,
        RefreshToken.is_deleted == False,
    ).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    if row.expires_at < datetime.utcnow():
        db.delete(row)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )
    user_auth = db.query(UserAuth).filter(UserAuth.user_id == row.user_id).first()
    if not user_auth or user_auth.is_deleted:
        db.delete(row)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    user = db.query(User).filter(User.id == row.user_id).first()
    if not user or not user.is_active or user.is_deleted:
        db.delete(row)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    db.delete(row)
    db.commit()
    return generate_token_response(db, user_auth)

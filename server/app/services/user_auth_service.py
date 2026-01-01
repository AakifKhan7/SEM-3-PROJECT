from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List, Optional
from app.models import UserAuth
from app.schemas.user_auth import UserAuthCreate, UserAuthUpdate
from app.utils.security import get_password_hash

def add(db: Session, auth_data: UserAuthCreate, created_by: Optional[int] = None) -> UserAuth:
    existing_auth = db.query(UserAuth).filter(UserAuth.email == auth_data.email).first()
    if existing_auth:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    existing_user_auth = db.query(UserAuth).filter(UserAuth.user_id == auth_data.user_id).first()
    if existing_user_auth:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has authentication"
        )
    
    hashed_password = get_password_hash(auth_data.password)
    
    new_auth = UserAuth(
        user_id=auth_data.user_id,
        email=auth_data.email,
        password=hashed_password,
        createdBy=created_by,
        updatedBy=created_by
    )
    
    try:
        db.add(new_auth)
        db.commit()
        db.refresh(new_auth)
        return new_auth
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user auth"
        )

def update(db: Session, auth_id: int, auth_data: UserAuthUpdate, updated_by: Optional[int] = None) -> UserAuth:
    user_auth = db.query(UserAuth).filter(UserAuth.id == auth_id, UserAuth.is_deleted == False).first()
    if not user_auth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User auth not found"
        )
    
    if auth_data.email is not None:
        existing = db.query(UserAuth).filter(UserAuth.email == auth_data.email, UserAuth.id != auth_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        user_auth.email = auth_data.email
    
    if auth_data.password is not None:
        user_auth.password = get_password_hash(auth_data.password)
    
    user_auth.updatedBy = updated_by
    
    try:
        db.commit()
        db.refresh(user_auth)
        return user_auth
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user auth"
        )

def list(db: Session, skip: int = 0, limit: int = 100, auth_id: Optional[int] = None, user_id: Optional[int] = None) -> List[UserAuth]:
    query = db.query(UserAuth).filter(UserAuth.is_deleted == False)
    
    if auth_id is not None:
        auth = query.filter(UserAuth.id == auth_id).first()
        return [auth] if auth else []
    
    if user_id is not None:
        auth = query.filter(UserAuth.user_id == user_id).first()
        return [auth] if auth else []
    
    return query.offset(skip).limit(limit).all()

def delete(db: Session, auth_id: int, updated_by: Optional[int] = None) -> UserAuth:
    user_auth = db.query(UserAuth).filter(UserAuth.id == auth_id, UserAuth.is_deleted == False).first()
    if not user_auth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User auth not found"
        )
    
    user_auth.is_deleted = True
    user_auth.updatedBy = updated_by
    
    try:
        db.commit()
        db.refresh(user_auth)
        return user_auth
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete user auth"
        )


from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List, Optional
from app.models import User
from app.schemas.user import UserCreate, UserUpdate
from datetime import datetime

def add(db: Session, user_data: UserCreate, created_by: Optional[int] = None) -> User:
    new_user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        is_active=user_data.is_active,
        createdBy=created_by,
        is_deleted=False,
        updatedBy=created_by,
        updatedAt=datetime.utcnow(),
        createdAt=datetime.utcnow()
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user"
        )

def update(db: Session, user_id: int, user_data: UserUpdate, updated_by: Optional[int] = None) -> User:
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user_data.first_name is not None:
        user.first_name = user_data.first_name
    if user_data.last_name is not None:
        user.last_name = user_data.last_name
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    user.updatedBy = updated_by
    
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user"
        )

def list(db: Session, skip: int = 0, limit: int = 100, user_id: Optional[int] = None) -> List[User]:
    query = db.query(User).filter(User.is_deleted == False)
    
    if user_id is not None:
        user = query.filter(User.id == user_id).first()
        return [user] if user else []
    
    return query.offset(skip).limit(limit).all()

def delete(db: Session, user_id: int, updated_by: Optional[int] = None) -> User:
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_deleted = True
    user.updatedBy = updated_by
    
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete user"
        )


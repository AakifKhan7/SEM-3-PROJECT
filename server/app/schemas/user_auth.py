from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserAuthBase(BaseModel):
    email: EmailStr = Field(..., max_length=100)

class UserAuthCreate(UserAuthBase):
    user_id: int
    password: str = Field(..., min_length=6, max_length=72)

class UserAuthUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=6, max_length=72)

class UserAuthResponse(UserAuthBase):
    id: int
    user_id: int
    createdAt: datetime
    createdBy: Optional[int]
    updatedAt: datetime
    updatedBy: Optional[int]
    is_deleted: bool

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr = Field(..., max_length=100)
    password: str = Field(..., min_length=6, max_length=72)

class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    user_id: int
    email: EmailStr


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AuthActivityBase(BaseModel):
    ip_address: str = Field(..., max_length=100)
    user_agent: str = Field(..., max_length=500)
    is_successful: bool = True

class AuthActivityCreate(AuthActivityBase):
    user_id: int
    user_auth_id: int
    login_time: Optional[datetime] = None

class AuthActivityUpdate(BaseModel):
    logout_time: Optional[datetime] = None
    is_successful: Optional[bool] = None

class AuthActivityResponse(AuthActivityBase):
    id: int
    user_id: int
    user_auth_id: int
    login_time: datetime
    logout_time: Optional[datetime]
    createdAt: datetime
    createdBy: Optional[int]
    updatedAt: datetime
    updatedBy: Optional[int]
    is_deleted: bool

    class Config:
        from_attributes = True


from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.schemas.user_auth import UserAuthResponse
    from app.schemas.user_role import UserRoleResponse

class UserBase(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    is_active: bool = True

class UserCreate(UserBase):
    email: EmailStr = Field(..., max_length=100)
    password: str = Field(..., min_length=6, max_length=72)

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    createdAt: datetime
    createdBy: Optional[int]
    updatedAt: datetime
    updatedBy: Optional[int]
    is_deleted: bool

    class Config:
        from_attributes = True

class UserWithAuthResponse(UserResponse):
    auth: Optional["UserAuthResponse"] = None

class UserWithRolesResponse(UserResponse):
    roles: List["UserRoleResponse"] = []


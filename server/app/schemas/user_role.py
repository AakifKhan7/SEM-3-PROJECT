from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserRoleBase(BaseModel):
    role_name: str = Field(..., max_length=50)

class UserRoleCreate(UserRoleBase):
    user_id: int

class UserRoleUpdate(BaseModel):
    role_name: Optional[str] = Field(None, max_length=50)

class UserRoleResponse(UserRoleBase):
    id: int
    user_id: int
    createdAt: datetime
    createdBy: Optional[int]
    updatedAt: datetime
    updatedBy: Optional[int]
    is_deleted: bool

    class Config:
        from_attributes = True


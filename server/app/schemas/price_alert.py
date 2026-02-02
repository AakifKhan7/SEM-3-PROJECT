from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PriceAlertCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    target_price: float = Field(..., gt=0)


class PriceAlertResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    target_price: float
    is_active: bool
    createdAt: datetime

    class Config:
        from_attributes = True

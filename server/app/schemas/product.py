from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ProductListingResponse(BaseModel):
    id: int
    platform_id: int
    product_url: str
    price: float
    original_price: Optional[float]
    discount_percentage: Optional[float]
    rating: Optional[float]
    availability_status: str
    last_scraped_at: datetime

    class Config:
        from_attributes = True

class ProductResponse(BaseModel):
    id: int
    name: str
    brand: Optional[str]
    category: Optional[str]
    description: Optional[str]
    listings: List[ProductListingResponse] = []

    class Config:
        from_attributes = True
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SavedSearchCreate(BaseModel):
    search_query: str = Field(..., min_length=1, max_length=500)
    filters_json: Optional[str] = None


class SavedSearchResponse(BaseModel):
    id: int
    user_id: int
    search_query: str
    filters_json: Optional[str] = None
    createdAt: datetime

    class Config:
        from_attributes = True
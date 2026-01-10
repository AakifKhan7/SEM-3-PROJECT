from sqlalchemy import Column, String
from app.models.base import BaseModel

class Platform(BaseModel):
    __tablename__ = "platforms"

    name = Column(String(100), nullable=False, index=True)
    base_url = Column(String(255), nullable=True)

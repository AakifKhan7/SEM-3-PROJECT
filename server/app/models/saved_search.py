from sqlalchemy import Column, Integer, ForeignKey, Text
from app.models.base import BaseModel

class SavedSearch(BaseModel):
    __tablename__ = "saved_search"

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    search_query = Column(Text, nullable=False)
    filters_json = Column(Text, nullable=True)

from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import BaseModel

class PriceHistory(BaseModel):
    __tablename__ = "price_history"

    product_listing_id = Column(
        Integer,
        ForeignKey("product_listings.id"),
        nullable=False,
        index=True
    )

    price = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("ProductListing", back_populates="price_history")

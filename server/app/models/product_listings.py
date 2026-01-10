from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import BaseModel

class ProductListing(BaseModel):
    __tablename__ = "product_listings"

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
        index=True
    )

    platform_id = Column(
        Integer,
        ForeignKey("platforms.id"),
        nullable=False,
        index=True
    )

    product_url = Column(String(500), nullable=False)
    platform_product_id = Column(String(255), nullable=True)

    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    discount_percentage = Column(Float, nullable=True)

    rating = Column(Float, nullable=True)
    rating_count = Column(Integer, nullable=True)

    last_scraped_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="listings")
    platform = relationship("Platform")
    price_history = relationship("PriceHistory", back_populates="listing")

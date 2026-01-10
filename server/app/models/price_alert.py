from sqlalchemy import Column, Integer, Float, Boolean, ForeignKey
from app.models.base import BaseModel

class PriceAlert(BaseModel):
    __tablename__ = "price_alert"

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
        index=True
    )

    target_price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)

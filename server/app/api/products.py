from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.product import ProductResponse, PriceHistoryPoint
from app.services import scraping_service
from app.models.price_history import PriceHistory
from app.models.product_listings import ProductListing
from typing import List

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("/search", response_model=List[ProductResponse])
def search_products(q: str = Query(..., min_length=3), db: Session = Depends(get_db)):
    """Search for products and update prices from scrapers."""
    products = scraping_service.search_and_sync_products(q, db)
    return products

@router.get("/{product_id}", response_model=ProductResponse)
def get_product_details(product_id: int, db: Session = Depends(get_db)):
    from app.models.product import Product
    return db.query(Product).filter(Product.id == product_id).first()

@router.get("/{product_id}/price-history", response_model=List[PriceHistoryPoint])
def get_price_history(product_id: int, db: Session = Depends(get_db)):
    """
    Return aggregated price history across all listings of a product,
    ordered by time.
    """
    # Join PriceHistory -> ProductListing to filter by product_id
    history_rows = (
        db.query(PriceHistory)
        .join(ProductListing, PriceHistory.product_listing_id == ProductListing.id)
        .filter(ProductListing.product_id == product_id)
        .order_by(PriceHistory.recorded_at.asc())
        .all()
    )
    return history_rows
    
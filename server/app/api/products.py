from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import JWTBearer
from app.schemas.product import ProductResponse, PriceHistoryPoint
from app.services import scraping_service
from app.models.price_history import PriceHistory
from app.models.product_listings import ProductListing
from app.models.product import Product
from typing import List
from fastapi import status

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("/list", response_model=List[ProductResponse])
def list_products(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """Return all products stored in the DB (admin use)."""
    return db.query(Product).filter(Product.is_deleted == False).limit(limit).all()

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(JWTBearer()),
):
    """Permanently delete a product and all related records (admin use)."""
    from app.models.price_alert import PriceAlert

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    try:
        # Get all listing IDs for this product to cascade into price_history
        listing_ids = [r.id for r in db.query(ProductListing.id).filter(ProductListing.product_id == product_id).all()]
        if listing_ids:
            db.query(PriceHistory).filter(PriceHistory.product_listing_id.in_(listing_ids)).delete(synchronize_session=False)
        # price_alert references products.id
        db.query(PriceAlert).filter(PriceAlert.product_id == product_id).delete(synchronize_session=False)
        # product_listings references products.id
        db.query(ProductListing).filter(ProductListing.product_id == product_id).delete(synchronize_session=False)
        # finally the product itself
        db.query(Product).filter(Product.id == product_id).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")
    return None

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
    
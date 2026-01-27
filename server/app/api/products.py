from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.product import ProductResponse
from app.services import product_service
from typing import List

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("/search", response_model=List[ProductResponse])
def search_products(q: str = Query(..., min_length=3), db: Session = Depends(get_db)):
    """Search for products and update prices from scrapers."""
    products = product_service.search_and_sync_products(db, q)
    return products

@router.get("/{product_id}", response_model=ProductResponse)
def get_product_details(product_id: int, db: Session = Depends(get_db)):
    from app.models.product import Product
    return db.query(Product).filter(Product.id == product_id).first()
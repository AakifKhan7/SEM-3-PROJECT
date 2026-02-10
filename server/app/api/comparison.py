from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.product import Product
from app.models.product_listings import ProductListing
from app.schemas.product import ProductListingResponse
from app.services.comparison_service import calculate_best_deal
from pydantic import BaseModel

router = APIRouter(prefix="/api/comparison", tags=["Comparison"])


@router.get("/best-deal", response_model=ProductListingResponse)
def get_best_deal(
    product_id: int = Query(..., description="Product ID to find best deal for"),
    db: Session = Depends(get_db),
):
    """
    Return the single best ProductListing for a given product.
    Current logic is price-focused.
    """
    product: Optional[Product] = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    listings: List[ProductListing] = (
        db.query(ProductListing)
        .options(joinedload(ProductListing.platform))
        .filter(ProductListing.product_id == product_id)
        .all()
    )
    if not listings:
        raise HTTPException(status_code=404, detail="No listings for this product")

    best = calculate_best_deal(listings)
    return best


class ComparisonRequest(BaseModel):
    product_id: int
    sort_by: str = "price"  # placeholder for future extension

@router.post("", response_model=List[ProductListingResponse])
def compare_listings(
    payload: ComparisonRequest,
    db: Session = Depends(get_db),
):
    """
    Simple comparison endpoint: returns all listings for the given product,
    sorted by price ascending for now.
    """
    listings: List[ProductListing] = (
        db.query(ProductListing)
        .options(joinedload(ProductListing.platform))
        .filter(ProductListing.product_id == payload.product_id)
        .all()
    )
    if not listings:
        raise HTTPException(status_code=404, detail="No listings for this product")

    # For now, just sort by price; later you can honor payload.sort_by
    listings_sorted = sorted(listings, key=lambda l: l.price or 0.0)
    return listings_sorted
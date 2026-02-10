from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.models.product_listings import ProductListing
from app.schemas.product import ProductListingResponse
from app.services.comparison_service import rank_listings
from pydantic import BaseModel

router = APIRouter(prefix="/api/comparison", tags=["Comparison"])


@router.get("/{product_id}", response_model=List[ProductListingResponse])
def get_ranked_listings(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Return all listings for a product ranked by composite score:
    - Discount (40%)
    - Price (40%, inverted so cheaper = better)
    - Rating (20%)
    
    Best deals appear first.
    """
    product: Optional[Product] = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    listings: List[ProductListing] = (
        db.query(ProductListing)
        .filter(ProductListing.product_id == product_id)
        .all()
    )
    if not listings:
        raise HTTPException(status_code=404, detail="No listings for this product")

    # Rank by composite score
    ranked = rank_listings(listings)
    
    # Return only the listing objects (with scores in metadata if needed)
    return [item["listing"] for item in ranked]
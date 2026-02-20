from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.models.product_listings import ProductListing
from app.schemas.product import ProductListingResponse
from app.services.comparison_service import rank_listings, compare_by_keyword
from pydantic import BaseModel

router = APIRouter(prefix="/api/comparison", tags=["Comparison"])


@router.get("/search", response_model=List[ProductListingResponse])
def compare_products_by_keyword(
    q: str = Query(..., min_length=3, description="Search keyword for products"),
    db: Session = Depends(get_db),
):
    """
    Compare products across platforms (Amazon and Flipkart) by search keyword.
    
    This endpoint:
    1. Searches for products matching the keyword in the database
    2. Fetches listings from Amazon and Flipkart for matching products
    3. Ranks them using composite scoring (discount 40%, price 40%, rating 20%)
    4. Returns ranked listings with best deals first
    
    Args:
        q: Search keyword (minimum 3 characters)
        db: Database session
    
    Returns:
        List of ranked ProductListings from Amazon and Flipkart
    """
    from app.services.comparison_service import compare_products_cross_platform
    
    result = compare_products_cross_platform(q, db)
    
    if not result or (not result["amazon"] and not result["flipkart"]):
        raise HTTPException(
            status_code=404, 
            detail=f"No products found for keyword '{q}'. Try searching on the Find Deals page first to populate the database."
        )
    
    # Extract listings from the result dictionary
    listings = []
    if result.get("amazon"):
        listings.append(result["amazon"])
    if result.get("flipkart"):
        listings.append(result["flipkart"])
        
    if not listings:
        return []

    # Rank by composite score (discount, price, rating)
    from app.services.comparison_service import rank_listings
    ranked = rank_listings(listings)
    
    # Extract only the listing objects from the ranked result
    ranked_listings = [item["listing"] for item in ranked]
    
    return ranked_listings


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
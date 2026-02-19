"""
Comparison service: rank product listings by composite score.
Combines discount, price, and rating into a single ranking.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.product_listings import ProductListing
from app.models.platform import Platform


def rank_listings(listings: List[ProductListing]) -> List[Dict[str, Any]]:
    """
    Rank listings using a composite score combining:
    - Discount (40%): higher discount = better
    - Price (40%): lower price = better
    - Rating (20%): higher rating = better
    
    Returns list of dicts with listing and score, sorted best → worst.
    """
    if not listings:
        return []
    
    # Collect data for normalization
    prices = [l.price for l in listings if l.price is not None]
    discounts = [l.discount_percentage for l in listings if l.discount_percentage is not None]
    ratings = [l.rating for l in listings if l.rating is not None]
    
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 1
    max_discount = max(discounts) if discounts else 100
    max_rating = max(ratings) if ratings else 5
    
    eps = 1e-8
    scored = []
    
    for listing in listings:
        # Normalize discount (0-1, higher is better)
        discount = listing.discount_percentage or 0
        norm_discount = min(discount / (max_discount + eps), 1.0)
        
        # Normalize price (0-1, inverted so lower price = higher score)
        price = listing.price or max_price
        norm_price = 1.0 - min((price - min_price) / (max_price - min_price + eps), 1.0)
        
        # Normalize rating (0-1, higher is better)
        rating = listing.rating or 0
        norm_rating = min(rating / (max_rating + eps), 1.0)
        
        # Composite score (weights: discount 40%, price 40%, rating 20%)
        score = (0.4 * norm_discount) + (0.4 * norm_price) + (0.2 * norm_rating)
        
        scored.append({
            "listing": listing,
            "score": round(score, 4),
            "norm_discount": round(norm_discount, 2),
            "norm_price": round(norm_price, 2),
            "norm_rating": round(norm_rating, 2),
        })
    
    # Sort by score descending (best first)
    scored.sort(key=lambda x: x["score"], reverse=True)
    
    return scored


def compare_by_keyword(query: str, db: Session) -> List[ProductListing]:
    """
    Search for products by keyword and return ranked listings across platforms.
    
    This function:
    1. Searches the database for products matching the keyword
    2. Fetches all listings for those products from Amazon and Flipkart
    3. Ranks them using the composite scoring algorithm
    4. Returns the ranked listings (best deals first)
    
    Args:
        query: Search keyword (e.g., "iPhone 15 Pro")
        db: Database session
    
    Returns:
        List of ProductListing objects ranked by composite score
    """
    # Search for products matching the keyword
    products = db.query(Product).filter(Product.name.ilike(f"%{query}%")).all()
    
    if not products:
        return []
    
    # Extract product IDs
    product_ids = [p.id for p in products]
    
    # Get all listings for these products from Amazon and Flipkart
    amazon_platform = db.query(Platform).filter(Platform.name == "Amazon").first()
    flipkart_platform = db.query(Platform).filter(Platform.name == "Flipkart").first()
    
    platform_ids = []
    if amazon_platform:
        platform_ids.append(amazon_platform.id)
    if flipkart_platform:
        platform_ids.append(flipkart_platform.id)
    
    if not platform_ids:
        return []
    
    # Query listings for matching products from Amazon and Flipkart only
    listings = (
        db.query(ProductListing)
        .filter(
            ProductListing.product_id.in_(product_ids),
            ProductListing.platform_id.in_(platform_ids)
        )
        .all()
    )
    
    if not listings:
        return []
    
    # Rank listings using composite score
    ranked = rank_listings(listings)
    
    # Return the listing objects sorted by score
    return [item["listing"] for item in ranked]
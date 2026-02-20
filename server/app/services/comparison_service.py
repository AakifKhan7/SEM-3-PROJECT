"""
Comparison service: rank product listings by composite score.
Combines discount, price, and rating into a single ranking.
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from difflib import SequenceMatcher
from app.models.product import Product
from app.models.product_listings import ProductListing
from app.models.platform import Platform
from app.services.scraping_service import search_and_sync_products


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


def compare_products_cross_platform(query: str, db: Session) -> Dict[str, Any]:
    """
    Compare products across platforms using fresh scraped data.
    """
    # 1. Scrape/Sync fresh data
    products = search_and_sync_products(query, db)
    
    if not products:
        return {
            "amazon": None,
            "flipkart": None,
            "comparison": None
        }

    # 2. Gather listings by platform
    amazon_listings = []
    flipkart_listings = []
    
    for product in products:
        if not product.listings:
            continue
            
        for listing in product.listings:
            # Ensure platform is loaded
            p_name = listing.platform.name if listing.platform else ""
            if not p_name and listing.platform_id:
                # Fallback if relationship not loaded
                plat = db.query(Platform).get(listing.platform_id)
                if plat:
                    p_name = plat.name
            
            if p_name == "Amazon":
                amazon_listings.append(listing)
            elif p_name == "Flipkart":
                flipkart_listings.append(listing)
                
    # 3. Find the single best matching product for the query on each platform
    def get_best_match(listings, search_query):
        if not listings:
            return None, 0.0
            
        best_listing = None
        best_score = -1.0
        
        for listing in listings:
            # Use product name for matching
            name = listing.product.name if listing.product else ""
            
            # Similarity score
            score = SequenceMatcher(None, search_query.lower(), name.lower()).ratio()
            
            # Boost logic
            if search_query.lower() in name.lower():
                score += 0.2
            
            if score > best_score:
                best_score = score
                best_listing = listing
        
        return best_listing, best_score

    best_amazon, a_score = get_best_match(amazon_listings, query)
    best_flipkart, f_score = get_best_match(flipkart_listings, query)
    
    # 4. Create comparison object
    comparison = {}
    if best_amazon and best_flipkart:
        # Calculate price difference
        price_a = best_amazon.price or 0
        price_f = best_flipkart.price or 0
        
        if price_a > 0 and price_f > 0:
            diff = price_a - price_f
            if diff > 0:
                comparison["cheaper"] = "Flipkart"
                comparison["price_diff"] = diff
                comparison["savings_pct"] = (diff / price_a) * 100
                comparison["message"] = f"Flipkart is cheaper by ₹{diff:.2f}"
            elif diff < 0:
                comparison["cheaper"] = "Amazon"
                comparison["price_diff"] = abs(diff)
                comparison["savings_pct"] = (abs(diff) / price_f) * 100
                comparison["message"] = f"Amazon is cheaper by ₹{abs(diff):.2f}"
            else:
                comparison["cheaper"] = "Equal"
                comparison["price_diff"] = 0
                comparison["message"] = "Prices are equal"
        
        # Rating comparison
        rating_a = best_amazon.rating or 0
        rating_f = best_flipkart.rating or 0
        
        if rating_a > rating_f:
             comparison["better_rated"] = "Amazon"
        elif rating_f > rating_a:
             comparison["better_rated"] = "Flipkart"
        else:
             comparison["better_rated"] = "Equal"

    return {
        "amazon": best_amazon,
        "flipkart": best_flipkart,
        "comparison": comparison
    }
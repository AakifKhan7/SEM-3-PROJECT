"""
Comparison service: rank product listings by composite score.
Combines discount, price, and rating into a single ranking.
"""

from typing import List, Dict, Any
from app.models.product_listings import ProductListing


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
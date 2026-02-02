from typing import List, Optional
from app.models.product_listings import ProductListing

def calculate_best_deal(
    listings: List[ProductListing],
    weights: dict | None = None,
) -> Optional[ProductListing]:
    """
    Very simple best-deal scorer based mainly on price.
    You can later extend this with rating / delivery weights.
    """
    if not listings:
        return None

    # Default weights – price dominates for now
    w = {
        "price": 1.0,
    }
    if weights:
        w.update(weights)

    def score(lst: ProductListing) -> float:
        # Lower price => lower score is better, so invert
        base_price = lst.price or 0.0
        return base_price * w["price"]

    return min(listings, key=score)
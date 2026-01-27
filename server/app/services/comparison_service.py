def calculate_best_deal(listings):
    if not listings:
        return None

    # Simple scoring: Price (lower is better)
    # In Phase 4, add Weightings for Rating and Delivery as per Architecture
    return min(listings, key=lambda x: x.price)
from sqlalchemy.orm import Session
from app.models import Product, ProductListing, Platform
from app.services.scrapers import AmazonScraper, FlipkartScraper
from app.models.price_history import PriceHistory
from datetime import datetime, timedelta


def search_and_sync_products(db: Session, query: str):
    """
    Search for products with database-first approach and freshness checking.
    
    Logic:
    1. Check database for products matching the query
    2. If found AND data is fresh (< 24 hours), return from database
    3. If not found OR data is stale, scrape from websites
    4. Always save scraped data to database
    5. Return the results
    """
    
    # STEP 1: Check Database First
    print(f"[SEARCH] Looking for '{query}' in database...")
    existing_products = db.query(Product).filter(Product.name.ilike(f"%{query}%")).all()
    
    if existing_products:
        print(f"[SEARCH] Found {len(existing_products)} products in database")
        
        # Check if data is fresh (scraped within last 24 hours)
        freshness_threshold = datetime.utcnow() - timedelta(hours=24)
        is_fresh = True
        
        for product in existing_products:
            listings = db.query(ProductListing).filter(
                ProductListing.product_id == product.id
            ).all()
            
            if not listings:
                print(f"[SEARCH] Product '{product.name}' has no listings - needs scraping")
                is_fresh = False
                break
            
            # Check if any listing is stale
            for listing in listings:
                if listing.last_scraped_at < freshness_threshold:
                    print(f"[SEARCH] Product '{product.name}' has stale data (last scraped: {listing.last_scraped_at}) - needs scraping")
                    is_fresh = False
                    break
            
            if not is_fresh:
                break
        
        if is_fresh:
            print(f"[SEARCH] ✓ Returning FRESH data from database (no scraping needed)")
            return existing_products
    else:
        print(f"[SEARCH] No products found in database for '{query}'")
    
    # STEP 2: Scrape from websites (data is stale or missing)
    print(f"[SEARCH] ⚡ Starting scraping for '{query}'...")
    
    with AmazonScraper(headless=True) as amazon, FlipkartScraper(headless=True) as flipkart:
        amz_results = amazon.search_products(query, max_results=3)
        fk_results = flipkart.search_products(query, max_results=3)
        all_results = amz_results + fk_results
    
    print(f"[SEARCH] Scraped {len(all_results)} products ({len(amz_results)} Amazon, {len(fk_results)} Flipkart)")
    
    if not all_results:
        print(f"[SEARCH] No results from scrapers")
        return existing_products if existing_products else []
    
    # STEP 3: Save all scraped data to database
    print(f"[SEARCH] Saving scraped data to database...")
    scraped_product_ids = []
    
    for item in all_results:
        try:
            # Skip items with no price
            if not item.current_price or item.current_price is None:
                print(f"[SKIP] Product '{item.name}' - missing price")
                continue
            
            try:
                current_price = float(item.current_price)
            except (ValueError, TypeError):
                print(f"[SKIP] Product '{item.name}' - invalid price: {item.current_price}")
                continue
            
            # Get or Create Product
            product = db.query(Product).filter(Product.name == item.name).first()
            if not product:
                product = Product(
                    name=item.name,
                    brand=item.brand,
                    category=item.category,
                    image_url=item.image_url
                )
                db.add(product)
                db.commit()
                db.refresh(product)
                print(f"[NEW] Created product: {product.name}")
            else:
                # Update image if missing
                if not product.image_url and item.image_url:
                    product.image_url = item.image_url
                    db.commit()
                print(f"[UPDATE] Updating existing product: {product.name}")
            
            scraped_product_ids.append(product.id)
            
            # Get Platform
            p_name = "Amazon" if "AMAZON" in item.unique_identifier else "Flipkart"
            platform = db.query(Platform).filter(Platform.name == p_name).first()
            if not platform:
                platform = Platform(name=p_name)
                db.add(platform)
                db.commit()
                db.refresh(platform)
            
            # Update or Create Listing
            listing = db.query(ProductListing).filter(
                ProductListing.product_id == product.id,
                ProductListing.platform_id == platform.id
            ).first()
            
            if listing:
                # Update existing listing
                listing.price = current_price
                listing.product_url = item.platform_url
                listing.availability_status = item.availability_status
                listing.last_scraped_at = datetime.utcnow()
                print(f"[UPDATE] Updated {p_name} listing for '{product.name}' - Price: ₹{current_price}")
            else:
                # Create new listing
                listing = ProductListing(
                    product_id=product.id,
                    platform_id=platform.id,
                    product_url=item.platform_url,
                    price=current_price,
                    availability_status=item.availability_status,
                    last_scraped_at=datetime.utcnow()
                )
                db.add(listing)
                db.flush()
                print(f"[NEW] Created {p_name} listing for '{product.name}' - Price: ₹{current_price}")
            
            # Always record price history when we scrape
            history = PriceHistory(
                product_listing_id=listing.id,
                price=current_price,
            )
            db.add(history)
            
        except Exception as e:
            print(f"[ERROR] Failed to save product '{item.name}': {str(e)}")
            continue
    
    db.commit()
    print(f"[SEARCH] ✓ Successfully saved {len(scraped_product_ids)} products to database")
    
    # STEP 4: Return all scraped products from database
    if scraped_product_ids:
        result_products = db.query(Product).filter(Product.id.in_(scraped_product_ids)).all()
        print(f"[SEARCH] Returning {len(result_products)} products")
        return result_products
    
    # Fallback: return existing products if scraping failed
    return existing_products if existing_products else []

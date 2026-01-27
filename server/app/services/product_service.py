from sqlalchemy.orm import Session
from app.models import Product, ProductListing, Platform
from app.services.scrapers import AmazonScraper, FlipkartScraper
from datetime import datetime


def search_and_sync_products(db: Session, query: str):
    # 1. Initialize Scrapers (built by Person 2)
    with AmazonScraper(headless=True) as amazon, FlipkartScraper(headless=True) as flipkart:
        amz_results = amazon.search_products(query, max_results=3)
        fk_results = flipkart.search_products(query, max_results=3)
        all_results = amz_results + fk_results

    # 2. Sync with Database
    for item in all_results:
        # Get or Create Product
        product = db.query(Product).filter(Product.name == item.name).first()
        if not product:
            product = Product(name=item.name, brand=item.brand, category=item.category)
            db.add(product)
            db.commit()
            db.refresh(product)

        # Get Platform ID
        p_name = "Amazon" if "AMAZON" in item.unique_identifier else "Flipkart"
        platform = db.query(Platform).filter(Platform.name == p_name).first()

        # Update or Create Listing
        listing = db.query(ProductListing).filter(
            ProductListing.product_id == product.id,
            ProductListing.platform_id == platform.id
        ).first()

        if listing:
            listing.price = float(item.current_price)
            listing.last_scraped_at = datetime.utcnow()
        else:
            new_listing = ProductListing(
                product_id=product.id, platform_id=platform.id,
                product_url=item.platform_url, price=float(item.current_price),
                availability_status=item.availability_status,
                platform_product_id=item.platform_product_id
            )
            db.add(new_listing)

    db.commit()
    return db.query(Product).filter(Product.name.ilike(f"%{query}%")).all()
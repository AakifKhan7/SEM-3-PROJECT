
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.product import Product
from app.models.product_listings import ProductListing
from app.models.platform import Platform
from app.services.scrapers.amazon import AmazonScraper
from app.services.scrapers.flipkart import FlipkartScraper
from app.services.scrapers.base import ScrapedProductData

from app.models.price_history import PriceHistory

logger = logging.getLogger(__name__)

def search_and_sync_products(query: str, db: Session) -> List[Product]:
    """
    Search for products by query.
    - First, check database for recent results (scraped < 24h ago).
    - If found and fresh, return DB results.
    - If not found or stale, scrape external platforms (Amazon, Flipkart).
    - Save/Update results in DB.
    - Return fresh results.
    """
    # 1. Check Database for existing products
    # We'll search for products with similar names or descriptions
    # For simplicity, we use ILIKE on the name
    existing_products = db.query(Product).filter(Product.name.ilike(f"%{query}%")).all()
    
    fresh_listings = []

    amazon_platform = db.query(Platform).filter(Platform.name == "Amazon").first()
    flipkart_platform = db.query(Platform).filter(Platform.name == "Flipkart").first()

    amazon_fresh_count = 0
    flipkart_fresh_count = 0
    
    if existing_products:
        # Check if we have fresh listings for these products
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        for product in existing_products:
            listings = db.query(ProductListing).filter(
                ProductListing.product_id == product.id,
                ProductListing.last_scraped_at >= cutoff_time
            ).all()
            
            for l in listings:
                fresh_listings.append(l)
                # Check platform
                if amazon_platform and l.platform_id == amazon_platform.id:
                    amazon_fresh_count += 1
                elif flipkart_platform and l.platform_id == flipkart_platform.id:
                    flipkart_fresh_count += 1

    needs_amazon = amazon_fresh_count == 0
    needs_flipkart = flipkart_fresh_count == 0

    # If we found fresh listings for both platforms, return them
    if not needs_amazon and not needs_flipkart:
        logger.info(f"Found fresh listings for both platforms in DB for query '{query}'")
        # Extract unique products from listings
        products = list({l.product for l in fresh_listings})
        return products
    
    logger.info(f"Missing fresh listings for '{query}'. needs_amazon={needs_amazon}, needs_flipkart={needs_flipkart}. Scraping external platforms...")
    
    # 2. Scrape External Platforms
    scraped_data: List[ScrapedProductData] = []
    
    # Scrape Amazon
    if needs_amazon:
        try:
            with AmazonScraper(headless=True) as amazon_scraper:
                amazon_results = amazon_scraper.search_products(query, fetch_details=False)
                scraped_data.extend(amazon_results)
        except Exception as e:
            logger.error(f"Error scraping Amazon: {e}")

    # Scrape Flipkart
    if needs_flipkart:
        try:
            with FlipkartScraper(headless=True) as flipkart_scraper:
                flipkart_results = flipkart_scraper.search_products(query, fetch_details=False)
                scraped_data.extend(flipkart_results)
        except Exception as e:
            logger.error(f"Error scraping Flipkart: {e}")

    if not scraped_data:
        # If we failed to scrape ANY new data, let's at least return ALL existing products from DB (fresh or stale)
        if existing_products:
            logger.info("Scraping failed for all missing platforms. Falling back to all existing DB records.")
            return existing_products
        return []

    # 3. Save/Update DB
    new_listings = []
    
    for item in scraped_data:
        # Resolve Platform
        platform_name = "Amazon" if "amazon" in (item.platform_url or "").lower() else "Flipkart"
        if "flipkart" in (item.platform_url or "").lower():
            platform_name = "Flipkart"
            
        platform = db.query(Platform).filter(Platform.name == platform_name).first()
        if not platform:
            # Create platform if missing (should be seeded, but safe fallback)
            platform = Platform(name=platform_name, base_url=item.platform_url.split("/")[0] if item.platform_url else "")
            db.add(platform)
            db.commit()
            db.refresh(platform)

        # Find or Create Product
        # We try to match by unique identifier (if available) or strict name match? 
        # Actually, for search results, we often get new products. 
        # A simple heuristic: if we have a unique_identifier (like ASIN), match on that?
        # But Product table doesn't have ASIN. ProductListing has `platform_product_id`.
        # So we should check if a Listing exists with that platform_id.
        
        existing_listing = db.query(ProductListing).filter(
            ProductListing.platform_product_id == item.platform_product_id,
            ProductListing.platform_id == platform.id
        ).first()

        product = None
        if existing_listing:
            product = existing_listing.product
        else:
            # Create new Product
            product = Product(
                name=item.name or "Unknown Product",
                brand=item.brand,
                category=item.category,
                description=item.description,
                image_url=item.image_url
            )
            db.add(product)
            db.commit()
            db.refresh(product)

        # Update or Create Listing
        if existing_listing:
            listing = existing_listing
            listing.price = item.current_price or 0
            listing.original_price = item.original_price
            listing.discount_percentage = item.discount_percentage
            listing.rating = float(item.rating) if item.rating is not None else (float(item.seller_rating) if item.seller_rating is not None else None)
            listing.rating_count = item.rating_count
            listing.delivery_time = item.delivery_time
        else:
            listing = ProductListing(
                product_id=product.id,
                platform_id=platform.id,
                product_url=item.platform_url,
                platform_product_id=item.platform_product_id,
                price=item.current_price or 0,
                original_price=item.original_price,
                discount_percentage=item.discount_percentage,
                rating=float(item.rating) if item.rating is not None else (float(item.seller_rating) if item.seller_rating is not None else None),
                rating_count=item.rating_count,
                availability_status=item.availability_status,
                delivery_time=item.delivery_time,
                last_scraped_at=datetime.utcnow()
            )
            db.add(listing)
        
        # Update fields that might change
        listing.price = item.current_price or listing.price
        listing.original_price = item.original_price
        listing.discount_percentage = item.discount_percentage
        listing.availability_status = item.availability_status
        listing.last_scraped_at = datetime.utcnow()
        
        db.commit()
        db.refresh(listing)
        new_listings.append(listing)
        
        # Add Price History
        history = PriceHistory(
            product_listing_id=listing.id,
            price=listing.price,
            recorded_at=datetime.utcnow()
        )
        db.add(history)
        db.commit()
        
    # Extract unique products from new listings
    new_products = list({l.product for l in new_listings})
    
    # Combine with existing products so we return BOTH newly scraped and previously cached results
    all_products = set(new_products)
    if existing_products:
        all_products.update(existing_products)
        
    return list(all_products)

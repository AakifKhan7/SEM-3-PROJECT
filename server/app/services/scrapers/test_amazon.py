"""
Test script for Amazon scraper.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.services.scrapers.amazon import AmazonScraper
from app.services.scrapers.base import ScrapedProductData


def print_product_data(product: ScrapedProductData, index: int = None):
    prefix = f"[{index}] " if index is not None else ""
    print(f"\n{prefix}{'='*60}")
    print(f"{prefix}Name: {product.name}")
    print(f"{prefix}Brand: {product.brand or 'N/A'}")
    print(f"{prefix}Category: {product.category or 'N/A'}")
    print(f"{prefix}Price: ₹{product.current_price or 'N/A'}")
    if product.original_price:
        print(f"{prefix}Original Price: ₹{product.original_price}")
    if product.discount_percentage:
        print(f"{prefix}Discount: {product.discount_percentage}%")
    print(f"{prefix}Rating: {product.seller_rating or 'N/A'}")
    print(f"{prefix}Availability: {product.availability_status}")
    print(f"{prefix}Seller: {product.seller_name or 'N/A'}")
    print(f"{prefix}Delivery: {product.delivery_time or 'N/A'}")
    if product.delivery_charges is not None:
        print(f"{prefix}Delivery Charges: ₹{product.delivery_charges}")
    print(f"{prefix}URL: {product.platform_url}")
    print(f"{prefix}Product ID: {product.platform_product_id or 'N/A'}")
    if product.image_url:
        img_display = product.image_url[:80] + "..." if len(product.image_url) > 80 else product.image_url
        print(f"{prefix}Image: {img_display}")
    if product.offers:
        print(f"{prefix}Offers: {json.dumps(product.offers, indent=2)}")
    print(f"{prefix}{'='*60}")


def main():
    query = "ZenBook 14"
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    
    print(f"Testing Amazon Scraper")
    print(f"Query: {query}")
    print(f"{'='*60}\n")
    
    scraper = AmazonScraper(headless=True, rate_limit_seconds=3.0)
    
    try:
        print("Searching for products...")
        print("-" * 60)
        print("Note: This will fetch detailed product information from each product page")
        print("This ensures accurate and complete data (slower but better quality)")
        print("-" * 60)
        results = scraper.search_products(query, max_results=10, fetch_details=True)
        
        if not results:
            print("No results found!")
            return
        
        print(f"\nFound {len(results)} products\n")
        
        for idx, product in enumerate(results, 1):
            print_product_data(product, index=idx)
        
        
        print("\n\n" + "="*60)
        print("Test Summary")
        print("="*60)
        print(f"Query: {query}")
        print(f"Search Results: {len(results)}")
        print(f"Test Status: PASSED")
        print("="*60)
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.cleanup()
        print("\nCleaned up resources")


if __name__ == "__main__":
    main()


import logging
import sys
import os

# Add server directory to path
sys.path.append(os.path.join(os.getcwd()))

from app.services.scrapers.flipkart import FlipkartScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.services.scrapers.flipkart")
logger.setLevel(logging.INFO)

def test_flipkart_scraper():
    print("Testing Flipkart Scraper...")
    try:
        with FlipkartScraper(headless=True) as scraper:
            query = "iphone 15"
            print(f"Searching for '{query}'...")
            results = scraper.search_products(query, max_results=3)
            
            # Dump HTML for inspection
            if scraper.driver:
                with open("flipkart_debug.html", "w", encoding="utf-8") as f:
                    f.write(scraper.driver.page_source)
                print("Dumped HTML to flipkart_debug.html")

            print(f"Found {len(results)} results.")
            for i, product in enumerate(results):
                print(f"[{i+1}] {product.name}")
                print(f"    Price: {product.current_price}")
                print(f"    URL: {product.platform_url}")
                print("-" * 40)
                
            if not results:
                print("No results found. Investigating logs...")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_flipkart_scraper()

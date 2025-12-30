from services.scrapers import AmazonScraper, FlipkartScraper

# Search products
with AmazonScraper(headless=True) as amazon:
    results = amazon.search_products("Samsung Galaxy S23 Ultra", max_results=10)
    for product in results:
        print(f"{product.name}: ₹{product.current_price}")

# Get detailed product info
with FlipkartScraper(headless=True) as flipkart:
    results = flipkart.search_products('Samsung Galaxy S23 Ultra')
    for product in results:
        print(f"{product.name}: ₹{product.current_price}")


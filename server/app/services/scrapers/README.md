# E-commerce Scrapers

Production-ready scrapers for Amazon and Flipkart with Selenium and BeautifulSoup.

## Features

- ✅ **Rate Limiting**: Automatic rate limiting to avoid being blocked
- ✅ **Error Handling**: Comprehensive error handling and logging
- ✅ **Data Normalization**: Unified data schema across all platforms
- ✅ **Dynamic Content**: Uses Selenium for JavaScript-rendered content
- ✅ **Fallback Support**: BeautifulSoup for static content parsing
- ✅ **Production Ready**: Handles edge cases, timeouts, and retries

## Usage

### Basic Usage

```python
from app.services.scrapers import AmazonScraper, FlipkartScraper

# Search for products
with AmazonScraper(headless=True) as amazon:
    results = amazon.search_products("laptop", max_results=5)
    for product in results:
        print(f"{product.name}: ₹{product.current_price}")

# Get product details
with FlipkartScraper(headless=True) as flipkart:
    product = flipkart.get_product_details("https://www.flipkart.com/p/product-id")
    if product:
        print(f"Name: {product.name}")
        print(f"Price: ₹{product.current_price}")
        print(f"Rating: {product.seller_rating}")
        print(f"Availability: {product.availability_status}")
```

### Advanced Usage

```python
from app.services.scrapers import AmazonScraper, ScrapedProductData

# Custom configuration
amazon = AmazonScraper(
    headless=True,
    rate_limit_seconds=3.0  # Wait 3 seconds between requests
)

try:
    # Search products
    results = amazon.search_products("smartphone", max_results=10)
    
    # Get detailed information for each product
    for result in results:
        if result.platform_url:
            details = amazon.get_product_details(result.platform_url)
            if details:
                # Access normalized data
                data_dict = details.to_dict()
                print(data_dict)
finally:
    amazon.cleanup()
```

### Data Structure

All scrapers return `ScrapedProductData` objects with the following fields:

```python
class ScrapedProductData:
    # Product info
    name: str
    brand: str
    category: str
    description: str
    image_url: str
    unique_identifier: str
    
    # Platform info
    platform_product_id: str
    platform_url: str
    
    # Pricing
    current_price: Decimal
    original_price: Decimal
    discount_percentage: Decimal
    currency: str  # Default: "INR"
    
    # Availability
    availability_status: str  # 'in_stock', 'out_of_stock', 'pre_order', 'unknown'
    
    # Seller
    seller_rating: Decimal  # 0-5
    seller_name: str
    
    # Delivery
    delivery_time: str
    delivery_charges: Decimal
    
    # Offers
    offers: List[Dict]  # List of offer dictionaries
    
    # Metadata
    scraped_at: datetime
```

### Integration with Database

```python
from app.services.scrapers import AmazonScraper
from app.models.product import ProductListing
from app.database import SessionLocal

def scrape_and_store(product_url: str, platform_id: int):
    """Scrape product and store in database."""
    with AmazonScraper() as scraper:
        product_data = scraper.get_product_details(product_url)
        
        if product_data:
            db = SessionLocal()
            try:
                # Convert to database model
                listing = ProductListing(
                    platform_id=platform_id,
                    platform_product_id=product_data.platform_product_id,
                    platform_url=product_data.platform_url,
                    current_price=product_data.current_price,
                    original_price=product_data.original_price,
                    discount_percentage=product_data.discount_percentage,
                    availability_status=product_data.availability_status,
                    seller_rating=product_data.seller_rating,
                    seller_name=product_data.seller_name,
                    delivery_time=product_data.delivery_time,
                    delivery_charges=product_data.delivery_charges,
                    offers=json.dumps(product_data.offers) if product_data.offers else None,
                    last_scraped_at=product_data.scraped_at
                )
                db.add(listing)
                db.commit()
            finally:
                db.close()
```

## Configuration

### Environment Variables

Set these in your `.env` file:

```env
# Scraping settings
SCRAPING_RATE_LIMIT_SECONDS=2
SCRAPING_HEADLESS=true
SCRAPING_TIMEOUT=30
```

### ChromeDriver

Make sure ChromeDriver is installed and in your PATH:

- Download from: https://chromedriver.chromium.org/
- Or use: `pip install webdriver-manager` (alternative approach)

## Error Handling

The scrapers handle various errors gracefully:

- **TimeoutException**: Page load timeout
- **NoSuchElementException**: Element not found
- **WebDriverException**: Browser errors
- **RequestException**: Network errors

All errors are logged and the scraper continues processing other items.

## Rate Limiting

Rate limiting is automatically enforced to prevent being blocked:

- Default: 2-3 seconds between requests
- Configurable per scraper instance
- Respects platform-specific limits

## Notes

- Always use context managers (`with` statement) to ensure proper cleanup
- Run in headless mode for production
- Monitor logs for scraping issues
- Adjust rate limits based on platform policies
- Some platforms may require additional headers or cookies


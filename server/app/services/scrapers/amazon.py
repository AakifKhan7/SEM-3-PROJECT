"""
Amazon scraper implementation.
Handles product search and detail extraction from Amazon India.
"""

import re
import logging
import time
from typing import List, Optional, Tuple
from decimal import Decimal
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base import BaseScraper, ScrapedProductData


logger = logging.getLogger(__name__)


class AmazonScraper(BaseScraper):
    """Scraper for Amazon India."""
    
    def __init__(self, headless: bool = True, rate_limit_seconds: float = 3.0):
        super().__init__(
            platform_name="Amazon",
            base_url="https://www.amazon.in",
            rate_limit_seconds=rate_limit_seconds,
            use_selenium=True,
            headless=headless,
            timeout=30
        )
    
    def _build_search_url(self, query: str) -> str:
        """Build Amazon search URL."""
        encoded_query = quote_plus(query)
        return f"{self.base_url}/s?k={encoded_query}"
    
    def _build_product_url(self, product_id: str) -> str:
        """Build Amazon product URL from ASIN."""
        return f"{self.base_url}/dp/{product_id}"
    
    def _extract_asin_from_url(self, url: str) -> Optional[str]:
        """Extract ASIN from Amazon URL."""
        # Pattern: /dp/ASIN or /gp/product/ASIN
        patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})',
            r'/product/([A-Z0-9]{10})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def _parse_amazon_price(self, soup: BeautifulSoup) -> Tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
        """
        Parse price information from Amazon page.
        Returns: (current_price, original_price, discount_percentage)
        """
        current_price = None
        original_price = None
        discount_percentage = None
        
        # Try different price selectors (Amazon has multiple formats)
        price_selectors = [
            '#priceblock_dealprice',
            '#priceblock_ourprice',
            '#priceblock_saleprice',
            '.a-price-whole',
            '.a-price .a-offscreen',
            '#price',
            '.a-price-range',
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                current_price = self._parse_price(price_text)
                if current_price:
                    break
        
        # Try to find original price (MRP/strikethrough)
        mrp_selectors = [
            '.a-price.a-text-price .a-offscreen',
            '.basisPrice .a-offscreen',
            '#priceblock_saleprice + .a-text-strike',
            '.a-text-strike',
        ]
        
        for selector in mrp_selectors:
            mrp_elem = soup.select_one(selector)
            if mrp_elem:
                price_text = mrp_elem.get_text(strip=True)
                original_price = self._parse_price(price_text)
                if original_price:
                    break
        
        # Calculate discount if both prices available
        if current_price and original_price and original_price > current_price:
            discount_percentage = ((original_price - current_price) / original_price) * 100
        
        # Try to find discount badge
        if not discount_percentage:
            discount_selectors = [
                '.savingsPercentage',
                '.a-size-large.a-color-price',
                '#priceblock_dealprice + .a-size-base',
            ]
            for selector in discount_selectors:
                discount_elem = soup.select_one(selector)
                if discount_elem:
                    discount_text = discount_elem.get_text(strip=True)
                    discount_percentage = self._parse_percentage(discount_text)
                    if discount_percentage:
                        break
        
        return current_price, original_price, discount_percentage
    
    def _extract_product_data_from_soup(self, soup: BeautifulSoup, product_url: str) -> Optional[ScrapedProductData]:
        """Extract product data from BeautifulSoup object."""
        try:
            product_data = ScrapedProductData()
            product_data.platform_url = product_url
            
            # Extract ASIN
            asin = self._extract_asin_from_url(product_url)
            if asin:
                product_data.platform_product_id = asin
                product_data.unique_identifier = f"AMAZON_{asin}"
            
            # Product name
            name_selectors = [
                '#productTitle',
                'h1.a-size-large',
                'h1 span',
                '.product-title',
            ]
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    product_data.name = name_elem.get_text(strip=True)
                    break
            
            brand_selectors = [
                '#brand',
                'a#brand',
                '#productByline_feature_div a',
                '#productByline_feature_div',
                '.po-brand .po-break-word',
                'tr.po-brand td.a-span9 span',
            ]
            for selector in brand_selectors:
                brand_elem = soup.select_one(selector)
                if brand_elem:
                    brand_text = brand_elem.get_text(strip=True)
                    if brand_text and brand_text.lower() not in ['brand', 'by']:
                        if 'by' in brand_text.lower():
                            product_data.brand = brand_text.split('by')[-1].strip().split('\n')[0]
                        else:
                            product_data.brand = brand_text.split('\n')[0]
                        if product_data.brand:
                            break
            
            category_selectors = [
                '#wayfinding-breadcrumbs_feature_div',
                '#nav-breadcrumb',
                '.nav-breadcrumb',
                '#breadcrumb_feature_div',
            ]
            for selector in category_selectors:
                breadcrumb = soup.select_one(selector)
                if breadcrumb:
                    categories = []
                    for a in breadcrumb.select('a'):
                        cat_text = a.get_text(strip=True)
                        if cat_text and cat_text.lower() not in ['all', 'home', 'amazon']:
                            categories.append(cat_text)
                    if categories:
                        product_data.category = ' > '.join(categories)
                        break
            
            # Description
            desc_selectors = [
                '#productDescription',
                '#feature-bullets',
                '.product-description',
            ]
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    product_data.description = desc_elem.get_text(strip=True, separator='\n')
                    break
            
            # Image URL
            img_selectors = [
                '#landingImage',
                '#imgBlkFront',
                '#main-image',
                '.a-dynamic-image',
            ]
            for selector in img_selectors:
                img_elem = soup.select_one(selector)
                if img_elem:
                    product_data.image_url = img_elem.get('src') or img_elem.get('data-src')
                    if product_data.image_url:
                        break
            
            # Price information
            current_price, original_price, discount_percentage = self._parse_amazon_price(soup)
            product_data.current_price = current_price
            product_data.original_price = original_price
            product_data.discount_percentage = discount_percentage
            
            availability_selectors = [
                '#availability span',
                '#availability',
                '#availability span.a-color-success',
                '#availability span.a-color-state',
                '.a-color-state',
                '#outOfStock',
                '#buybox span',
                '.a-section.a-spacing-none.a-spacing-top-mini span',
                '#exports_desktop_qualifiedBuybox',
            ]
            for selector in availability_selectors:
                avail_elem = soup.select_one(selector)
                if avail_elem:
                    avail_text = avail_elem.get_text(strip=True)
                    if avail_text:
                        product_data.availability_status = self._normalize_availability(avail_text)
                        if product_data.availability_status != 'unknown':
                            break
            
            if product_data.availability_status == 'unknown':
                buy_box = soup.select_one('#buybox')
                if buy_box:
                    buy_text = buy_box.get_text(strip=True).lower()
                    if 'add to cart' in buy_text or 'buy now' in buy_text:
                        product_data.availability_status = 'in_stock'
                    elif 'out of stock' in buy_text or 'currently unavailable' in buy_text:
                        product_data.availability_status = 'out_of_stock'
            
            # Rating
            rating_elem = soup.select_one('#acrPopover .a-icon-alt')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                product_data.seller_rating = self._parse_rating(rating_text)
            
            seller_selectors = [
                '#sellerProfileTriggerId',
                '#merchant-info a',
                '#merchant-info',
                '.a-section.a-spacing-none.a-spacing-top-mini span',
                '#bylineInfo',
            ]
            for selector in seller_selectors:
                seller_elem = soup.select_one(selector)
                if seller_elem:
                    seller_text = seller_elem.get_text(strip=True)
                    if seller_text:
                        if 'Sold by' in seller_text:
                            product_data.seller_name = seller_text.split('Sold by')[-1].split('Fulfilled')[0].split('and')[0].strip()
                        elif 'by' in seller_text.lower() and len(seller_text) < 100:
                            parts = seller_text.split('by')
                            if len(parts) > 1:
                                product_data.seller_name = parts[-1].strip().split('\n')[0].split('(')[0].strip()
                        else:
                            product_data.seller_name = seller_text.split('\n')[0].split('(')[0].strip()
                        if product_data.seller_name and len(product_data.seller_name) < 100:
                            break
            
            delivery_selectors = [
                '#delivery-block',
                '#mir-layout-DELIVERY_BLOCK',
                '#ddmDeliveryMessage',
                '.a-section.a-spacing-mini',
                '#contextualIngressPt',
                '.a-color-base.a-text-bold',
            ]
            for selector in delivery_selectors:
                delivery_elem = soup.select_one(selector)
                if delivery_elem:
                    delivery_text = delivery_elem.get_text(strip=True)
                    if delivery_text and ('delivery' in delivery_text.lower() or 'dispatch' in delivery_text.lower() or 'free' in delivery_text.lower()):
                        product_data.delivery_time = delivery_text
                        break
            
            if not product_data.delivery_time:
                delivery_sections = soup.select('[id*="delivery"], [id*="shipping"], [class*="delivery"]')
                for section in delivery_sections:
                    text = section.get_text(strip=True)
                    if text and ('delivery' in text.lower() or 'dispatch' in text.lower()):
                        product_data.delivery_time = text[:200]
                        break
            
            # Delivery charges (usually free for Prime, try to extract)
            if 'free' in (product_data.delivery_time or '').lower():
                product_data.delivery_charges = Decimal('0')
            else:
                # Try to extract delivery charges from text
                delivery_text = product_data.delivery_time or ''
                charge_match = re.search(r'₹\s*(\d+)', delivery_text)
                if charge_match:
                    product_data.delivery_charges = Decimal(charge_match.group(1))
            
            # Offers (try to extract from badges or offers section)
            offers = []
            offer_badges = soup.select('.a-badge-label, .a-badge-text')
            for badge in offer_badges:
                offer_text = badge.get_text(strip=True)
                if offer_text and offer_text not in ['Best Seller', 'Amazon\'s Choice']:
                    offers.append({"type": "badge", "text": offer_text})
            
            if offers:
                product_data.offers = offers
            
            return product_data
            
        except Exception as e:
            logger.error(f"Error extracting product data from Amazon page: {e}")
            return None
    
    def search_products(self, query: str, max_results: int = 10, fetch_details: bool = True) -> List[ScrapedProductData]:
        """
        Search for products on Amazon.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            fetch_details: If True, fetch detailed product info from each product page.
                          If False, only extract basic info from search results page.
        """
        results = []
        
        try:
            search_url = self._build_search_url(query)
            logger.info(f"Searching Amazon for: {query}")
            
            html_content = self._get_page_content(search_url)
            if not html_content:
                logger.error("Failed to fetch search results")
                return results
            
            if self.use_selenium and self.driver:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-component-type="s-search-result"], .s-result-item'))
                    )
                    time.sleep(2)
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                    time.sleep(1)
                    html_content = self.driver.page_source
                except TimeoutException:
                    logger.warning("Timeout waiting for search results, using current page source")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            product_containers = soup.select('[data-component-type="s-search-result"]')
            
            if not product_containers:
                product_containers = soup.select('.s-result-item')
            
            if not product_containers:
                product_containers = soup.select('[data-asin]')
            
            logger.info(f"Found {len(product_containers)} product containers")
            
            product_urls = []
            for container in product_containers:
                try:
                    if len(product_urls) >= max_results:
                        break
                    
                    is_sponsored = (
                        container.select_one('[data-component-type="s-ads-result"]') or
                        container.get('data-ad-id') or
                        container.select_one('.s-sponsored-label') or
                        container.select_one('[data-component-type="sponsored-result"]')
                    )
                    if is_sponsored:
                        continue
                    
                    sponsored_label = container.select_one('.s-label-popover-default, [aria-label*="Sponsored"]')
                    if sponsored_label:
                        label_text = sponsored_label.get_text(strip=True).lower()
                        if 'sponsored' in label_text:
                            continue
                    
                    link_elem = container.select_one('h2 a, .s-title-instructions-style a')
                    if not link_elem:
                        continue
                    
                    product_path = link_elem.get('href', '')
                    if not product_path or product_path.startswith('javascript:') or 'void(0)' in product_path:
                        continue
                    
                    if product_path.startswith('/'):
                        product_url = urljoin(self.base_url, product_path)
                    elif product_path.startswith('http'):
                        product_url = product_path
                    else:
                        continue
                    
                    if not product_url.startswith('http'):
                        continue
                    
                    if '/dp/' not in product_url and '/gp/product/' not in product_url:
                        asin = container.get('data-asin')
                        if asin:
                            product_url = self._build_product_url(asin)
                        else:
                            continue
                    
                    if product_url not in product_urls:
                        product_urls.append(product_url)
                    
                except Exception as e:
                    logger.warning(f"Error processing search result item: {e}")
                    continue
            
            logger.info(f"Found {len(product_urls)} valid product URLs")
            
            if fetch_details:
                for idx, product_url in enumerate(product_urls, 1):
                    try:
                        logger.info(f"Fetching details for product {idx}/{len(product_urls)}: {product_url}")
                        product_data = self.get_product_details(product_url)
                        if product_data:
                            results.append(product_data)
                        else:
                            logger.warning(f"Failed to fetch details for {product_url}")
                    except Exception as e:
                        logger.error(f"Error fetching product details: {e}")
                        continue
            else:
                for container in product_containers[:max_results]:
                    try:
                        if len(results) >= max_results:
                            break
                        
                        link_elem = container.select_one('h2 a, .s-title-instructions-style a')
                        if not link_elem:
                            continue
                        
                        product_path = link_elem.get('href', '')
                        if not product_path or product_path.startswith('javascript:') or 'void(0)' in product_path:
                            continue
                        
                        if product_path.startswith('/'):
                            product_url = urljoin(self.base_url, product_path)
                        elif product_path.startswith('http'):
                            product_url = product_path
                        else:
                            continue
                        
                        if '/dp/' not in product_url and '/gp/product/' not in product_url:
                            asin = container.get('data-asin')
                            if asin:
                                product_url = self._build_product_url(asin)
                            else:
                                continue
                        
                        product_data = ScrapedProductData()
                        product_data.platform_url = product_url
                        
                        name_elem = container.select_one('h2 a span, h2 span')
                        if name_elem:
                            product_data.name = name_elem.get_text(strip=True)
                        
                        price_container = container.select_one('.a-price')
                        if price_container:
                            whole_part = price_container.select_one('.a-price-whole')
                            fraction_part = price_container.select_one('.a-price-fraction')
                            if whole_part:
                                price_text = whole_part.get_text(strip=True)
                                if fraction_part:
                                    price_text += '.' + fraction_part.get_text(strip=True)
                                product_data.current_price = self._parse_price(price_text)
                        
                        asin = self._extract_asin_from_url(product_url)
                        if not asin:
                            asin = container.get('data-asin')
                        if asin:
                            product_data.platform_product_id = asin
                            product_data.unique_identifier = f"AMAZON_{asin}"
                        
                        if product_data.name:
                            results.append(product_data)
                    except Exception as e:
                        logger.warning(f"Error processing search result: {e}")
                        continue
            
            logger.info(f"Returning {len(results)} products from Amazon search")
            
        except Exception as e:
            logger.error(f"Error searching Amazon: {e}")
        
        return results
    
    def get_product_details(self, product_url: str) -> Optional[ScrapedProductData]:
        """Get detailed product information from Amazon product page."""
        try:
            logger.info(f"Fetching product details from: {product_url}")
            
            html_content = self._get_page_content(product_url)
            if not html_content:
                logger.error("Failed to fetch product page")
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check if page loaded correctly (not a 404 or error page)
            if soup.select_one('#productTitle') is None and soup.select_one('h1') is None:
                logger.warning("Product page may not have loaded correctly")
                return None
            
            product_data = self._extract_product_data_from_soup(soup, product_url)
            
            if product_data:
                logger.info(f"Successfully extracted product data: {product_data.name}")
            else:
                logger.warning("Failed to extract product data")
            
            return product_data
            
        except Exception as e:
            logger.error(f"Error getting product details from Amazon: {e}")
            return None


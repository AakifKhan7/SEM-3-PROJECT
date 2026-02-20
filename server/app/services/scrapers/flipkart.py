"""
Flipkart scraper implementation.
Handles product search and detail extraction from Flipkart.
"""

import re
import logging
import time
from typing import List, Optional, Tuple
from decimal import Decimal
from urllib.parse import quote_plus, urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base import BaseScraper, ScrapedProductData


logger = logging.getLogger(__name__)


class FlipkartScraper(BaseScraper):
    """Scraper for Flipkart."""
    
    def __init__(self, headless: bool = True, rate_limit_seconds: float = 3.0):
        super().__init__(
            platform_name="Flipkart",
            base_url="https://www.flipkart.com",
            rate_limit_seconds=rate_limit_seconds,
            use_selenium=True,
            headless=headless,
            timeout=30
        )
    
    def _build_search_url(self, query: str) -> str:
        """Build Flipkart search URL."""
        encoded_query = quote_plus(query)
        return f"{self.base_url}/search?q={encoded_query}"
    
    def _build_product_url(self, product_id: str) -> str:
        """Build Flipkart product URL from product ID."""
        return f"{self.base_url}/p/{product_id}"
    
    def _extract_product_id_from_url(self, url: str) -> Optional[str]:
        """Extract product ID from Flipkart URL."""
        # Pattern: /p/product-name/p/pid or /product-name/p/pid
        patterns = [
            r'/p/([^/?]+)',
            r'pid=([^&]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def _parse_flipkart_price(self, soup: BeautifulSoup) -> Tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
        """
        Parse price information from Flipkart page using XPath and structural selectors.
        Returns: (current_price, original_price, discount_percentage)
        """
        current_price = None
        original_price = None
        discount_percentage = None
        
        if self.driver:
            try:
                price_xpath = "/html/body/div[1]/div/div[3]/div[1]/div[2]/div[2]/div/div[3]/div[1]/div/div[1]"
                price_elem = self.driver.find_element(By.XPATH, price_xpath)
                if price_elem:
                    price_text = price_elem.text.strip()
                    if price_text:
                        price_match = re.search(r'₹\s*([\d,]+)(?:\s|%|off|$|[^\d,])', price_text)
                        if price_match:
                            try:
                                price_val = Decimal(price_match.group(1).replace(',', ''))
                                if 1000 <= price_val <= 5000000:
                                    current_price = price_val
                            except:
                                pass
            except (NoSuchElementException, Exception):
                pass
        
        if not current_price:
            try:
                body = soup.select_one('body')
                if body:
                    div1 = body.find('div', recursive=False)
                    if div1:
                        div2 = div1.find('div', recursive=False)
                        if div2:
                            div3_list = div2.find_all('div', recursive=False)
                            if len(div3_list) >= 3:
                                target_div = div3_list[2]
                                div1_inner = target_div.find('div', recursive=False)
                                if div1_inner:
                                    div2_list = div1_inner.find_all('div', recursive=False)
                                    if len(div2_list) >= 2:
                                        price_container = div2_list[1]
                                        price_text = price_container.get_text()
                                        price_match = re.search(r'₹\s*([\d,]+)(?:\s|%|off|$|[^\d,])', price_text)
                                        if price_match:
                                            try:
                                                price_val = Decimal(price_match.group(1).replace(',', ''))
                                                if 1000 <= price_val <= 5000000:
                                                    current_price = price_val
                                            except:
                                                pass
            except:
                pass
        
        if not current_price:
            h1_elem = soup.select_one('h1')
            if h1_elem:
                price_section = h1_elem.find_next_sibling('div')
                if price_section:
                    price_text = price_section.get_text()
                    price_match = re.search(r'₹\s*([\d,]+)(?:\s|%|off|$|[^\d,])', price_text)
                    if price_match:
                        try:
                            price_val = Decimal(price_match.group(1).replace(',', ''))
                            if 1000 <= price_val <= 5000000:
                                current_price = price_val
                        except:
                            pass
        
        main_text = soup.get_text()
        
        price_pattern = r'₹\s*([\d,]+)(?:\s|%|off|discount|$|[^\d])'
        all_matches = re.findall(price_pattern, main_text)
        
        valid_prices = []
        for match in all_matches:
            try:
                price_val = Decimal(match.replace(',', ''))
                if 1000 <= price_val <= 5000000:
                    valid_prices.append(price_val)
            except:
                pass
        
        if valid_prices:
            valid_prices = sorted(set(valid_prices))
            if not current_price:
                current_price = valid_prices[0]
            if len(valid_prices) > 1:
                if not original_price:
                    original_price = valid_prices[-1]
                elif valid_prices[-1] > original_price:
                    original_price = valid_prices[-1]
        
        if not original_price and self.driver:
            try:
                price_xpath = "/html/body/div[1]/div/div[3]/div[1]/div[2]/div[2]/div/div[3]/div[1]/div/div[1]"
                price_container = self.driver.find_element(By.XPATH, price_xpath)
                if price_container:
                    price_text = price_container.text
                    if price_text:
                        price_matches = re.findall(r'₹\s*([\d,]+)(?:\s|%|off|discount|$|[^\d,])', price_text)
                        if price_matches:
                            prices = []
                            for m in price_matches:
                                try:
                                    p = Decimal(m.replace(',', ''))
                                    if 1000 <= p <= 5000000:
                                        prices.append(p)
                                except:
                                    pass
                            if prices:
                                prices = sorted(set(prices))
                                if len(prices) >= 2:
                                    if not current_price:
                                        current_price = prices[0]
                                    original_price = prices[-1]
                                elif len(prices) == 1 and not current_price:
                                    current_price = prices[0]
            except (NoSuchElementException, Exception):
                pass
        
        if not original_price:
            try:
                body = soup.select_one('body')
                if body:
                    div1 = body.find('div', recursive=False)
                    if div1:
                        div2 = div1.find('div', recursive=False)
                        if div2:
                            div3_list = div2.find_all('div', recursive=False)
                            if len(div3_list) >= 3:
                                target_div = div3_list[2]
                                div1_inner = target_div.find('div', recursive=False)
                                if div1_inner:
                                    div2_list = div1_inner.find_all('div', recursive=False)
                                    if len(div2_list) >= 2:
                                        price_container = div2_list[1]
                                        price_text = price_container.get_text()
                                        price_matches = re.findall(r'₹\s*([\d,]+)(?:\s|%|off|discount|$|[^\d,])', price_text)
                                        if price_matches:
                                            prices = []
                                            for m in price_matches:
                                                try:
                                                    p = Decimal(m.replace(',', ''))
                                                    if 1000 <= p <= 5000000:
                                                        prices.append(p)
                                                except:
                                                    pass
                                            if prices:
                                                prices = sorted(set(prices))
                                                if len(prices) >= 2:
                                                    if not current_price:
                                                        current_price = prices[0]
                                                    original_price = prices[-1]
                                                elif len(prices) == 1 and not current_price:
                                                    current_price = prices[0]
            except:
                pass
        
        
        discount_match = re.search(r'(\d+)%\s*(?:off|discount)', main_text, re.IGNORECASE)
        if discount_match:
            try:
                discount_percentage = Decimal(discount_match.group(1))
                if discount_percentage > 100:
                    discount_percentage = None
            except:
                pass
        
        if original_price and current_price:
            if original_price <= current_price:
                if original_price > 1000 and current_price > original_price * 10:
                    current_price = original_price
            elif original_price > current_price:
                if not discount_percentage:
                    discount_percentage = ((original_price - current_price) / original_price) * 100
                    if discount_percentage > 100:
                        discount_percentage = None
        
        if not current_price and original_price and original_price > 1000:
            current_price = original_price
        
        return current_price, original_price, discount_percentage
    
    def _extract_product_data_from_soup(self, soup: BeautifulSoup, product_url: str) -> Optional[ScrapedProductData]:
        """Extract product data from BeautifulSoup object."""
        try:
            product_data = ScrapedProductData()
            product_data.platform_url = product_url.split('?')[0] if product_url else None
            
            # Extract product ID
            product_id = self._extract_product_id_from_url(product_url)
            if product_id:
                product_data.platform_product_id = product_id
                product_data.unique_identifier = f"FLIPKART_{product_id}"
            
            name_elem = soup.select_one('h1')
            if name_elem:
                product_data.name = name_elem.get_text(strip=True)
            
            if not product_data.name:
                name_elem = soup.select_one('h1 span, h1 > span')
                if name_elem:
                    product_data.name = name_elem.get_text(strip=True)
            
            if not product_data.name:
                title_elem = soup.select_one('title')
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    if '|' in title_text:
                        product_data.name = title_text.split('|')[0].strip()
                    else:
                        product_data.name = title_text
            
            if product_data.name:
                name_parts = product_data.name.split()
                if name_parts:
                    product_data.brand = name_parts[0]
            
            brand_link = soup.select_one('a[href*="brand"]')
            if brand_link:
                brand_text = brand_link.get_text(strip=True)
                if brand_text and brand_text.lower() not in ['brand'] and len(brand_text) < 50:
                    product_data.brand = brand_text
            
            if self.driver:
                try:
                    category_xpath = "/html/body/div[1]/div/div[3]/div[1]/div[2]/div[1]/div[1]/div/div[3]/a"
                    category_elem = self.driver.find_element(By.XPATH, category_xpath)
                    if category_elem:
                        cat_text = category_elem.text.strip()
                        if cat_text and len(cat_text) > 1 and len(cat_text) < 50:
                            product_data.category = cat_text
                except (NoSuchElementException, Exception):
                    pass
            
            if not product_data.category:
                try:
                    body = soup.select_one('body')
                    if body:
                        div1 = body.find('div', recursive=False)
                        if div1:
                            div2 = div1.find('div', recursive=False)
                            if div2:
                                div3_list = div2.find_all('div', recursive=False)
                                if len(div3_list) >= 3:
                                    target_div = div3_list[2]
                                    div1_inner = target_div.find('div', recursive=False)
                                    if div1_inner:
                                        div2_list = div1_inner.find_all('div', recursive=False)
                                        if len(div2_list) >= 1:
                                            category_container = div2_list[0]
                                            div1_cat = category_container.find('div', recursive=False)
                                            if div1_cat:
                                                div_cat = div1_cat.find('div', recursive=False)
                                                if div_cat:
                                                    div3_cat_list = div_cat.find_all('div', recursive=False)
                                                    if len(div3_cat_list) >= 3:
                                                        category_link = div3_cat_list[2].find('a')
                                                        if category_link:
                                                            cat_text = category_link.get_text(strip=True)
                                                            if cat_text and len(cat_text) > 1 and len(cat_text) < 50:
                                                                product_data.category = cat_text
                except:
                    pass
            
            if not product_data.category:
                nav_elem = soup.select_one('nav')
                if nav_elem:
                    nav_links = nav_elem.select('a')
                    if nav_links:
                        categories = []
                        seen_categories = set()
                        for link in nav_links:
                            cat_text = link.get_text(strip=True)
                            href = link.get('href', '')
                            if cat_text and href:
                                if '/c/' in href or '/category/' in href or '/browse/' in href:
                                    cat_lower = cat_text.lower()
                                    if cat_lower not in ['home', 'flipkart', 'all', 'more', 'view all'] and len(cat_text) > 1 and len(cat_text) < 50:
                                        if cat_lower not in seen_categories:
                                            categories.append(cat_text)
                                            seen_categories.add(cat_lower)
                        if categories:
                            product_data.category = ' > '.join(categories[:5])
            
            if not product_data.category:
                all_links = soup.select('a[href*="/c/"], a[href*="/category/"], a[href*="/browse/"]')
                if all_links:
                    categories = []
                    seen_categories = set()
                    for link in all_links:
                        cat_text = link.get_text(strip=True)
                        href = link.get('href', '')
                        if cat_text and href:
                            cat_lower = cat_text.lower()
                            if cat_lower not in ['home', 'flipkart', 'all', 'more', 'view all'] and len(cat_text) > 1 and len(cat_text) < 50:
                                if cat_lower not in seen_categories:
                                    categories.append(cat_text)
                                    seen_categories.add(cat_lower)
                    if categories:
                        product_data.category = ' > '.join(categories[:5])
            
            # Description
            desc_selectors = [
                '._1mXcCf',
                '._3la3Fn',
                '.product-description',
            ]
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    product_data.description = desc_elem.get_text(strip=True, separator='\n')
                    break
            
            # High-level features/description
            if not product_data.description:
                features_elem = soup.select_one('._2418kt')
                if features_elem:
                    features = [li.get_text(strip=True) for li in features_elem.select('li')]
                    product_data.description = '\n'.join(features)
            
            img_selectors = [
                '._396cs4._2amPTt._3qGmMb',
                '._396cs4',
                'img[class*="product"]',
                '#container img',
                '._2r_T1I',
            ]
            for selector in img_selectors:
                img_elem = soup.select_one(selector)
                if img_elem:
                    img_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src')
                    if img_url:
                        if img_url.startswith('//'):
                            product_data.image_url = 'https:' + img_url
                        elif img_url.startswith('/'):
                            product_data.image_url = self.base_url + img_url
                        else:
                            product_data.image_url = img_url
                        if 'placeholder' not in product_data.image_url.lower() and product_data.image_url:
                            break
            
            current_price, original_price, discount_percentage = self._parse_flipkart_price(soup)
            product_data.current_price = current_price
            product_data.original_price = original_price
            product_data.discount_percentage = discount_percentage
            
            
            page_text_lower = soup.get_text().lower()
            
            if 'add to cart' in page_text_lower or 'buy now' in page_text_lower:
                product_data.availability_status = "in_stock"
            elif 'out of stock' in page_text_lower or 'currently unavailable' in page_text_lower or 'sold out' in page_text_lower:
                product_data.availability_status = "out_of_stock"
            else:
                add_to_cart = soup.select_one('button[type="button"], button')
                if add_to_cart:
                    button_text = add_to_cart.get_text(strip=True).lower()
                    if 'add to cart' in button_text or 'buy now' in button_text:
                        product_data.availability_status = "in_stock"
                    elif 'out of stock' in button_text or 'unavailable' in button_text:
                        product_data.availability_status = "out_of_stock"
                
                if product_data.availability_status == "unknown":
                    main_content = soup.select_one('main, [role="main"]')
                    if main_content:
                        main_text = main_content.get_text().lower()
                        if 'add to cart' in main_text or 'buy now' in main_text:
                            product_data.availability_status = "in_stock"
                        elif 'out of stock' in main_text or 'unavailable' in main_text:
                            product_data.availability_status = "out_of_stock"
            
            rating_elem = soup.select_one('[id*="rating"], [id*="Rating"], [class*="rating"], [class*="Rating"]')
            if rating_elem:
                rating_text = rating_elem.get_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    try:
                        rating_val = Decimal(rating_match.group(1))
                        if 0 < rating_val <= 5:
                            product_data.rating = rating_val
                    except:
                        pass
            
            if not product_data.rating:
                page_text = soup.get_text()
                rating_patterns = [
                    r'(\d+\.?\d*)\s*(?:out of|/)\s*5',
                    r'(\d+\.?\d*)\s*stars?',
                    r'rating[:\s]+(\d+\.?\d*)',
                    r'rated\s+(\d+\.?\d*)',
                    r'★\s*(\d+\.?\d*)',
                    r'(\d+\.?\d*)\s*★',
                ]
                
                for pattern in rating_patterns:
                    rating_match = re.search(pattern, page_text, re.IGNORECASE)
                    if rating_match:
                        try:
                            rating_val = Decimal(rating_match.group(1))
                            if 0 < rating_val <= 5:
                                product_data.rating = rating_val
                                break
                        except:
                            pass
            
            if not product_data.rating:
                rating_section = soup.select_one('h1 ~ div, h1 + div, h1 ~ span')
                if rating_section:
                    rating_text = rating_section.get_text()
                    rating_match = re.search(r'(\d+\.?\d*)\s*(?:out of|/|stars|★)', rating_text, re.IGNORECASE)
                    if rating_match:
                        try:
                            rating_val = Decimal(rating_match.group(1))
                            if 0 < rating_val <= 5:
                                product_data.rating = rating_val
                        except:
                            pass
            
            if not product_data.rating:
                all_divs = soup.select('div, span')
                for elem in all_divs:
                    elem_text = elem.get_text(strip=True)
                    rating_match = re.search(r'^(\d+\.?\d*)\s*(?:out of|/)\s*5$', elem_text, re.IGNORECASE)
                    if rating_match:
                        try:
                            rating_val = Decimal(rating_match.group(1))
                            if 0 < rating_val <= 5:
                                product_data.rating = rating_val
                                break
                        except:
                            pass
            
            seller_elem = soup.select_one('#sellerName, [id="sellerName"]')
            if seller_elem:
                seller_text = seller_elem.get_text(strip=True)
                if seller_text:
                    product_data.seller_name = seller_text.split('\n')[0].split('|')[0].strip()
            
            if not product_data.seller_name:
                invalid_sellers = ['become a seller', 'seller', 'view more', 'view all', 'see more', 'see other sellers', 'other sellers', 'sold by', 'flipkart']
                
                seller_patterns = [
                    r'sold\s+by[:\s]+([^,\n\r]+)',
                    r'seller[:\s]+([^,\n\r]+)',
                    r'from[:\s]+([^,\n\r]+)',
                ]
                
                page_text = soup.get_text()
                for pattern in seller_patterns:
                    seller_match = re.search(pattern, page_text, re.IGNORECASE)
                    if seller_match:
                        seller_text = seller_match.group(1).strip()
                        seller_text = seller_text.split('\n')[0].split('|')[0].strip()
                        if seller_text.lower() not in invalid_sellers and len(seller_text) > 2 and len(seller_text) < 100:
                            product_data.seller_name = seller_text
                            break
                
                if not product_data.seller_name:
                    seller_links = soup.select('a[href*="seller"], a[href*="merchant"]')
                    for link in seller_links:
                        seller_text = link.get_text(strip=True)
                        if seller_text:
                            seller_text = seller_text.split('\n')[0].split('|')[0].strip()
                            if seller_text.lower() not in invalid_sellers and len(seller_text) > 2 and len(seller_text) < 100:
                                product_data.seller_name = seller_text
                                break
            
            page_text = soup.get_text()
            
            delivery_patterns = [
                r'(free\s+delivery|delivery\s+by|dispatch\s+in|delivered\s+by|delivery\s+in).*?(\d+\s*(?:day|hour|minute|week)s?)',
                r'(delivery\s+in|dispatch\s+in)\s*(\d+\s*(?:day|hour|minute|week)s?)',
                r'(free\s+delivery)',
                r'(delivery\s+by\s+\d+)',
                r'(delivered\s+by\s+\d+)',
            ]
            
            for pattern in delivery_patterns:
                delivery_match = re.search(pattern, page_text, re.IGNORECASE)
                if delivery_match:
                    delivery_text = delivery_match.group(0)
                    if 'offer' not in delivery_text.lower() and 'bank' not in delivery_text.lower() and 'cashback' not in delivery_text.lower():
                        product_data.delivery_time = delivery_text[:150]
                        break
            
            if not product_data.delivery_time:
                main_content = soup.select_one('main, [role="main"]')
                if main_content:
                    main_text = main_content.get_text()
                    for pattern in delivery_patterns:
                        delivery_match = re.search(pattern, main_text, re.IGNORECASE)
                        if delivery_match:
                            delivery_text = delivery_match.group(0)
                            if 'offer' not in delivery_text.lower() and 'bank' not in delivery_text.lower():
                                product_data.delivery_time = delivery_text[:150]
                                break
            
            if not product_data.delivery_time:
                delivery_section = soup.select_one('div, section')
                if delivery_section:
                    section_text = delivery_section.get_text()
                    delivery_match = re.search(r'(delivery|dispatch).*?(\d+\s*(?:day|hour|minute|week)s?)', section_text, re.IGNORECASE)
                    if delivery_match:
                        delivery_text = delivery_match.group(0)
                        if 'offer' not in delivery_text.lower() and 'bank' not in delivery_text.lower():
                            product_data.delivery_time = delivery_text[:150]
            
            # Delivery charges
            if 'free' in (product_data.delivery_time or '').lower():
                product_data.delivery_charges = Decimal('0')
            else:
                # Try to extract delivery charges
                delivery_text = product_data.delivery_time or ''
                charge_match = re.search(r'₹\s*(\d+)', delivery_text)
                if charge_match:
                    product_data.delivery_charges = Decimal(charge_match.group(1))
            
            # Offers
            offers = []
            offer_elements = soup.select('._3D89xM, ._2TpdnF')
            for offer_elem in offer_elements:
                offer_text = offer_elem.get_text(strip=True)
                if offer_text and 'offer' in offer_text.lower():
                    offers.append({"type": "offer", "text": offer_text})
            
            # Bank offers
            bank_offers = soup.select('._3D89xM')
            for bank_offer in bank_offers:
                offer_text = bank_offer.get_text(strip=True)
                if offer_text:
                    offers.append({"type": "bank_offer", "text": offer_text})
            
            if offers:
                product_data.offers = offers
            
            return product_data
            
        except Exception as e:
            logger.error(f"Error extracting product data from Flipkart page: {e}")
            return None
    
    def _extract_product_data_from_product_page(self, soup, url):
        """Extract data when landing directly on a product page"""
        try:
            # Title
            title_elem = soup.select_one('h1.CEn5rD > span.LMizgS, span.B_NuCI, h1.YH7t_4')
            name = title_elem.text.strip() if title_elem else "Unknown Product"
            
            # Price
            price_elem = soup.select_one('div.hZ3P6w.bnqy13, div.Nx9bqj.CxhGGd, div._30jeq3._16Jk6d')
            current_price = self._parse_price(price_elem.text) if price_elem else None
            
            # Original Price
            org_price_elem = soup.select_one('div.kRYCnD, div._3I9_wc._2p6lqe')
            original_price = self._parse_price(org_price_elem.text) if org_price_elem else current_price
            
            # Rating
            rating_elem = soup.select_one('div.MKiFS6, div.XQDdHH, div._3LWZlK')
            rating = float(rating_elem.text.strip()) if rating_elem and rating_elem.text.strip().replace('.','',1).isdigit() else None
            
            # Image
            img_elem = soup.select_one('img.DByuf4, img._396cs4, img.q6DClP')
            image_url = img_elem.get('src') if img_elem else None
            
            if not current_price:
                return None

            return ScrapedProductData(
                name=name,
                current_price=current_price,
                original_price=original_price or current_price,
                rating=rating,
                review_count=0,
                image_url=image_url,
                product_url=url,
                source='Flipkart'
            )
        except Exception as e:
            print(f"Error extracting from product page: {e}")
            return None

    def search_products(self, query: str, max_results: int = 10, fetch_details: bool = True) -> List[ScrapedProductData]:
        """
        Search for products on Flipkart.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            fetch_details: If True, fetch detailed product info from each product page.
                          If False, only extract basic info from search results page.
        """
        results = []
        
        try:
            search_url = self._build_search_url(query)
            logger.info(f"Searching Flipkart for: {query}")
            
            html_content = self._get_page_content(search_url)
            if not html_content:
                logger.error("Failed to fetch search results")
                return results
            
            if self.use_selenium and self.driver:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.cPHDOP, div.slAVV4, ._1AtVbE, ._2kHMtA, [data-id]'))
                    )
                    time.sleep(2)
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                    time.sleep(1)
                    html_content = self.driver.page_source
                except TimeoutException:
                    logger.warning("Timeout waiting for search results, using current page source")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check if we were redirected to a product page directly
            if soup.find('h1', class_='CEn5rD') or soup.find('span', class_='B_NuCI'):
                logger.info("Redirected to product page directly.")
                product_data = self._extract_product_data_from_product_page(soup, self.driver.current_url if self.driver else search_url)
                if product_data:
                    return [product_data]
            
            # Reliable approach: Find title elements or product links first, then walk up to their container
            title_elems = soup.select('._4rR01T, ._2WkVRV, .RG5Slk, .KzDlHZ, .wjcEIp')
            if not title_elems:
                # Fallback: find any link that looks like a product link
                link_elems = soup.select('a[href*="/p/"]')
                # Filter out obvious non-product links (like generic category links if they somehow have /p/)
                title_elems = [a for a in link_elems if a.get_text(strip=True)]
            
            product_containers = []
            seen_containers = set()
            
            for elem in title_elems:
                # Walk up to find a suitable outer container
                container = elem.find_parent('div', class_=lambda x: x and any(c in x for c in ['_1AtVbE', '_2kHMtA', 'cPHDOP', 'slAVV4', 'jIjQ8S', 'col-12-12', 'Vba09Z']))
                # If no specific class parent found, just go up 3-4 levels
                if not container:
                    curr = elem
                    for _ in range(4):
                        if curr.parent and curr.parent.name == 'div':
                            curr = curr.parent
                    container = curr
                
                if container and container not in seen_containers:
                    seen_containers.add(container)
                    product_containers.append(container)

            
            logger.info(f"Found {len(product_containers)} product containers")
            
            product_urls = []
            for container in product_containers:
                try:
                    if len(product_urls) >= max_results:
                        break
                    
                    link_elem = container.select_one('a[href*="/p/"]')
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
                    
                    if '/p/' not in product_url:
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
                        
                        link_elem = container.select_one('a[href*="/p/"]')
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
                        
                        if '/p/' not in product_url:
                            continue
                        
                        product_data = ScrapedProductData()
                        product_data.platform_url = product_url.split('?')[0] if product_url else None
                        
                        name_elem = container.select_one('._4rR01T, ._2WkVRV, .s1Q9rs, .KzDlHZ, .wjcEIp, .RG5Slk')
                        if name_elem:
                            product_data.name = name_elem.get_text(strip=True)
                        elif elem.name != 'a':
                            # If we couldn't find it inside, maybe 'elem' itself is the title!
                            product_data.name = elem.get_text(strip=True)
                        
                        price_elem = container.select_one('._30jeq3, ._1_WHN1, .Nx9bqj, .yRaY8j')
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            product_data.current_price = self._parse_price(price_text)
                        
                        if not product_data.current_price:
                            # Fallback to regex on raw text since Flipkart randomizes class names constantly
                            text = container.get_text(separator=' ', strip=True)
                            from re import findall
                            prices = findall(r'₹[0-9,]+', text)
                            if prices:
                                product_data.current_price = self._parse_price(prices[0])
                                if len(prices) > 1:
                                    product_data.original_price = self._parse_price(prices[1])
                        
                        product_id = self._extract_product_id_from_url(product_url)
                        if product_id:
                            product_data.platform_product_id = product_id
                            product_data.unique_identifier = f"FLIPKART_{product_id}"
                        
                        logger.info(f"DEBUG LOOP: name={product_data.name}, price={product_data.current_price}, pid={product_id}")
                        if product_data.name:
                            results.append(product_data)
                        else:
                            logger.info("DEBUG LOOP: Name missing!")
                    except Exception as e:
                        logger.warning(f"Error processing search result: {e}")
                        continue
            
            logger.info(f"Returning {len(results)} products from Flipkart search")
            
        except Exception as e:
            logger.error(f"Error searching Flipkart: {e}")
        
        return results
    
    def get_product_details(self, product_url: str) -> Optional[ScrapedProductData]:
        """Get detailed product information from Flipkart product page."""
        try:
            logger.info(f"Fetching product details from: {product_url}")
            
            html_content = self._get_page_content(product_url)
            if not html_content:
                logger.error("Failed to fetch product page")
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check if page loaded correctly
            if soup.select_one('.B_NuCI') is None and soup.select_one('h1') is None:
                logger.warning("Product page may not have loaded correctly")
                return None
            
            product_data = self._extract_product_data_from_soup(soup, product_url)
            
            if product_data:
                logger.info(f"Successfully extracted product data: {product_data.name}")
            else:
                logger.warning("Failed to extract product data")
            
            return product_data
            
        except Exception as e:
            logger.error(f"Error getting product details from Flipkart: {e}")
            return None


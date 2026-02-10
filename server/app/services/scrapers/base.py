"""
Base scraper class for all e-commerce platform scrapers.
Provides common functionality like rate limiting, error handling, and data normalization.
"""

import time
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Any
from datetime import datetime
from decimal import Decimal
import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException
)
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


class ScrapedProductData:
    """Normalized product data structure matching database schema."""
    
    def __init__(self):
        # Product basic info
        self.name: Optional[str] = None
        self.brand: Optional[str] = None
        self.category: Optional[str] = None
        self.description: Optional[str] = None
        self.image_url: Optional[str] = None
        self.unique_identifier: Optional[str] = None
        
        # Platform-specific info
        self.platform_product_id: Optional[str] = None
        self.platform_url: Optional[str] = None
        
        # Pricing info
        self.current_price: Optional[Decimal] = None
        self.original_price: Optional[Decimal] = None
        self.discount_percentage: Optional[Decimal] = None
        self.currency: str = "INR"
        
        # Availability
        self.availability_status: str = "unknown"  # 'in_stock', 'out_of_stock', 'pre_order'
        
        # Seller info
        self.seller_rating: Optional[Decimal] = None
        self.seller_name: Optional[str] = None
        
        # Product Rating
        self.rating: Optional[Decimal] = None
        self.rating_count: Optional[int] = None
        
        # Delivery info
        self.delivery_time: Optional[str] = None
        self.delivery_charges: Optional[Decimal] = None
        
        # Offers
        self.offers: List[Dict[str, Any]] = []
        
        # Metadata
        self.scraped_at: datetime = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "name": self.name,
            "brand": self.brand,
            "category": self.category,
            "description": self.description,
            "image_url": self.image_url,
            "unique_identifier": self.unique_identifier,
            "platform_product_id": self.platform_product_id,
            "platform_url": self.platform_url,
            "current_price": float(self.current_price) if self.current_price else None,
            "original_price": float(self.original_price) if self.original_price else None,
            "discount_percentage": float(self.discount_percentage) if self.discount_percentage else None,
            "currency": self.currency,
            "availability_status": self.availability_status,
            "seller_rating": float(self.seller_rating) if self.seller_rating else None,
            "seller_name": self.seller_name,
            "rating": float(self.rating) if self.rating else None,
            "rating_count": self.rating_count,
            "delivery_time": self.delivery_time,
            "delivery_charges": float(self.delivery_charges) if self.delivery_charges else None,
            "offers": json.dumps(self.offers) if self.offers else None,
            "scraped_at": self.scraped_at
        }


class BaseScraper(ABC):
    """Abstract base class for all e-commerce platform scrapers."""
    
    def __init__(
        self,
        platform_name: str,
        base_url: str,
        rate_limit_seconds: float = 2.0,
        use_selenium: bool = True,
        headless: bool = True,
        timeout: int = 30
    ):
        """
        Initialize base scraper.
        
        Args:
            platform_name: Name of the platform (e.g., 'Amazon', 'Flipkart')
            base_url: Base URL of the platform
            rate_limit_seconds: Minimum seconds between requests
            use_selenium: Whether to use Selenium for dynamic content
            headless: Run browser in headless mode
            timeout: Timeout for page loads in seconds
        """
        self.platform_name = platform_name
        self.base_url = base_url
        self.rate_limit_seconds = rate_limit_seconds
        self.use_selenium = use_selenium
        self.headless = headless
        self.timeout = timeout
        
        self.last_request_time = 0.0
        self.driver: Optional[webdriver.Chrome] = None
        self.session: Optional[requests.Session] = None
        
        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
    
    def _get_chrome_options(self) -> Options:
        """Get Chrome options for Selenium."""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(f"--user-agent={self.user_agents[0]}")
        options.add_argument("--window-size=1920,1080")
        return options
    
    def _init_selenium_driver(self) -> webdriver.Chrome:
        """Initialize Selenium WebDriver."""
        try:
            options = self._get_chrome_options()
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize Selenium driver: {e}")
            raise
    
    def _init_requests_session(self) -> requests.Session:
        """Initialize requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            "User-Agent": self.user_agents[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })
        return session
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_seconds:
            sleep_time = self.rate_limit_seconds - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_page_content(self, url: str) -> Optional[str]:
        """
        Fetch page content using Selenium or requests.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string, or None if failed
        """
        self._rate_limit()
        
        try:
            if self.use_selenium:
                if not self.driver:
                    self.driver = self._init_selenium_driver()
                
                self.driver.get(url)
                # Wait for page to load
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                return self.driver.page_source
            else:
                if not self.session:
                    self.session = self._init_requests_session()
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
                
        except TimeoutException:
            logger.error(f"Timeout while fetching {url}")
            return None
        except requests.RequestException as e:
            logger.error(f"Request error while fetching {url}: {e}")
            return None
        except WebDriverException as e:
            logger.error(f"WebDriver error while fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while fetching {url}: {e}")
            return None
    
    def _parse_price(self, price_text: str) -> Optional[Decimal]:
        """
        Parse price from text string.
        
        Args:
            price_text: Price as string (e.g., "₹1,234.56", "$99.99")
            
        Returns:
            Decimal price or None if parsing fails
        """
        if not price_text:
            return None
        
        try:
            # Remove currency symbols and spaces
            price_text = re.sub(r'[^\d.,]', '', price_text)
            # Replace comma with nothing (for Indian number format)
            price_text = price_text.replace(',', '')
            # Convert to float then Decimal
            return Decimal(str(float(price_text)))
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse price '{price_text}': {e}")
            return None
    
    def _parse_rating(self, rating_text: str) -> Optional[Decimal]:
        """
        Parse rating from text string.
        
        Args:
            rating_text: Rating as string (e.g., "4.5", "4.5 out of 5")
            
        Returns:
            Decimal rating (0-5) or None if parsing fails
        """
        if not rating_text:
            return None
        
        try:
            # Extract first decimal number
            match = re.search(r'(\d+\.?\d*)', str(rating_text))
            if match:
                rating = Decimal(match.group(1))
                # Normalize to 0-5 scale if needed
                if rating > 5:
                    rating = rating / 10
                return rating
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse rating '{rating_text}': {e}")
        
        return None
    
    def _parse_percentage(self, percentage_text: str) -> Optional[Decimal]:
        """
        Parse percentage from text string.
        
        Args:
            percentage_text: Percentage as string (e.g., "25%", "25% off")
            
        Returns:
            Decimal percentage or None if parsing fails
        """
        if not percentage_text:
            return None
        
        try:
            match = re.search(r'(\d+\.?\d*)', str(percentage_text))
            if match:
                return Decimal(match.group(1))
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse percentage '{percentage_text}': {e}")
        
        return None
    
    def _normalize_availability(self, availability_text: str) -> str:
        """
        Normalize availability status to standard values.
        
        Args:
            availability_text: Availability text from website
            
        Returns:
            Normalized status: 'in_stock', 'out_of_stock', or 'pre_order'
        """
        if not availability_text:
            return "unknown"
        
        text_lower = availability_text.lower()
        
        if any(word in text_lower for word in ['in stock', 'available', 'add to cart', 'buy now']):
            return "in_stock"
        elif any(word in text_lower for word in ['out of stock', 'unavailable', 'sold out']):
            return "out_of_stock"
        elif any(word in text_lower for word in ['pre-order', 'preorder', 'coming soon']):
            return "pre_order"
        else:
            return "unknown"
    
    def _build_search_url(self, query: str) -> str:
        """
        Build search URL for the platform.
        
        Args:
            query: Search query string
            
        Returns:
            Complete search URL
        """
        raise NotImplementedError("Subclasses must implement _build_search_url")
    
    def _build_product_url(self, product_id: str) -> str:
        """
        Build product detail URL for the platform.
        
        Args:
            product_id: Platform-specific product ID
            
        Returns:
            Complete product URL
        """
        raise NotImplementedError("Subclasses must implement _build_product_url")
    
    @abstractmethod
    def search_products(self, query: str, max_results: int = 10) -> List[ScrapedProductData]:
        """
        Search for products on the platform.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of ScrapedProductData objects
        """
        pass
    
    @abstractmethod
    def get_product_details(self, product_url: str) -> Optional[ScrapedProductData]:
        """
        Get detailed product information from a product page.
        
        Args:
            product_url: Full URL to the product page
            
        Returns:
            ScrapedProductData object or None if failed
        """
        pass
    
    def cleanup(self):
        """Clean up resources (close driver, session, etc.)."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
            finally:
                self.driver = None
        
        if self.session:
            try:
                self.session.close()
            except Exception as e:
                logger.warning(f"Error closing session: {e}")
            finally:
                self.session = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()
        return False


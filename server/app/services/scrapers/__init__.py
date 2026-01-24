"""
Scrapers module for e-commerce platforms.
Provides scrapers for Amazon, Flipkart, and other platforms.
"""

from .base import BaseScraper, ScrapedProductData
from .amazon import AmazonScraper
from .flipkart import FlipkartScraper

__all__ = [
    'BaseScraper',
    'ScrapedProductData',
    'AmazonScraper',
    'FlipkartScraper',
]


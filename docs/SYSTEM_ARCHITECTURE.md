# Best Deal Aggregator - System Architecture

## 1. Overview

The Best Deal Aggregator is a full-stack web application that collects, processes, and compares product pricing data from multiple e-commerce platforms to help users find the best deals.

## 2. Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL 14+
- **Authentication**: JWT (JSON Web Tokens) + Basic Auth
- **Web Scraping**: BeautifulSoup4, Selenium, Requests
- **Task Queue**: Celery (optional, for async scraping)
- **API Documentation**: FastAPI auto-generated Swagger/OpenAPI

### Frontend
- **HTML5**: Structure
- **CSS**: Styling with Bootstrap 5 and Tailwind CSS
- **JavaScript**: Vanilla JS or lightweight framework for interactions
- **Build Tool**: Vite or simple static file serving

### Infrastructure
- **Web Server**: Uvicorn (ASGI server for FastAPI)
- **Database**: PostgreSQL with connection pooling
- **Caching**: Redis (optional, for caching frequently accessed data)

## 3. System Components

### 3.1 Frontend Layer
- **Search Interface**: Product search input and filters
- **Comparison View**: Side-by-side product comparison across platforms
- **User Dashboard**: User profile, saved searches, price alerts
- **Authentication**: Login/Register pages
- **Product Detail Page**: Detailed product information with price history

### 3.2 Backend API Layer (FastAPI)
```
/api/auth          - Authentication endpoints (register, login, refresh token)
/api/products      - Product search and retrieval
/api/comparison    - Comparison logic and ranking
/api/scraping      - Manual trigger for scraping (admin)
/api/users         - User management
/api/alerts        - Price alert management
```

### 3.3 Scraping/Ingestion Layer
- **Scraping Service**: Modular scrapers for each e-commerce platform
- **Data Normalization**: Convert different formats to unified schema
- **Cache Manager**: Check database for existing data and timestamps
- **Update Scheduler**: Periodic scraping tasks

### 3.4 Database Layer (PostgreSQL)
- **User Management**: Users, sessions, authentication
- **Product Catalog**: Products, variants, metadata
- **Price History**: Historical pricing data with timestamps
- **Scraping Logs**: Track scraping activities and failures
- **User Preferences**: Saved searches, alerts, filters

### 3.5 Business Logic Layer
- **Deal Ranking Algorithm**: Configurable rules for "best deal"
- **Price History Analyzer**: Track price trends
- **Notification System**: Price drop alerts

## 4. Database Schema

### 4.1 Users and Authentication
```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- JWT Refresh Tokens
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 Products and Pricing
```sql
-- E-commerce Platforms
CREATE TABLE platforms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    base_url VARCHAR(200) NOT NULL,
    scraper_class VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE
);

-- Products (normalized)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    brand VARCHAR(100),
    category VARCHAR(100),
    description TEXT,
    image_url VARCHAR(500),
    unique_identifier VARCHAR(200), -- SKU or product code
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product Listings (platform-specific)
CREATE TABLE product_listings (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    platform_id INTEGER REFERENCES platforms(id) ON DELETE CASCADE,
    platform_product_id VARCHAR(200), -- ID on the platform
    platform_url VARCHAR(500),
    current_price DECIMAL(10, 2),
    original_price DECIMAL(10, 2),
    discount_percentage DECIMAL(5, 2),
    currency VARCHAR(10) DEFAULT 'INR',
    availability_status VARCHAR(50), -- 'in_stock', 'out_of_stock', 'pre_order'
    seller_rating DECIMAL(3, 2),
    seller_name VARCHAR(200),
    delivery_time VARCHAR(100),
    delivery_charges DECIMAL(10, 2),
    offers TEXT, -- JSON string of offers
    last_scraped_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(product_id, platform_id)
);

-- Price History
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    product_listing_id INTEGER REFERENCES product_listings(id) ON DELETE CASCADE,
    price DECIMAL(10, 2) NOT NULL,
    original_price DECIMAL(10, 2),
    discount_percentage DECIMAL(5, 2),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_product_listing_scraped (product_listing_id, scraped_at)
);
```

### 4.3 Scraping Management
```sql
-- Scraping Jobs
CREATE TABLE scraping_jobs (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    platform_id INTEGER REFERENCES platforms(id),
    status VARCHAR(50), -- 'pending', 'running', 'completed', 'failed'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scraping Configuration
CREATE TABLE scraping_config (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER REFERENCES platforms(id),
    cache_duration_hours INTEGER DEFAULT 24, -- Data validity period
    scraping_interval_hours INTEGER DEFAULT 24,
    last_scraped_at TIMESTAMP,
    is_enabled BOOLEAN DEFAULT TRUE
);
```

### 4.4 User Features
```sql
-- Saved Searches
CREATE TABLE saved_searches (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    search_query VARCHAR(500) NOT NULL,
    filters JSONB, -- Store filter preferences
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Price Alerts
CREATE TABLE price_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product_listing_id INTEGER REFERENCES product_listings(id) ON DELETE CASCADE,
    target_price DECIMAL(10, 2),
    alert_type VARCHAR(50), -- 'below_price', 'price_drop'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 5. API Endpoints Specification

### 5.1 Authentication (`/api/auth`)
```
POST   /api/auth/register          - Register new user
POST   /api/auth/login             - Login (returns JWT access + refresh token)
POST   /api/auth/refresh           - Refresh access token
POST   /api/auth/logout            - Invalidate refresh token
GET    /api/auth/me                - Get current user info
```

### 5.2 Products (`/api/products`)
```
GET    /api/products/search        - Search products (query params: q, category, filters)
GET    /api/products/{product_id}  - Get product details
GET    /api/products/{product_id}/comparison - Get comparison across platforms
GET    /api/products/{product_id}/price-history - Get price history chart data
```

### 5.3 Comparison (`/api/comparison`)
```
POST   /api/comparison             - Compare products (body: product_ids[], sort_by)
GET    /api/comparison/best-deal   - Get best deal for a product
```

### 5.4 User Features (`/api/users`)
```
GET    /api/users/saved-searches   - Get user's saved searches
POST   /api/users/saved-searches   - Save a search
DELETE /api/users/saved-searches/{id} - Delete saved search
GET    /api/users/alerts           - Get user's price alerts
POST   /api/users/alerts           - Create price alert
DELETE /api/users/alerts/{id}      - Delete price alert
```

### 5.5 Admin/Scraping (`/api/admin`)
```
POST   /api/admin/scrape/{product_id} - Trigger manual scrape
GET    /api/admin/scraping-status     - Get scraping job status
GET    /api/admin/stats               - System statistics
```

## 6. Data Flow

### 6.1 Product Search Flow
```
User Search Request
    ↓
Frontend → Backend API (/api/products/search)
    ↓
Backend checks DB for matching products
    ↓
For each product listing:
    - Check last_scraped_at timestamp
    - If data is stale (older than cache_duration), trigger scrape
    - Otherwise, return cached data
    ↓
Return search results with current prices
```

### 6.2 Scraping Flow
```
Scraping Trigger (Manual or Scheduled)
    ↓
Check scraping_config for platform settings
    ↓
For each platform:
    - Initialize platform-specific scraper
    - Fetch product data from platform
    - Normalize data to unified schema
    - Update product_listings table
    - Insert new entry in price_history
    - Update last_scraped_at timestamp
    ↓
Log scraping job status
```

### 6.3 Comparison Flow
```
Comparison Request
    ↓
Fetch product_listings for all platforms
    ↓
Apply ranking algorithm:
    - Calculate score based on:
      * Price (lower is better)
      * Discount percentage
      * Seller rating
      * Delivery time
      * Delivery charges
    - Apply user preferences/weights if any
    ↓
Sort and return ranked results
```

## 7. Scraping Rules Implementation

### Rule 1: Check Existing Data
```python
# Pseudo-code
def get_product_data(product_id, platform_id):
    listing = get_product_listing(product_id, platform_id)
    
    if listing and listing.last_scraped_at:
        cache_duration = get_scraping_config(platform_id).cache_duration_hours
        age_hours = (now() - listing.last_scraped_at).total_seconds() / 3600
        
        if age_hours < cache_duration:
            return listing  # Return cached data
    return None  # Need to scrape
```

### Rule 2: Show Price History
```python
# When returning product data
product_data = {
    "current_price": listing.current_price,
    "price_history": [
        {
            "price": ph.price,
            "date": ph.scraped_at,
            "discount": ph.discount_percentage
        }
        for ph in get_price_history(listing.id)
    ]
}
```

## 8. Best Deal Ranking Algorithm

### Scoring Formula (Configurable)
```python
def calculate_deal_score(listing, weights):
    score = 0
    
    # Price score (normalized, lower price = higher score)
    price_score = (max_price - listing.current_price) / (max_price - min_price) * 100
    score += price_score * weights['price']  # e.g., 0.4
    
    # Discount score
    discount_score = listing.discount_percentage
    score += discount_score * weights['discount']  # e.g., 0.2
    
    # Rating score
    rating_score = (listing.seller_rating / 5.0) * 100
    score += rating_score * weights['rating']  # e.g., 0.2
    
    # Delivery score (faster = better)
    delivery_score = calculate_delivery_score(listing.delivery_time)
    score += delivery_score * weights['delivery']  # e.g., 0.2
    
    return score
```

### Default Weights
- Price: 40%
- Discount: 20%
- Seller Rating: 20%
- Delivery Time: 20%

## 9. Security Considerations

1. **Authentication**
   - Password hashing using bcrypt
   - JWT tokens with expiration (access: 15min, refresh: 7days)
   - Refresh token rotation

2. **API Security**
   - Rate limiting on scraping endpoints
   - Input validation and sanitization
   - SQL injection prevention (ORM/parameterized queries)

3. **Scraping Ethics**
   - Respect robots.txt
   - Rate limiting between requests
   - User-Agent headers
   - Error handling for blocked requests

## 10. Deployment Architecture

```
┌─────────────┐
│   Frontend  │  (Static files served via Nginx/CDN)
│  (HTML/CSS/ │
│   JS)       │
└──────┬──────┘
       │ HTTP/HTTPS
       ↓
┌──────────────────┐
│   Nginx/Proxy    │
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│   FastAPI App    │  (Uvicorn workers)
│   (Backend API)  │
└──────┬───────────┘
       │
       ├──────────────┐
       ↓              ↓
┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │ Redis Cache  │
│  (Database)  │  │   (Optional) │
└──────────────┘  └──────────────┘

Background Services:
┌──────────────────┐
│ Scraping Service │  (Celery workers or cron jobs)
└──────────────────┘
```

## 11. File Structure

```
project-root/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # DB connection
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   └── ...
│   │   ├── schemas/             # Pydantic schemas
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   └── ...
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── products.py
│   │   │   ├── comparison.py
│   │   │   └── ...
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── scraping_service.py
│   │   │   ├── comparison_service.py
│   │   │   └── scrapers/        # Platform-specific scrapers
│   │   │       ├── base.py
│   │   │       ├── amazon.py
│   │   │       ├── flipkart.py
│   │   │       └── ...
│   │   ├── utils/
│   │   │   ├── security.py      # JWT, password hashing
│   │   │   └── helpers.py
│   │   └── middleware/
│   │       └── auth.py
│   ├── alembic/                 # Database migrations
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── search.html
│   ├── comparison.html
│   ├── dashboard.html
│   ├── css/
│   │   ├── styles.css
│   │   └── ...
│   ├── js/
│   │   ├── auth.js
│   │   ├── search.js
│   │   ├── comparison.js
│   │   ├── api.js
│   │   └── ...
│   └── assets/
├── docs/                        # Additional documentation
├── tests/
│   ├── backend/
│   └── frontend/
├── docker-compose.yml           # For local development
├── README.md
├── SYSTEM_ARCHITECTURE.md
└── DEVELOPMENT_GUIDE.md
```

## 12. Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/deal_aggregator

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# API
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Scraping
DEFAULT_CACHE_DURATION_HOURS=24
SCRAPING_RATE_LIMIT_SECONDS=2
```


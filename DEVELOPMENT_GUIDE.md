# Best Deal Aggregator - Development Guide for Team of 3

## Team Roles & Responsibilities

### Person 1: Backend Developer (API + Database)
**Focus Areas:**
- FastAPI backend setup and structure
- Database schema design and migrations
- Authentication system (JWT + Basic Auth)
- API endpoints implementation
- Database queries and optimization

### Person 2: Scraping & Data Processing Developer
**Focus Areas:**
- Web scraping implementation for multiple platforms
- Data normalization and storage
- Scraping cache logic (timestamp-based)
- Price history tracking
- Scraping job management

### Person 3: Frontend Developer (UI/UX)
**Focus Areas:**
- Frontend HTML/CSS/JS implementation
- Bootstrap and Tailwind CSS integration
- User interface for search, comparison, and dashboard
- API integration from frontend
- User authentication flows (login/register)

---

## Development Phases & Timeline

### Phase 1: Project Setup & Foundation (Week 1)

#### All Team Members
- [ ] Clone repository and set up development environment
- [ ] Review architecture document
- [ ] Set up Git workflow and branch strategy

#### Person 1: Backend Foundation
- [ ] Initialize FastAPI project structure
- [ ] Set up PostgreSQL database
- [ ] Create database models (User, Product, ProductListing, PriceHistory, etc.)
- [ ] Set up Alembic for database migrations
- [ ] Create `.env.example` file with required variables
- [ ] Set up basic FastAPI app with CORS and middleware

**Deliverables:**
- Working FastAPI app with database connection
- All database models defined
- Initial migration files

#### Person 2: Scraping Foundation
- [ ] Research target e-commerce platforms (Amazon, Flipkart, etc.)
- [ ] Set up base scraper class structure
- [ ] Create scraping configuration schema
- [ ] Implement basic HTTP request handling with rate limiting
- [ ] Set up error handling and logging for scrapers

**Deliverables:**
- Base scraper class
- Scraping configuration structure
- Documentation of target platforms

#### Person 3: Frontend Foundation
- [ ] Create HTML structure for main pages (index, login, register, search, comparison)
- [ ] Set up Bootstrap 5 and Tailwind CSS
- [ ] Create base CSS file with theme colors and typography
- [ ] Implement responsive navigation bar
- [ ] Create basic layout components

**Deliverables:**
- Static HTML pages with basic styling
- Responsive navigation
- Base CSS framework setup

---

### Phase 2: Authentication System (Week 2)

#### Person 1: Backend Authentication
- [ ] Implement user registration endpoint (`POST /api/auth/register`)
- [ ] Implement user login endpoint (`POST /api/auth/login`)
- [ ] Implement JWT token generation (access + refresh tokens)
- [ ] Implement token refresh endpoint (`POST /api/auth/refresh`)
- [ ] Implement logout endpoint (`POST /api/auth/logout`)
- [ ] Create authentication middleware for protected routes
- [ ] Add password hashing with bcrypt
- [ ] Create user profile endpoint (`GET /api/auth/me`)

**Deliverables:**
- Complete authentication API
- JWT token system working
- Protected route middleware

#### Person 3: Frontend Authentication
- [ ] Create login page UI with form validation
- [ ] Create registration page UI
- [ ] Implement login API call from frontend
- [ ] Implement registration API call
- [ ] Store JWT tokens in localStorage/sessionStorage
- [ ] Create API utility functions for authenticated requests
- [ ] Implement redirect logic (logged-in users can't access login page)
- [ ] Add error handling and user feedback messages

**Deliverables:**
- Functional login and registration pages
- Token storage and management
- API helper functions

---

### Phase 3: Product Database & Basic Scraping (Week 3)

#### Person 1: Product API Endpoints
- [ ] Implement product search endpoint (`GET /api/products/search`)
- [ ] Implement product detail endpoint (`GET /api/products/{id}`)
- [ ] Create product comparison endpoint (`GET /api/products/{id}/comparison`)
- [ ] Add pagination to search results
- [ ] Implement basic filtering and sorting

**Deliverables:**
- Product search API
- Product detail API
- Comparison endpoint skeleton

#### Person 2: Basic Scraping Implementation
- [ ] Implement scraper for Platform 1 (e.g., Flipkart)
  - Extract product name, price, discount, rating
  - Extract seller information
  - Extract delivery time and charges
- [ ] Implement scraper for Platform 2 (e.g., Amazon)
- [ ] Create data normalization service (convert to unified schema)
- [ ] Implement scraping cache logic:
  - Check `last_scraped_at` timestamp
  - Compare with `cache_duration_hours`
  - Return cached data if fresh, else trigger scrape
- [ ] Integrate scraping with product API endpoints
- [ ] Store scraped data in database (ProductListing table)

**Deliverables:**
- Working scrapers for 2 platforms
- Cache logic implemented
- Data stored in database

#### Person 3: Search Interface
- [ ] Create product search page UI
- [ ] Implement search form with filters
- [ ] Connect search form to backend API
- [ ] Display search results in card/list layout
- [ ] Add loading states and error handling
- [ ] Implement pagination UI

**Deliverables:**
- Search page with results display
- API integration working

---

### Phase 4: Comparison & Best Deal Algorithm (Week 4)

#### Person 1: Comparison Algorithm
- [ ] Implement best deal ranking algorithm
- [ ] Create comparison endpoint (`GET /api/comparison/best-deal`)
- [ ] Implement configurable scoring weights (price, rating, delivery, discount)
- [ ] Add endpoint for custom comparison (`POST /api/comparison`)

**Deliverables:**
- Comparison algorithm implemented
- Best deal calculation working

#### Person 2: Price History
- [ ] Implement price history storage on each scrape
- [ ] Create price history endpoint (`GET /api/products/{id}/price-history`)
- [ ] Add price history data to product detail responses
- [ ] Implement timestamp-based history queries

**Deliverables:**
- Price history tracking
- History API endpoint

#### Person 3: Comparison UI
- [ ] Create product comparison page layout
- [ ] Display side-by-side comparison cards
- [ ] Show best deal badge/highlight
- [ ] Integrate price history chart (using Chart.js or similar)
- [ ] Add "View on Platform" buttons with affiliate links

**Deliverables:**
- Comparison view page
- Price history visualization

---

### Phase 5: User Features (Week 5)

#### Person 1: User Features API
- [ ] Implement saved searches endpoints
  - `GET /api/users/saved-searches`
  - `POST /api/users/saved-searches`
  - `DELETE /api/users/saved-searches/{id}`
- [ ] Implement price alerts endpoints
  - `GET /api/users/alerts`
  - `POST /api/users/alerts`
  - `DELETE /api/users/alerts/{id}`
- [ ] Create user dashboard endpoint

**Deliverables:**
- Saved searches API
- Price alerts API

#### Person 3: User Dashboard
- [ ] Create user dashboard page
- [ ] Display saved searches list
- [ ] Display active price alerts
- [ ] Add functionality to create/delete saved searches
- [ ] Add functionality to create/delete price alerts
- [ ] Create product detail page with save/search options

**Deliverables:**
- User dashboard
- Saved searches UI
- Price alerts UI

#### Person 2: Scraping Enhancements
- [ ] Add more platforms (Platform 3, Platform 4)
- [ ] Improve error handling and retry logic
- [ ] Add scraping job status tracking
- [ ] Implement scheduled scraping (optional: using Celery or cron)

**Deliverables:**
- Additional platform scrapers
- Improved scraping reliability

---

### Phase 6: Polish & Testing (Week 6)

#### All Team Members
- [ ] Write unit tests for their components
- [ ] Integration testing
- [ ] Bug fixing
- [ ] Code review and refactoring

#### Person 1: Backend Testing & Optimization
- [ ] Write tests for API endpoints
- [ ] Database query optimization
- [ ] Add API documentation (FastAPI auto-docs)
- [ ] Performance testing

#### Person 2: Scraping Testing
- [ ] Test scrapers with various products
- [ ] Handle edge cases (missing data, blocked requests)
- [ ] Test cache logic thoroughly
- [ ] Verify price history accuracy

#### Person 3: Frontend Testing & UI Polish
- [ ] Test on different browsers
- [ ] Mobile responsiveness testing
- [ ] UI/UX improvements
- [ ] Loading states and error messages refinement

**Deliverables:**
- Tested and polished application
- Documentation

---

## Development Setup Instructions

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Node.js (optional, for frontend tooling)
- Git

### Backend Setup (Person 1)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file from .env.example
cp .env.example .env
# Edit .env with your database credentials

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup (Person 3)
```bash
cd frontend
# Serve using Python's HTTP server or any static file server
python -m http.server 8080
# Or use Live Server extension in VS Code
```

### Database Setup
```bash
# Create database
createdb deal_aggregator

# Run migrations (from backend directory)
cd backend
alembic upgrade head
```

---

## Git Workflow

### Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/feature-name` - Feature branches
- `fix/bug-name` - Bug fix branches

### Workflow
1. Create feature branch from `develop`
   ```bash
   git checkout develop
   git pull
   git checkout -b feature/your-feature-name
   ```

2. Work on feature and commit regularly
   ```bash
   git add .
   git commit -m "Descriptive commit message"
   ```

3. Push and create Pull Request to `develop`
   ```bash
   git push origin feature/your-feature-name
   ```

4. After code review, merge to `develop`
5. Once stable, merge `develop` to `main`

---

## Communication & Coordination

### Daily Standups (15 minutes)
- What did you complete yesterday?
- What are you working on today?
- Any blockers?

### Weekly Sync Meeting (1 hour)
- Review progress
- Discuss integration points
- Plan next week's tasks

### Tools
- **Git**: Version control
- **GitHub/GitLab Issues**: Task tracking
- **Discord/Slack**: Daily communication
- **Shared Documentation**: Google Docs/Notion (optional)

---

## Integration Points

### Backend ↔ Frontend
- **API Contract**: Document all endpoints in Swagger (auto-generated by FastAPI)
- **Data Format**: Agree on request/response JSON structure
- **Error Handling**: Standardize error response format
  ```json
  {
    "detail": "Error message",
    "code": "ERROR_CODE"
  }
  ```

### Backend ↔ Scraping
- **Service Interface**: Define clean service methods
  ```python
  scraping_service.get_product_data(product_id, platform_id)
  scraping_service.scrape_product(product_name, platform_id)
  ```
- **Data Schema**: Use Pydantic models for scraped data validation

### Scraping ↔ Database
- **Cache Check**: Scraping service checks database first
- **Update Strategy**: Insert new price history, update existing listings

---

## Testing Checklist

### Person 1 (Backend)
- [ ] All API endpoints return correct status codes
- [ ] Authentication works (protected routes require JWT)
- [ ] Database queries are optimized
- [ ] Error handling is comprehensive

### Person 2 (Scraping)
- [ ] Scrapers work for all target platforms
- [ ] Cache logic works (doesn't scrape if data is fresh)
- [ ] Price history is stored correctly
- [ ] Handles scraping failures gracefully

### Person 3 (Frontend)
- [ ] All pages load correctly
- [ ] Forms validate input
- [ ] API calls handle errors
- [ ] UI is responsive on mobile/tablet/desktop
- [ ] Authentication flow works end-to-end

---

## Deployment Checklist

### Pre-deployment
- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] Frontend assets built/minified
- [ ] API documentation updated

### Deployment Steps
1. Deploy database (migrations)
2. Deploy backend API
3. Deploy frontend (static files)
4. Configure reverse proxy (Nginx)
5. Set up SSL certificates
6. Monitor logs

---

## Useful Resources

### FastAPI
- Official Docs: https://fastapi.tiangolo.com
- Database Tutorial: https://fastapi.tiangolo.com/tutorial/sql-databases/

### Web Scraping
- BeautifulSoup Docs: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- Requests Library: https://requests.readthedocs.io

### PostgreSQL
- Official Docs: https://www.postgresql.org/docs/

### Frontend
- Bootstrap Docs: https://getbootstrap.com/docs/5.3/
- Tailwind CSS Docs: https://tailwindcss.com/docs

---

## Troubleshooting Common Issues

### Backend Issues
- **Database connection error**: Check `.env` file and PostgreSQL service
- **Migration errors**: Check Alembic version history
- **CORS errors**: Update `CORS_ORIGINS` in config

### Scraping Issues
- **Blocked requests**: Add delays, rotate User-Agents
- **Data not found**: Check selector paths, handle missing elements
- **Rate limiting**: Implement exponential backoff

### Frontend Issues
- **API calls failing**: Check CORS, API base URL
- **Token expired**: Implement automatic token refresh
- **Styling conflicts**: Check Bootstrap/Tailwind class conflicts

---

## Notes

- **Always test locally before pushing**
- **Write clear commit messages**
- **Update documentation as you build**
- **Don't commit sensitive data (passwords, API keys)**
- **Keep code DRY (Don't Repeat Yourself)**
- **Ask for help when blocked - don't waste time**


# Best Deal Aggregator

A full-stack web application that helps users find the most cost-effective place to buy products across multiple online platforms by aggregating and comparing prices, discounts, ratings, and delivery information.

## Project Overview

This project automatically collects product data from various e-commerce websites, normalizes and compares the information, and presents the best deals to users based on price, seller reliability, delivery time, and active offers.

## Key Features

- 🔍 **Product Search**: Search across multiple e-commerce platforms
- 💰 **Price Comparison**: Compare prices, discounts, and offers side-by-side
- 📊 **Price History**: Track historical pricing data
- 🔔 **Price Alerts**: Get notified when prices drop
- 👤 **User Accounts**: Multi-user support with JWT authentication
- ⚡ **Smart Caching**: Efficient data scraping with timestamp-based caching

## Technology Stack

- **Backend**: Python (FastAPI)
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5, Tailwind CSS
- **Authentication**: JWT + Basic Auth
- **Web Scraping**: BeautifulSoup4, Selenium, Requests

## Documentation

- **[System Architecture](SYSTEM_ARCHITECTURE.md)** - Complete system design, database schema, API specifications, and technical architecture
- **[Development Guide](DEVELOPMENT_GUIDE.md)** - Step-by-step development guide for a team of 3, including task distribution and timeline

## Quick Start

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   createdb deal_aggregator
   cd backend
   alembic upgrade head
   ```

3. **Run Backend**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Run Frontend**
   ```bash
   cd frontend
   python -m http.server 8080
   ```

## Team Structure

- **Person 1**: Backend Developer (API + Database + Authentication)
- **Person 2**: Scraping & Data Processing Developer
- **Person 3**: Frontend Developer (UI/UX + API Integration)

## Project Status

🚧 **In Development** - See [Development Guide](DEVELOPMENT_GUIDE.md) for current phase and tasks.

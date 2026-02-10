from fastapi import FastAPI # Trigger reload
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.models import User, UserAuth, UserRole
from app.api import auth
from app.api import products
from app.api import comparison
from app.api import users

app = FastAPI(
    title="Product Comparison API",
    description="Backend API for product comparison and scraping",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

app.include_router(products.router)

app.include_router(comparison.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {"message": "Product Comparison API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


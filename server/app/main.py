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
app.add_middleware(
    CORSMiddleware,
    # You can replace "*" with your exact frontend URL for better security, e.g., ["http://localhost:3000"]
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], # This allows GET, POST, OPTIONS, etc.
    allow_headers=["*"], # This allows all headers (important for your JWTBearer token!)
)

@app.on_event("startup")
async def startup_event():
    init_db()

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

class ForceCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            response = Response(content="OK", status_code=200)
        else:
            response = await call_next(request)
        origin = request.headers.get("origin")
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
        return response

app.add_middleware(ForceCORSMiddleware)

from app.api import admin

app.include_router(auth.router)

app.include_router(products.router)

app.include_router(comparison.router)
app.include_router(users.router)
app.include_router(admin.router)

@app.get("/")
async def root():
    return {"message": "Product Comparison API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, Product, SavedSearch, UserAuth
from app.api.auth import JWTBearer

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(JWTBearer())]
)

@router.get("/stats/graphs")
async def get_admin_graphs(db: Session = Depends(get_db)):
    # 1. User registrations over time
    users_by_date = db.query(func.date(User.createdAt), func.count(User.id)).group_by(func.date(User.createdAt)).order_by(func.date(User.createdAt)).all()
    
    # 2. Products by category
    products_by_category = db.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
    
    # 3. Searches per user
    searches_by_user = db.query(
        UserAuth.email, 
        func.count(SavedSearch.id)
    ).join(UserAuth, UserAuth.user_id == SavedSearch.user_id).group_by(UserAuth.email).order_by(func.count(SavedSearch.id).desc()).limit(10).all()
    
    # Generate User Graph
    user_dates = [str(r[0]) for r in users_by_date]
    user_counts = [r[1] for r in users_by_date]
    
    if not user_dates:
        user_dates = ['No Data']
        user_counts = [0]
        
    # INCREASED SIZE HERE
    plt.figure(figsize=(10, 6)) 
    plt.plot(user_dates, user_counts, marker='o', color='#3b82f6')
    plt.xlabel('Date', fontsize=15)
    plt.ylabel('Count', fontsize=15)
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    buf_user = io.BytesIO()
    plt.savefig(buf_user, format='png', transparent=True)
    buf_user.seek(0)
    user_graph_base64 = base64.b64encode(buf_user.read()).decode('utf-8')
    plt.close()
    
    # Generate Product Graph
    cat_names = [str(r[0]) if r[0] else "Unknown" for r in products_by_category]
    cat_counts = [r[1] for r in products_by_category]
    
    if not cat_names:
        cat_names = ['No Data']
        cat_counts = [0]
        
    # INCREASED SIZE HERE
    plt.figure(figsize=(10, 6))
    plt.bar(cat_names, cat_counts, color='#10b981')
    plt.xlabel('Category', fontsize=15)
    plt.ylabel('Count', fontsize=15)
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.tight_layout()
    
    buf_prod = io.BytesIO()
    plt.savefig(buf_prod, format='png', transparent=True)
    buf_prod.seek(0)
    prod_graph_base64 = base64.b64encode(buf_prod.read()).decode('utf-8')
    plt.close()
    
    # Generate Searches Graph
    search_users = [str(r[0]).split('@')[0] if r[0] else "Unknown" for r in searches_by_user]
    search_counts = [r[1] for r in searches_by_user]

    if not search_users:
        search_users = ['No Data']
        search_counts = [0]

    # INCREASED SIZE HERE
    plt.figure(figsize=(10, 6))
    plt.bar(search_users, search_counts, color='#8b5cf6')
    plt.xlabel('User', fontsize=15)
    plt.ylabel('Searches', fontsize=15)
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.xticks(rotation=45)
    plt.tight_layout()

    buf_search = io.BytesIO()
    plt.savefig(buf_search, format='png', transparent=True)
    buf_search.seek(0)
    search_graph_base64 = base64.b64encode(buf_search.read()).decode('utf-8')
    plt.close()

    return {
        "user_graph": f"data:image/png;base64,{user_graph_base64}",
        "product_graph": f"data:image/png;base64,{prod_graph_base64}",
        "search_graph": f"data:image/png;base64,{search_graph_base64}"
    }
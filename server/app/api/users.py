from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import JWTBearer, get_current_user_id
from app.models import SavedSearch, PriceAlert, User
from app.schemas.saved_search import SavedSearchCreate, SavedSearchResponse
from app.schemas.price_alert import PriceAlertCreate, PriceAlertResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/api/users", tags=["Users"])


# ---- Admin: List All Users ----

@router.get("/list")
def list_all_users(
    db: Session = Depends(get_db),
    token_data: dict = Depends(JWTBearer()),
):
    """Return all non-deleted users with email (admin use)."""
    from app.models.user_auth import UserAuth
    users = db.query(User).filter(User.is_deleted == False).order_by(User.createdAt.desc()).all()
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.auth.email if u.auth else None,
            "is_active": u.is_active,
            "phone": u.phone,
            "created_at": u.createdAt.isoformat() if u.createdAt else None,
        })
    return result


@router.patch("/{user_id}/deactivate")
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(JWTBearer()),
):
    """Toggle a user's active status (admin use)."""
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return {"id": user.id, "is_active": user.is_active}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(JWTBearer()),
):
    """Permanently delete a user and all related records (admin use)."""
    from app.models.auth_activity import AuthActivity
    from app.models.refresh_token import RefreshToken
    from app.models.user_auth import UserAuth
    from app.models.user_role import UserRole
    from app.models.saved_search import SavedSearch
    from app.models.price_alert import PriceAlert

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        # Delete in FK dependency order using bulk queries (synchronize_session=False
        # skips SQLAlchemy's ORM cascade which was causing NotNullViolation)
        # 1. auth_activity depends on user_id AND user_auth_id
        db.query(AuthActivity).filter(AuthActivity.user_id == user_id).delete(synchronize_session=False)
        # 2. refresh_tokens
        db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete(synchronize_session=False)
        # 3. user_auth
        db.query(UserAuth).filter(UserAuth.user_id == user_id).delete(synchronize_session=False)
        # 4. user_role
        db.query(UserRole).filter(UserRole.user_id == user_id).delete(synchronize_session=False)
        # 5. saved_search
        db.query(SavedSearch).filter(SavedSearch.user_id == user_id).delete(synchronize_session=False)
        # 6. price_alert
        db.query(PriceAlert).filter(PriceAlert.user_id == user_id).delete(synchronize_session=False)
        # 7. delete the user itself
        db.query(User).filter(User.id == user_id).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
    return None





@router.get("/saved-searches", response_model=List[SavedSearchResponse])
def list_saved_searches(
    request: Request,
    db: Session = Depends(get_db),
    token_data: dict = Depends(JWTBearer()),
):
    """Return the current user's saved searches."""
    user_id = get_current_user_id(request)
    items = db.query(SavedSearch).filter(
        SavedSearch.user_id == user_id,
        SavedSearch.is_deleted == False,
    ).order_by(SavedSearch.createdAt.desc()).all()
    return items


@router.get("/activity", response_model=List[dict])
def list_recent_activity(
    request: Request,
    db: Session = Depends(get_db),
    token_data: dict = Depends(JWTBearer()),
):
    """Return the current user's recent login activity."""
    from app.models.auth_activity import AuthActivity
    user_id = get_current_user_id(request)
    activities = db.query(AuthActivity).filter(
        AuthActivity.user_id == user_id,
        AuthActivity.is_deleted == False,
    ).order_by(AuthActivity.login_time.desc()).limit(10).all()
    
    result = []
    for a in activities:
        result.append({
            "id": a.id,
            "ip_address": a.ip_address,
            "user_agent": a.user_agent,
            "is_successful": a.is_successful,
            "login_time": a.login_time.isoformat() if a.login_time else None,
            "logout_time": a.logout_time.isoformat() if a.logout_time else None
        })
    return result


@router.post("/saved-searches", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
def create_saved_search(
    request: Request,
    body: SavedSearchCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(JWTBearer()),
):
    """Save a new search for the current user."""
    user_id = get_current_user_id(request)
    item = SavedSearch(
        user_id=user_id,
        search_query=body.search_query,
        filters_json=body.filters_json,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/saved-searches/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_search(
    request: Request,
    search_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(JWTBearer()),
):
    """Delete a saved search (only if it belongs to the current user)."""
    user_id = get_current_user_id(request)
    item = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == user_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Saved search not found")
    db.delete(item)
    db.commit()
    return None


# ---- Price Alerts ----

@router.get("/alerts", response_model=List[PriceAlertResponse])
def list_alerts(
    request: Request,
    db: Session = Depends(get_db),
    token_data: dict = Depends(JWTBearer()),
):
    """Return the current user's price alerts."""
    user_id = get_current_user_id(request)
    items = db.query(PriceAlert).filter(
        PriceAlert.user_id == user_id,
        PriceAlert.is_deleted == False,
    ).order_by(PriceAlert.createdAt.desc()).all()
    return items


@router.post("/alerts", response_model=PriceAlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    request: Request,
    body: PriceAlertCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(JWTBearer()),
):
    """Create a new price alert for the current user."""
    user_id = get_current_user_id(request)
    item = PriceAlert(
        user_id=user_id,
        product_id=body.product_id,
        target_price=body.target_price,
        is_active=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    request: Request,
    alert_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(JWTBearer()),
):
    """Delete a price alert (only if it belongs to the current user)."""
    user_id = get_current_user_id(request)
    item = db.query(PriceAlert).filter(
        PriceAlert.id == alert_id,
        PriceAlert.user_id == user_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Price alert not found")
    db.delete(item)
    db.commit()
    return None


# ---- Dashboard ----

@router.get("/dashboard")
def get_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    token_data: dict = Depends(JWTBearer()),
):
    """Summary for the user dashboard: counts and recent items."""
    user_id = get_current_user_id(request)
    saved_count = db.query(SavedSearch).filter(
        SavedSearch.user_id == user_id,
        SavedSearch.is_deleted == False,
    ).count()
    alerts_count = db.query(PriceAlert).filter(
        PriceAlert.user_id == user_id,
        PriceAlert.is_deleted == False,
        PriceAlert.is_active == True,
    ).count()
    recent_searches = (
        db.query(SavedSearch)
        .filter(SavedSearch.user_id == user_id, SavedSearch.is_deleted == False)
        .order_by(SavedSearch.createdAt.desc())
        .limit(5)
        .all()
    )
    recent_alerts = (
        db.query(PriceAlert)
        .filter(PriceAlert.user_id == user_id, PriceAlert.is_deleted == False)
        .order_by(PriceAlert.createdAt.desc())
        .limit(5)
        .all()
    )
    return {
        "saved_searches_count": saved_count,
        "active_alerts_count": alerts_count,
        "recent_saved_searches": [SavedSearchResponse.model_validate(s) for s in recent_searches],
        "recent_alerts": [PriceAlertResponse.model_validate(a) for a in recent_alerts],
    }

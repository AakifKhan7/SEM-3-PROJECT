from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import JWTBearer, get_current_user_id
from app.models import SavedSearch, PriceAlert
from app.schemas.saved_search import SavedSearchCreate, SavedSearchResponse
from app.schemas.price_alert import PriceAlertCreate, PriceAlertResponse

router = APIRouter(prefix="/api/users", tags=["Users"])


# ---- Saved Searches ----

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

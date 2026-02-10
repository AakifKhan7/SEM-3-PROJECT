from app.database import get_db
from app.models import Product, ProductListing
from sqlalchemy.orm import Session
import datetime

def check_data():
    db = next(get_db())
    try:
        products = db.query(Product).all()
        print(f"Total Products: {len(products)}")
        for p in products:
            print(f"Product: {p.name}")
            listings = db.query(ProductListing).filter(ProductListing.product_id == p.id).all()
            print(f"  Listings: {len(listings)}")
            for l in listings:
                print(f"    - Platform: {l.platform.name if l.platform else 'None'}")
                print(f"      Price: {l.price}")
                print(f"      Last Scraped: {l.last_scraped_at}")
                age = datetime.datetime.utcnow() - l.last_scraped_at
                print(f"      Age: {age} (Total Seconds: {age.total_seconds()})")
                is_fresh = age.total_seconds() < 24 * 3600
                print(f"      Is Fresh (<24h): {is_fresh}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_data()

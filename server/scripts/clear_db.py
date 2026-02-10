from app.database import engine
from sqlalchemy import text

def clear_products():
    with engine.connect() as connection:
        print("Clearing products table...")
        # Cascade will handle listings and price_history if FKs are set up correctly, 
        # but let's be safe and truncate pertinent tables or just products if cascade works.
        # SQLAlchemy usually handles cascade on ORM level, raw SQL needs CASCADE.
        try:
            connection.execute(text("TRUNCATE TABLE products CASCADE;"))
            connection.commit()
            print("Products cleared.")
        except Exception as e:
            print(f"Error clearing products: {e}")
            # Fallback if CASCADE is not supported or permission issues (unlikely in dev)
            try:
                connection.execute(text("DELETE FROM price_history;"))
                connection.execute(text("DELETE FROM product_listings;"))
                connection.execute(text("DELETE FROM products;"))
                connection.commit()
                print("Tables cleared manually.")
            except Exception as e2:
                 print(f"Error clearing manual: {e2}")

if __name__ == "__main__":
    clear_products()

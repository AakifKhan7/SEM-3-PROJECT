import sys
import os
from sqlalchemy import text

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine

def add_image_column():
    print("Attempting to add image_url column to products table...")
    with engine.connect() as connection:
        try:
            connection.execute(text("ALTER TABLE products ADD COLUMN image_url VARCHAR(500);"))
            connection.commit()
            print("Successfully added image_url column.")
        except Exception as e:
            if "duplicate column" in str(e):
                 print("Column image_url already exists.")
            else:
                print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_image_column()

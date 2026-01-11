import sys
import os

# Add parent dir to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

def migrate():
    print("Migrating database...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN last_seen TIMESTAMP WITH TIME ZONE;"))
            conn.commit()
            print("Successfully added 'last_seen' column to users table.")
        except Exception as e:
            print(f"Migration failed (column might already exist): {e}")

if __name__ == "__main__":
    migrate()

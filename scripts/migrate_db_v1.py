import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    print("Migrating database...")
    # Create engine efficiently
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        try:
            # Check if column exists
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='users' AND column_name='pending_reminder_message';"
            ))
            if result.fetchone():
                print("Column 'pending_reminder_message' already exists.")
                return

            print("Adding 'pending_reminder_message' column to 'users' table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN pending_reminder_message VARCHAR;"))
            print("Migration successful!")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()

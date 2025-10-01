"""Database verification script."""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from app.models.base import Base

# Load environment variables
load_dotenv()


def verify_database():
    """Verify database connection and tables."""
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost:5432/qeem")

    try:
        # Create engine
        engine = create_engine(DATABASE_URL)

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")

        # Check if tables exist
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]

            if tables:
                print(f"✅ Found {len(tables)} tables:")
                for table in tables:
                    print(f"   - {table}")
            else:
                print(
                    "⚠️  No tables found. Run 'alembic upgrade head' to create tables.")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

    return True


if __name__ == "__main__":
    verify_database()

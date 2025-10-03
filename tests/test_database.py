"""Database verification tests."""

import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TestDatabaseConnection:
    """Test database connectivity and basic operations."""

    @pytest.fixture(scope="class")
    def engine(self):
        """Create database engine for testing."""
        DATABASE_URL = os.getenv(
            "DATABASE_URL", "postgresql://user:password@localhost:5432/qeem")
        return create_engine(DATABASE_URL)

    def test_database_connection(self, engine):
        """Test basic database connection."""
        if not os.getenv("DATABASE_URL", "").startswith("postgresql"):
            pytest.skip("PostgreSQL not configured; skipping PG-specific test")
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.fetchone()[0] == 1
        except OperationalError as e:
            pytest.fail(f"Database connection failed: {e}")

    def test_postgresql_version(self, engine):
        """Test PostgreSQL version retrieval."""
        if not os.getenv("DATABASE_URL", "").startswith("postgresql"):
            pytest.skip("PostgreSQL not configured; skipping PG-specific test")
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                assert "PostgreSQL" in version
                print(f"✅ PostgreSQL version: {version}")
        except OperationalError as e:
            pytest.fail(f"Failed to get PostgreSQL version: {e}")

    def test_database_exists(self, engine):
        """Test that the qeem database exists."""
        if not os.getenv("DATABASE_URL", "").startswith("postgresql"):
            pytest.skip("PostgreSQL not configured; skipping PG-specific test")
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT current_database()"))
                db_name = result.fetchone()[0]
                assert db_name == "qeem"
                print(f"✅ Connected to database: {db_name}")
        except OperationalError as e:
            pytest.fail(f"Database 'qeem' does not exist: {e}")


class TestDatabaseSchema:
    """Test database schema and table structure."""

    @pytest.fixture(scope="class")
    def engine(self):
        """Create database engine for testing."""
        DATABASE_URL = os.getenv(
            "DATABASE_URL", "postgresql://user:password@localhost:5432/qeem")
        return create_engine(DATABASE_URL)

    def test_tables_exist(self, engine):
        """Test that all required tables exist."""
        expected_tables = {
            "users",
            "user_profiles",
            "rate_calculations",
            "market_statistics",
            "invoices",
            "contracts",
            "alembic_version"
        }

        try:
            with engine.connect() as conn:
                # Use SQLite-compatible query
                if "sqlite" in str(engine.url):
                    result = conn.execute(text("""
                        SELECT name 
                        FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                        ORDER BY name
                    """))
                else:
                    # PostgreSQL query
                    result = conn.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name
                    """))

                existing_tables = {row[0] for row in result.fetchall()}

                # In CI environment, tables might not exist yet
                if not existing_tables and "test_ci.db" in str(engine.url):
                    pytest.skip(
                        "No tables found in CI environment - migrations not run")

                missing_tables = expected_tables - existing_tables
                if missing_tables:
                    pytest.fail(f"Missing tables: {missing_tables}")

                print(f"✅ Found {len(existing_tables)} tables:")
                for table in sorted(existing_tables):
                    print(f"   - {table}")

        except OperationalError as e:
            pytest.fail(f"Failed to check tables: {e}")

    def test_users_table_structure(self, engine):
        """Test users table has required columns."""
        required_columns = {
            "id", "email", "password_hash", "is_active",
            "is_verified", "role", "created_at", "updated_at"
        }

        try:
            with engine.connect() as conn:
                # Check if users table exists first
                if "sqlite" in str(engine.url):
                    # Check if table exists
                    result = conn.execute(text("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='users'
                    """))
                    if not result.fetchone():
                        pytest.skip(
                            "Users table not found - migrations not applied")

                    result = conn.execute(text("PRAGMA table_info(users)"))
                    # row[1] is column name
                    existing_columns = {row[1] for row in result.fetchall()}
                else:
                    # PostgreSQL query
                    result = conn.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'users' AND table_schema = 'public'
                    """))
                    existing_columns = {row[0] for row in result.fetchall()}

                missing_columns = required_columns - existing_columns
                if missing_columns:
                    pytest.fail(
                        f"Missing columns in users table: {missing_columns}")

                print(f"✅ Users table has {len(existing_columns)} columns")

        except OperationalError as e:
            pytest.fail(f"Failed to check users table structure: {e}")

    def test_alembic_version_table(self, engine):
        """Test that alembic version tracking is working."""
        try:
            with engine.connect() as conn:
                # Check if alembic_version table exists first
                if "sqlite" in str(engine.url):
                    # For SQLite, check if table exists
                    result = conn.execute(text("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='alembic_version'
                    """))
                    if not result.fetchone():
                        pytest.skip(
                            "Alembic version table not found - migrations not applied")

                result = conn.execute(
                    text("SELECT version_num FROM alembic_version"))
                version = result.fetchone()

                if version:
                    print(f"✅ Current Alembic version: {version[0]}")
                else:
                    pytest.fail(
                        "No Alembic version found - migrations may not have been applied")

        except OperationalError as e:
            pytest.fail(f"Failed to check Alembic version: {e}")


class TestDatabasePermissions:
    """Test database user permissions."""

    @pytest.fixture(scope="class")
    def engine(self):
        """Create database engine for testing."""
        DATABASE_URL = os.getenv(
            "DATABASE_URL", "postgresql://user:password@localhost:5432/qeem")
        return create_engine(DATABASE_URL)

    def test_user_permissions(self, engine):
        """Test that the database user has required permissions."""
        try:
            with engine.connect() as conn:
                # Test SELECT permission
                if "sqlite" in str(engine.url):
                    # SQLite doesn't have current_user, just test basic connection
                    result = conn.execute(text("SELECT 1"))
                    assert result.fetchone()[0] == 1
                    print("✅ SQLite connection successful")
                else:
                    # PostgreSQL query
                    result = conn.execute(text("SELECT current_user"))
                    current_user = result.fetchone()[0]
                    print(f"✅ Connected as user: {current_user}")

                # Test CREATE permission (for future migrations)
                conn.execute(
                    text("CREATE TEMP TABLE test_permissions (id int)"))
                conn.execute(text("DROP TABLE test_permissions"))
                print("✅ User has CREATE/DROP permissions")

        except OperationalError as e:
            pytest.fail(f"Permission test failed: {e}")


if __name__ == "__main__":
    """Run tests directly for quick verification."""
    import sys

    # Simple verification without pytest
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost:5432/qeem")

    try:
        engine = create_engine(DATABASE_URL)

        print("🔍 Database Verification")
        print("=" * 50)

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL: {version}")

            result = conn.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"✅ Database: {db_name}")

            result = conn.execute(text("SELECT current_user"))
            user = result.fetchone()[0]
            print(f"✅ User: {user}")

        # Test tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]

            if tables:
                print(f"✅ Tables ({len(tables)}):")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("⚠️  No tables found. Run 'alembic upgrade head'")

        print("\n🎉 Database verification completed successfully!")

    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        sys.exit(1)

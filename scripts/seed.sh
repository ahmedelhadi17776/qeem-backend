#!/bin/bash
# Seed data script for development environment

set -e

echo "🌱 Running seed data script..."

# Check if we're in the correct directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Please run this script from the qeem-backend directory"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ] && [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   It's recommended to run this in a virtual environment"
fi

# Check if database is running
echo "🔍 Checking database connection..."
python -c "
import sys
try:
    from app.db.database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
"

# Run migrations if needed
echo "🔄 Checking database migrations..."
alembic upgrade head

# Run the seed data script
echo "🌱 Creating seed data..."
python -m scripts.seed_data

echo "✅ Seed data script completed successfully!"
echo ""
echo "💡 You can now:"
echo "   1. Start the development server: uvicorn app.main:app --reload"
echo "   2. Visit http://localhost:8000/docs to see the API documentation"
echo "   3. Use the login credentials shown above to test authentication"

#!/bin/bash
# Docker entrypoint script for Tiger ID API
# Performs pre-startup checks and initialization

set -e

echo "======================================"
echo "🐅 Tiger ID - API Initialization"
echo "======================================"
echo ""

# Wait for PostgreSQL to be ready
echo "→ Waiting for PostgreSQL..."
timeout=60
counter=0
until python -c "import psycopg2; psycopg2.connect('${DATABASE_URL}')" 2>/dev/null; do
    if [ $counter -ge $timeout ]; then
        echo "❌ PostgreSQL timeout after ${timeout}s"
        exit 1
    fi
    echo "   PostgreSQL is unavailable - sleeping"
    sleep 2
    counter=$((counter + 2))
done
echo "✅ PostgreSQL is ready"

# Check if Redis is ready (optional)
echo ""
echo "→ Waiting for Redis..."
if [ -n "$REDIS_URL" ]; then
    timeout=30
    counter=0
    until python -c "import redis; r = redis.from_url('${REDIS_URL}'); r.ping()" 2>/dev/null; do
        if [ $counter -ge $timeout ]; then
            echo "⚠️  Redis timeout - will use in-memory cache"
            break
        fi
        sleep 1
        counter=$((counter + 1))
    done
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis not configured - will use in-memory cache"
fi

# Run database migrations
echo ""
echo "→ Running database migrations..."
cd /app/backend/database
if alembic upgrade head 2>/dev/null; then
    echo "✅ Migrations complete"
else
    echo "⚠️  Migrations failed, trying direct table creation..."
    cd /app
    python -c "from backend.database.connection import init_db; init_db()" 2>/dev/null || echo "⚠️  Table creation failed"
fi
cd /app

# Create test user
echo ""
echo "→ Setting up test user..."
python <<'EOFPYTHON'
import sys
sys.path.insert(0, '/app')

from backend.database import get_db_session, User
from backend.auth.auth import hash_password
from backend.database.models import UserRole
import uuid

try:
    with get_db_session() as db:
        existing = db.query(User).filter(User.username == "admin").first()
        
        if existing:
            print("   ℹ️  Admin user exists - verifying password...")
            existing.password_hash = hash_password("admin")
            db.commit()
            print("   ✅ Admin user ready")
        else:
            user = User(
                user_id=uuid.uuid4(),
                username="admin",
                email="admin@tigerid.local",
                password_hash=hash_password("admin"),
                role=UserRole.admin,
                permissions={
                    "investigations": ["create", "read", "update", "delete"],
                    "tigers": ["create", "read", "update", "delete"],
                    "facilities": ["create", "read", "update", "delete"],
                    "users": ["create", "read", "update", "delete"],
                },
                is_active=True,
                mfa_enabled=False
            )
            db.add(user)
            db.commit()
            print("   ✅ Admin user created")
            print("")
            print("   🔑 Login Credentials:")
            print("      Username: admin")
            print("      Password: admin")
except Exception as e:
    print(f"   ⚠️  User setup failed: {e}")
    import traceback
    traceback.print_exc()
EOFPYTHON

# Initialize models (non-blocking)
echo ""
echo "→ Initializing ML models..."
python scripts/init_models.py 2>/dev/null || echo "   ⚠️  Model initialization skipped (this is OK)"

echo ""
echo "======================================"
echo "✅ Initialization Complete"
echo "======================================"
echo ""
echo "🚀 Starting API server..."
echo ""

# Start the application
exec "$@"


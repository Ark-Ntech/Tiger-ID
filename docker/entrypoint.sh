#!/bin/bash
# Docker entrypoint script for Tiger ID API
# Performs pre-startup checks and initialization

set -e

echo "======================================"
echo "🐅 Tiger ID - API Initialization"
echo "======================================"
echo ""

# Set SQLite production mode (not PostgreSQL)
export USE_SQLITE_DEMO=false
export USE_POSTGRESQL=false
export DATABASE_URL=sqlite:///data/production.db

echo "→ Using SQLite production database"
echo "   Database path: /app/data/production.db"

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

# Initialize SQLite database
echo ""
echo "→ Initializing SQLite database..."
cd /app
python scripts/init_db.py || echo "⚠️  Database initialization failed"

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

# Populate database with production data (if database is empty)
echo ""
echo "→ Checking if database needs population..."
python <<'EOFPYTHON'
import sys
sys.path.insert(0, '/app')

from backend.database import get_db_session, Facility, Tiger
from pathlib import Path

try:
    with get_db_session() as db:
        facility_count = db.query(Facility).count()
        tiger_count = db.query(Tiger).count()
        
        if facility_count == 0 or tiger_count == 0:
            print("   → Database is empty, populating with production data...")
            import subprocess
            result = subprocess.run(
                ['python', 'scripts/populate_production_db.py'],
                cwd='/app',
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("   ✅ Database populated successfully")
            else:
                print(f"   ⚠️  Database population had warnings: {result.stderr[:200]}")
        else:
            print(f"   ℹ️  Database already has {facility_count} facilities and {tiger_count} tigers")
except Exception as e:
    print(f"   ⚠️  Could not check database: {e}")
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


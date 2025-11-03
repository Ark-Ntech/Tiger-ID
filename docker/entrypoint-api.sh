#!/bin/bash
set -e

echo "======================================"
echo "🐅 Tiger ID - API Container Starting"
echo "======================================"
echo ""

# Wait for PostgreSQL to be ready
echo "→ Waiting for PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "postgres" -U "tiger_user" -d "tiger_investigation" -c '\q' 2>/dev/null; do
  echo "   PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "✅ PostgreSQL is ready"

# Wait for Redis to be ready
echo ""
echo "→ Waiting for Redis..."
until redis-cli -h redis ping 2>/dev/null; do
  echo "   Redis is unavailable - sleeping"
  sleep 1
done
echo "✅ Redis is ready"

# Run database migrations
echo ""
echo "→ Running database migrations..."
cd /app/backend/database
alembic upgrade head
cd /app
echo "✅ Migrations complete"

# Create test user if it doesn't exist
echo ""
echo "→ Creating test user..."
python <<EOF
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
            print("   ℹ️  Admin user already exists")
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
            print("   📝 Login: admin / admin")
except Exception as e:
    print(f"   ⚠️  Could not create user: {e}")
EOF

echo ""
echo "======================================"
echo "✅ API Container Ready"
echo "======================================"
echo ""
echo "🚀 Starting API server..."
echo ""

# Start the application
exec "$@"


#!/bin/bash
set -e

echo "=========================================="
echo "Tiger ID - SQLite Database Initialization"
echo "=========================================="

# Initialize SQLite database
echo "Initializing SQLite database..."
python -c "
from backend.database import init_db, engine
from sqlalchemy import text

# Initialize database schema
init_db()

# Create test user if not exists
try:
    from backend.database import SessionLocal
    from backend.database.models import User
    from passlib.hash import bcrypt

    db = SessionLocal()

    # Check if admin user exists
    admin = db.query(User).filter(User.username == 'admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@tigerid.local',
            password_hash=bcrypt.hash('admin'),
            role='admin'
        )
        db.add(admin)
        db.commit()
        print('Created admin user (username: admin, password: admin)')
    else:
        print('Admin user already exists')

    db.close()
except Exception as e:
    print(f'User creation skipped: {e}')

print('Database initialized successfully')
"

echo "=========================================="
echo "Starting Tiger ID API..."
echo "=========================================="

# Execute the main command
exec "$@"

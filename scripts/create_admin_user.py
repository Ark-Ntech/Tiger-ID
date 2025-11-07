#!/usr/bin/env python3
"""Create admin user if it doesn't exist"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Use SQLite for production (not PostgreSQL)
os.environ['USE_POSTGRESQL'] = 'false'
os.environ['USE_SQLITE_DEMO'] = 'false'

from backend.database.sqlite_connection import get_sqlite_session
from backend.database.models import User, UserRole
from backend.auth.auth import hash_password, verify_password
import uuid

def main():
    """Create admin user if it doesn't exist"""
    with get_sqlite_session() as db:
        existing = db.query(User).filter(User.username == "admin").first()
        
        if existing:
            print("[OK] Admin user already exists")
            print(f"   Username: {existing.username}")
            print(f"   Email: {existing.email}")
            print(f"   Is active: {existing.is_active}")
            # Verify password works
            if verify_password("admin", existing.password_hash):
                print("[OK] Password verification: PASSED")
            else:
                print("[WARNING] Password verification: FAILED - updating password")
                existing.password_hash = hash_password("admin")
                db.commit()
                print("[OK] Password updated")
        else:
            admin = User(
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
            db.add(admin)
            db.commit()
            print("[OK] Admin user created successfully")
            print("   Username: admin")
            print("   Password: admin")
            print("   Email: admin@tigerid.local")

if __name__ == "__main__":
    main()


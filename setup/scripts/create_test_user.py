#!/usr/bin/env python3
"""Create or update test user"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import get_db_session, User
from backend.auth.auth import hash_password
from backend.database.models import UserRole
import uuid


def create_test_user(username="admin", password="admin", email="admin@tigerid.local", role="admin"):
    """Create or update test user"""
    with get_db_session() as db:
        existing = db.query(User).filter(User.username == username).first()
        
        if existing:
            print(f"⚠️  User '{username}' exists - updating password...")
            existing.password_hash = hash_password(password)
            db.commit()
            print(f"✅ Password updated")
        else:
            user = User(
                user_id=uuid.uuid4(),
                username=username,
                email=email,
                password_hash=hash_password(password),
                role=UserRole[role],
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
            print(f"✅ User created")
        
        print(f"\n🔑 Credentials:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin")
    parser.add_argument("--email", default="admin@tigerid.local")
    parser.add_argument("--role", default="admin", choices=["admin", "investigator", "analyst", "supervisor"])
    args = parser.parse_args()
    
    try:
        create_test_user(args.username, args.password, args.email, args.role)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


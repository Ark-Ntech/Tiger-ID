#!/usr/bin/env python3
"""
Database setup script - Runs migrations and creates test user
"""

import sys
import os
from pathlib import Path
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description, cwd=None):
    """Run a command and handle errors"""
    print(f"\n→ {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        print(f"✅ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        if e.stderr:
            print(f"   {e.stderr.strip()}")
        return False


def check_database_connection():
    """Check if database is accessible"""
    print("\n→ Checking database connection...")
    try:
        from backend.database.connection import engine
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n   💡 Start database with: docker compose up -d postgres redis")
        return False


def run_migrations():
    """Run Alembic migrations"""
    migrations_dir = project_root / "backend" / "database"
    return run_command(
        "alembic upgrade head",
        "Running database migrations",
        cwd=str(migrations_dir)
    )


def create_test_user():
    """Create test user"""
    print("\n→ Creating test user...")
    try:
        from backend.database import get_db_session, User
        from backend.auth.auth import hash_password
        from backend.database.models import UserRole
        import uuid
        
        with get_db_session() as db:
            existing = db.query(User).filter(User.username == "admin").first()
            
            if existing:
                print("   ℹ️  Admin user exists - updating password...")
                existing.password_hash = hash_password("admin")
                db.commit()
                print("✅ Admin password updated")
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
                print("✅ Admin user created")
        
        print("\n   🔑 Login Credentials:")
        print("      Username: admin")
        print("      Password: admin")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def main():
    """Main setup function"""
    print("="*60)
    print("🐅 Tiger ID - Database Setup")
    print("="*60)
    
    if not check_database_connection():
        sys.exit(1)
    
    run_migrations()
    create_test_user()
    
    print("\n" + "="*60)
    print("✅ Database setup complete!")
    print("="*60)
    print("\n🚀 Start servers: setup\\windows\\START_SERVERS.bat")
    print()


if __name__ == "__main__":
    main()


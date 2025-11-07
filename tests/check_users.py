"""Check users in database"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path.parent))

from backend.database.sqlite_connection import get_sqlite_session
from backend.database.models import User

def check_users():
    """Check what users exist in the database"""
    with get_sqlite_session() as db:
        users = db.query(User).all()
        
        print(f"Total users: {len(users)}")
        for user in users:
            print(f"  - {user.username} (ID: {user.user_id}, Role: {user.role})")
        
        return users

if __name__ == "__main__":
    users = check_users()
    
    if users:
        print("\nYou can use one of these usernames for testing")
    else:
        print("\nNo users found. You need to create a user first.")
        print("Run: python scripts/create_admin_user.py")


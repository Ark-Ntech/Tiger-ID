#!/usr/bin/env python3
"""Seed or reset the admin user with a secure password.

This script ensures a consistent admin user exists in the database
with proper credentials that meet password strength requirements.

Usage:
    python scripts/seed_admin.py                    # Create/update admin user
    python scripts/seed_admin.py --reset            # Reset admin password
    python scripts/seed_admin.py --password "..."   # Set custom password

Default admin credentials:
    Username: admin
    Password: Admin123!
    Email: admin@tigerid.local
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import uuid
from typing import Optional


# Default secure admin password that meets requirements:
# - At least 8 characters
# - At least one uppercase letter
# - At least one lowercase letter
# - At least one digit
# - At least one special character
DEFAULT_ADMIN_PASSWORD = "Admin123!"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_EMAIL = "admin@tigerid.local"


def validate_password_strength(password: str) -> list[str]:
    """Validate password meets security requirements."""
    import re
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password):
        errors.append("Password must contain at least one special character")

    return errors


def seed_admin_user(
    password: Optional[str] = None,
    reset: bool = False,
    verbose: bool = True
) -> bool:
    """
    Create or update the admin user in the database.

    Args:
        password: Custom password (uses DEFAULT_ADMIN_PASSWORD if None)
        reset: If True, update existing admin password
        verbose: Print status messages

    Returns:
        True if successful, False otherwise
    """
    from backend.database import get_db_session
    from backend.database.models import User, UserRole
    from backend.auth.auth import hash_password

    # Use default password if not specified
    password = password or DEFAULT_ADMIN_PASSWORD

    # Validate password strength
    errors = validate_password_strength(password)
    if errors:
        if verbose:
            print("Password validation failed:")
            for error in errors:
                print(f"  - {error}")
        return False

    try:
        with get_db_session() as db:
            existing = db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()

            if existing:
                if reset:
                    # Update existing admin password
                    existing.password_hash = hash_password(password)
                    db.commit()
                    if verbose:
                        print(f"[OK] Admin password reset successfully")
                        print(f"     Username: {DEFAULT_ADMIN_USERNAME}")
                        print(f"     Password: {password}")
                else:
                    if verbose:
                        print(f"[INFO] Admin user already exists (use --reset to change password)")
                    return True
            else:
                # Create new admin user
                admin = User(
                    user_id=uuid.uuid4(),
                    username=DEFAULT_ADMIN_USERNAME,
                    email=DEFAULT_ADMIN_EMAIL,
                    password_hash=hash_password(password),
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

                if verbose:
                    print(f"[OK] Admin user created")
                    print(f"     Username: {DEFAULT_ADMIN_USERNAME}")
                    print(f"     Password: {password}")
                    print(f"     Email: {DEFAULT_ADMIN_EMAIL}")

            return True

    except Exception as e:
        if verbose:
            print(f"[ERROR] Failed to seed admin user: {e}")
        return False


def verify_admin_login(password: Optional[str] = None, verbose: bool = True) -> bool:
    """
    Verify that admin login works with the given password.

    Args:
        password: Password to test (uses DEFAULT_ADMIN_PASSWORD if None)
        verbose: Print status messages

    Returns:
        True if login successful, False otherwise
    """
    from backend.database import get_db_session
    from backend.auth.auth import authenticate_user

    password = password or DEFAULT_ADMIN_PASSWORD

    try:
        with get_db_session() as db:
            user = authenticate_user(db, DEFAULT_ADMIN_USERNAME, password)

            if user:
                if verbose:
                    print(f"[OK] Admin login verified successfully")
                return True
            else:
                if verbose:
                    print(f"[FAIL] Admin login failed - incorrect password")
                return False

    except Exception as e:
        if verbose:
            print(f"[ERROR] Failed to verify admin login: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Seed or reset admin user credentials",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Default credentials:
    Username: {DEFAULT_ADMIN_USERNAME}
    Password: {DEFAULT_ADMIN_PASSWORD}
    Email: {DEFAULT_ADMIN_EMAIL}

Examples:
    python scripts/seed_admin.py                    # Create admin if missing
    python scripts/seed_admin.py --reset            # Reset to default password
    python scripts/seed_admin.py --password "NewPass1!"  # Set custom password
    python scripts/seed_admin.py --verify           # Test admin login
"""
    )

    parser.add_argument(
        "--password", "-p",
        help="Custom admin password (must meet strength requirements)"
    )
    parser.add_argument(
        "--reset", "-r",
        action="store_true",
        help="Reset existing admin password"
    )
    parser.add_argument(
        "--verify", "-v",
        action="store_true",
        help="Verify admin login works"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress output messages"
    )

    args = parser.parse_args()
    verbose = not args.quiet

    if args.verify:
        success = verify_admin_login(args.password, verbose=verbose)
        sys.exit(0 if success else 1)

    success = seed_admin_user(
        password=args.password,
        reset=args.reset,
        verbose=verbose
    )

    if success and verbose:
        # Verify the login works
        print("\nVerifying admin login...")
        verify_admin_login(args.password, verbose=verbose)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

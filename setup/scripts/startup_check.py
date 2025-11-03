#!/usr/bin/env python3
"""Validate system requirements and configuration"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def check_database():
    try:
        from backend.database.connection import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✅ Database connection")
        return True
    except Exception as e:
        print(f"❌ Database connection: {e}")
        return False


def check_redis():
    try:
        from backend.services.cache_service import get_cache_service
        cache = get_cache_service()
        if cache.is_available():
            print("✅ Redis connection")
        else:
            print("⚠️  Redis not available (OK - using memory cache)")
        return True
    except:
        print("⚠️  Redis check failed (OK)")
        return True


def check_directories():
    for directory in ["data/storage", "data/models", "logs"]:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
    print("✅ Required directories")
    return True


def main():
    print("\n" + "="*60)
    print("🐅 Tiger ID - Startup Check")
    print("="*60 + "\n")
    
    results = [
        check_directories(),
        check_database(),
        check_redis(),
    ]
    
    print("\n" + "="*60)
    if all(results):
        print("✅ All checks passed!")
    else:
        print("⚠️  Some checks failed (see above)")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()


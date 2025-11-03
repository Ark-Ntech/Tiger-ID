#!/usr/bin/env python3
"""Verify project organization is correct"""

from pathlib import Path

project_root = Path(__file__).parent.parent.parent

checks = {
    "Setup Structure": [
        "setup/windows/START_DOCKER.bat",
        "setup/windows/STOP_DOCKER.bat",
        "setup/windows/START_SERVERS.bat",
        "setup/windows/SETUP_ALL.bat",
        "setup/windows/SETUP_DATABASE.bat",
        "setup/scripts/setup_all.py",
        "setup/scripts/setup_database.py",
        "setup/scripts/create_test_user.py",
        "setup/scripts/test_integration.py",
        "setup/scripts/startup_check.py",
        "setup/docs/SETUP_GUIDE.md",
        "setup/docs/REACT_MIGRATION.md",
        "setup/docs/DOCKER_GUIDE.md",
        "setup/docs/TROUBLESHOOTING.md",
    ],
    "Root Documentation": [
        "START.md",
        "README.md",
        "DOCUMENTATION_INDEX.md",
        "PROJECT_STRUCTURE.md",
    ],
    "Frontend": [
        "frontend/src/App.tsx",
        "frontend/src/main.tsx",
        "frontend/package.json",
        "frontend/Dockerfile",
    ],
    "Backend": [
        "backend/api/app.py",
        "backend/api/websocket_routes.py",
        "backend/services/websocket_service.py",
    ],
    "Docker": [
        "docker-compose.yml",
        "docker-compose.dev.yml",
        "docker-compose.quickstart.yml",
        "docker/entrypoint.sh",
    ],
}

def main():
    print("\n" + "="*60)
    print("🔍 Tiger ID - Organization Verification")
    print("="*60 + "\n")
    
    all_good = True
    
    for category, files in checks.items():
        print(f"\n{category}:")
        for file_path in files:
            full_path = project_root / file_path
            if full_path.exists():
                print(f"  ✅ {file_path}")
            else:
                print(f"  ❌ {file_path} - MISSING!")
                all_good = False
    
    print("\n" + "="*60)
    if all_good:
        print("✅ All files properly organized!")
    else:
        print("❌ Some files are missing!")
    print("="*60 + "\n")
    
    return all_good

if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)


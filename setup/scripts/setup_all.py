#!/usr/bin/env python3
"""Complete system setup - installs dependencies and configures database"""

import sys
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description, cwd=None):
    """Run a command"""
    print(f"\n→ {description}...")
    try:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd)
        print(f"✅ {description}")
        return True
    except:
        print(f"❌ {description} - Failed")
        return False


def main():
    """Main setup"""
    print("="*60)
    print("🐅 Tiger ID - Complete Setup")
    print("="*60)
    
    # Backend deps
    run_command(
        "pip install -r requirements.txt",
        "Installing backend dependencies",
        cwd=str(project_root)
    )
    
    # Frontend deps
    run_command(
        "npm install --legacy-peer-deps",
        "Installing frontend dependencies",
        cwd=str(project_root / "frontend")
    )
    
    # Database setup
    print("\n→ Setting up database...")
    print("   (Requires PostgreSQL to be running)")
    
    setup_db = project_root / "setup" / "scripts" / "setup_database.py"
    if run_command(f"python {setup_db}", "Database setup"):
        print("\n✅ Complete setup finished!")
        print("\n🚀 Start servers: setup\\windows\\START_SERVERS.bat")
    else:
        print("\n⚠️  Database setup failed")
        print("   Start database: docker compose up -d postgres redis")
        print("   Then run: setup\\windows\\SETUP_DATABASE.bat")


if __name__ == "__main__":
    main()


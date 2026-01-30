"""Test Modal connection and list deployed apps"""

import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import modal
    print(f"✅ Modal SDK version: {modal.__version__}")
    print()

    # Try to get app
    print("Attempting to connect to Modal app 'tiger-id-models'...")
    try:
        # Try using App.lookup()
        app = modal.App.lookup("tiger-id-models", create_if_missing=False)
        print(f"✅ Found app: tiger-id-models")
        print()

        # Try to list classes
        print("Attempting to connect to TigerReIDModel class...")
        try:
            tiger_reid_cls = modal.Cls.from_name("tiger-id-models", "TigerReIDModel")
            print(f"✅ Found TigerReIDModel class")
            print()

            # Try to create instance
            print("Creating instance...")
            instance = tiger_reid_cls()
            print(f"✅ Created instance successfully")
            print()

            print("="*70)
            print("SUCCESS: Modal connection working!")
            print("="*70)

        except modal.exception.NotFoundError as e:
            print(f"❌ TigerReIDModel class not found: {e}")
            print()
            print("This means the app exists but the class isn't deployed.")
            print("Run: modal deploy backend/modal_app.py")

    except modal.exception.NotFoundError as e:
        print(f"❌ App 'tiger-id-models' not found: {e}")
        print()
        print("This means the Modal app hasn't been deployed yet.")
        print("Run: modal deploy backend/modal_app.py")

except ImportError:
    print("❌ Modal SDK not installed")
    print("Run: pip install modal")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

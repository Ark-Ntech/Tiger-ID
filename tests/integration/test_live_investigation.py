"""Simple live test of Investigation 2.0 workflow with auto-discovery"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Force SQLite database
os.environ['DATABASE_URL'] = 'sqlite:///data/production.db'

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

# Disable mock mode
os.environ["MODAL_USE_MOCK"] = "false"

print("="*70)
print("LIVE INVESTIGATION 2.0 TEST WITH AUTO-DISCOVERY")
print("="*70)
print()

async def test_investigation():
    """Test full investigation workflow"""
    from backend.database.connection import get_db_session
    from backend.agents.investigation2_workflow import Investigation2Workflow
    from backend.services.investigation_service import InvestigationService
    from backend.database.models import User

    # Load test image
    image_path = Path("data/models/atrw/images/Amur Tigers/test/000000.jpg")
    print(f"[1] Loading test image: {image_path}")

    if not image_path.exists():
        print(f"ERROR: Image not found at {image_path}")
        return False

    with open(image_path, 'rb') as f:
        image_bytes = f.read()

    print(f"[OK] Image loaded: {len(image_bytes):,} bytes")
    print()

    # Create investigation
    with get_db_session() as db:
        print(f"[2] Creating investigation...")

        # Get admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("ERROR: Admin user not found")
            return False

        # Create investigation
        investigation_service = InvestigationService(db)
        investigation = investigation_service.create_investigation(
            title="Live Test - Auto-Discovery",
            description="Testing Investigation 2.0 workflow with auto-discovery enabled",
            priority="high",
            created_by=admin_user.user_id
        )

        investigation_id = investigation.investigation_id
        print(f"[OK] Investigation created: {investigation_id}")
        print()

        # Create workflow
        print(f"[3] Initializing Investigation 2.0 workflow...")
        workflow = Investigation2Workflow(db=db)
        print(f"[OK] Workflow initialized")
        print()

        # Prepare context
        context = {
            "location": "Test Facility, Texas",
            "date": "2026-01-13",
            "notes": "Live test of Investigation 2.0 with auto-discovery"
        }

        # Run workflow
        print("="*70)
        print("STARTING INVESTIGATION WORKFLOW")
        print("="*70)
        print()
        print("This will execute all 7 phases:")
        print("  1. Upload & Parse")
        print("  2. Web Intelligence (Gemini Search)")
        print("  3. Tiger Detection (MegaDetector)")
        print("  4. Stripe Analysis (4 ReID Models)")
        print("  5. Visual Analysis (OmniVinci)")
        print("  6. Report Generation (Gemini Pro)")
        print("  7. Complete (Auto-Discovery)")
        print()
        print("Please wait...")
        print()

        try:
            final_state = await workflow.run(
                investigation_id=investigation_id,
                uploaded_image=image_bytes,
                context=context
            )

            print()
            print("="*70)
            print("INVESTIGATION COMPLETE")
            print("="*70)
            print()

            # Print results
            print(f"Status: {final_state.get('status')}")
            print(f"Phase: {final_state.get('phase')}")
            print(f"Errors: {len(final_state.get('errors', []))}")
            print()

            # Tiger detection
            if final_state.get('detected_tigers'):
                tigers = final_state['detected_tigers']
                print(f"[TIGER DETECTION] {len(tigers)} tiger(s) detected")
                for i, tiger in enumerate(tigers, 1):
                    print(f"  Tiger {i}: confidence={tiger.get('confidence', 0):.2f}")
                print()

            # Stripe analysis
            if final_state.get('database_matches'):
                matches = final_state['database_matches']
                total = sum(len(m) for m in matches.values())
                print(f"[STRIPE ANALYSIS] {total} total matches across {len(matches)} models")
                for model, model_matches in matches.items():
                    if model_matches:
                        top = model_matches[0]
                        print(f"  {model}: {len(model_matches)} matches (top: {top.get('similarity', 0):.3f})")
                print()

            # Auto-discovery
            if final_state.get('report', {}).get('new_discovery'):
                discovery = final_state['report']['new_discovery']
                print("="*70)
                print("[NEW DISCOVERY] Auto-discovery created new records!")
                print("="*70)
                print(f"Tiger ID: {discovery.get('tiger_id')}")
                print(f"Tiger Name: {discovery.get('tiger_name')}")
                print(f"Facility: {discovery.get('facility_name')}")
                print(f"Location: {discovery.get('location')}")
                print(f"Confidence: {discovery.get('confidence'):.2f}")
                print(f"Is New Facility: {discovery.get('is_new_facility')}")
                print("="*70)
                print()
            else:
                print("[AUTO-DISCOVERY] No new discovery (strong match found or no facility info)")
                print()

            # Location analysis
            if final_state.get('report', {}).get('location_analysis'):
                location = final_state['report']['location_analysis']
                print(f"[LOCATION ANALYSIS] {len(location.get('sources', []))} location sources found")
                if location.get('primary_location'):
                    primary = location['primary_location']
                    print(f"  Primary: {primary.get('facility', primary.get('city', 'Unknown'))}")
                    print(f"  Confidence: {primary.get('confidence', 'unknown')}")
                print()

            print("="*70)
            print("[SUCCESS] Investigation completed successfully!")
            print("="*70)

            return True

        except Exception as e:
            print()
            print("="*70)
            print("[ERROR] Investigation failed!")
            print("="*70)
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main entry point"""
    try:
        success = await test_investigation()
        return 0 if success else 1
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

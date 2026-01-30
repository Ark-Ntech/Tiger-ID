"""Test auto-discovery integration with Investigation 2.0 workflow"""

import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Force SQLite database for tests
os.environ['DATABASE_URL'] = 'sqlite:///data/production.db'

from backend.database.connection import get_db_session
from backend.database.models import Tiger, TigerImage, Facility
from backend.services.auto_discovery_service import AutoDiscoveryService
from uuid import uuid4


async def test_auto_discovery_service():
    """Test AutoDiscoveryService methods"""
    print("\n" + "="*70)
    print("AUTO-DISCOVERY SERVICE INTEGRATION TEST")
    print("="*70)

    # Get database session using context manager
    with get_db_session() as db:
        service = AutoDiscoveryService(db)

        # Test 1: Extract facility info from mock web intelligence
        print("\n[TEST 1] Extract Facility Info from Web Intelligence")
        print("-" * 70)

        mock_web_intelligence = {
            "citations": [
                {
                    "title": "Tigers at Dallas Zoo",
                    "snippet": "The Dallas Zoo in Dallas, Texas is home to several Amur tigers",
                    "uri": "https://example.com/dallas-zoo",
                    "relevance_score": 0.9
                },
                {
                    "title": "Big Cat Rescue Tampa",
                    "snippet": "Big Cat Rescue sanctuary in Tampa, Florida rescues tigers",
                    "uri": "https://example.com/big-cat-rescue",
                    "relevance_score": 0.85
                }
            ],
            "summary": "Found information about Dallas Zoo, Texas where several tigers are kept"
        }

        facilities = service.extract_facility_info(mock_web_intelligence)
        print(f"Extracted {len(facilities)} facilities:")
        for i, facility in enumerate(facilities, 1):
            print(f"  {i}. {facility.get('name')} - {facility.get('city')}, {facility.get('state')}")
            print(f"     Confidence: {facility.get('confidence')}, Source: {facility.get('source')}")

        if len(facilities) > 0:
            print("[PASS] Facility extraction working")
        else:
            print("[FAIL] No facilities extracted")
            return False

        # Test 2: Check should_create_new_tiger logic
        print("\n[TEST 2] Should Create New Tiger Logic")
        print("-" * 70)

        # Case 1: No matches - should create new
        should_create_1 = service.should_create_new_tiger([])
        print(f"No matches: should_create = {should_create_1} (expected: True)")

        # Case 2: Low similarity - should create new
        low_match = [{"similarity": 0.75}]
        should_create_2 = service.should_create_new_tiger(low_match)
        print(f"Low similarity (0.75): should_create = {should_create_2} (expected: True)")

        # Case 3: High similarity - should NOT create new
        high_match = [{"similarity": 0.95}]
        should_create_3 = service.should_create_new_tiger(high_match)
        print(f"High similarity (0.95): should_create = {should_create_3} (expected: False)")

        if should_create_1 and should_create_2 and not should_create_3:
            print("[PASS] Should create new tiger logic working correctly")
        else:
            print("[FAIL] Logic not working as expected")
            return False

        # Test 3: Database schema check
        print("\n[TEST 3] Database Schema Check")
        print("-" * 70)

        # Check if is_reference field exists in Tiger model
        tiger_columns = [col.name for col in Tiger.__table__.columns]
        required_tiger_fields = ['is_reference', 'discovered_at', 'discovered_by_investigation_id', 'discovery_confidence']

        print("Tiger model fields:")
        for field in required_tiger_fields:
            present = field in tiger_columns
            status = "[OK]" if present else "[MISSING]"
            print(f"  {status} {field}")

        # Check TigerImage fields
        image_columns = [col.name for col in TigerImage.__table__.columns]
        required_image_fields = ['is_reference', 'discovered_by_investigation_id']

        print("\nTigerImage model fields:")
        for field in required_image_fields:
            present = field in image_columns
            status = "[OK]" if present else "[MISSING]"
            print(f"  {status} {field}")

        # Check Facility fields
        facility_columns = [col.name for col in Facility.__table__.columns]
        required_facility_fields = ['coordinates', 'discovered_at', 'discovered_by_investigation_id']

        print("\nFacility model fields:")
        for field in required_facility_fields:
            present = field in facility_columns
            status = "[OK]" if present else "[MISSING]"
            print(f"  {status} {field}")

        all_fields_present = (
            all(f in tiger_columns for f in required_tiger_fields) and
            all(f in image_columns for f in required_image_fields) and
            all(f in facility_columns for f in required_facility_fields)
        )

        if all_fields_present:
            print("\n[PASS] All required database fields present")
        else:
            print("\n[FAIL] Some database fields missing")
            return False

        # Test 4: Check database state
        print("\n[TEST 4] Database State Check")
        print("-" * 70)

        total_tigers = db.query(Tiger).count()
        reference_tigers = db.query(Tiger).filter(Tiger.is_reference == True).count()
        real_tigers = db.query(Tiger).filter(Tiger.is_reference == False).count()

        total_facilities = db.query(Facility).count()

        print(f"Total tigers: {total_tigers}")
        print(f"  - Reference (ATRW): {reference_tigers}")
        print(f"  - Real (discovered): {real_tigers}")
        print(f"Total facilities: {total_facilities}")

        print("\n[PASS] Database state check complete")

        # Test 5: Check Investigation 2.0 workflow integration
        print("\n[TEST 5] Investigation 2.0 Workflow Integration Check")
        print("-" * 70)

        try:
            from backend.agents.investigation2_workflow import Investigation2Workflow
            print("[OK] Investigation2Workflow imports successfully")

            # Check if AutoDiscoveryService is imported
            with open("backend/agents/investigation2_workflow.py", "r", encoding="utf-8") as f:
                workflow_code = f.read()
                if "from backend.services.auto_discovery_service import AutoDiscoveryService" in workflow_code:
                    print("[OK] AutoDiscoveryService imported in workflow")
                else:
                    print("[FAIL] AutoDiscoveryService not imported in workflow")
                    return False

                if "auto_discovery = AutoDiscoveryService" in workflow_code:
                    print("[OK] AutoDiscoveryService instantiated in workflow")
                else:
                    print("[FAIL] AutoDiscoveryService not instantiated in workflow")
                    return False

                if "process_investigation_discovery" in workflow_code:
                    print("[OK] process_investigation_discovery called in workflow")
                else:
                    print("[FAIL] process_investigation_discovery not called in workflow")
                    return False

            print("\n[PASS] Workflow integration complete")

        except Exception as e:
            print(f"[FAIL] Workflow integration check failed: {e}")
            return False

        return True


async def main():
    """Main test function"""
    try:
        success = await test_auto_discovery_service()

        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)

        if success:
            print("[SUCCESS] All auto-discovery integration tests passed!")
            print("\nNext steps:")
            print("1. Run ATRW reference ingestion: python scripts/ingest_atrw_reference.py")
            print("2. Geocode facilities: python scripts/geocode_facilities.py")
            print("3. Test with live investigation: python test_workflow_direct.py")
            return 0
        else:
            print("[FAILURE] Some tests failed - review output above")
            return 1

    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

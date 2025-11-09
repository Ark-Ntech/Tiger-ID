"""Direct test of Investigation 2.0 workflow"""

import asyncio
import sys
import os
from pathlib import Path
from uuid import uuid4
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables (including OpenAI API key)
load_dotenv()

# IMPORTANT: Disable mock mode to use real Modal
os.environ["MODAL_USE_MOCK"] = "false"

# Verify configuration
print(f"[CONFIG] MODAL_USE_MOCK: {os.getenv('MODAL_USE_MOCK', 'not set')}")
print(f"[CONFIG] OPENAI_API_KEY: {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
print()

async def test_workflow():
    """Test the workflow directly"""
    from backend.database import get_db_session
    from backend.agents.investigation2_workflow import Investigation2Workflow
    from backend.services.investigation_service import InvestigationService
    
    print("[TEST] ========================================")
    print("[TEST] Starting workflow test...")
    print("[TEST] ========================================")
    
    # Read test image
    image_path = Path("data/models/atrw/images/Amur Tigers/test/000000.jpg")
    if not image_path.exists():
        print(f"[TEST] Image not found: {image_path}")
        return
    
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    print(f"[TEST] Image loaded: {len(image_bytes)} bytes")
    
    # Create investigation
    db_gen = get_db_session()
    db = next(db_gen)
    
    try:
        from backend.database.models import User
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("[TEST] Admin user not found")
            return
        
        investigation_service = InvestigationService(db)
        investigation = investigation_service.create_investigation(
            title="Workflow Test",
            description="Direct workflow test",
            priority="high",
            created_by=admin_user.user_id
        )
        
        investigation_id = investigation.investigation_id
        print(f"[TEST] Investigation created: {investigation_id}")
        
        # Create workflow
        workflow = Investigation2Workflow(db=db)
        print("[TEST] Workflow instance created")
        
        # Prepare context
        context = {
            "location": "Test Location",
            "date": "2025-11-09",
            "notes": "Direct workflow test"
        }
        
        # Run workflow
        print("[TEST] ========================================")
        print("[TEST] Starting workflow.run()...")
        print("[TEST] ========================================")
        
        final_state = await workflow.run(
            investigation_id=investigation_id,
            uploaded_image=image_bytes,
            context=context
        )
        
        print("[TEST] ========================================")
        print(f"[TEST] Workflow completed!")
        print(f"[TEST] Final status: {final_state.get('status')}")
        print(f"[TEST] Phase: {final_state.get('phase')}")
        print(f"[TEST] Errors: {len(final_state.get('errors', []))}")
        print("[TEST] ========================================")
        
        # Detailed results
        if final_state.get('detected_tigers'):
            print(f"\n[TEST] TIGER DETECTION:")
            print(f"  Tigers detected: {len(final_state['detected_tigers'])}")
            for i, tiger in enumerate(final_state['detected_tigers'], 1):
                bbox = tiger.get('bbox', {})
                if isinstance(bbox, dict):
                    print(f"  Tiger {i}: confidence={tiger.get('confidence', 0):.2f}, bbox=[{bbox.get('x1')}, {bbox.get('y1')}, {bbox.get('x2')}, {bbox.get('y2')}]")
                elif isinstance(bbox, list):
                    print(f"  Tiger {i}: confidence={tiger.get('confidence', 0):.2f}, bbox={bbox}")
                else:
                    print(f"  Tiger {i}: confidence={tiger.get('confidence', 0):.2f}")
        
        if final_state.get('database_matches'):
            print(f"\n[TEST] STRIPE ANALYSIS RESULTS:")
            total_matches = sum(len(matches) for matches in final_state['database_matches'].values())
            print(f"  Total matches: {total_matches} across {len(final_state['database_matches'])} models")
            for model_name, matches in final_state['database_matches'].items():
                print(f"  {model_name}: {len(matches)} matches")
                if matches:
                    top_match = matches[0]
                    print(f"    Top match: {top_match.get('tiger_name')} (similarity: {top_match.get('similarity', 0):.3f})")
        
        if final_state.get('reverse_search_results'):
            print(f"\n[TEST] REVERSE IMAGE SEARCH:")
            results = final_state['reverse_search_results']
            print(f"  Providers searched: {len(results)}")
            for provider, data in results.items():
                matches = data.get('matches', []) if isinstance(data, dict) else data
                print(f"  {provider}: {len(matches) if matches else 0} results")
        
        if final_state.get('report'):
            print(f"\n[TEST] REPORT:")
            report = final_state['report']
            print(f"  Report type: {type(report)}")
            if isinstance(report, dict):
                print(f"  Report keys: {list(report.keys())}")
                if 'summary' in report:
                    summary = report['summary'][:200] + "..." if len(str(report['summary'])) > 200 else report['summary']
                    print(f"  Summary: {summary}")
            else:
                preview = str(report)[:200] + "..." if len(str(report)) > 200 else str(report)
                print(f"  Content preview: {preview}")
        
        print("\n[TEST] ========================================")
        print("[TEST] Workflow test completed successfully!")
        print("[TEST] ========================================")
        
    except Exception as e:
        print(f"[TEST] ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            db.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_workflow())


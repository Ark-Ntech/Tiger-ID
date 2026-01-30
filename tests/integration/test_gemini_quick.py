"""Quick test script for Gemini integration"""

import asyncio
import sys
import os

# Load .env file
from dotenv import load_dotenv
load_dotenv()

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.models.gemini_chat import get_gemini_flash_model, get_gemini_pro_model


async def test_gemini_flash_basic():
    """Test basic chat with Gemini Flash"""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Chat with Gemini Flash")
    print("=" * 60)

    try:
        model = get_gemini_flash_model()
        result = await model.chat(
            message="What is 2+2? Answer with just the number.",
            temperature=0.1
        )

        print(f"Success: {result['success']}")
        print(f"Response: {result['response']}")
        print(f"Model: {result['model']}")

        if "4" in result["response"]:
            print("[PASS] Gemini Flash basic chat works!")
            return True
        else:
            print("[FAIL] Expected '4' in response")
            return False

    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gemini_search_grounding():
    """Test Search Grounding"""
    print("\n" + "=" * 60)
    print("TEST 2: Search Grounding with Gemini Flash")
    print("=" * 60)

    try:
        model = get_gemini_flash_model()
        result = await model.chat(
            message="What are the latest tiger conservation efforts in 2025-2026?",
            enable_search_grounding=True
        )

        print(f"Success: {result['success']}")
        print(f"Response length: {len(result['response'])} chars")
        print(f"Citations found: {len(result.get('citations', []))}")
        print(f"Model: {result['model']}")

        if result.get('citations'):
            print("\nFirst 3 citations:")
            for i, cite in enumerate(result['citations'][:3], 1):
                print(f"  {i}. {cite.get('title', 'No title')}")
                print(f"     {cite.get('uri', 'No URI')}")

        if result['success'] and len(result.get('citations', [])) > 0:
            print("\n[PASS] Search Grounding works!")
            return True
        else:
            print("\n[WARN] No citations found (may still work)")
            return result['success']

    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gemini_pro_report():
    """Test Gemini Pro for report generation"""
    print("\n" + "=" * 60)
    print("TEST 3: Report Generation with Gemini Pro")
    print("=" * 60)

    try:
        model = get_gemini_pro_model()
        result = await model.chat(
            message="Generate a 2-sentence summary of tiger conservation efforts worldwide.",
            temperature=0.7,
            max_tokens=200
        )

        print(f"Success: {result['success']}")
        print(f"Response: {result['response']}")
        print(f"Model: {result['model']}")

        if result['success'] and len(result['response']) > 50:
            print("\n[PASS] Gemini Pro report generation works!")
            return True
        else:
            print("\n[FAIL] Response too short or failed")
            return False

    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("GEMINI INTEGRATION QUICK TEST SUITE")
    print("=" * 60)

    results = []

    try:
        # Test 1: Basic chat
        results.append(await test_gemini_flash_basic())

        # Test 2: Search Grounding
        results.append(await test_gemini_search_grounding())

        # Test 3: Gemini Pro
        results.append(await test_gemini_pro_report())

        print("\n" + "=" * 60)
        if all(results):
            print("ALL TESTS PASSED!")
            print("=" * 60)
            print("\nGemini integration is working correctly.")
            print("You can now proceed with Phase 2: Update Investigation2 Workflow\n")
            return 0
        else:
            print("SOME TESTS FAILED")
            print("=" * 60)
            print(f"\nPassed: {sum(results)}/{len(results)} tests")
            print("Please fix the issues before proceeding.\n")
            return 1

    except Exception as e:
        print("\n" + "=" * 60)
        print("ERROR RUNNING TESTS")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        print("\nPlease fix the issues before proceeding.\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

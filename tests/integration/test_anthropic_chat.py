"""Test script for Anthropic Claude chat integration."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()


async def test_basic_chat():
    """Test basic chat functionality."""
    print("\n" + "="*60)
    print("TEST 1: Basic Chat")
    print("="*60)

    from backend.models.anthropic_chat import get_anthropic_fast_model

    model = get_anthropic_fast_model()
    result = await model.chat("Hello, Claude! Please respond with a brief greeting.")

    print(f"Success: {result.get('success')}")
    print(f"Model: {result.get('model')}")
    print(f"Response: {result.get('response', '')[:200]}...")

    if result.get('error'):
        print(f"Error: {result.get('error')}")

    return result.get('success', False)


async def test_web_search():
    """Test web search integration."""
    print("\n" + "="*60)
    print("TEST 2: Web Search Integration")
    print("="*60)

    from backend.models.anthropic_chat import get_anthropic_fast_model

    model = get_anthropic_fast_model()
    result = await model.chat(
        "Search for recent tiger conservation news in India",
        enable_web_search=True
    )

    print(f"Success: {result.get('success')}")
    print(f"Model: {result.get('model')}")
    print(f"Response length: {len(result.get('response', ''))} chars")
    print(f"Citations: {len(result.get('citations', []))}")

    if result.get('citations'):
        print("\nTop citations:")
        for i, cite in enumerate(result.get('citations', [])[:3], 1):
            print(f"  {i}. {cite.get('title', 'No title')[:50]}")
            print(f"     {cite.get('uri', 'No URI')[:60]}")

    if result.get('error'):
        print(f"Error: {result.get('error')}")

    return result.get('success', False)


async def test_quality_model():
    """Test the quality (Opus) model."""
    print("\n" + "="*60)
    print("TEST 3: Quality Model (Opus)")
    print("="*60)

    from backend.models.anthropic_chat import get_anthropic_quality_model

    model = get_anthropic_quality_model()
    result = await model.chat(
        "Analyze the importance of stripe pattern analysis in tiger identification for wildlife conservation.",
        max_tokens=500
    )

    print(f"Success: {result.get('success')}")
    print(f"Model: {result.get('model')}")
    print(f"Response length: {len(result.get('response', ''))} chars")
    print(f"Response preview: {result.get('response', '')[:300]}...")

    if result.get('error'):
        print(f"Error: {result.get('error')}")

    return result.get('success', False)


async def test_tool_calling():
    """Test tool calling capability."""
    print("\n" + "="*60)
    print("TEST 4: Tool Calling")
    print("="*60)

    from backend.models.anthropic_chat import get_anthropic_fast_model

    model = get_anthropic_fast_model()

    # Define a custom tool
    tools = [
        {
            "name": "get_tiger_info",
            "description": "Get information about a specific tiger by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "tiger_id": {
                        "type": "string",
                        "description": "The ID of the tiger to look up"
                    }
                },
                "required": ["tiger_id"]
            }
        }
    ]

    result = await model.chat(
        "Look up information about tiger T-123",
        tools=tools
    )

    print(f"Success: {result.get('success')}")
    print(f"Model: {result.get('model')}")
    print(f"Tool calls: {len(result.get('tool_calls', []))}")

    if result.get('tool_calls'):
        for tc in result.get('tool_calls', []):
            print(f"  - {tc.get('name')}: {tc.get('arguments')}")

    if result.get('error'):
        print(f"Error: {result.get('error')}")

    return result.get('success', False)


async def main():
    """Run all tests."""
    print("="*60)
    print("ANTHROPIC CLAUDE INTEGRATION TESTS")
    print("="*60)

    results = []

    # Test 1: Basic chat
    try:
        results.append(("Basic Chat", await test_basic_chat()))
    except Exception as e:
        print(f"Test 1 failed with exception: {e}")
        results.append(("Basic Chat", False))

    # Test 2: Web search
    try:
        results.append(("Web Search", await test_web_search()))
    except Exception as e:
        print(f"Test 2 failed with exception: {e}")
        results.append(("Web Search", False))

    # Test 3: Quality model
    try:
        results.append(("Quality Model", await test_quality_model()))
    except Exception as e:
        print(f"Test 3 failed with exception: {e}")
        results.append(("Quality Model", False))

    # Test 4: Tool calling
    try:
        results.append(("Tool Calling", await test_tool_calling()))
    except Exception as e:
        print(f"Test 4 failed with exception: {e}")
        results.append(("Tool Calling", False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = 0
    for name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  {name}: {status}")
        if success:
            passed += 1

    print(f"\nTotal: {passed}/{len(results)} tests passed")

    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

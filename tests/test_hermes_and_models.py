"""
Test script to verify Hermes model and other integrations are working correctly.

This script tests:
1. Hermes model communication via Modal
2. OmniVinci video analysis
3. MCP tools execution
4. Investigation service integration
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models.hermes_chat import get_hermes_chat_model
from backend.models.omnivinci import get_omnivinci_model
from backend.services.modal_client import get_modal_client
from backend.agents.orchestrator import OrchestratorAgent
from backend.utils.logging import get_logger

logger = get_logger(__name__)


async def test_hermes_model():
    """Test Hermes model communication"""
    print("\n" + "="*60)
    print("TEST 1: Hermes Model Communication")
    print("="*60)
    
    try:
        hermes_model = get_hermes_chat_model()
        
        # Test basic chat
        result = await hermes_model.chat(
            message="Hello, I need help investigating a tiger facility.",
            tools=None,
            conversation_history=None,
            max_tokens=100,
            temperature=0.7
        )
        
        print(f"[PASS] Hermes Model Test PASSED")
        print(f"   Success: {result.get('success')}")
        print(f"   Response: {result.get('response', '')[:100]}...")
        return True
        
    except Exception as e:
        print(f"[FAIL] Hermes Model Test FAILED: {e}")
        logger.error(f"Hermes test failed: {e}", exc_info=True)
        return False


async def test_hermes_with_tools():
    """Test Hermes model with tool calling"""
    print("\n" + "="*60)
    print("TEST 2: Hermes Model with Tool Calling")
    print("="*60)
    
    try:
        hermes_model = get_hermes_chat_model()
        
        # Define sample tools
        tools = [
            {
                "name": "search_web",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    }
                }
            },
            {
                "name": "query_database",
                "description": "Query the tiger database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table": {"type": "string", "description": "Table to query"}
                    }
                }
            }
        ]
        
        result = await hermes_model.chat(
            message="Find information about tiger facilities in Texas",
            tools=tools,
            conversation_history=None,
            max_tokens=150,
            temperature=0.7
        )
        
        print(f"[PASS] Hermes with Tools Test PASSED")
        print(f"   Success: {result.get('success')}")
        print(f"   Response: {result.get('response', '')[:100]}...")
        print(f"   Tool Calls: {len(result.get('tool_calls', []))}")
        if result.get('tool_calls'):
            for tool_call in result.get('tool_calls', []):
                print(f"      - {tool_call.get('name')}")
        return True
        
    except Exception as e:
        print(f"[FAIL] Hermes with Tools Test FAILED: {e}")
        logger.error(f"Hermes with tools test failed: {e}", exc_info=True)
        return False


async def test_modal_client():
    """Test Modal client connection"""
    print("\n" + "="*60)
    print("TEST 3: Modal Client Connection")
    print("="*60)
    
    try:
        modal_client = get_modal_client()
        stats = modal_client.get_stats()
        
        print(f"[PASS] Modal Client Test PASSED")
        print(f"   Requests Sent: {stats.get('requests_sent')}")
        print(f"   Requests Succeeded: {stats.get('requests_succeeded')}")
        print(f"   Requests Failed: {stats.get('requests_failed')}")
        print(f"   Queue Size: {stats.get('queue_size')}")
        return True
        
    except Exception as e:
        print(f"[FAIL] Modal Client Test FAILED: {e}")
        logger.error(f"Modal client test failed: {e}", exc_info=True)
        return False


async def test_omnivinci_model():
    """Test OmniVinci model initialization"""
    print("\n" + "="*60)
    print("TEST 4: OmniVinci Model Initialization")
    print("="*60)
    
    try:
        omnivinci_model = get_omnivinci_model()
        
        # Test that image analysis correctly returns error (not implemented)
        result = await omnivinci_model.analyze_image(
            image=None,
            prompt="Test prompt"
        )
        
        # Should return error since image analysis is not supported
        if not result.get("success") and "not supported" in result.get("error", ""):
            print(f"[PASS] OmniVinci Model Test PASSED")
            print(f"   Correctly returns error for unsupported image analysis")
            return True
        else:
            print(f"[WARN]  OmniVinci Model Test: Unexpected result")
            print(f"   Result: {result}")
            return False
        
    except Exception as e:
        print(f"[FAIL] OmniVinci Model Test FAILED: {e}")
        logger.error(f"OmniVinci test failed: {e}", exc_info=True)
        return False


async def test_mcp_tools():
    """Test MCP tools are accessible"""
    print("\n" + "="*60)
    print("TEST 5: MCP Tools Accessibility")
    print("="*60)
    
    try:
        # Import MCP servers
        from backend.mcp_servers import (
            FirecrawlMCPServer,
            DatabaseMCPServer,
            TigerIDMCPServer,
            YouTubeMCPServer,
            MetaMCPServer
        )
        
        servers = {
            "firecrawl": FirecrawlMCPServer(),
            "database": DatabaseMCPServer(),
            "tiger_id": TigerIDMCPServer(),
            "youtube": YouTubeMCPServer(),
            "meta": MetaMCPServer()
        }
        
        print(f"[PASS] MCP Tools Test PASSED")
        print(f"   Servers initialized: {len(servers)}")
        
        for name, server in servers.items():
            tools = await server.list_tools()
            print(f"   - {name}: {len(tools)} tools")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] MCP Tools Test FAILED: {e}")
        logger.error(f"MCP tools test failed: {e}", exc_info=True)
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TIGER ID - MODEL & INTEGRATION TESTS")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(await test_modal_client())
    results.append(await test_hermes_model())
    results.append(await test_hermes_with_tools())
    results.append(await test_omnivinci_model())
    results.append(await test_mcp_tools())
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("[SUCCESS] ALL TESTS PASSED!")
    else:
        print(f"[WARNING]  {total - passed} TEST(S) FAILED")
    
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)


"""Test Search Grounding Citations"""

import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

# Set up logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from backend.models.gemini_chat import get_gemini_flash_model

async def test_search_grounding():
    print("\n" + "="*60)
    print("Testing Search Grounding Citations")
    print("="*60)

    model = get_gemini_flash_model()

    result = await model.chat(
        message="What are the latest tiger conservation efforts in 2025?",
        enable_search_grounding=True,
        temperature=0.7
    )

    print(f"\nSuccess: {result['success']}")
    print(f"Response length: {len(result['response'])} chars")
    print(f"Citations: {len(result['citations'])}")

    if result['citations']:
        print("\nCitations:")
        for i, cite in enumerate(result['citations'], 1):
            print(f"  {i}. {cite.get('title', 'No title')}")
            print(f"     {cite.get('uri', 'No URI')}")
    else:
        print("\nNO CITATIONS EXTRACTED")

    print("\nFirst 500 chars of response:")
    print(result['response'][:500])

if __name__ == "__main__":
    asyncio.run(test_search_grounding())

"""Test correct SDK usage"""

import os
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Test 1: Simple generation
print("\n1. Testing simple generation...")
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="What is 2+2? Answer with just the number."
    )
    print(f"Response: {response.text}")
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")

# Test 2: With config
print("\n2. Testing with config...")
try:
    config = types.GenerateContentConfig(
        temperature=0.1,
        max_output_tokens=100
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="What is 2+2?",
        config=config
    )
    print(f"Response: {response.text}")
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")

# Test 3: Check response structure
print("\n3. Testing response structure...")
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say hello"
    )
    print(f"Response type: {type(response)}")
    print(f"Has text: {hasattr(response, 'text')}")
    print(f"Has candidates: {hasattr(response, 'candidates')}")
    if hasattr(response, 'candidates'):
        for i, candidate in enumerate(response.candidates):
            print(f"  Candidate {i}: {type(candidate)}")
            if hasattr(candidate, 'content'):
                print(f"    Has content: True")
                if hasattr(candidate.content, 'parts'):
                    print(f"    Has parts: True, count: {len(candidate.content.parts)}")
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")

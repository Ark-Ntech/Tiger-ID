"""List available Gemini models"""

import os
from dotenv import load_dotenv
load_dotenv()

from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("\nAvailable Gemini models:\n")
print("=" * 80)

for model in client.models.list():
    print(f"Model: {model.name}")
    print(f"  Display name: {model.display_name}")
    if hasattr(model, 'supported_generation_methods'):
        print(f"  Supported methods: {model.supported_generation_methods}")
    print()

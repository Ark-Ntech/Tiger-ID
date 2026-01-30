"""Test the tiger-id-models app"""

import sys
import os
import asyncio
from pathlib import Path
from PIL import Image
import io

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import modal

async def test_tiger_id_models_app():
    print("="*70)
    print("TESTING 'tiger-id-models' APP")
    print("="*70)
    print()

    # Test all classes that should be in the app
    classes_to_test = {
        "TigerReIDModel": "generate_embedding",
        "MegaDetectorModel": "detect",
        "WildlifeToolsModel": "generate_embedding",
        "RAPIDReIDModel": "generate_embedding",
        "CVWC2019ReIDModel": "generate_embedding",
        "OmniVinciModel": "analyze_image"
    }

    for class_name, method_name in classes_to_test.items():
        print(f"\nTesting {class_name}:")
        print("-" * 40)

        try:
            # Look up class
            print(f"[1] Looking up class...")
            cls = modal.Cls.from_name("tiger-id-models", class_name)
            print(f"    [OK] Class found")

            # Try to hydrate
            print(f"[2] Hydrating class...")
            await cls.hydrate()
            print(f"    [OK] Hydration succeeded!")

            # Create instance
            print(f"[3] Creating instance...")
            instance = cls()
            print(f"    [OK] Instance created")

            # Access method
            print(f"[4] Accessing method '{method_name}'...")
            method = getattr(instance, method_name)
            print(f"    [OK] Method accessed")

            # Check if method has remote.aio
            if hasattr(method, 'remote') and hasattr(method.remote, 'aio'):
                print(f"    [OK] Method has .remote.aio()")
            else:
                print(f"    [WARN] Method missing .remote.aio()")

            print(f"    ✅ {class_name} is functional!")

        except Exception as e:
            print(f"    ❌ {class_name} failed: {e}")

    print()
    print("="*70)
    print("Testing actual method call with TigerReIDModel")
    print("="*70)
    print()

    try:
        # Load test image
        image_path = Path("data/models/atrw/images/Amur Tigers/test/000000.jpg")
        if not image_path.exists():
            print(f"Test image not found: {image_path}")
            return

        image = Image.open(image_path).convert("RGB")
        buf = io.BytesIO()
        image.save(buf, format='JPEG')
        image_bytes = buf.getvalue()

        print(f"Loaded test image: {len(image_bytes)} bytes")

        # Call generate_embedding
        cls = modal.Cls.from_name("tiger-id-models", "TigerReIDModel")
        instance = cls()

        print("Calling generate_embedding.remote.aio()...")
        result = await instance.generate_embedding.remote.aio(image_bytes)

        print(f"✅ SUCCESS! Got result:")
        print(f"   Keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        if isinstance(result, dict) and 'embedding' in result:
            import numpy as np
            emb = np.array(result['embedding'])
            print(f"   Embedding shape: {emb.shape}")

    except Exception as e:
        print(f"❌ Method call failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tiger_id_models_app())

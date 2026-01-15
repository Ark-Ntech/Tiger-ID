"""Test calling TigerReIDModel.generate_embedding"""

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

async def test_tiger_reid():
    print("="*70)
    print("Testing TigerReIDModel.generate_embedding()")
    print("="*70)
    print()

    # Get the class
    print("[1] Getting TigerReIDModel class from Modal...")
    tiger_reid_cls = modal.Cls.from_name('tiger-id-models', 'TigerReIDModel')
    print("[OK] Got class")
    print()

    # Create instance
    print("[2] Creating instance...")
    instance = tiger_reid_cls()
    print("[OK] Created instance")
    print()

    # Load test image
    print("[3] Loading test image...")
    image_path = Path("data/models/atrw/images/Amur Tigers/test/000000.jpg")
    if not image_path.exists():
        print(f"[ERROR] Image not found: {image_path}")
        return

    image = Image.open(image_path).convert("RGB")
    print(f"[OK] Loaded image: {image.size}")
    print()

    # Convert to bytes
    print("[4] Converting image to bytes...")
    buf = io.BytesIO()
    image.save(buf, format='JPEG')
    image_bytes = buf.getvalue()
    print(f"[OK] Image bytes: {len(image_bytes)} bytes")
    print()

    # Call generate_embedding
    print("[5] Calling instance.generate_embedding.remote.aio()...")
    try:
        result = await instance.generate_embedding.remote.aio(image_bytes)
        print(f"[OK] Got result: {type(result)}")
        print(f"     Keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        if isinstance(result, dict) and 'embedding' in result:
            import numpy as np
            emb = np.array(result['embedding'])
            print(f"     Embedding shape: {emb.shape}")
        print()
        print("="*70)
        print("SUCCESS!")
        print("="*70)
        return True
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_tiger_reid())
    sys.exit(0 if success else 1)

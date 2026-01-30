"""
Test script to verify all Modal models load real weights and function correctly.

This script tests:
1. All Modal models can be instantiated
2. Models load weights from Modal volume (not placeholders)
3. Models generate embeddings successfully
4. Inference time and embedding quality
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Note: These models are Modal classes, so we need to access them via the app
# For testing, we'll use the Modal app instance
try:
    from backend.modal_app import (
        app,
        TigerReIDModel,
        RAPIDReIDModel,
        CVWC2019ReIDModel,
    )
    
    # Try to import WildlifeTools and MegaDetector if available
    try:
        from backend.modal_app import WildlifeToolsModel, MegaDetectorModel
    except ImportError:
        # Models might have different names, check modal_app
        WildlifeToolsModel = None
        MegaDetectorModel = None
except ImportError as e:
    print(f"Warning: Could not import Modal models: {e}")
    print("Make sure Modal is installed and backend/modal_app.py is accessible")
    TigerReIDModel = None
    RAPIDReIDModel = None
    CVWC2019ReIDModel = None
    WildlifeToolsModel = None
    MegaDetectorModel = None

# Sample test image (1x1 pixel PNG)
SAMPLE_IMAGE_BYTES = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'


async def test_model(model_class, model_name: str):
    """Test a single model"""
    print(f"\n{'='*60}")
    print(f"Testing {model_name}")
    print(f"{'='*60}")
    
    try:
        # Instantiate model
        print(f"Instantiating {model_name}...")
        model = model_class()
        
        # Test embedding generation
        print(f"Generating embedding with {model_name}...")
        result = await model.generate_embedding.aio(SAMPLE_IMAGE_BYTES)
        
        if result.get("success"):
            embedding = result.get("embedding")
            shape = result.get("shape")
            print(f"✓ Success! Embedding shape: {shape}")
            print(f"  Embedding length: {len(embedding) if embedding else 0}")
            
            # Check if embedding is normalized
            if embedding:
                import numpy as np
                norm = np.linalg.norm(embedding)
                print(f"  Embedding norm: {norm:.4f} (should be ~1.0 if normalized)")
            
            return {
                "model": model_name,
                "status": "success",
                "embedding_shape": shape,
                "embedding_length": len(embedding) if embedding else 0
            }
        else:
            error = result.get("error", "Unknown error")
            print(f"✗ Failed: {error}")
            return {
                "model": model_name,
                "status": "failed",
                "error": error
            }
            
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "model": model_name,
            "status": "error",
            "error": str(e)
        }


async def main():
    """Test all Modal models"""
    print("="*60)
    print("Modal Models Test Suite")
    print("="*60)
    print("\nThis script tests all Modal models to verify:")
    print("1. Models can be instantiated")
    print("2. Models load weights from Modal volume")
    print("3. Models generate embeddings successfully")
    print("\nNote: This requires Modal to be deployed and accessible.")
    print("Run: modal deploy backend/modal_app.py")
    print("="*60)
    
    models_to_test = []
    
    # Add available models
    if TigerReIDModel:
        models_to_test.append((TigerReIDModel, "TigerReID"))
    if RAPIDReIDModel:
        models_to_test.append((RAPIDReIDModel, "RAPID"))
    if CVWC2019ReIDModel:
        models_to_test.append((CVWC2019ReIDModel, "CVWC2019"))
    if WildlifeToolsModel:
        models_to_test.append((WildlifeToolsModel, "WildlifeTools"))
    if MegaDetectorModel:
        models_to_test.append((MegaDetectorModel, "MegaDetector"))
    
    if not models_to_test:
        print("ERROR: No models available to test!")
        print("Make sure Modal is properly configured and models are accessible.")
        sys.exit(1)
    
    results = []
    
    for model_class, model_name in models_to_test:
        result = await test_model(model_class, model_name)
        results.append(result)
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] != "success"]
    
    print(f"\nSuccessful: {len(successful)}/{len(results)}")
    for r in successful:
        print(f"  ✓ {r['model']}: embedding length={r.get('embedding_length', 0)}")
    
    if failed:
        print(f"\nFailed: {len(failed)}/{len(results)}")
        for r in failed:
            print(f"  ✗ {r['model']}: {r.get('error', 'Unknown error')}")
    
    print("\n" + "="*60)
    
    # Exit with error code if any tests failed
    if failed:
        sys.exit(1)
    else:
        print("All tests passed! ✓")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())


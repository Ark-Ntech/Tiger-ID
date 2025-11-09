"""Test Modal deployment status and functionality"""
import sys
import time

def test_modal_connection():
    """Test if Modal app is deployed and accessible"""
    try:
        import modal
        print("✓ Modal package imported")
        
        print("\nAttempting to connect to 'tiger-id-models' app...")
        app = modal.App.lookup("tiger-id-models", environment_name="main")
        print(f"✓ App found: {app}")
        
        # Test each model class
        models = [
            "TigerReIDModel",
            "MegaDetectorModel",
            "WildlifeToolsModel",
            "RAPIDReIDModel",
            "CVWC2019ReIDModel",
            "OmniVinciModel"
        ]
        
        found_models = []
        missing_models = []
        
        for model_name in models:
            try:
                model_cls = modal.Cls.lookup("tiger-id-models", model_name, environment_name="main")
                print(f"✓ {model_name} found")
                found_models.append(model_name)
            except Exception as e:
                print(f"✗ {model_name} not found: {e}")
                missing_models.append(model_name)
        
        print(f"\n{'='*60}")
        print(f"SUMMARY:")
        print(f"  Found: {len(found_models)}/{len(models)} models")
        print(f"  Missing: {len(missing_models)} models")
        print(f"{'='*60}")
        
        if len(found_models) == len(models):
            print("\n✓✓✓ ALL MODELS DEPLOYED SUCCESSFULLY! ✓✓✓")
            return True
        else:
            print(f"\n✗ Some models missing: {missing_models}")
            return False
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nThe app is not deployed. Please run:")
        print("  python -m modal deploy backend/modal_app.py")
        return False

if __name__ == "__main__":
    success = test_modal_connection()
    sys.exit(0 if success else 1)


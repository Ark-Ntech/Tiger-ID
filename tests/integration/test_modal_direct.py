"""Test Modal deployment directly"""
import modal
from pathlib import Path

# Try to connect to the deployed app
try:
    print("Connecting to Modal app 'tiger-id-models'...")
    
    # Try to look up the app
    app = modal.App.lookup("tiger-id-models", environment_name="main")
    
    print(f"✓ Found app: {app}")
    
    # Try to get the MegaDetectorModel class
    print("\nLooking for MegaDetectorModel...")
    MegaDetectorModel = modal.Cls.lookup("tiger-id-models", "MegaDetectorModel", environment_name="main")
    
    print(f"✓ Found MegaDetectorModel: {MegaDetectorModel}")
    
    print("\n✓ Modal deployment is accessible!")
    print("The functions are deployed and can be called.")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nThis means the deployment didn't complete successfully.")
    print("The app needs to be deployed with: modal deploy backend/modal_app.py")


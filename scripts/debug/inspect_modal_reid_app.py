"""Inspect the reid Modal app in detail"""

import sys
import os

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import modal
import asyncio

async def inspect_reid_app():
    print("="*70)
    print("INSPECTING MODAL 'reid' APP")
    print("="*70)
    print()

    # Try to get the App object
    try:
        print("[1] Looking up 'reid' app by name...")
        # Note: modal.App.from_name() is for referencing deployed apps
        app = modal.App.lookup("reid", create_if_missing=False)
        print(f"[OK] App found: {app}")
        print(f"     Type: {type(app)}")
        print()
    except Exception as e:
        print(f"[FAIL] Could not look up app: {e}")
        print()

    # Try to get the TigerReIDModel class
    print("[2] Looking up TigerReIDModel class...")
    try:
        cls = modal.Cls.from_name("reid", "TigerReIDModel")
        print(f"[OK] Class found: {cls}")
        print(f"     Type: {type(cls)}")
        print(f"     Has _is_hydrated: {hasattr(cls, '_is_hydrated')}")
        if hasattr(cls, '_is_hydrated'):
            print(f"     Is hydrated: {cls._is_hydrated}")
        print()
    except Exception as e:
        print(f"[FAIL] Could not look up class: {e}")
        import traceback
        traceback.print_exc()
        print()
        return

    # Try to manually hydrate the class
    print("[3] Attempting to manually hydrate class...")
    try:
        await cls.hydrate()
        print("[OK] Hydration succeeded")
        print(f"     Has _is_hydrated: {hasattr(cls, '_is_hydrated')}")
        if hasattr(cls, '_is_hydrated'):
            print(f"     Is hydrated: {cls._is_hydrated}")
        print()
    except Exception as e:
        print(f"[FAIL] Hydration failed: {e}")
        import traceback
        traceback.print_exc()
        print()

    # Try to create an instance
    print("[4] Creating instance...")
    try:
        instance = cls()
        print(f"[OK] Instance created: {instance}")
        print(f"     Type: {type(instance)}")
        print()
    except Exception as e:
        print(f"[FAIL] Could not create instance: {e}")
        import traceback
        traceback.print_exc()
        print()
        return

    # Try to access the generate_embedding method
    print("[5] Accessing generate_embedding method...")
    try:
        method = instance.generate_embedding
        print(f"[OK] Method accessed: {method}")
        print(f"     Type: {type(method)}")
        print(f"     Has remote: {hasattr(method, 'remote')}")
        if hasattr(method, 'remote'):
            print(f"     remote type: {type(method.remote)}")
            print(f"     Has aio: {hasattr(method.remote, 'aio')}")
        print()
    except Exception as e:
        print(f"[FAIL] Could not access method: {e}")
        import traceback
        traceback.print_exc()
        print()

    # Try to call the method
    print("[6] Attempting to call method (without arguments)...")
    try:
        # Just try to access the callable, don't actually call it
        callable_method = method.remote.aio
        print(f"[OK] Method callable accessed: {callable_method}")
        print(f"     Type: {type(callable_method)}")
        print()
    except Exception as e:
        print(f"[FAIL] Could not access callable: {e}")
        import traceback
        traceback.print_exc()
        print()

if __name__ == "__main__":
    asyncio.run(inspect_reid_app())

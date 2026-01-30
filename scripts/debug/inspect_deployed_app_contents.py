"""Try to inspect what's actually deployed in the Modal apps"""

import sys
import os

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import modal
import asyncio

async def inspect_app(app_name):
    print(f"\n{'='*70}")
    print(f"Inspecting app: {app_name}")
    print('='*70)

    try:
        # Look up the app
        app = modal.App.lookup(app_name, create_if_missing=False)
        print(f"✓ App found: {app}")

        # Try to access app internals
        print(f"\nApp object attributes:")
        interesting_attrs = ['name', 'description', '_all_functions', '_function_mounts',
                            '_registered_functions', '_registered_classes', 'registered_functions',
                            'registered_classes', '_object_handles']

        for attr in interesting_attrs:
            if hasattr(app, attr):
                try:
                    value = getattr(app, attr)
                    if callable(value):
                        print(f"  {attr}: <callable>")
                    elif isinstance(value, (list, dict, set)):
                        print(f"  {attr}: {type(value).__name__} with {len(value)} items")
                        if len(value) > 0 and len(value) < 20:
                            for item in (list(value) if isinstance(value, (set, dict)) else value):
                                print(f"    - {item}")
                    else:
                        print(f"  {attr}: {value}")
                except Exception as e:
                    print(f"  {attr}: <error: {e}>")

        # Try to get app ID
        if hasattr(app, 'app_id'):
            print(f"\nApp ID: {app.app_id}")

        # Try to call any methods that might list contents
        if hasattr(app, 'list_functions'):
            try:
                funcs = await app.list_functions()
                print(f"\nFunctions: {funcs}")
            except Exception as e:
                print(f"\nCouldn't list functions: {e}")

    except Exception as e:
        print(f"✗ Failed to inspect app: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("="*70)
    print("INSPECTING DEPLOYED MODAL APPS")
    print("="*70)

    apps = ["reid", "detector", "vlm", "tiger-id-models"]

    for app_name in apps:
        await inspect_app(app_name)

    print(f"\n{'='*70}")
    print("SUMMARY")
    print('='*70)
    print("\nThe apps exist but we need to find what classes/functions")
    print("are actually registered in them. Modal may not expose this")
    print("information through the Python SDK.")

if __name__ == "__main__":
    asyncio.run(main())

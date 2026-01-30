"""Test looking up classes with different environment settings"""

import sys
import os
import asyncio

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import modal

async def test_environments():
    print("="*70)
    print("TESTING DIFFERENT ENVIRONMENT LOOKUPS")
    print("="*70)
    print()

    apps_to_test = ["reid", "tiger-id-models"]
    environments_to_test = [None, "main", "dev", "prod", ""]

    for app_name in apps_to_test:
        print(f"\n{'='*70}")
        print(f"Testing app: {app_name}")
        print('='*70)

        for env in environments_to_test:
            env_str = f"'{env}'" if env is not None else "None (default)"
            print(f"\n  Environment: {env_str}")
            try:
                # Try to look up TigerReIDModel with different environments
                if env is None:
                    cls = modal.Cls.from_name(app_name, "TigerReIDModel")
                else:
                    cls = modal.Cls.from_name(app_name, "TigerReIDModel", environment_name=env)

                print(f"    [OK] Class reference created")

                # Try to hydrate
                await cls.hydrate()
                print(f"    [✅ SUCCESS] Hydration worked with environment: {env_str}")

                # If we got here, this is the right combination!
                print(f"\n    🎯 FOUND WORKING COMBINATION:")
                print(f"       App: '{app_name}'")
                print(f"       Environment: {env_str}")

            except modal.exception.NotFoundError as e:
                error_msg = str(e)
                if "not found in environment" in error_msg:
                    print(f"    [X] App not found in this environment")
                elif "not found in app" in error_msg:
                    print(f"    [X] Class not found in app")
                else:
                    print(f"    [X] {error_msg}")
            except Exception as e:
                print(f"    [X] Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_environments())

"""List what's actually in the reid app"""

import sys
import os

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import modal

print("="*70)
print("LISTING CONTENTS OF 'reid' APP")
print("="*70)
print()

try:
    # Look up the app
    app = modal.App.lookup("reid", create_if_missing=False)
    print(f"App: {app}")
    print(f"App name: {app.name if hasattr(app, 'name') else 'N/A'}")
    print()

    # Try to list all objects/attributes
    print("App attributes:")
    for attr in dir(app):
        if not attr.startswith('_'):
            try:
                value = getattr(app, attr)
                print(f"  {attr}: {type(value).__name__}")
            except:
                print(f"  {attr}: <error accessing>")
    print()

    # Try to access registered objects
    if hasattr(app, '_all_functions'):
        print("Functions:")
        for func in app._all_functions:
            print(f"  - {func}")

    if hasattr(app, '_all_classes'):
        print("Classes:")
        for cls in app._all_classes:
            print(f"  - {cls}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

"""Check all deployed Modal apps and their classes"""

import sys
import os

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import modal

# Apps to check
apps = {
    'vlm': ['OmniVinciModel'],
    'detector': ['MegaDetectorModel'],
    'reid': ['TigerReIDModel', 'WildlifeToolsModel', 'RAPIDReIDModel', 'CVWC2019ReIDModel'],
}

print("="*70)
print("CHECKING DEPLOYED MODAL APPS")
print("="*70)
print()

results = {}

for app_name, class_names in apps.items():
    print(f"\nApp: {app_name}")
    print("-" * 40)
    results[app_name] = {}

    for class_name in class_names:
        try:
            cls = modal.Cls.from_name(app_name, class_name)
            print(f"  [OK] {class_name}")
            results[app_name][class_name] = True
        except Exception as e:
            print(f"  [FAIL] {class_name}: {str(e)[:60]}")
            results[app_name][class_name] = False

print()
print("="*70)
print("SUMMARY")
print("="*70)
print()

for app_name, classes in results.items():
    found = sum(1 for v in classes.values() if v)
    total = len(classes)
    print(f"{app_name}: {found}/{total} classes found")

print()

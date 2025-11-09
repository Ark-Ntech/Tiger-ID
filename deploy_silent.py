"""Deploy Modal app with live output streaming and Windows encoding handling"""
import subprocess
import sys
import os
import re

# Set UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

print("Starting Modal deployment...")
print("This may take 5-10 minutes for first-time image builds.")
print("=" * 80)
print("")

def clean_line(line):
    """Remove problematic Unicode characters for Windows console"""
    if line is None:
        return ""
    # Replace box-drawing and special characters with ASCII equivalents
    replacements = {
        '\u250c': '+', '\u2510': '+', '\u2514': '+', '\u2518': '+',
        '\u251c': '+', '\u2524': '+', '\u252c': '+', '\u2534': '+',
        '\u253c': '+', '\u2500': '-', '\u2502': '|', '\u2501': '=',
        '\u2503': '|', '\u254b': '+', '\u2550': '=', '\u2551': '|',
        '\u2554': '+', '\u2557': '+', '\u255a': '+', '\u255d': '+',
        '\u2560': '+', '\u2563': '+', '\u2566': '+', '\u2569': '+',
        '\u256c': '+', '\u2580': '#', '\u2584': '#', '\u2588': '#',
        '\u258c': '#', '\u2590': '#', '\u2591': '.', '\u2592': ':',
        '\u2593': '#', '\u25a0': '#', '\u25cf': '*', '\u2717': 'x',
        '\u2713': 'OK', '\u2714': 'OK', '\u27a4': '=>',
    }
    for old, new in replacements.items():
        line = line.replace(old, new)
    # Remove any remaining non-ASCII characters
    line = re.sub(r'[^\x00-\x7F]+', '?', line)
    return line

# Run deployment with live output streaming
try:
    process = subprocess.Popen(
        [sys.executable, "-m", "modal", "deploy", "backend/modal_app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        bufsize=1,  # Line buffered
        universal_newlines=True
    )
    
    # Stream output line by line
    for line in process.stdout:
        cleaned = clean_line(line.rstrip())
        if cleaned:  # Only print non-empty lines
            print(cleaned)
    
    # Wait for process to complete
    return_code = process.wait()
    
    print("")
    print("=" * 80)
    print(f"Exit code: {return_code}")
    
    if return_code == 0:
        print("\n[OK] Deployment completed successfully!")
        
        # Test if app is accessible
        print("\nTesting app accessibility...")
        import modal
        try:
            app = modal.App.lookup("tiger-id-models", environment_name="main")
            print(f"[OK] App is accessible: {app}")
            
            # Try to list model classes
            print("\nLooking up model classes...")
            models = [
                "TigerReIDModel",
                "MegaDetectorModel", 
                "WildlifeToolsModel",
                "RAPIDReIDModel",
                "CVWC2019ReIDModel",
                "OmniVinciModel"
            ]
            found = 0
            for model_name in models:
                try:
                    modal.Cls.lookup("tiger-id-models", model_name, environment_name="main")
                    print(f"  [OK] {model_name}")
                    found += 1
                except:
                    print(f"  [WARN] {model_name} not found")
            
            print(f"\n[OK] Found {found}/{len(models)} models")
            
        except Exception as e:
            print(f"[WARN] App not fully accessible: {e}")
            print("Deployment may still be processing. Wait 30 seconds and try again.")
    else:
        print(f"\n[ERROR] Deployment failed with exit code {return_code}")
        sys.exit(return_code)
        
except KeyboardInterrupt:
    print("\n\n[WARN] Deployment interrupted by user")
    sys.exit(130)
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
    sys.exit(1)


"""
Script to upload model weights to Modal volume.

This script allows you to upload trained model weights directly to Modal volumes
for CVWC2019 and RAPID models. It can download weights automatically or upload
manually downloaded weights.

Usage:
    # Download and upload automatically (if available):
    modal run scripts/upload_weights_to_modal.py --model cvwc2019 --download
    modal run scripts/upload_weights_to_modal.py --model rapid --download
    
    # Upload manually downloaded weights:
    modal run scripts/upload_weights_to_modal.py --model cvwc2019 --weights path/to/best_model.pth
    modal run scripts/upload_weights_to_modal.py --model rapid --weights path/to/model.pth
    
    # List available models and their status:
    modal run scripts/upload_weights_to_modal.py --list
"""

import argparse
import sys
import os
import urllib.request
import tempfile
import shutil
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    requests = None

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import modal
from backend.modal_app import app, models_volume, MODEL_CACHE_DIR


# Create Modal function to handle volume writes (streams directly to volume)
@app.function(
    volumes={MODEL_CACHE_DIR: models_volume},
    timeout=600,
)
def upload_weights_to_volume_streaming(model_name: str, download_url: str, volume_path: str):
    """Download weights directly from URL and write to Modal volume (no local storage)."""
    import requests
    from pathlib import Path
    
    # Ensure directory exists
    volume_file = Path(volume_path)
    volume_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading {model_name} weights from: {download_url}")
    print(f"Writing directly to Modal volume: {volume_path}")
    
    # Stream download directly to volume (no local storage)
    with requests.get(download_url, stream=True, timeout=600) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        downloaded = 0
        
        with open(volume_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}% ({downloaded / (1024*1024):.2f} MB / {total_size / (1024*1024):.2f} MB)", end='', flush=True)
    
    print(f"\n✓ Downloaded and saved to Modal volume: {volume_path}")
    print(f"  File size: {volume_file.stat().st_size / (1024*1024):.2f} MB")
    
    # Commit volume
    models_volume.commit()
    
    return f"Uploaded {model_name} weights to {volume_path}"


# Create Modal function to handle volume writes from bytes (for local files)
@app.function(
    volumes={MODEL_CACHE_DIR: models_volume},
    timeout=300,
)
def upload_weights_to_volume(model_name: str, weight_data: bytes, volume_path: str):
    """Upload weight data to Modal volume from bytes."""
    from pathlib import Path
    
    # Ensure directory exists
    volume_file = Path(volume_path)
    volume_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write file directly to volume
    with open(volume_file, 'wb') as f:
        f.write(weight_data)
    
    # Commit volume
    models_volume.commit()
    
    return f"Uploaded {model_name} weights to {volume_path}"


def upload_cvwc2019_weights(local_weight_path: Path):
    """Upload CVWC2019 weights to Modal volume."""
    print(f"Uploading CVWC2019 weights from {local_weight_path}...")
    
    if not local_weight_path.exists():
        raise FileNotFoundError(f"Weight file not found: {local_weight_path}")
    
    # Read weights
    with open(local_weight_path, 'rb') as f:
        weight_data = f.read()
    
    # Upload to Modal volume using Modal function
    volume_path = f"{MODEL_CACHE_DIR}/cvwc2019/best_model.pth"
    
    # Call Modal function to upload
    result = upload_weights_to_volume.remote(
        model_name="cvwc2019",
        weight_data=weight_data,
        volume_path=volume_path
    )
    
    print(f"✓ Successfully uploaded CVWC2019 weights to Modal volume: {volume_path}")
    return volume_path


def download_cvwc2019_weights() -> Optional[str]:
    """
    Get CVWC2019 weights download URL from GitHub repository.
    Returns URL to download directly to Modal volume (no local storage).
    
    Note: According to the README (data/models/cvwc2019/README.md), trained weights are on Baidu Pan:
    https://pan.baidu.com/s/1c9kJXWLN-g-GHSAz5EHpzQ
    These require manual download as Baidu Pan requires Chinese account.
    """
    print("Finding CVWC2019 weights download URL...")
    
    if not requests:
        print("ERROR: 'requests' library not installed. Install with: pip install requests")
        return None
    
    # GitHub repository
    repo_owner = "LcenArthas"
    repo_name = "CWCV2019-Amur-Tiger-Re-ID"
    
    try:
        # Try to download from GitHub releases first
        releases_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
        print(f"Checking GitHub releases: {releases_url}")
        
        response = requests.get(releases_url, timeout=10)
        if response.status_code == 200:
            releases = response.json()
            if releases:
                print(f"Found {len(releases)} releases")
                # Try to download from latest release
                latest_release = releases[0]
                for asset in latest_release.get('assets', []):
                    if 'model' in asset['name'].lower() or 'weight' in asset['name'].lower() or asset['name'].endswith('.pth') or asset['name'].endswith('.zip'):
                        download_url = asset['browser_download_url']
                        print(f"Found weight file in release: {asset['name']}")
                        print(f"Download URL: {download_url}")
                        return download_url
        
        # Check repository contents for weight files
        print("No releases found. Checking repository contents...")
        contents_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"
        contents_response = requests.get(contents_url, timeout=10)
        if contents_response.status_code == 200:
            contents = contents_response.json()
            # Look for trained_weight or checkpoints directories
            for item in contents:
                if item['type'] == 'dir' and ('weight' in item['name'].lower() or 'checkpoint' in item['name'].lower()):
                    print(f"Found directory: {item['name']}")
                    # Could check subdirectory, but trained weights are on Baidu Pan
        
        # Note: Trained weights are on Baidu Pan, not in GitHub repo
        print("\n" + "="*80)
        print("CVWC2019 Trained Weights Information")
        print("="*80)
        print("According to the repository README, trained weights are on Baidu Pan:")
        print("  Link: https://pan.baidu.com/s/1c9kJXWLN-g-GHSAz5EHpzQ")
        print("\nBaidu Pan requires:")
        print("  - Chinese account registration")
        print("  - Manual download")
        print("\nAfter downloading, use:")
        print("  modal run scripts/upload_weights_to_modal.py --model cvwc2019 --weights <path/to/weights.pth>")
        print("="*80)
        return None
        
    except Exception as e:
        print(f"ERROR: Failed to find weights: {e}")
        import traceback
        traceback.print_exc()
        return None


def download_rapid_weights() -> Optional[str]:
    """
    Get RAPID weights download URL from repository.
    Returns URL to download directly to Modal volume (no local storage).
    
    Note: RAPID weights may need to be obtained from paper repository.
    """
    print("Finding RAPID weights download URL from repository...")
    
    if not requests:
        print("ERROR: 'requests' library not installed. Install with: pip install requests")
        return None
    
    # RAPID repository URLs to check
    # Note: RAPID for animal re-identification may not have a public repository
    # The name "RAPID" is also used for other projects (river routing, etc.)
    possible_repos = [
        ("rapid-reid", "rapid"),
        ("rapid-reid", "RAPID"),
    ]
    
    for owner, repo in possible_repos:
        try:
            repo_url = f"https://github.com/{owner}/{repo}"
            print(f"Checking repository: {repo_url}")
            
            # Check if repository exists
            response = requests.get(f"https://api.github.com/repos/{owner}/{repo}", timeout=10)
            if response.status_code == 200:
                print(f"Found repository: {repo_url}")
                
                # Check releases
                releases_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
                releases_response = requests.get(releases_url, timeout=10)
                if releases_response.status_code == 200:
                    releases = releases_response.json()
                    if releases:
                        latest_release = releases[0]
                        for asset in latest_release.get('assets', []):
                            if 'model' in asset['name'].lower() or 'weight' in asset['name'].lower() or asset['name'].endswith('.pth'):
                                download_url = asset['browser_download_url']
                                print(f"Found weight file in release: {asset['name']}")
                                return download_url
                
                # Check if weights are in repository
                print("No releases found. Checking repository contents...")
                break
        except Exception as e:
            continue
    
    print("Could not find RAPID weights in public repositories.")
    print("Note: RAPID trained weights may require manual download from paper repository.")
    print("Please check the RAPID paper for repository links or contact authors.")
    print("Use --weights option after downloading manually.")
    return None


def upload_rapid_weights(local_weight_path: Path):
    """Upload RAPID weights to Modal volume."""
    print(f"Uploading RAPID weights from {local_weight_path}...")
    
    if not local_weight_path.exists():
        raise FileNotFoundError(f"Weight file not found: {local_weight_path}")
    
    # Read weights
    with open(local_weight_path, 'rb') as f:
        weight_data = f.read()
    
    # Upload to Modal volume using Modal function
    volume_path = f"{MODEL_CACHE_DIR}/rapid/checkpoints/model.pth"
    
    # Call Modal function to upload
    result = upload_weights_to_volume.remote(
        model_name="rapid",
        weight_data=weight_data,
        volume_path=volume_path
    )
    
    print(f"✓ Successfully uploaded RAPID weights to Modal volume: {volume_path}")
    return volume_path


def list_models():
    """List available models and their weight status."""
    print("=" * 80)
    print("Model Weights Status")
    print("=" * 80)
    print()
    
    models = {
        'cvwc2019': {
            'name': 'CVWC2019',
            'description': 'Part-pose guided tiger re-identification',
            'volume_path': f'{MODEL_CACHE_DIR}/cvwc2019/best_model.pth',
            'download_info': 'Download from: https://github.com/LcenArthas/CWCV2019-Amur-Tiger-Re-ID\n  Check README.md for Baidu Pan links'
        },
        'rapid': {
            'name': 'RAPID',
            'description': 'Real-time animal pattern re-identification',
            'volume_path': f'{MODEL_CACHE_DIR}/rapid/checkpoints/model.pth',
            'download_info': 'Download from paper repository or contact authors'
        }
    }
    
    for model_key, model_info in models.items():
        print(f"Model: {model_info['name']}")
        print(f"  Description: {model_info['description']}")
        print(f"  Volume Path: {model_info['volume_path']}")
        print(f"  Download: {model_info['download_info']}")
        print()
    
    print("=" * 80)
    print("\nTo upload weights:")
    print("  modal run scripts/upload_weights_to_modal.py --model <model> --weights <path>")
    print("  modal run scripts/upload_weights_to_modal.py --model <model> --download")


def main():
    """Main function to upload weights."""
    parser = argparse.ArgumentParser(
        description="Upload model weights to Modal volume"
    )
    parser.add_argument(
        '--model',
        type=str,
        choices=['cvwc2019', 'rapid'],
        help='Model to upload weights for'
    )
    parser.add_argument(
        '--weights',
        type=str,
        help='Path to local weight file'
    )
    parser.add_argument(
        '--download',
        action='store_true',
        help='Attempt to download weights automatically'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available models and their status'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run - check if file exists but do not upload'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_models()
        return
    
    if not args.model:
        print("ERROR: --model is required (or use --list to see available models)")
        parser.print_help()
        sys.exit(1)
    
    weight_path = None
    
    # Try to download if requested
    if args.download:
        print(f"\n{'='*80}")
        print(f"Downloading {args.model.upper()} weights from repository...")
        print(f"{'='*80}\n")
        
        download_url = None
        if args.model == 'cvwc2019':
            download_url = download_cvwc2019_weights()
        elif args.model == 'rapid':
            download_url = download_rapid_weights()
        
        if download_url:
            # Stream directly to Modal volume (no local storage)
            print(f"\n{'='*80}")
            print(f"Streaming {args.model.upper()} weights directly to Modal volume...")
            print(f"{'='*80}\n")
            
            volume_path = f"{MODEL_CACHE_DIR}/{args.model}/best_model.pth" if args.model == 'cvwc2019' else f"{MODEL_CACHE_DIR}/rapid/checkpoints/model.pth"
            
            try:
                result = upload_weights_to_volume_streaming.remote(
                    model_name=args.model,
                    download_url=download_url,
                    volume_path=volume_path
                )
                print(f"\n✓ Successfully uploaded {args.model} weights to Modal volume!")
                print(f"  Volume path: {volume_path}")
                print("\nNext steps:")
                print("  1. Deploy Modal app: modal deploy backend/modal_app.py")
                print("  2. Test models: python scripts/test_modal_models.py")
                return
            except Exception as e:
                print(f"ERROR: Failed to upload weights to Modal: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
        else:
            print(f"\nERROR: Could not find {args.model} weights download URL.")
            print("Please download weights manually and use --weights option.")
            sys.exit(1)
    elif args.weights:
        weight_path = Path(args.weights)
    else:
        print("ERROR: Either --weights or --download must be specified")
        parser.print_help()
        sys.exit(1)
    
    if not weight_path or not weight_path.exists():
        print(f"ERROR: Weight file not found: {weight_path}")
        print("\nTo download weights:")
        if args.model == 'cvwc2019':
            print("  CVWC2019: Download from https://github.com/LcenArthas/CWCV2019-Amur-Tiger-Re-ID")
            print("  Check data/models/cvwc2019/README.md for Baidu Pan links")
        elif args.model == 'rapid':
            print("  RAPID: Download from paper repository or contact authors")
        sys.exit(1)
    
    if args.dry_run:
        print(f"DRY RUN: Would upload {args.model} weights from {weight_path}")
        print(f"  File size: {weight_path.stat().st_size / (1024*1024):.2f} MB")
        return
    
    try:
        if args.model == 'cvwc2019':
            upload_cvwc2019_weights(weight_path)
        elif args.model == 'rapid':
            upload_rapid_weights(weight_path)
        
        print("\n✓ Upload complete!")
        print("\nNext steps:")
        print("  1. Deploy Modal app: modal deploy backend/modal_app.py")
        print("  2. Test models: python scripts/test_modal_models.py")
        
    except Exception as e:
        print(f"ERROR: Failed to upload weights: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


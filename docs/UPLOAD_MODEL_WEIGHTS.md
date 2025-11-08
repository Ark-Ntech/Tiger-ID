# Uploading Model Weights to Modal

This guide explains how to upload model weights to Modal for CVWC2019 and RAPID models.

## Quick Start

### List Available Models

```bash
modal run scripts/upload_weights_to_modal.py --list
```

### Upload Weights

#### Option 1: Automatic Download (if weights exist locally)

```bash
modal run scripts/upload_weights_to_modal.py --model cvwc2019 --download
modal run scripts/upload_weights_to_modal.py --model rapid --download
```

#### Option 2: Manual Upload

```bash
modal run scripts/upload_weights_to_modal.py --model cvwc2019 --weights path/to/best_model.pth
modal run scripts/upload_weights_to_modal.py --model rapid --weights path/to/model.pth
```

## CVWC2019 Weights

### Downloading Weights

CVWC2019 trained weights need to be downloaded manually:

1. **From GitHub Repository**
   - Repository: https://github.com/LcenArthas/CWCV2019-Amur-Tiger-Re-ID
   - Check the README.md for download links

2. **From Baidu Pan** (may require Chinese account)
   - Check `data/models/cvwc2019/README.md` for Baidu Pan links
   - Download the trained model weights (usually named `best_model.pth`)

3. **Common Locations to Check**
   - `data/models/cvwc2019/pretrained_model/best_model.pth`
   - `data/models/cvwc2019/checkpoints/best_model.pth`
   - `data/models/cvwc2019/logs/best_model.pth`

### Uploading to Modal

Once you have the weights file:

```bash
modal run scripts/upload_weights_to_modal.py --model cvwc2019 --weights path/to/best_model.pth
```

The weights will be uploaded to: `/models/cvwc2019/best_model.pth` in the Modal volume.

## RAPID Weights

### Downloading Weights

RAPID trained weights may need to be obtained from:

1. **Paper Repository** (if available)
   - Check the RAPID paper for repository links
   - Download trained model weights

2. **Contact Authors**
   - If weights are not publicly available, contact the paper authors

3. **Common Locations to Check**
   - `data/models/rapid/checkpoints/model.pth`

### Uploading to Modal

Once you have the weights file:

```bash
modal run scripts/upload_weights_to_modal.py --model rapid --weights path/to/model.pth
```

The weights will be uploaded to: `/models/rapid/checkpoints/model.pth` in the Modal volume.

## Verification

After uploading weights, verify they're in Modal:

1. **Deploy Modal App**
   ```bash
   modal deploy backend/modal_app.py
   ```

2. **Test Models**
   ```bash
   python scripts/test_modal_models.py
   ```

3. **Check Model Loading**
   - The models should load weights from Modal volume automatically
   - Check logs for "Loaded [model] weights from [path]" messages

## Troubleshooting

### Weights Not Found

If weights are not found locally:

1. **Check Local Paths**
   - Run `--download` to check common locations
   - Manually check `data/models/` directories

2. **Download Manually**
   - Follow download instructions above
   - Place weights in expected locations
   - Then run upload script

### Upload Fails

If upload fails:

1. **Check Modal Connection**
   - Ensure Modal CLI is authenticated: `modal token new`
   - Check Modal app is deployed

2. **Check File Size**
   - Large files may take time to upload
   - Check Modal volume size limits

3. **Check File Format**
   - Ensure weights are in `.pth` format
   - Verify file is not corrupted

### Model Not Loading Weights

If model doesn't load weights after upload:

1. **Check Volume Path**
   - Verify weights are in correct path in Modal volume
   - Check `MODEL_CACHE_DIR` matches volume mount

2. **Check Model Code**
   - Verify model loading code checks for weights
   - Check error messages in logs

3. **Redeploy**
   - Redeploy Modal app after uploading weights
   - Restart Modal functions

## Notes

- **ImageNet Pretrained**: If trained weights are not available, models will use ImageNet pretrained weights as fallback
- **Volume Persistence**: Modal volumes persist across deployments, so weights only need to be uploaded once
- **Volume Size**: Check Modal volume size limits for large weight files
- **Version Control**: Consider versioning weights using the model version management system


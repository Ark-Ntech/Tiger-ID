# Tiger Dataset Download Guide

## Critical Issue

The application currently has **0 tigers** in the database because the ATRW (Amur Tiger Re-identification in the Wild) dataset has not been downloaded.

## Required Dataset: ATRW

**ATRW** is the primary dataset for tiger re-identification:
- **92 individual tigers**
- **3,649 images** (or 8,076 videos that can be extracted to images)
- **Source:** Amur Tiger Re-identification in the Wild
- **License:** CC BY-NC-SA 4.0

## Download Options

### Option 1: LILA Science (Recommended)
1. Visit: https://lila.science/datasets/atrw
2. Download the dataset
3. Extract to: `data/models/atrw/images/`
4. Expected structure:
   ```
   data/models/atrw/images/
   ├── tiger_001/
   │   ├── image1.jpg
   │   ├── image2.jpg
   │   └── ...
   ├── tiger_002/
   │   └── ...
   └── ...
   ```

### Option 2: Kaggle
1. Visit: https://www.kaggle.com/datasets/quadeer15sh/amur-tiger-reidentification
2. Requires Kaggle account and API setup
3. Download and extract to same location

### Option 3: WildlifeReID-10k (Alternative)
The WildlifeReID-10k dataset includes tiger images:
- **10,772 individual animals** including tigers
- **140,488 images** total
- Download from: https://www.kaggle.com/datasets/wildlifedatasets/wildlifereid-10k
- Extract to: `data/datasets/wildlife-datasets/data/WildlifeReID10k/`

## Automated Download

Use the provided download script:

```bash
# Download ATRW dataset (requires kagglehub)
python scripts/download_datasets.py

# Or download manually (see instructions below)
python scripts/download_datasets.py --no-kaggle
```

**Prerequisites:**
```bash
pip install kagglehub
```

## Manual Download

If automated download fails, follow these steps:

1. **Download ATRW dataset:**
   - Visit: https://lila.science/datasets/atrw
   - Or: https://www.kaggle.com/datasets/quadeer15sh/amur-tiger-reidentification
   - Extract to: `data/models/atrw/images/`

2. **Verify structure:** Ensure images are organized by tiger ID in subdirectories

3. **Run population script:**
   ```bash
   python scripts/populate_production_db.py
   ```

4. **Check results:** The script should report tigers created and images processed

## Expected Output

After successful download and population:
```
✓ Tiger images: X tigers created, Y images processed
```

Instead of:
```
⚠ No tiger directories found
✓ Tiger images: 0 tigers created, 0 images processed
```

## Troubleshooting

### Issue: "No tiger directories found"
- **Cause:** Images directory is empty or structure is wrong
- **Solution:** Verify images are in subdirectories named by tiger ID

### Issue: "ATRW images directory not found"
- **Cause:** Directory doesn't exist
- **Solution:** Create `data/models/atrw/images/` directory

### Issue: Images not processing
- **Cause:** Wrong file format or permissions
- **Solution:** Ensure images are .jpg, .jpeg, .png, .gif, .bmp, or .webp

## Model Weights

The RE-ID model also needs trained weights:
- **File:** `data/models/tiger_reid_model.pth`
- **Status:** Currently using untrained model
- **Impact:** Embeddings may not be accurate

### Download Model Weights

Use the provided download script:

```bash
# Download all model weights
python scripts/download_model_weights.py

# Or download only TigerReIDModel weights
python scripts/download_model_weights.py --tiger-reid-only
```

**Note:** Pre-trained TigerReIDModel weights may not be publicly available. If not available:
1. Train the model using the ATRW dataset
2. Follow training instructions in `backend/models/reid.py`
3. Or use untrained model (ResNet50 ImageNet pretrained) - functional but less accurate


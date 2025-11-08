# CVWC2019 Architecture Implementation Status

## Current Status

The CVWC2019 model is currently implemented with a placeholder ResNet50 architecture. The full architecture requires implementation of the part-pose guided re-identification system described in the CVWC2019 paper.

## Full Architecture Requirements

The CVWC2019 model uses a multi-stream architecture:

### 1. Global Stream
- **Backbone**: ResNet152
- **Purpose**: Extract global features from the entire tiger image
- **Output**: Global feature vector (2048-dim)

### 2. Part Body Stream
- **Backbone**: ResNet34
- **Purpose**: Extract features from tiger body parts (excluding paws)
- **Input**: Cropped body regions
- **Output**: Part body feature vector (512-dim)

### 3. Part Paw Stream
- **Backbone**: ResNet34
- **Purpose**: Extract features from tiger paw patterns
- **Input**: Cropped paw regions
- **Output**: Part paw feature vector (512-dim)

### 4. Feature Fusion Pipeline
- Combine global, part body, and part paw features
- Weighted fusion or concatenation
- Final embedding dimension: 3072-dim (2048 + 512 + 512)

## Implementation Steps

To implement the full CVWC2019 architecture:

1. **Add Model Code to Modal Image**
   ```python
   # Add data/models/cvwc2019 to Modal image
   cvwc2019_image = (
       modal.Image.debian_slim(python_version="3.11")
       .apt_install("git")
       .pip_install(...)
       .run_commands("git clone https://github.com/LcenArthas/CWCV2019-Amur-Tiger-Re-ID /models/cvwc2019")
   )
   ```

2. **Import and Build Model**
   ```python
   from data.models.cvwc2019.modeling import build_model
   from data.models.cvwc2019.config import cfg
   
   # Load config
   cfg.merge_from_file("configs/cvwc2019.yaml")
   
   # Build model
   model = build_model(cfg)
   ```

3. **Load Trained Weights**
   ```python
   weight_path = Path(MODEL_CACHE_DIR) / "cvwc2019" / "best_model.pth"
   checkpoint = torch.load(weight_path, map_location=device)
   model.load_state_dict(checkpoint['state_dict'])
   ```

4. **Implement Part Detection**
   - Use pose estimation to detect body parts
   - Crop body and paw regions
   - Process each region through respective streams

5. **Feature Fusion**
   - Combine features from all three streams
   - Apply learned fusion weights
   - Normalize final embedding

## Current Implementation

The current implementation (`CVWC2019ReIDModel` in `backend/modal_app.py`) uses:
- ResNet50 as a placeholder
- ImageNet pretrained weights
- Simple feature extraction (2048-dim)

## Next Steps

1. **Obtain Model Weights**
   - Download from GitHub: https://github.com/LcenArthas/CWCV2019-Amur-Tiger-Re-ID
   - Check paper supplement for Baidu Pan links
   - Contact authors if needed

2. **Upload Weights to Modal**
   ```bash
   python scripts/upload_weights_to_modal.py --model cvwc2019 --path /path/to/best_model.pth
   ```

3. **Implement Full Architecture**
   - Clone repository code
   - Integrate into Modal app
   - Test with actual weights

## References

- Paper: "Part-Pose Guided Amur Tiger Re-identification" (CVWC2019)
- GitHub: https://github.com/LcenArthas/CWCV2019-Amur-Tiger-Re-ID
- Dataset: ATRW (Amur Tiger Re-identification in the Wild)


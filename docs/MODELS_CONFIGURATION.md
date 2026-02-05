# Models Configuration Summary

This document summarizes all models in the `data/models` directory and their configuration in the `.env` file.

## Models Overview

### 1. **MegaDetector** (Animal Detection)
- **Location**: `data/models/md_v5a.0.0.pt` (or `data/models/megadetector/`)
- **Status**: ✅ Configured
- **Type**: Object detection model for wildlife
- **Source**: GitHub releases or LILA
- **Environment Variables**:
  - `MEGADETECTOR_MODEL_PATH` - Model path (default: `./data/models/md_v5a.0.0.pt`)
  - `MEGADETECTOR_VERSION` - Model version (default: `v5`)

### 2. **Wildlife-Tools / MegaDescriptor-L** (Primary Re-ID)
- **Location**: `data/models/wildlife-tools/`
- **Status**: ✅ Configured - **Best Performer**
- **Type**: MegaDescriptor-L-384 Vision Transformer
- **Embedding Dimension**: 1536
- **Ensemble Weight**: 0.40 (highest)
- **Environment Variables**:
  - `WILDLIFETOOLS_MODEL_PATH` - Model path (default: `./data/models/wildlife-tools/`)
  - `WILDLIFETOOLS_MODEL_TYPE` - Model type: `megadescriptor` or `wildfusion` (default: `megadescriptor`)
  - `WILDLIFETOOLS_ENABLED` - Enable model (default: `true`)

### 3. **CVWC2019** (Part-Pose Tiger Re-ID)
- **Location**: `data/models/cvwc2019/`
- **Status**: ✅ Configured - **Fixed in Phase 1**
- **Type**: Part-pose guided Re-ID model
- **Backbone**: ResNet152 (corrected from placeholder ResNet50)
- **Embedding Dimension**: 2048
- **Ensemble Weight**: 0.30
- **Environment Variables**:
  - `CVWC2019_MODEL_PATH` - Model path (default: `./data/models/cvwc2019/checkpoints/model.pth`)
  - `CVWC2019_ENABLED` - Enable model (default: `true`)

### 4. **TransReID** (Vision Transformer Re-ID)
- **Location**: `data/models/transreid/`
- **Status**: ✅ **NEW** - Added in Phase 2
- **Type**: ViT-Base transformer architecture
- **Embedding Dimension**: 768
- **Ensemble Weight**: 0.20
- **Environment Variables**:
  - `TRANSREID_MODEL_PATH` - Model path (default: `./data/models/transreid/vit_base.pth`)
  - `TRANSREID_ENABLED` - Enable model (default: `true`)
- **Implementation**: `backend/models/transreid.py`

### 5. **MegaDescriptor-B** (Fast Variant)
- **Location**: `data/models/megadescriptor-b/`
- **Status**: ✅ **NEW** - Added in Phase 2
- **Type**: MegaDescriptor-B-224 (smaller, faster variant)
- **Embedding Dimension**: 1024
- **Ensemble Weight**: 0.15
- **Environment Variables**:
  - `MEGADESCRIPTOR_B_MODEL_PATH` - Model path (default: `./data/models/megadescriptor-b/`)
  - `MEGADESCRIPTOR_B_ENABLED` - Enable model (default: `true`)
- **Implementation**: `backend/models/megadescriptor_b.py`

### 6. **TigerReID** (Baseline Siamese Network)
- **Location**: `data/models/tiger_reid_model.pth`
- **Status**: ✅ Configured
- **Type**: ResNet50-based Siamese network
- **Embedding Dimension**: 2048
- **Ensemble Weight**: 0.10
- **Environment Variables**:
  - `REID_MODEL_PATH` - Model path (default: `./data/models/tiger_reid_model.pth`)
  - `EMBEDDING_DIM` - Embedding dimension (default: `2048`)

### 7. **RAPID** (Edge-Optimized Re-ID)
- **Location**: `data/models/rapid/checkpoints/model.pth`
- **Status**: ✅ Configured
- **Type**: Real-time Re-ID model optimized for edge devices
- **Embedding Dimension**: 2048
- **Ensemble Weight**: 0.05 (lowest)
- **Environment Variables**:
  - `RAPID_MODEL_PATH` - Model path (default: `./data/models/rapid/checkpoints/model.pth`)
  - `RAPID_ENABLED` - Enable model (default: `true`)

### 8. **Pose Model** (Tiger Pose Estimation)
- **Location**: `data/models/tiger_pose_model.pth`
- **Status**: ✅ Configured
- **Type**: Pose estimation model for part-based analysis
- **Environment Variables**:
  - `POSE_MODEL_PATH` - Model path (default: `./data/models/tiger_pose_model.pth`)

---

## Embedding Dimensions Summary

| Model | Backbone | Embedding Dim | Ensemble Weight | Calibration Temp |
|-------|----------|---------------|-----------------|------------------|
| wildlife_tools (MegaDescriptor-L) | ViT-L/14 | 1536 | 0.40 | 1.0 (reference) |
| cvwc2019_reid | ResNet152 | 2048 | 0.30 | 0.85 |
| transreid | ViT-Base | 768 | 0.20 | 1.1 |
| megadescriptor_b | ViT-B/16 | 1024 | 0.15 | 1.0 |
| tiger_reid | ResNet50 | 2048 | 0.10 | 0.9 |
| rapid_reid | ResNet50 | 2048 | 0.05 | 0.95 |

---

## Ensemble Configuration

### Environment Variables
```bash
# Ensemble mode: staggered | parallel | weighted
ENSEMBLE_MODE=weighted

# Model-specific weights (optional, defaults to values above)
WILDLIFE_TOOLS_WEIGHT=0.40
CVWC2019_WEIGHT=0.30
TRANSREID_WEIGHT=0.20
MEGADESCRIPTOR_B_WEIGHT=0.15
TIGER_REID_WEIGHT=0.10
RAPID_WEIGHT=0.05

# Enable/disable re-ranking
ENABLE_RERANKING=true
RERANKING_K1=20
RERANKING_K2=6
RERANKING_LAMBDA=0.3

# Confidence calibration
ENABLE_CALIBRATION=true
```

### Ensemble Modes

1. **Staggered** (`staggered`)
   - Sequential execution with early exit
   - Stops if high-confidence match found
   - Best for: Quick identifications with clear matches

2. **Parallel** (`parallel`)
   - All models run simultaneously
   - Majority voting for consensus
   - Best for: Maximum accuracy, unlimited compute

3. **Weighted** (`weighted`) - **Recommended**
   - Combines weighted scoring, calibration, re-ranking
   - Post-processing with K-reciprocal re-ranking
   - Best for: Production use with balanced speed/accuracy

---

## Datasets

### 1. **ATRW Dataset**
- **Location**: `data/models/atrw/`
- **Environment Variable**: `ATRW_DATASET_PATH` (default: `./data/models/atrw/`)

### 2. **MetaWild Dataset**
- **Location**: `data/datasets/metawild/`
- **Environment Variable**: `METAWILD_DATASET_PATH` (default: `./data/datasets/metawild/`)

### 3. **Wildlife Datasets**
- **Location**: `data/datasets/wildlife-datasets/`
- **Environment Variable**: `WILDLIFE_DATASETS_PATH` (default: `./data/datasets/wildlife-datasets/`)

### 4. **Individual Animal Re-ID Dataset**
- **Location**: `data/datasets/individual-animal-reid/`
- **Environment Variable**: `INDIVIDUAL_ANIMAL_REID_PATH` (default: `./data/datasets/individual-animal-reid/`)

---

## General Model Configuration

```bash
# Device configuration
MODEL_DEVICE=cuda
BATCH_SIZE=32

# Modal GPU deployment
MODAL_GPU_TYPE=T4  # T4 for most models, A100 for heavy inference
```

---

## Image Deduplication

The discovery pipeline uses SHA256 content hashing to prevent duplicate images from being processed by the ML ensemble:

- Hashing occurs **before** GPU inference (saves compute)
- Duplicate images are tracked via `content_hash` and `is_duplicate_of` fields
- See `backend/services/image_pipeline_service.py` for implementation

## Installation Notes

### Model Download Script
Use `scripts/download_models.py` to download models:
```bash
python scripts/download_models.py --model megadetector
python scripts/download_models.py --model wildlife_tools
python scripts/download_models.py --model transreid
python scripts/download_models.py --model megadescriptor_b
python scripts/download_models.py --model all
```

### Modal Deployment
Models are deployed via Modal for GPU inference:
```bash
modal deploy backend/modal_app.py
```

---

## Modal Volume Caching

Model weights are cached in Modal volumes for fast cold starts and persistent storage.

### How It Works

1. **First deployment**: Model weights download from HuggingFace/source
2. **Volume storage**: Weights cached in Modal persistent volumes
3. **Subsequent runs**: Loaded from cache (no re-download)
4. **Container restart**: Cache persists across container restarts

### Volume Configuration

Defined in `backend/modal_app.py`:

```python
model_volume = modal.Volume.from_name("tiger-id-model-cache", create_if_missing=True)

@app.function(
    volumes={"/cache": model_volume},
    ...
)
```

### Cache Paths

| Model | Cache Path |
|-------|------------|
| MegaDetector | `/cache/megadetector/` |
| Wildlife-Tools | `/cache/wildlife-tools/` |
| CVWC2019 | `/cache/cvwc2019/` |
| TransReID | `/cache/transreid/` |
| MegaDescriptor-B | `/cache/megadescriptor-b/` |
| TigerReID | `/cache/tiger-reid/` |
| RAPID | `/cache/rapid/` |

### Cache Management

**Check volume size:**
```bash
modal volume list
```

**Clear cache (forces re-download):**
```bash
modal volume delete tiger-id-model-cache
```

### TTL and Eviction

- **Volume TTL**: Persistent (no automatic eviction)
- **Container TTL**: Modal manages container lifecycle
- **Cache invalidation**: Delete volume or redeploy with new paths

---

## Configuration Files

- **`.env.example`** - Contains all model environment variables with defaults
- **`config/settings.yaml`** - YAML configuration file (optional, env vars take precedence)
- **`backend/config/settings.py`** - Pydantic settings models
- **`backend/infrastructure/modal/model_registry.py`** - Model registry with dimensions

---

## Verification

All models in `data/models/` have corresponding environment variables:
- ✅ MegaDetector - Detection
- ✅ Wildlife-Tools (MegaDescriptor-L) - Primary Re-ID
- ✅ CVWC2019 - Part-pose Re-ID
- ✅ TransReID - Transformer Re-ID (NEW)
- ✅ MegaDescriptor-B - Fast variant (NEW)
- ✅ TigerReID - Baseline
- ✅ RAPID - Edge-optimized
- ✅ Pose Model - Pose estimation
- ✅ ATRW Dataset - Training data

---

## Removed Models

### OmniVinci (Removed)
- **Status**: ❌ Removed in Phase 2
- **Reason**: Did not work reliably for tiger re-identification
- **Alternative**: Claude vision API used for visual analysis in reports

---

*Last Updated: February 2026*

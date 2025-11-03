# Models Configuration Summary

This document summarizes all models in the `data/models` directory and their configuration in the `.env` file.

## Models Overview

### 1. **OmniVinci** (Omni-Modal LLM)
- **Location**: `data/models/omnivinci/omnivinci/`
- **Status**: ✅ Installed locally
- **Type**: Multi-modal (vision, audio, text) language model
- **Source**: HuggingFace (`nvidia/omnivinci`)
- **Environment Variables**:
  - `OMNIVINCI_API_KEY` - API key (optional, for cloud API)
  - `OMNIVINCI_USE_LOCAL` - Use local model (default: `false`)
  - `OMNIVINCI_MODEL_PATH` - Local model path (default: `./data/models/omnivinci/omnivinci`)
  - `OMNIVINCI_TORCH_DTYPE` - Torch dtype (default: `torch.float16`)
  - `OMNIVINCI_DEVICE_MAP` - Device mapping (default: `auto`)
  - `OMNIVINCI_NUM_VIDEO_FRAMES` - Video frames (default: `128`)
  - `OMNIVINCI_LOAD_AUDIO` - Load audio in video (default: `true`)
  - `OMNIVINCI_AUDIO_LENGTH` - Audio length (default: `max_3600`)

### 2. **MegaDetector** (Animal Detection)
- **Location**: `data/models/md_v5a.0.0.pt` (or `data/models/megadetector/`)
- **Status**: ✅ Configured
- **Type**: Object detection model for wildlife
- **Source**: GitHub releases or LILA
- **Environment Variables**:
  - `MEGADETECTOR_MODEL_PATH` - Model path (default: `./data/models/md_v5a.0.0.pt`)
  - `MEGADETECTOR_VERSION` - Model version (default: `v5`)

### 3. **CVWC2019** (Tiger Re-ID)
- **Location**: `data/models/cvwc2019/`
- **Status**: ✅ Configured
- **Type**: Part-pose guided Re-ID model
- **Environment Variables**:
  - `CVWC2019_MODEL_PATH` - Model path (default: `./data/models/cvwc2019/checkpoints/model.pth`)
  - `CVWC2019_ENABLED` - Enable model (default: `false`)

### 4. **Wildlife-Tools** (Re-ID Tools)
- **Location**: `data/models/wildlife-tools/`
- **Status**: ✅ Configured
- **Type**: Wildlife Re-ID tools (MegaDescriptor, WildFusion)
- **Environment Variables**:
  - `WILDLIFETOOLS_MODEL_PATH` - Model path (default: `./data/models/wildlife-tools/`)
  - `WILDLIFETOOLS_MODEL_TYPE` - Model type: `megadescriptor` or `wildfusion` (default: `megadescriptor`)
  - `WILDLIFETOOLS_ENABLED` - Enable model (default: `false`)

### 5. **RAPID** (Real-time Animal Pattern re-ID)
- **Location**: `data/models/rapid/checkpoints/model.pth`
- **Status**: ✅ Configured
- **Type**: Real-time Re-ID model
- **Environment Variables**:
  - `RAPID_MODEL_PATH` - Model path (default: `./data/models/rapid/checkpoints/model.pth`)
  - `RAPID_ENABLED` - Enable model (default: `false`)

### 6. **Pose Model** (Tiger Pose Estimation)
- **Location**: `data/models/tiger_pose_model.pth`
- **Status**: ✅ Configured
- **Type**: Pose estimation model
- **Environment Variables**:
  - `POSE_MODEL_PATH` - Model path (default: `./data/models/tiger_pose_model.pth`)

### 7. **Re-ID Model** (Tiger Re-ID)
- **Location**: `data/models/tiger_reid_model.pth`
- **Status**: ✅ Configured
- **Type**: Siamese network Re-ID model
- **Environment Variables**:
  - `REID_MODEL_PATH` - Model path (default: `./data/models/tiger_reid_model.pth`)
  - `EMBEDDING_DIM` - Embedding dimension (default: `512`)

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

## General Model Configuration

- `MODEL_DEVICE` - Device to use (default: `cuda`)
- `BATCH_SIZE` - Batch size for inference (default: `32`)

## Installation Notes

### OmniVinci Installation
The OmniVinci model has been installed locally. To use it:
1. Set `OMNIVINCI_USE_LOCAL=true` in your `.env` file
2. Ensure the model path points to `./data/models/omnivinci/omnivinci`

### Model Download Script
Use `scripts/download_models.py` to download models:
```bash
python scripts/download_models.py --model omnivinci
python scripts/download_models.py --model megadetector
python scripts/download_models.py --model all
```

## Configuration Files

- **`.env.example`** - Contains all model environment variables with defaults
- **`config/settings.yaml`** - YAML configuration file (optional, env vars take precedence)
- **`backend/config/settings.py`** - Pydantic settings models

## Verification

All models in `data/models/` have corresponding environment variables in `.env.example`:
- ✅ OmniVinci - Configured and installed
- ✅ MegaDetector - Configured
- ✅ CVWC2019 - Configured
- ✅ Wildlife-Tools - Configured
- ✅ RAPID - Configured
- ✅ Pose Model - Configured
- ✅ Re-ID Model - Configured
- ✅ ATRW Dataset - Configured

## Next Steps

1. Copy `.env.example` to `.env` if not already done
2. Update `.env` with your specific model paths if they differ from defaults
3. Set `OMNIVINCI_USE_LOCAL=true` to use the locally installed OmniVinci model
4. Enable specific models by setting their `*_ENABLED` flags to `true`


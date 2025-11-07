# Model Preloading Configuration

This document explains how model preloading works in the Tiger ID application.

## Overview

Model preloading allows the application to load RE-ID models into memory on startup, reducing inference latency for the first request.

## Configuration

### Enable Model Preloading

Set the following environment variable:
```env
MODEL_PRELOAD_ON_STARTUP=true
```

Or in `config/settings.yaml`:
```yaml
models:
  preload_on_startup: true
```

### Current Status

Model preloading is **configured but not fully implemented**:
- The configuration option exists (`MODEL_PRELOAD_ON_STARTUP`)
- The lifespan function checks for this setting
- However, actual model loading is deferred to first use

## How It Works

1. **On Startup**: The application checks `MODEL_PRELOAD_ON_STARTUP` setting
2. **If Enabled**: Logs "Preloading models on startup..." message
3. **Actual Loading**: Models are loaded on first use (lazy loading)

## Model Initialization Script

The application also checks for `scripts/init_models.py`:
- If found, runs it during startup (non-blocking)
- Script should download/verify model weights
- 5-minute timeout

## Available Models

Models that can be preloaded:
- **TigerReIDModel** - Primary RE-ID model (`./data/models/tiger_reid_model.pth`)
- **MegaDetector** - Animal detection (`./data/models/md_v5a.0.0.pt`)
- **RAPID** - Real-time Animal Pattern re-ID (if enabled)
- **WildlifeTools** - MegaDescriptor/WildFusion (if enabled)
- **CVWC2019** - CVWC2019 Re-ID model (if enabled)

## Verification

### Check Model Availability

```bash
curl http://localhost:8000/api/v1/models/available
```

### Check Health Endpoint

```bash
curl http://localhost:8000/health
```

The health endpoint should show model status.

## Troubleshooting

### Models Not Loading

1. **Check Model Paths**: Verify model files exist at configured paths
2. **Check Logs**: Look for model loading errors in startup logs
3. **Check GPU**: If using CUDA, verify GPU is available
4. **Check Permissions**: Ensure model files are readable

### Slow Startup

- Model preloading can slow startup (especially with large models)
- Consider disabling for development: `MODEL_PRELOAD_ON_STARTUP=false`
- Models will load on first use instead

### Memory Issues

- Preloading multiple models can use significant memory
- Monitor memory usage
- Consider preloading only essential models

## Future Improvements

1. **Async Preloading**: Load models in background without blocking startup
2. **Selective Preloading**: Preload only specified models
3. **Model Pooling**: Keep multiple model instances for parallel inference
4. **Health Checks**: Verify models are loaded correctly

## Manual Model Loading

Models can be loaded manually via API:
```bash
# Test model availability
curl -X GET http://localhost:8000/api/v1/models/available \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Models will be loaded automatically on first use if not preloaded.


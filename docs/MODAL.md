# Modal GPU Infrastructure

This document consolidates all Modal deployment, configuration, and operational guidance for the Tiger ID system.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Deployed Models](#deployed-models)
- [Architecture Overview](#architecture-overview)
- [Monitoring & Logging](#monitoring--logging)
- [Cost Estimates](#cost-estimates)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Deploy the Modal App

```bash
# Install Modal CLI if needed
pip install modal

# Authenticate with Modal
modal token set --token-id <your-token-id> --token-secret <your-token-secret>

# Deploy all models to Modal
modal deploy backend/modal_app.py
```

**Note:** First deployment takes 5-10 minutes to build Docker images and download model weights. Subsequent deployments are much faster.

### 2. Configure Environment

Add to your `.env` file:

```env
MODAL_ENABLED=true
MODAL_MAX_RETRIES=3
MODAL_TIMEOUT=120
```

### 3. Verify Deployment

```bash
# Check app is deployed
modal app list

# You should see: tiger-id-models
```

### 4. Test Integration

```bash
python -m pytest tests/test_modal_integration.py -v
```

---

## Prerequisites

- Modal CLI installed (`pip install modal`)
- Modal account authenticated (`modal token set`)
- Python 3.11+
- `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` environment variables (for CI/CD)

---

## Environment Configuration

### Required Variables

```env
# Modal Core Settings
MODAL_ENABLED=true
MODAL_WORKSPACE=ark-ntech
MODAL_APP_NAME=tiger-id-models
MODAL_MAX_RETRIES=3
MODAL_RETRY_DELAY=1.0
MODAL_TIMEOUT=120
MODAL_QUEUE_MAX_SIZE=100
MODAL_FALLBACK_TO_QUEUE=true
```

### Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `MODAL_ENABLED` | `true` | Enable/disable Modal for model inference |
| `MODAL_WORKSPACE` | `ark-ntech` | Modal workspace name |
| `MODAL_APP_NAME` | `tiger-id-models` | Modal app name |
| `MODAL_MAX_RETRIES` | `3` | Max retry attempts for failed requests |
| `MODAL_RETRY_DELAY` | `1.0` | Initial retry delay in seconds |
| `MODAL_TIMEOUT` | `120` | Request timeout in seconds |
| `MODAL_QUEUE_MAX_SIZE` | `100` | Max requests to queue when Modal unavailable |
| `MODAL_FALLBACK_TO_QUEUE` | `true` | Queue requests on failure |

### Accessing Settings in Code

```python
from backend.config.settings import get_settings

settings = get_settings()

# Access Modal configuration
workspace = settings.modal.workspace           # "ark-ntech"
app_name = settings.modal.app_name             # "tiger-id-models"
deployment_url = settings.modal.deployment_url # Computed URL to Modal dashboard
```

### Minimal Configuration

For quick testing:

```env
MODAL_ENABLED=true
SECRET_KEY=test-secret-key-change-in-production
JWT_SECRET_KEY=test-jwt-secret-change-in-production
```

---

## Deployed Models

The Tiger ID Modal app includes 6 models for the re-identification ensemble:

| Model | GPU | Embedding Dim | Weight | Purpose |
|-------|-----|---------------|--------|---------|
| WildlifeToolsModel | A100-40GB | 1536 | 0.40 | MegaDescriptor-L embeddings (best performer) |
| CVWC2019ReIDModel | T4 | 2048 | 0.30 | Part-pose guided Re-ID |
| TransReIDModel | T4 | 768 | 0.20 | Vision Transformer features |
| MegaDescriptorBModel | T4 | 1024 | 0.15 | Fast MegaDescriptor variant |
| TigerReIDModel | T4 | 2048 | 0.10 | ResNet50 baseline |
| RAPIDReIDModel | T4 | 2048 | 0.05 | Edge-optimized Re-ID |

Additional models:
- **MegaDetectorModel** (T4) - Wildlife detection for tiger cropping

All models are **fully open source** with no external API dependencies.

---

## Architecture Overview

### Before Migration
- Models loaded locally on server startup
- Required GPU/CPU resources 24/7
- Manual model weight management
- Limited scalability

### After Migration
- Models deployed on Modal serverless infrastructure
- GPU resources allocated on-demand
- Automatic model weight caching in Modal volumes
- Horizontal scaling handled by Modal
- Request queueing for resilience

### Key Components

**Modal Client Service** (`backend/services/modal_client.py`):
- Lazy loading of Modal function references
- Automatic retry logic with exponential backoff
- Request queueing when Modal unavailable
- Configurable timeouts and retry limits
- Total timeout tracking to prevent gateway timeouts (default: 90s max)
- Statistics tracking (requests sent/succeeded/failed/queued)

**Modal App** (`backend/modal_app.py`):
- Defines all model functions with GPU specifications
- Handles model weight caching in Modal volumes
- Configures container images with PyTorch dependencies

### Performance Characteristics

| Metric | Value |
|--------|-------|
| Cold start | 5-15 seconds (first request) |
| Warm embeddings | <1 second |
| Detection | 2-5 seconds |
| Model weights | Cached in Modal volumes (persistent) |

---

## Monitoring & Logging

### View App Status

```bash
modal app list
```

### View Logs

```bash
# Tail logs
modal app logs tiger-id-models --tail

# Full logs
modal app logs tiger-id-models
```

### Modal Dashboard

Visit: https://modal.com/apps

### Application Statistics

Monitor via `modal_client.get_stats()`:
- Requests sent/succeeded/failed/queued
- Failure rates
- Queue size

### Production Monitoring

1. Check Modal dashboard for GPU usage and costs
2. Monitor request queue size
3. Set up alerts for high failure rates
4. Review logs for Modal unavailability events

---

## Cost Estimates

Modal charges for GPU time only when processing:

| GPU Type | Cost/Hour | Used By |
|----------|-----------|---------|
| T4 | ~$0.50 | TigerReID, MegaDetector, RAPID, CVWC2019, TransReID, MegaDescriptor-B |
| A100-40GB | ~$3.50 | WildlifeTools (MegaDescriptor-L) |

**Cost Optimization Tips:**
- Models run on-demand (no idle charges)
- Model weights cached (no re-download)
- Use staggered ensemble mode for early exit
- Batch multiple images when possible

---

## Troubleshooting

### Deployment Fails

```bash
# Check for errors
modal app logs tiger-id-models --tail

# Try redeploying
modal deploy backend/modal_app.py
```

### Modal App Not Found

```
ModalUnavailableError: Modal app not deployed
```

**Solution:** Deploy the Modal app:
```bash
modal deploy backend/modal_app.py
```

### Request Timeout

```
asyncio.TimeoutError: Request timeout
```

**Solution:** Increase `MODAL_TIMEOUT` or check Modal service status.

### Queue Full

```
ModalClientError: Request queue is full
```

**Solution:** Increase `MODAL_QUEUE_MAX_SIZE` or wait for queued requests to process.

### Model Loading Errors

Check Modal app logs for specific errors:
```bash
modal app logs tiger-id-models
```

Common causes:
- Model weights not downloaded
- Insufficient GPU memory
- Container build failure

### Models Not Working

```bash
# Check if app is running
modal app list

# Redeploy if needed
modal deploy backend/modal_app.py
```

### Cold Start Latency

First requests to a model take 5-15 seconds for container spin-up. This is normal. Subsequent requests are fast.

---

## Additional Resources

- **Modal Documentation**: https://modal.com/docs
- **Modal Discord**: https://discord.gg/modal
- **Model Registry**: `backend/infrastructure/modal/model_registry.py`
- **Modal Client**: `backend/services/modal_client.py`
- **Ensemble Strategies**: [ENSEMBLE_STRATEGIES.md](./ENSEMBLE_STRATEGIES.md)

---

*Last Updated: February 2026*

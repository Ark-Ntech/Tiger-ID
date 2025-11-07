# Modal Setup Guide for Tiger ID

## Quick Start - Deploy Models to Modal

### Prerequisites
- ✅ Modal CLI installed (`modal` package)
- ✅ Modal authenticated (token configured)

### Step 1: Deploy the Modal App

Run this command to deploy all models to Modal:

```powershell
python -m modal deploy backend/modal_app.py
```

**Note:** The first deployment will take 5-10 minutes as it builds Docker images and downloads model weights. Subsequent deployments are much faster.

### Step 2: All Models Are Now Open Source! 🎉

**No API keys needed!** All models, including OmniVinci, are now running as fully open-source models on Modal.

OmniVinci now uses NVIDIA's open-source model from:
- **GitHub**: https://github.com/NVlabs/OmniVinci
- **HuggingFace**: https://huggingface.co/nvidia/omnivinci
- **License**: Apache 2.0 (free for commercial use!)

The model will automatically download from HuggingFace during first deployment.

### Step 3: Configure Your Application

Add to your `.env` file:

```env
MODAL_ENABLED=true
MODAL_MAX_RETRIES=3
MODAL_TIMEOUT=120
```

### Step 4: Verify Deployment

Check that your app is deployed:

```powershell
python -m modal app list
```

You should see `tiger-id-models` in the list.

### Step 5: Test the Integration

Run the tests to verify everything works:

```powershell
python -m pytest tests/test_modal_integration.py -v
```

## Monitoring Your Modal App

### View App Status
```powershell
python -m modal app list
```

### View Logs
```powershell
python -m modal app logs tiger-id-models
```

### View Modal Dashboard
Visit: https://modal.com/apps

## Models Deployed

Your Modal app includes 6 fully open-source models:

1. **TigerReIDModel** - Tiger re-identification (GPU: T4)
2. **MegaDetectorModel** - Animal detection (GPU: T4)
3. **WildlifeToolsModel** - MegaDescriptor embeddings (GPU: A100-40GB)
4. **RAPIDReIDModel** - RAPID re-identification (GPU: T4)
5. **CVWC2019ReIDModel** - Part-pose guided ReID (GPU: T4)
6. **OmniVinciModel** - Video+audio analysis (GPU: A100-40GB) ⭐ NEW: Now fully open source!

## Cost Estimates

Modal charges for GPU time:
- **T4 GPU**: ~$0.50/hour
- **A100-40GB GPU**: ~$3.50/hour

Since models run on-demand, you only pay when processing images/videos.

## Troubleshooting

### Deployment Fails
```powershell
# Check for errors
python -m modal app logs tiger-id-models --tail

# Try redeploying
python -m modal deploy backend/modal_app.py
```

### Models Not Working
```powershell
# Check if app is running
python -m modal app list

# Redeploy if stopped
python -m modal deploy backend/modal_app.py
```

### OmniVinci Model Issues
```powershell
# Check model logs
python -m modal app logs tiger-id-models --tail

# OmniVinci uses A100 GPU - ensure your Modal account has access
# The model downloads from HuggingFace on first run (may take a few minutes)
```

## Next Steps

1. **Start Your Application**: Run your Tiger ID backend
2. **Test Inference**: Upload a tiger image and verify it uses Modal
3. **Test Video Analysis**: Upload a video with tigers to test OmniVinci
4. **Monitor Costs**: Check Modal dashboard for GPU usage
5. **Add More Models**: Extend `backend/modal_app.py` as needed

## What's New: Fully Open Source Stack

✅ **All models are now 100% open source and run on Modal!**

Previously, OmniVinci required calling NVIDIA's external API (paid service). Now it runs the actual open-source OmniVinci model directly on Modal's A100 GPUs.

**Benefits:**
- No external API dependencies
- No API keys needed
- More privacy (videos stay on your infrastructure)
- Full control over the model
- Apache 2.0 license (free for commercial use)

## Support

- Modal Docs: https://modal.com/docs
- Modal Discord: https://discord.gg/modal
- Tiger ID Issues: Create an issue in your repository

---

**Status**: Ready to deploy! 🚀

Run: `python -m modal deploy backend/modal_app.py`


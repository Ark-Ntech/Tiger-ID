# RAPID Architecture Implementation

## Status: Implemented

The RAPID (Real-time Animal Pattern Re-Identification) model is integrated into the Tiger ID 6-model ensemble system as an edge-optimized variant.

---

## Ensemble Integration

| Property | Value |
|----------|-------|
| **Ensemble Weight** | 0.05 (lowest - speed-focused) |
| **Embedding Dimension** | 2048 |
| **Calibration Temperature** | 0.95 |
| **Implementation** | `backend/models/rapid_reid.py` |

---

## Architecture

RAPID is designed for real-time animal pattern matching on edge devices.

### Model Structure
- **Backbone**: ResNet50 (optimized)
- **Input Size**: 224×224 pixels
- **Output**: 2048-dimensional embedding
- **Design Goal**: Speed over maximum accuracy

### Key Features
- Lightweight architecture optimized for inference speed
- Works on edge devices (Raspberry Pi, mobile)
- Sub-100ms inference target
- Acceptable accuracy trade-off for real-time use

---

## Configuration

### Environment Variables
```bash
RAPID_MODEL_PATH=./data/models/rapid/checkpoints/model.pth
RAPID_ENABLED=true
```

### Model Registry Entry
```python
# backend/infrastructure/modal/model_registry.py
"rapid_reid": {
    "embedding_dim": 2048,
    "input_size": (224, 224),
    "backbone": "resnet50",
    "weight": 0.05,
    "calibration_temp": 0.95
}
```

---

## Calibration

RAPID tends to produce slightly higher similarity scores. Temperature scaling normalizes this:

```python
# Calibration formula
calibrated_score = raw_score ** (1 / 0.95)
```

- Temperature 0.95 (< 1.0) slightly spreads scores
- Minor adjustment compared to other models
- Aligns with wildlife_tools reference scale

---

## Usage in Ensemble

### Why Low Weight (0.05)?
RAPID is included in the ensemble primarily for:
1. **Diversity**: Different optimization target adds ensemble diversity
2. **Speed**: Contributes to staggered mode early exit
3. **Edge Compatibility**: Validates model works on constrained hardware

The low weight ensures it doesn't significantly impact accuracy while providing these benefits.

### Staggered Mode
- Run order: Last (6th)
- Early exit threshold: 0.90
- Often skipped due to earlier models meeting threshold

### Weighted Mode
```python
# Weight contribution (minimal)
weighted_contribution = raw_score * 0.05 / sum(all_weights)
```

### Parallel Mode
- One vote per model
- Top-3 candidates submitted for voting
- Equal voting weight despite low ensemble weight

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| ATRW Accuracy | ~85% (individual) |
| Inference Time | ~50ms (GPU), ~200ms (CPU) |
| Memory Usage | ~500MB VRAM |
| Input Size | 224×224 |
| Target FPS | 10+ (edge device) |

### Strengths
- Very fast inference
- Low memory footprint
- Edge device compatible
- Real-time capable

### Weaknesses
- Lower accuracy than heavyweight models
- Less robust to viewpoint changes
- Minimal contribution to ensemble accuracy

---

## Edge Deployment

RAPID can be deployed on edge devices for real-time identification:

```python
# Example: Raspberry Pi deployment
from backend.models.rapid_reid import RAPIDReIDModel

model = RAPIDReIDModel(device='cpu')
model.load_weights('data/models/rapid/checkpoints/model.pth')

# Real-time inference
for frame in camera_stream:
    embedding = model.extract_embedding(frame)
    # Compare against pre-loaded gallery
    matches = compare_embeddings(embedding, gallery)
```

---

## Code Example

```python
from backend.services.tiger.identification_service import TigerIdentificationService

service = TigerIdentificationService()

# RAPID contributes 5% to weighted ensemble
service.set_ensemble_mode('weighted')
results = await service.identify(image=image_bytes, top_k=10)

# Check RAPID specific results
for match in results.matches:
    rapid_score = match.model_scores.get('rapid_reid', 0)
    print(f"RAPID: {rapid_score:.2%}")
```

---

## References

- **Paper**: "RAPID: Real-time Animal Pattern Re-identification"
- **Journal**: BioRxiv preprint (2025)
- **Link**: https://www.biorxiv.org/content/10.1101/2025.07.07.663143.full.pdf
- **Focus**: Edge device deployment, real-time inference

---

## Future Improvements

1. **Quantization**: INT8 quantization for even faster edge inference
2. **TensorRT**: NVIDIA TensorRT optimization for Jetson devices
3. **ONNX**: Export to ONNX for broader device compatibility
4. **Mobile**: TensorFlow Lite conversion for mobile deployment

---

*Last Updated: February 2026*

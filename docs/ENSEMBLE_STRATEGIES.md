# Ensemble Strategies
## Tiger Re-ID Multi-Model Ensemble Documentation

This document describes the 6-model ensemble system used for tiger re-identification in Tiger ID.

---

## Overview

Tiger ID employs a weighted ensemble of 6 re-identification models to maximize accuracy and robustness. The ensemble combines:
- Different architectures (CNN, ViT)
- Different training approaches (contrastive, triplet, part-based)
- Different optimization targets (accuracy, speed)

---

## Model Weights

Models are weighted based on empirical performance on the ATRW tiger dataset:

```python
MODEL_WEIGHTS = {
    "wildlife_tools": 0.40,   # MegaDescriptor-L-384 (best performer)
    "cvwc2019_reid": 0.30,    # Part-pose ResNet152
    "transreid": 0.20,        # ViT-Base transformer
    "megadescriptor_b": 0.15, # MegaDescriptor-B-224 (fast variant)
    "tiger_reid": 0.10,       # Baseline ResNet50
    "rapid_reid": 0.05,       # Edge-optimized
}
```

### Weight Rationale

| Model | Weight | Rationale |
|-------|--------|-----------|
| wildlife_tools | 0.40 | Highest accuracy (94.33% on ATRW), specialized for wildlife |
| cvwc2019_reid | 0.30 | Part-pose guidance captures unique tiger body part features |
| transreid | 0.20 | Transformer attention provides viewpoint invariance |
| megadescriptor_b | 0.15 | Fast inference, good accuracy trade-off |
| tiger_reid | 0.10 | Reliable baseline, consistent performance |
| rapid_reid | 0.05 | Speed-optimized, contributes to ensemble diversity |

**Total**: 1.20 (normalized to 1.0 during scoring)

---

## Calibration Temperatures

Different models produce scores on different scales. Temperature scaling normalizes them:

```python
CALIBRATION_TEMPS = {
    "wildlife_tools": 1.0,    # Reference (no adjustment)
    "cvwc2019_reid": 0.85,    # Tends higher → reduce temperature
    "transreid": 1.1,         # Tends lower → increase temperature
    "megadescriptor_b": 1.0,  # Similar to L variant
    "tiger_reid": 0.9,        # Slightly high
    "rapid_reid": 0.95,       # Slightly high
}
```

### Calibration Formula

```python
calibrated_score = raw_score / temperature
```

- **Temperature < 1.0**: Spreads scores (makes high scores higher)
- **Temperature = 1.0**: No change
- **Temperature > 1.0**: Compresses scores (makes high scores lower)

### Temperature Bounds

To prevent extreme calibration, temperatures are clamped to safe bounds:

```python
MIN_TEMPERATURE = 0.1   # Prevents extreme score spreading
MAX_TEMPERATURE = 5.0   # Prevents extreme score compression
```

Any temperature value outside these bounds is automatically clamped. Attempting to set a temperature outside bounds via `ConfidenceCalibrator.set_temperature()` raises a `ValueError`.

### Implementation

```python
# backend/services/confidence_calibrator.py
from backend.services.confidence_calibrator import ConfidenceCalibrator

calibrator = ConfidenceCalibrator()
calibrated = calibrator.calibrate(
    raw_score=0.85,
    model_name="cvwc2019_reid"
)
```

---

## Ensemble Modes

Four ensemble execution modes are available:

### 1. Staggered Mode (`staggered`)

Sequential execution with early exit on high-confidence matches.

```python
service.set_ensemble_mode('staggered')
```

**Behavior**:
1. Run models in order of weight (highest first)
2. If confidence exceeds threshold (e.g., 0.90), stop early
3. Return result from highest-confidence model

**Best for**:
- Quick identifications
- Clear matches (high similarity)
- Resource-constrained environments

**Trade-offs**:
- ✅ Faster for obvious matches
- ❌ May miss nuanced matches
- ❌ Less robust consensus

### 2. Parallel Mode (`parallel`)

All models run simultaneously with majority voting.

```python
service.set_ensemble_mode('parallel')
```

**Behavior**:
1. Run all 6 models in parallel
2. Each model votes for top-k candidates
3. Aggregate votes with equal weight
4. Return ranked candidates by vote count

**Best for**:
- Maximum accuracy required
- Unlimited compute budget
- Verification tasks

**Trade-offs**:
- ✅ Most robust
- ✅ Consensus-based
- ❌ Highest compute cost
- ❌ Slower than staggered

### 3. Weighted Mode (`weighted`) - **Recommended**

Combines weighted scoring, calibration, and re-ranking.

```python
service.set_ensemble_mode('weighted')
```

**Behavior**:
1. Run all models in parallel
2. Calibrate scores using temperature scaling
3. Apply model weights to calibrated scores
4. Combine into final weighted score
5. Apply K-reciprocal re-ranking for final ordering

**Best for**:
- Production deployments
- Balanced speed/accuracy
- Investigation workflows

**Trade-offs**:
- ✅ Best overall accuracy
- ✅ Normalized scores across models
- ✅ Re-ranking improves mAP
- ⚠️ More complex pipeline

### 4. Verified Mode (`verified`)

Extends weighted mode with MatchAnything geometric verification.

```python
service.set_ensemble_mode('verified')
```

**Behavior**:
1. Run all models in parallel (same as weighted)
2. Calibrate and weight scores
3. Get top-k candidates
4. Run MatchAnything keypoint verification on each candidate
5. Combine ReID scores with geometric match scores using adaptive weights
6. Re-rank based on combined scores

**Best for**:
- High-stakes identifications (trafficking investigations)
- When ReID models disagree
- When additional verification confidence is needed

**Trade-offs**:
- ✅ Highest confidence through geometric verification
- ✅ Detects ReID/verification disagreements
- ✅ Adaptive weighting based on confidence spread
- ❌ Additional latency (~200-400ms per candidate)
- ❌ Requires MatchAnything model loaded

**Verification Thresholds**:
| Metric | Threshold | Result |
|--------|-----------|--------|
| Keypoint matches < 25 | insufficient_matches | Skipped |
| Combined score < 0.70 | low_confidence | Needs review |
| Combined score ≥ 0.70 | verified | Accepted |
| Matches ≥ 100 AND score ≥ 0.85 | high_confidence | Strong match |

**Adaptive Weighting**:
- High ReID spread (>0.15): Trust ReID more (up to 75% weight)
- Low ReID spread (<0.05): Trust verification more (ReID down to 40%)
- Default: 60% ReID, 40% geometric verification

---

## Post-Processing Pipeline

### MatchAnything Geometric Verification

Keypoint-based geometric verification using ELOFTR matching.

**Implementation**: `backend/models/matchanything.py`

```python
from backend.models.matchanything import MatchAnythingModel

matcher = MatchAnythingModel()
result = matcher.verify_match(
    query_image=query,
    gallery_image=gallery,
    min_matches=25
)
# Returns: num_matches, geometric_score, inlier_ratio
```

**Features**:
- ELOFTR keypoint detection and matching
- RANSAC-based geometric verification
- Sigmoid normalization for match counts
- Multi-gallery support (compares against up to 3 images per tiger)
- Side-view preference for gallery selection

### K-Reciprocal Re-Ranking

Re-ranking considers reciprocal neighbors to improve ranking quality.

**Implementation**: `backend/services/reranking_service.py`

```python
from backend.services.reranking_service import RerankingService

reranker = RerankingService()
reranked_results = reranker.rerank(
    query_embedding=query,
    gallery_embeddings=gallery,
    initial_rankings=rankings,
    k1=20,  # Number of nearest neighbors
    k2=6,   # Number of reciprocal neighbors
    lambda_value=0.3  # Weighting factor
)
```

**Parameters**:
- `k1`: Number of k-nearest neighbors to consider
- `k2`: Number of k-reciprocal nearest neighbors
- `lambda`: Balance between original and expanded neighbors

**Performance Impact**:
- +3-5% mAP improvement on average
- Minimal latency overhead (~10-50ms)

### Multi-View Fusion

Combines embeddings from multiple views of the same tiger.

**Implementation**: `backend/services/embedding_service.py`

```python
from backend.services.embedding_service import fuse_multi_view_embeddings

fused_embedding = fuse_multi_view_embeddings(
    embeddings=[emb1, emb2, emb3],
    quality_scores=[0.9, 0.7, 0.85],
    fusion_method='quality_weighted'
)
```

**Fusion Methods**:
- `mean`: Simple average
- `quality_weighted`: Weighted by image quality scores
- `attention`: Learned attention weights (if model supports)

---

## Embedding Dimensions

| Model | Dimension | Storage per Tiger |
|-------|-----------|-------------------|
| wildlife_tools | 1536 | 6.1 KB |
| cvwc2019_reid | 2048 | 8.2 KB |
| transreid | 768 | 3.1 KB |
| megadescriptor_b | 1024 | 4.1 KB |
| tiger_reid | 2048 | 8.2 KB |
| rapid_reid | 2048 | 8.2 KB |
| **Total** | 9472 | ~37.9 KB |

*Storage assumes float32 (4 bytes per dimension)*

---

## Code Examples

### Basic Identification

```python
from backend.services.tiger.identification_service import TigerIdentificationService

service = TigerIdentificationService()
service.set_ensemble_mode('weighted')

results = await service.identify(
    image=image_bytes,
    top_k=10,
    threshold=0.7
)

for match in results.matches:
    print(f"{match.tiger_name}: {match.similarity:.2%}")
```

### Custom Weights

```python
from backend.services.tiger.ensemble_strategy import WeightedEnsembleStrategy

strategy = WeightedEnsembleStrategy(
    weights={
        "wildlife_tools": 0.50,  # Increase primary model
        "cvwc2019_reid": 0.25,
        "transreid": 0.15,
        "megadescriptor_b": 0.10,
        # Disable baseline models
        "tiger_reid": 0.0,
        "rapid_reid": 0.0,
    }
)

results = await strategy.identify(query_embedding, gallery)
```

### With Re-Ranking

```python
from backend.services.reranking_service import RerankingService
from backend.services.confidence_calibrator import ConfidenceCalibrator

# Get raw results
raw_results = await service.identify_raw(image)

# Calibrate scores
calibrator = ConfidenceCalibrator()
calibrated = [
    {**r, 'score': calibrator.calibrate(r['score'], r['model'])}
    for r in raw_results
]

# Re-rank
reranker = RerankingService()
final_results = reranker.rerank(
    query_embedding=query,
    gallery_embeddings=gallery,
    initial_rankings=calibrated
)
```

---

## Configuration

### Environment Variables

```bash
# Ensemble mode
ENSEMBLE_MODE=weighted

# Re-ranking
ENABLE_RERANKING=true
RERANKING_K1=20
RERANKING_K2=6
RERANKING_LAMBDA=0.3

# Calibration
ENABLE_CALIBRATION=true

# Thresholds
EARLY_EXIT_THRESHOLD=0.90
MATCH_THRESHOLD=0.70
```

### Runtime Configuration

```python
from backend.config import settings

# Override at runtime
settings.ensemble_mode = 'parallel'
settings.enable_reranking = True
settings.match_threshold = 0.75
```

---

## Performance Benchmarks

### ATRW Dataset Results

| Mode | mAP | Rank-1 | Avg Time |
|------|-----|--------|----------|
| Single (best) | 89.2% | 94.3% | 120ms |
| Parallel (voting) | 91.5% | 95.8% | 450ms |
| Weighted (calibrated) | 92.8% | 96.2% | 480ms |
| Weighted + Re-rank | **94.1%** | **97.0%** | 520ms |

### Latency Breakdown

| Stage | Time |
|-------|------|
| Image preprocessing | 15ms |
| MegaDetector detection | 80ms |
| Model inference (parallel) | 350ms |
| Calibration | 5ms |
| Weighted scoring | 10ms |
| Re-ranking | 40ms |
| **Total** | ~500ms |

### Timeouts

| Operation | Timeout | Configuration |
|-----------|---------|---------------|
| Gallery image loading | 10s | `IMAGE_LOAD_TIMEOUT` in `ensemble_strategy.py` |
| Modal single request | 60s | `MODAL_TIMEOUT` env var |
| Modal total operation | 90s | `MAX_TOTAL_TIMEOUT` in `modal_client.py` |

The total timeout tracking prevents gateway timeouts (most gateways timeout at 60-120s) by aborting retries when approaching the limit.

---

## Troubleshooting

### Low Ensemble Agreement

**Symptom**: Models disagree significantly on matches.

**Solutions**:
1. Check image quality scores
2. Verify calibration temperatures are appropriate
3. Consider re-training on domain-specific data

### Calibration Issues

**Symptom**: One model dominates results.

**Solutions**:
1. Adjust calibration temperature for that model
2. Verify score distributions match expected ranges
3. Check for model-specific preprocessing issues

### Re-Ranking Degradation

**Symptom**: Re-ranking makes results worse.

**Solutions**:
1. Reduce k1/k2 parameters
2. Increase lambda to weight original rankings more
3. Disable re-ranking for small galleries (<100 tigers)

---

## Discovery Integration

The 6-model ensemble integrates with the continuous discovery pipeline:

1. **Image Deduplication**: SHA256 hashing occurs before ensemble inference, preventing redundant GPU compute for duplicate images discovered from multiple sources
2. **Quality Filtering**: OpenCV-based quality assessment filters out low-quality images before ensemble processing
3. **Batch Processing**: Discovered images are batched for efficient ensemble inference

## References

- **MegaDescriptor**: [WildlifeDatasets WACV 2024](https://arxiv.org/html/2311.09118v2)
- **K-Reciprocal Re-Ranking**: [CVPR 2017](https://arxiv.org/abs/1701.08398)
- **TransReID**: [ICCV 2021](https://arxiv.org/abs/2102.04378)
- **CVWC2019**: [ICCVW 2019](http://openaccess.thecvf.com/content_ICCVW_2019/papers/CVWC/)

---

*Last Updated: February 2026*

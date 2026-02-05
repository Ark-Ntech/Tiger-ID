# Tiger ID Models Research

This document provides comprehensive information about all ML models used in the Tiger ID Investigation 2.0 workflow, including research papers, repositories, architectures, and use cases.

---

## Model Ensemble Overview

Tiger ID uses a 6-model ensemble for tiger re-identification:

| Model | Weight | Embedding Dim | Architecture | Purpose |
|-------|--------|---------------|--------------|---------|
| Wildlife-Tools (MegaDescriptor-L) | 0.40 | 1536 | ViT-L/14 | Primary - Best accuracy |
| CVWC2019 | 0.30 | 2048 | ResNet152 | Part-pose guided |
| TransReID | 0.20 | 768 | ViT-Base | Transformer-based |
| MegaDescriptor-B | 0.15 | 1024 | ViT-B/16 | Fast variant |
| TigerReID | 0.10 | 2048 | ResNet50 | Baseline |
| RAPID | 0.05 | 2048 | ResNet50 | Edge-optimized |

---

## 1. WildlifeTools / MegaDescriptor-L (Primary Model)

### Overview
The highest-performing model in our ensemble, MegaDescriptor-L-384 achieves 94.33% accuracy on the ATRW tiger dataset.

### Research & Resources
- **GitHub**: https://github.com/WildlifeDatasets/wildlife-tools
- **Paper**: "MegaDescriptor: State of the art feature extractor for wildlife re-identification" (WACV 2024)
- **ArXiv**: https://arxiv.org/html/2311.09118v2
- **Organization**: WildlifeDatasets
- **License**: Open source

### Architecture
- **Base**: ViT-L/14 (Vision Transformer Large)
- **Input Size**: 384×384 pixels
- **Output**: 1536-dimensional embedding
- **Training**: Contrastive learning on diverse wildlife datasets

### Performance
| Dataset | Accuracy |
|---------|----------|
| ATRW (Tigers) | 94.33% |
| Amur Leopard | 92.1% |
| Multi-species | 90.5% |

### Use in Workflow
- **Ensemble Weight**: 0.40 (highest)
- **Calibration Temperature**: 1.0 (reference)
- **Purpose**: Primary re-identification backbone

---

## 2. CVWC2019 (Part-Pose Guided Tiger Re-ID)

### Overview
Winner of the CVWC2019 competition at ICCV 2019 Workshop, using part-pose guided approach for Amur Tiger Re-Identification.

### Research Paper
- **Title**: "Part-Pose Guided Amur Tiger Re-Identification"
- **Conference**: ICCVW 2019 (Computer Vision for Wildlife Conservation)
- **Link**: http://openaccess.thecvf.com/content_ICCVW_2019/papers/CVWC/Liu_Part-Pose_Guided_Amur_Tiger_Re-Identification_ICCVW_2019_paper.pdf
- **Award**: 🏆 1st Place in both Tiger Re-ID tracks

### Repository
- **GitHub**: https://github.com/LcenArthas/CWCV2019-Amur-Tiger-Re-ID
- **License**: Research/Academic use
- **Language**: Python (PyTorch)

### Architecture (Fixed in Phase 1)

**Note**: Implementation was corrected in Phase 1 to use proper ResNet152 backbone (was placeholder ResNet50).

1. **Global Stream**
   - Backbone: **ResNet152** (corrected)
   - Purpose: Extract global features from entire tiger image
   - Output: 2048-dimensional feature vector

2. **Part Body Stream**
   - Backbone: ResNet34
   - Purpose: Extract features from tiger body parts (excluding paws)
   - Output: 512-dimensional feature vector

3. **Part Paw Stream**
   - Backbone: ResNet34
   - Purpose: Extract features from tiger paw patterns
   - Output: 512-dimensional feature vector

4. **Feature Fusion**
   - Combined embedding: 3072-dimensional (2048 + 512 + 512)
   - Simplified to 2048-dim in ensemble integration

### Use in Workflow
- **Ensemble Weight**: 0.30
- **Calibration Temperature**: 0.85 (tends toward higher scores)
- **Embedding Dimension**: 2048

### Dataset
- **ATRW**: Amur Tiger Re-identification in the Wild
- **Size**: 92 individual tigers
- **Annotations**: Bounding boxes, identity labels, pose keypoints

---

## 3. TransReID (NEW - Vision Transformer)

### Overview
Transformer-based re-identification model added in Phase 2, leveraging attention mechanisms for robust feature extraction.

### Research Paper
- **Title**: "TransReID: Transformer-based Object Re-Identification"
- **Conference**: ICCV 2021
- **ArXiv**: https://arxiv.org/abs/2102.04378
- **GitHub**: https://github.com/damo-cv/TransReID

### Architecture
- **Base**: ViT-Base (Vision Transformer)
- **Patch Size**: 16×16
- **Input Size**: 256×128 (standard ReID) or 224×224 (our config)
- **Output**: 768-dimensional embedding

### Key Features
- Side Information Embedding (SIE) for camera/viewpoint awareness
- Jigsaw Patch Module (JPM) for part-level features
- Self-attention for global context modeling

### Use in Workflow
- **Ensemble Weight**: 0.20
- **Calibration Temperature**: 1.1 (tends toward lower scores)
- **Implementation**: `backend/models/transreid.py`

### Performance Characteristics
- Strong on viewpoint-invariant matching
- Good generalization across lighting conditions
- Moderate inference speed

---

## 4. MegaDescriptor-B (NEW - Fast Variant)

### Overview
Fast variant of MegaDescriptor added in Phase 2 for speed-optimized scenarios.

### Research & Resources
- Same as MegaDescriptor-L (WildlifeDatasets)
- **Variant**: MegaDescriptor-B-224 (Base, smaller input)

### Architecture
- **Base**: ViT-B/16 (Vision Transformer Base)
- **Input Size**: 224×224 pixels (vs 384 for L variant)
- **Output**: 1024-dimensional embedding

### Use in Workflow
- **Ensemble Weight**: 0.15
- **Calibration Temperature**: 1.0
- **Implementation**: `backend/models/megadescriptor_b.py`

### Performance vs MegaDescriptor-L
| Metric | MegaDescriptor-L | MegaDescriptor-B |
|--------|------------------|------------------|
| Input Size | 384×384 | 224×224 |
| Embedding Dim | 1536 | 1024 |
| Inference Speed | Slower | ~2x faster |
| Accuracy | Higher | Slightly lower |

---

## 5. TigerReID (Baseline Siamese Network)

### Overview
Custom Siamese network implementation for tiger stripe pattern matching, serving as baseline model.

### Architecture
- **Base**: ResNet50 (pretrained on ImageNet)
- **Modification**: Classification head removed
- **Output**: 2048-dimensional embedding
- **Training**: Triplet loss with hard negative mining
- **Input Size**: 224×224 pixels

### Implementation Details
- **Framework**: PyTorch
- **Normalization**: ImageNet statistics
- **Preprocessing**: Resize → Center crop → Normalize

### Use in Workflow
- **Ensemble Weight**: 0.10
- **Calibration Temperature**: 0.9
- **Purpose**: Reliable baseline, fast inference

### Similarity Metric
- **Method**: Cosine similarity
- **Threshold**: 0.8 (default)
- **Normalization**: L2 normalization of embeddings

---

## 6. RAPID (Real-time Animal Pattern Re-ID)

### Overview
Real-time animal pattern re-identification model optimized for edge devices and rapid inference.

### Research Paper
- **Title**: "RAPID: Real-time Animal Pattern Re-identification"
- **Journal**: BioRxiv preprint
- **Link**: https://www.biorxiv.org/content/10.1101/2025.07.07.663143.full.pdf
- **Year**: 2025

### Architecture
- Lightweight architecture optimized for speed
- ResNet50-based backbone
- Designed for edge device deployment
- Focus on real-time inference (<100ms per image)

### Use in Workflow
- **Ensemble Weight**: 0.05 (lowest, speed-focused)
- **Calibration Temperature**: 0.95
- **Embedding Dimension**: 2048

### Performance Characteristics
- **Speed**: Optimized for real-time inference
- **Accuracy**: Trade-off between speed and accuracy
- **Deployment**: Edge device compatible

---

## 7. MegaDetector v5 (Detection)

### Overview
Microsoft's wildlife detection model designed to detect animals, people, and vehicles in camera trap images.

### Research & Resources
- **Organization**: Microsoft AI for Earth
- **GitHub**: https://github.com/microsoft/CameraTraps
- **Model**: YOLOv5-based architecture
- **Version**: v5a.0.0
- **License**: Open source

### Architecture
- **Base**: YOLOv5 object detection
- **Categories**: Animal (0), Person (1), Vehicle (2)
- **Input Size**: 640×640 pixels
- **Output**: Bounding boxes with confidence scores

### Use in Workflow
- **Node**: Tiger Detection
- **Purpose**: Detect tigers in images, generate crops for Re-ID
- **Threshold**: 0.5 confidence (default)

### Download
- **URL**: https://github.com/microsoft/CameraTraps/releases/download/v5.0/md_v5a.0.0.pt
- **Size**: ~150 MB

---

## Post-Processing Techniques

### K-Reciprocal Re-Ranking

**Implementation**: `backend/services/reranking_service.py`

Re-ranking improves results by considering reciprocal neighbors:
- **Improvement**: +3-5% mAP on average
- **Parameters**:
  - `k1`: Number of nearest neighbors (default: 20)
  - `k2`: Number of reciprocal neighbors (default: 6)
  - `lambda`: Weighting factor (default: 0.3)

**Paper**: "Re-ranking Person Re-identification with k-reciprocal Encoding" (CVPR 2017)

### Confidence Calibration

**Implementation**: `backend/services/confidence_calibrator.py`

Temperature scaling normalizes scores across models:

```python
CALIBRATION_TEMPS = {
    "wildlife_tools": 1.0,    # Reference
    "cvwc2019_reid": 0.85,    # Higher scores → reduce temp
    "transreid": 1.1,         # Lower scores → increase temp
    "megadescriptor_b": 1.0,
    "tiger_reid": 0.9,
    "rapid_reid": 0.95,
}
```

**Formula**: `calibrated_score = score^(1/temperature)`

### Multi-View Fusion

**Implementation**: `backend/services/embedding_service.py`

Combines embeddings from multiple views of the same tiger:
- Quality-weighted averaging
- Outlier filtering
- Adaptive fusion based on view diversity

---

## DINOv2 Evaluation (NOT RECOMMENDED)

Evaluated DINOv2 for potential addition to ensemble. **Decision: Do NOT add.**

| Model | ATRW Tiger Accuracy |
|-------|---------------------|
| MegaDescriptor-L | 94.33% |
| DINOv2 | 88.47% |

**Reasons**:
- MegaDescriptor outperforms DINOv2 by ~6% on tiger re-ID
- DINOv2 uses larger input (518×518) but performs worse
- Research shows DINOv2 provides "only marginal improvement" when added to specialized models
- Our 6-model ensemble already includes MegaDescriptor-L (best performer)

**Source**: [WildlifeDatasets WACV 2024](https://arxiv.org/html/2311.09118v2)

---

## Workflow Integration Summary

### Investigation 2.0 Pipeline

```
1. Upload & Parse
   ↓
2. Reverse Image Search (Anthropic + DuckDuckGo)
   ↓
3. Tiger Detection (MegaDetector v5)
   ↓
4. Stripe Analysis (Parallel execution)
   ├── Wildlife-Tools (0.40)
   ├── CVWC2019 (0.30)
   ├── TransReID (0.20)
   ├── MegaDescriptor-B (0.15)
   ├── TigerReID (0.10)
   └── RAPID (0.05)
   ↓
5. Post-Processing
   ├── Confidence Calibration
   ├── Weighted Ensemble
   └── K-Reciprocal Re-Ranking
   ↓
6. Report Generation (Claude)
   ↓
7. Complete
```

### Model Execution Environment
- **Backend**: Modal serverless GPU compute
- **GPU Types**: T4 (standard), A100 (heavy inference)
- **Caching**: Model weights cached in Modal volumes
- **Timeout**: 600-900 seconds per inference

---

## References & Citations

### CVWC2019
```bibtex
@inproceedings{liu2019part,
  title={Part-Pose Guided Amur Tiger Re-Identification},
  author={Liu, Xinyu and others},
  booktitle={ICCV Workshops},
  year={2019}
}
```

### TransReID
```bibtex
@inproceedings{he2021transreid,
  title={TransReID: Transformer-based Object Re-Identification},
  author={He, Shuting and others},
  booktitle={ICCV},
  year={2021}
}
```

### MegaDescriptor
```bibtex
@inproceedings{cermak2024megadescriptor,
  title={MegaDescriptor: State of the art feature extractor for wildlife re-identification},
  author={Čermák, Vojtěch and others},
  booktitle={WACV},
  year={2024}
}
```

### MegaDetector
```bibtex
@software{beery2019megadetector,
  title={MegaDetector},
  author={Beery, Sara and Morris, Dan and Yang, Siyu},
  organization={Microsoft AI for Earth},
  year={2019}
}
```

### K-Reciprocal Re-Ranking
```bibtex
@inproceedings{zhong2017reranking,
  title={Re-ranking Person Re-identification with k-reciprocal Encoding},
  author={Zhong, Zhun and others},
  booktitle={CVPR},
  year={2017}
}
```

---

*Last Updated: February 2026*

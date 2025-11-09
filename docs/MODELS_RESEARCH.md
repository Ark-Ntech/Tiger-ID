# Tiger ID Models Research

This document provides comprehensive information about all ML models used in the Tiger ID Investigation 2.0 workflow, including research papers, repositories, architectures, and use cases.

---

## 1. CVWC2019 (Part-Pose Guided Tiger Re-ID)

### Overview
Part-pose guided approach for Amur Tiger Re-Identification, winner of the CVWC2019 competition at ICCV 2019 Workshop.

### Research Paper
- **Title**: "Part-Pose Guided Amur Tiger Re-Identification"
- **Conference**: ICCVW 2019 (Computer Vision for Wildlife Conservation)
- **Link**: http://openaccess.thecvf.com/content_ICCVW_2019/papers/CVWC/Liu_Part-Pose_Guided_Amur_Tiger_Re-Identification_ICCVW_2019_paper.pdf
- **Award**: 🏆 1st Place in both Tiger Re-ID in Plain Track and Tiger Re-ID in Wild Track

### Repository
- **GitHub**: https://github.com/LcenArthas/CWCV2019-Amur-Tiger-Re-ID
- **License**: Research/Academic use
- **Language**: Python (PyTorch)

### Architecture
Multi-stream architecture combining global and part-based features:

1. **Global Stream**
   - Backbone: ResNet152
   - Purpose: Extract global features from entire tiger image
   - Output: 2048-dimensional feature vector

2. **Part Body Stream**
   - Backbone: ResNet34
   - Purpose: Extract features from tiger body parts (excluding paws)
   - Input: Cropped body regions based on pose estimation
   - Output: 512-dimensional feature vector

3. **Part Paw Stream**
   - Backbone: ResNet34
   - Purpose: Extract features from tiger paw patterns
   - Input: Cropped paw regions
   - Output: 512-dimensional feature vector

4. **Feature Fusion**
   - Combined embedding: 3072-dimensional (2048 + 512 + 512)
   - Weighted fusion based on learned importance

### Use in Workflow
- **Node**: Stripe Analysis
- **Purpose**: High-accuracy tiger re-identification using part-pose guidance
- **Input**: Cropped tiger images from MegaDetector
- **Output**: 3072-dimensional embedding for database matching
- **Performance**: State-of-the-art accuracy on ATRW dataset

### Dataset
- **ATRW**: Amur Tiger Re-identification in the Wild
- **Size**: 92 individual tigers
- **Annotations**: Bounding boxes, identity labels, pose keypoints

---

## 2. RAPID (Real-time Animal Pattern Re-ID)

### Overview
Real-time animal pattern re-identification model optimized for edge devices and rapid inference.

### Research Paper
- **Title**: "RAPID: Real-time Animal Pattern Re-identification"
- **Journal**: BioRxiv preprint
- **Link**: https://www.biorxiv.org/content/10.1101/2025.07.07.663143.full.pdf
- **Year**: 2025

### Architecture
- Lightweight architecture optimized for speed
- Designed for edge device deployment
- Focus on real-time inference (<100ms per image)
- Current implementation: ResNet50-based (placeholder until full architecture is available)

### Use in Workflow
- **Node**: Stripe Analysis
- **Purpose**: Fast tiger re-identification for real-time applications
- **Input**: Cropped tiger images
- **Output**: Embedding vector for similarity matching
- **Advantage**: Speed-optimized for rapid processing

### Performance Characteristics
- **Speed**: Optimized for real-time inference
- **Accuracy**: Balanced trade-off between speed and accuracy
- **Deployment**: Edge device compatible

---

## 3. OmniVinci (Multi-modal LLM)

### Overview
NVIDIA's omni-modal language model capable of understanding and analyzing video, audio, and text inputs simultaneously.

### Research & Resources
- **Organization**: NVIDIA Research (NVlabs)
- **GitHub**: https://github.com/NVlabs/OmniVinci
- **HuggingFace**: nvidia/omnivinci
- **License**: Apache 2.0
- **Paper**: Check GitHub repository for associated publications

### Capabilities
- **Video Analysis**: Frame-by-frame and temporal understanding
- **Audio Processing**: Speech and sound analysis
- **Text Generation**: Natural language understanding and generation
- **Multi-modal Fusion**: Integrates vision, audio, and text

### Architecture
- Transformer-based multi-modal architecture
- Vision encoder for image/video processing
- Audio encoder for sound analysis
- Language model for text generation
- Cross-modal attention mechanisms

### Use in Workflow
- **Node**: Omnivinci Comparison
- **Purpose**: Compare uploaded tiger images with database matches using advanced multi-modal understanding
- **Input**: Tiger images (uploaded + database matches)
- **Output**: Similarity analysis with natural language explanations
- **Advantage**: Can provide detailed reasoning about similarities/differences

### Model Specifications
- **GPU Requirement**: A100-40GB (or similar high-end GPU)
- **Video Frames**: 128 frames default
- **Audio Support**: Optional audio analysis
- **Context Window**: Large context for comprehensive analysis

---

## 4. MegaDetector v5

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
- **Categories**:
  - Class 0: Animal
  - Class 1: Person
  - Class 2: Vehicle
- **Input Size**: 640x640 pixels
- **Output**: Bounding boxes with confidence scores

### Use in Workflow
- **Node**: Tiger Detection
- **Purpose**: Detect tigers in uploaded and scraped images
- **Input**: Full images from upload or web scraping
- **Output**: Bounding boxes and cropped tiger regions
- **Advantage**: Robust to various lighting, angles, and backgrounds

### Performance
- **Confidence Threshold**: 0.5 (default)
- **NMS Threshold**: 0.45
- **Speed**: Fast inference on GPU (T4)
- **Accuracy**: High detection rate for wildlife in natural settings

### Download
- **URL**: https://github.com/microsoft/CameraTraps/releases/download/v5.0/md_v5a.0.0.pt
- **Size**: ~150 MB

---

## 5. WildlifeTools (MegaDescriptor/WildFusion)

### Overview
Open-source toolkit for wildlife re-identification providing training and inference capabilities with pre-trained models.

### Research & Resources
- **GitHub**: https://github.com/WildlifeDatasets/wildlife-tools
- **Organization**: WildlifeDatasets
- **License**: Open source
- **Documentation**: Available in repository

### Models Included
1. **MegaDescriptor**
   - Purpose: General wildlife feature extraction
   - Architecture: Vision transformer-based
   - Output: High-dimensional embeddings

2. **WildFusion**
   - Purpose: Multi-species fusion model
   - Architecture: Ensemble approach
   - Output: Unified embeddings across species

### Use in Workflow
- **Node**: Stripe Analysis
- **Purpose**: Extract wildlife-optimized embeddings for tiger matching
- **Input**: Cropped tiger images
- **Output**: Embedding vectors for similarity search
- **Advantage**: Trained specifically on wildlife datasets

### Features
- Pre-trained models for various species
- Easy integration via Python package
- Support for custom dataset training
- Efficient batch processing

---

## 6. TigerReID (Custom Siamese Network)

### Overview
Custom Siamese network implementation for tiger stripe pattern matching, baseline model for the system.

### Architecture
- **Base**: ResNet50 (pretrained on ImageNet)
- **Modification**: Classification head removed
- **Output**: 2048-dimensional embedding
- **Training**: Triplet loss with hard negative mining
- **Input Size**: 224x224 pixels

### Implementation Details
- **Framework**: PyTorch
- **Normalization**: ImageNet statistics (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
- **Preprocessing**: 
  - Resize to 256x256
  - Center crop to 224x224
  - Tensor normalization

### Use in Workflow
- **Node**: Stripe Analysis
- **Purpose**: Baseline tiger re-identification
- **Input**: Cropped tiger images
- **Output**: 2048-dimensional embedding
- **Advantage**: Fast, reliable baseline model

### Similarity Metric
- **Method**: Cosine similarity
- **Threshold**: 0.8 (default)
- **Normalization**: L2 normalization of embeddings

---

## 7. GPT-5-mini (via HermesChatModel)

### Overview
OpenAI's language model used for report generation and analysis synthesis in the Investigation 2.0 workflow.

### Model Specifications
- **Model**: gpt-5-mini (configured in settings)
- **Provider**: OpenAI API
- **API**: Chat Completions endpoint
- **Context**: Large context window for comprehensive reports

### Capabilities
- **Text Generation**: High-quality report writing
- **Analysis Synthesis**: Combining multiple data sources
- **Tool Calling**: Native function calling support
- **Structured Output**: JSON and formatted text generation

### Use in Workflow
- **Node**: Report Generation
- **Purpose**: Generate comprehensive investigation reports
- **Input**: All findings from previous nodes:
  - Reverse search results
  - Detected tigers
  - Stripe analysis from all models
  - Omnivinci comparisons
  - Database matches
- **Output**: Structured report with:
  - Executive summary
  - Detailed findings
  - Match confidence scores
  - Recommendations
  - Evidence sources

### Configuration
- **Max Tokens**: 2048 (default, configurable)
- **Temperature**: 0.7 (balanced creativity and consistency)
- **API Key**: Set via OPENAI_API_KEY environment variable

---

## Workflow Integration Summary

### Investigation 2.0 Pipeline

```
1. Upload & Parse
   ↓
2. Reverse Image Search (ImageSearchService)
   ↓
3. Tiger Detection (MegaDetector v5)
   ↓
4. Stripe Analysis (Parallel execution)
   ├── TigerReID
   ├── CVWC2019
   ├── RAPID
   └── WildlifeTools
   ↓
5. Omnivinci Comparison (OmniVinci)
   ↓
6. Report Generation (GPT-5-mini)
   ↓
7. Complete
```

### Model Execution Environment
- **Backend**: Modal serverless GPU compute
- **GPU Types**: T4 (lighter models), A100-40GB (OmniVinci)
- **Caching**: Model weights cached in Modal volumes
- **Timeout**: 600-900 seconds per inference

### Performance Optimization
- **Parallel Execution**: Stripe analysis models run simultaneously
- **Batch Processing**: Multiple images processed efficiently
- **Caching**: Pre-loaded models reduce cold start time
- **Async Operations**: Non-blocking API calls throughout workflow

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

### MegaDetector
```bibtex
@software{beery2019megadetector,
  title={MegaDetector},
  author={Beery, Sara and Morris, Dan and Yang, Siyu},
  organization={Microsoft AI for Earth},
  year={2019}
}
```

### Wildlife Conservation Datasets
- **ATRW**: Amur Tiger Re-identification in the Wild
- **Camera Traps**: LILA BC (Labeled Information Library of Alexandria: Biology and Conservation)

---

## Future Enhancements

1. **Model Updates**
   - Obtain full trained weights for CVWC2019
   - Integrate complete RAPID architecture
   - Fine-tune models on custom tiger dataset

2. **New Models**
   - Pose estimation for part-based analysis
   - Temporal models for video sequences
   - Multi-species support

3. **Optimization**
   - Model quantization for faster inference
   - Ensemble weighting based on confidence
   - Active learning for continuous improvement

---

*Last Updated: November 2025*


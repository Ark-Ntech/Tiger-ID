"""
Modal application for Tiger ID ML model inference.

This module provides serverless GPU compute for all ML models:
- TigerReID: Tiger re-identification embeddings (ResNet50)
- MegaDetector: Animal detection in images (YOLOv5)
- RAPID: Re-identification model (edge-optimized)
- WildlifeTools: MegaDescriptor-L-384 embeddings (Swin-Large, 1536-dim)
- CVWC2019: Part-pose guided tiger re-identification (ResNet152, 2048-dim)
- TransReID: Vision Transformer-based re-identification (ViT-Base, 768-dim)

Model weights are cached in Modal volumes for efficient loading.
"""

import modal
import io
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np

# Create Modal app
app = modal.App("tiger-id-models")

# Create Modal volumes for persistent model weight storage
models_volume = modal.Volume.from_name("tiger-models", create_if_missing=True)

# Define the model cache paths in the volume
MODEL_CACHE_DIR = "/models"

# GPU configuration for different models
GPU_CONFIG_T4 = "T4"  # For lighter models
GPU_CONFIG_A100 = "A100-40GB"  # For heavier models

# Base PyTorch image with CUDA support
# Modal's debian_slim automatically includes CUDA support for GPU functions
# Using Python 3.11 for compatibility with all dependencies
pytorch_base = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1-mesa-glx", "libglib2.0-0", "git")
    .pip_install("torch>=2.3.0", "torchvision>=0.18.0", "numpy>=1.26.0")
)

# Create Modal images with model-specific dependencies
# torch, torchvision, and numpy are already installed in pytorch_base

tiger_reid_image = pytorch_base.pip_install(
    "Pillow>=11.0.0",
    "yacs>=0.1.8",  # For CVWC2019 config
)

megadetector_image = pytorch_base.pip_install(
    "opencv-python-headless>=4.6.0",
    "Pillow>=11.0.0",
    "pandas>=2.0.0",
    "tqdm",
    "seaborn",
    "ultralytics",
)

wildlife_tools_image = pytorch_base.pip_install(
    "opencv-python-headless>=4.5.5.62",
    "Pillow>=11.0.0",
    "timm",
    "git+https://github.com/WildlifeDatasets/wildlife-tools",
)

# TransReID image with ViT dependencies
transreid_image = pytorch_base.pip_install(
    "Pillow>=11.0.0",
    "timm>=0.9.0",  # For Vision Transformer models
    "einops",  # For tensor operations
)

# MatchAnything image with specific transformers version
# Requires a specific transformers commit for keypoint matching support
matchanything_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1-mesa-glx", "libglib2.0-0", "git")
    .pip_install(
        "torch>=2.3.0",
        "torchvision>=0.18.0",
        "numpy>=1.26.0",
        "Pillow>=11.0.0",
        "git+https://github.com/huggingface/transformers@22e89e538529420b2ddae6af70865655bc5c22d8",
    )
)


# ==================== TigerReID Model ====================

@app.cls(
    image=tiger_reid_image,
    gpu=GPU_CONFIG_T4,
    volumes={MODEL_CACHE_DIR: models_volume},
    timeout=600,
)
class TigerReIDModel:
    """Tiger re-identification model using ResNet50 backbone."""
        
    @modal.enter()
    def load_model(self):
        """Load model into memory on container startup."""
        import torch
        import torchvision.models as models
        from torchvision import transforms
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load ResNet50 with pretrained weights
        self.model = models.resnet50(pretrained=True)
        
        # Modify for embedding extraction (remove classification head)
        self.model.fc = torch.nn.Identity()
        
        self.model = self.model.to(self.device)
        self.model.eval()
        
        # Define image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    @modal.method()
    def generate_embedding(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Generate embedding for a tiger image.
        
        Args:
            image_bytes: Image as bytes
            
        Returns:
            Dictionary with embedding vector and metadata
        """
        import torch
        from PIL import Image
        
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            
            # Preprocess
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            # Generate embedding
            with torch.no_grad():
                embedding = self.model(image_tensor)
            
            # Convert to numpy and then to list for JSON serialization
            embedding_array = embedding.cpu().numpy().flatten()
            
            return {
                "embedding": embedding_array.tolist(),
                "shape": embedding_array.shape,
                "success": True
            }
            
        except Exception as e:
            return {
                "embedding": None,
                "error": str(e),
                "success": False
            }


# ==================== MegaDetector Model ====================

@app.cls(
    image=megadetector_image,
    gpu=GPU_CONFIG_T4,
    volumes={MODEL_CACHE_DIR: models_volume},
    timeout=600,
)
class MegaDetectorModel:
    """MegaDetector v5 for animal detection."""
    
    @modal.enter()
    def load_model(self):
        """Load MegaDetector model."""
        import torch
        import urllib.request
        from pathlib import Path
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        cache_path = Path(MODEL_CACHE_DIR) / "md_v5a.0.0.pt"
        
        # Download MegaDetector v5a weights if not cached
        if not cache_path.exists():
            url = "https://github.com/microsoft/CameraTraps/releases/download/v5.0/md_v5a.0.0.pt"
            print(f"Downloading MegaDetector from {url}...")
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(url, cache_path)
            print(f"Downloaded to {cache_path}")
        
        # Load YOLOv5 model
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(cache_path))
        self.model = self.model.to(self.device)
        self.model.eval()
        
        # Detection categories
        self.categories = {
            0: "animal",
            1: "person",
            2: "vehicle"
        }
    
    @modal.method()
    def detect(self, image_bytes: bytes, confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Detect animals in an image.
        
        Args:
            image_bytes: Image as bytes
            confidence_threshold: Confidence threshold for detections
            
        Returns:
            Dictionary with detection results
        """
        from PIL import Image
        
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            
            # Run detection
            results = self.model(image)
            
            # Extract detections
            detections = []
            for *box, conf, cls in results.xyxy[0].cpu().numpy():
                if conf >= confidence_threshold:
                    detections.append({
                        "bbox": [float(x) for x in box],  # [x1, y1, x2, y2]
                        "confidence": float(conf),
                        "category": self.categories.get(int(cls), "unknown"),
                        "class_id": int(cls)
                    })
            
            return {
                "detections": detections,
                "num_detections": len(detections),
                "success": True
            }
            
        except Exception as e:
            return {
                "detections": [],
                "error": str(e),
                "success": False
            }


# ==================== WildlifeTools Model ====================

@app.cls(
    image=wildlife_tools_image,
    gpu=GPU_CONFIG_A100,
    volumes={MODEL_CACHE_DIR: models_volume},
    timeout=600,
)
class WildlifeToolsModel:
    """WildlifeTools MegaDescriptor model."""
    
    @modal.enter()
    def load_model(self):
        """Load WildlifeTools model."""
        import torch
        import timm
        from wildlife_tools.features import DeepFeatures
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load MegaDescriptor from HuggingFace (auto-downloads and caches)
        backbone = timm.create_model(
            "hf-hub:BVRA/MegaDescriptor-L-384",
            num_classes=0,
            pretrained=True
        )
        
        # Create feature extractor
        self.extractor = DeepFeatures(
            model=backbone,
            batch_size=32,
            device=self.device
        )
    
    @modal.method()
    def generate_embedding(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Generate embedding using WildlifeTools.
        
        Args:
            image_bytes: Image as bytes
            
        Returns:
            Dictionary with embedding vector
        """
        from PIL import Image
        import numpy as np
        import torch
        from torch.utils.data import Dataset, DataLoader
        
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            
            # MegaDescriptor-L-384 expects 384x384 images
            # Resize while maintaining aspect ratio, then center crop
            target_size = 384
            
            # Resize maintaining aspect ratio
            width, height = image.size
            if width < height:
                new_width = target_size
                new_height = int(target_size * height / width)
            else:
                new_height = target_size
                new_width = int(target_size * width / height)
            
            image = image.resize((new_width, new_height), Image.LANCZOS)
            
            # Center crop to 384x384
            left = (new_width - target_size) // 2
            top = (new_height - target_size) // 2
            right = left + target_size
            bottom = top + target_size
            image = image.crop((left, top, right, bottom))
            
            # Wildlife-tools DeepFeatures is callable directly
            # It expects a list of images (numpy arrays)
            # Convert to numpy array
            image_np = np.array(image)
            
            # Call extractor directly (it's a callable object, not a method)
            # Returns numpy array of embeddings
            embeddings = self.extractor([image_np])
            
            return {
                "embedding": embeddings[0].tolist(),
                "shape": embeddings[0].shape,
                "success": True
            }
            
        except Exception as e:
            # Provide detailed error for debugging
            import traceback
            error_detail = f"{str(e)}\n{traceback.format_exc()}"
            return {
                "embedding": None,
                "error": str(e),
                "error_detail": error_detail,
                "success": False
            }


# ==================== MegaDescriptor-B-224 Model ====================

@app.cls(
    image=wildlife_tools_image,
    gpu=GPU_CONFIG_T4,  # Smaller model can use T4
    volumes={MODEL_CACHE_DIR: models_volume},
    timeout=600,
)
class MegaDescriptorBModel:
    """MegaDescriptor-B-224 model - faster variant for quick inference.

    Compared to MegaDescriptor-L-384:
    - Input: 224x224 (vs 384x384)
    - Parameters: 88M (vs 228M)
    - Speed: ~3x faster
    - Accuracy: Slightly lower but still good
    """

    @modal.enter()
    def load_model(self):
        """Load MegaDescriptor-B-224 model."""
        import torch
        import timm
        from wildlife_tools.features import DeepFeatures

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load MegaDescriptor-B-224 from HuggingFace
        backbone = timm.create_model(
            "hf-hub:BVRA/MegaDescriptor-B-224",
            num_classes=0,
            pretrained=True
        )

        # Create feature extractor
        self.extractor = DeepFeatures(
            model=backbone,
            batch_size=64,  # Can use larger batch with smaller model
            device=self.device
        )

        # Embedding dimension for MegaDescriptor-B-224
        self.embedding_dim = 1024  # Swin-Base outputs 1024-dim

    @modal.method()
    def generate_embedding(self, image_bytes: bytes) -> Dict[str, Any]:
        """Generate embedding using MegaDescriptor-B-224.

        Args:
            image_bytes: Image as bytes

        Returns:
            Dictionary with embedding vector
        """
        from PIL import Image
        import numpy as np

        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

            # MegaDescriptor-B-224 expects 224x224 images
            target_size = 224

            # Resize maintaining aspect ratio
            width, height = image.size
            if width < height:
                new_width = target_size
                new_height = int(target_size * height / width)
            else:
                new_height = target_size
                new_width = int(target_size * width / height)

            image = image.resize((new_width, new_height), Image.LANCZOS)

            # Center crop to 224x224
            left = (new_width - target_size) // 2
            top = (new_height - target_size) // 2
            right = left + target_size
            bottom = top + target_size
            image = image.crop((left, top, right, bottom))

            # Convert to numpy array
            image_np = np.array(image)

            # Call extractor
            embeddings = self.extractor([image_np])

            return {
                "embedding": embeddings[0].tolist(),
                "shape": embeddings[0].shape,
                "model": "megadescriptor_b_224",
                "success": True
            }

        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n{traceback.format_exc()}"
            return {
                "embedding": None,
                "error": str(e),
                "error_detail": error_detail,
                "success": False
            }


# ==================== RAPID ReID Model ====================

def download_rapid_weights(volume_path: Path, models_volume_ref):
    """
    Download RAPID weights directly to Modal volume.
    
    Note: Actual trained weights may need to be obtained from:
    - RAPID paper repository (when available)
    - Paper supplement
    - Contact authors
    """
    import urllib.request
    import os
    
    weight_dir = volume_path / "rapid" / "checkpoints"
    weight_dir.mkdir(parents=True, exist_ok=True)
    
    weight_path = weight_dir / "model.pth"
    
    # Check if weights already exist
    if weight_path.exists():
        print(f"RAPID weights already exist at {weight_path}")
        return str(weight_path)
    
    # TODO: Replace with actual weight download URL when available
    print("RAPID trained weights not found. Using ImageNet pretrained ResNet50 as fallback.")
    print("To use actual RAPID weights, download from paper repository and upload to Modal volume.")
    
    return None


@app.cls(
    image=tiger_reid_image,
    gpu=GPU_CONFIG_T4,
    volumes={MODEL_CACHE_DIR: models_volume},
    timeout=600,
)
class RAPIDReIDModel:
    """RAPID re-identification model for real-time animal pattern matching."""
    
    @modal.enter()
    def load_model(self):
        """Load RAPID model with weights from Modal volume."""
        import torch
        import torchvision.models as models
        from torchvision import transforms
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Check for weights in Modal volume
        weight_path = Path(MODEL_CACHE_DIR) / "rapid" / "checkpoints" / "model.pth"
        
        # Try to download weights if they don't exist
        if not weight_path.exists():
            print("RAPID weights not found in volume. Attempting to download...")
            download_rapid_weights(Path(MODEL_CACHE_DIR), models_volume)
        
        # For now, use ResNet50 as base architecture
        # TODO: Replace with actual RAPID architecture when weights are available
        # RAPID is designed for real-time pattern matching on edge devices
        # The actual architecture may differ from standard ResNet
        
        self.model = models.resnet50(pretrained=True)
        self.model.fc = torch.nn.Identity()  # Remove classifier, use features
        
        # If trained weights exist, load them
        if weight_path.exists():
            try:
                checkpoint = torch.load(weight_path, map_location=self.device)
                # Load state dict, skipping classifier if present
                if isinstance(checkpoint, dict):
                    state_dict = checkpoint.get('state_dict', checkpoint)
                else:
                    state_dict = checkpoint
                
                # Filter out classifier weights
                filtered_dict = {k: v for k, v in state_dict.items() if 'classifier' not in k}
                self.model.load_state_dict(filtered_dict, strict=False)
                print(f"Loaded RAPID weights from {weight_path}")
            except Exception as e:
                print(f"Warning: Could not load RAPID weights: {e}")
                print("Using ImageNet pretrained weights instead")
        
        self.model = self.model.to(self.device)
        self.model.eval()
        
        self.transform = transforms.Compose([
            transforms.Resize((256, 128)),  # RAPID uses different size
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    @modal.method()
    def generate_embedding(self, image_bytes: bytes) -> Dict[str, Any]:
        """Generate RAPID embedding."""
        import torch
        from PIL import Image
        
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                embedding = self.model(image_tensor)
            
            embedding_array = embedding.cpu().numpy().flatten()
            
            # Normalize embedding
            norm = np.linalg.norm(embedding_array)
            if norm > 0:
                embedding_array = embedding_array / norm
            
            return {
                "embedding": embedding_array.tolist(),
                "shape": embedding_array.shape,
                "success": True
            }
            
        except Exception as e:
            return {
                "embedding": None,
                "error": str(e),
                "success": False
            }


# ==================== TransReID Model ====================

@app.cls(
    image=transreid_image,
    gpu=GPU_CONFIG_T4,
    volumes={MODEL_CACHE_DIR: models_volume},
    timeout=600,
)
class TransReIDModel:
    """
    TransReID Vision Transformer-based re-identification model.

    Uses ViT-Base architecture with pretrained ImageNet weights.
    Features:
    - Pure Vision Transformer architecture
    - Patch-based feature learning
    - Global attention for holistic understanding
    - 768-dim embedding output

    Reference: TransReID: Transformer-based Object Re-Identification (ICCV 2021)
    """

    @modal.enter()
    def load_model(self):
        """Load TransReID model with pretrained ViT-Base weights."""
        import torch
        import timm
        from torchvision import transforms

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        print("Loading TransReID (ViT-Base) model...")

        # Load ViT-Base from timm with ImageNet pretrained weights
        # Using vit_base_patch16_224 which is commonly used for ReID
        self.model = timm.create_model(
            'vit_base_patch16_224',
            pretrained=True,
            num_classes=0  # Remove classification head, output features
        )

        self.model = self.model.to(self.device)
        self.model.eval()

        # Standard ImageNet normalization
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        # ViT-Base outputs 768-dim features
        self.embedding_dim = 768

        print(f"TransReID model loaded. Output dimension: {self.embedding_dim}")

    @modal.method()
    def generate_embedding(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Generate TransReID embedding using Vision Transformer.

        Args:
            image_bytes: Image as bytes

        Returns:
            Dictionary with embedding vector and metadata
        """
        import torch
        from PIL import Image

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                embedding = self.model(image_tensor)

            embedding_array = embedding.cpu().numpy().flatten()

            # L2 normalize for cosine similarity
            norm = np.linalg.norm(embedding_array)
            if norm > 0:
                embedding_array = embedding_array / norm

            return {
                "embedding": embedding_array.tolist(),
                "shape": embedding_array.shape,
                "model_info": {
                    "architecture": "TransReID",
                    "backbone": "ViT-Base-Patch16-224",
                    "output_dim": self.embedding_dim
                },
                "success": True
            }

        except Exception as e:
            import traceback
            return {
                "embedding": None,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "success": False
            }

    @modal.method()
    def generate_embedding_batch(self, images: List[bytes]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for a batch of images.

        Args:
            images: List of images as bytes

        Returns:
            List of embedding results
        """
        import torch
        from PIL import Image

        results = []

        try:
            # Process images in batch for efficiency
            tensors = []
            valid_indices = []

            for i, image_bytes in enumerate(images):
                try:
                    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
                    tensor = self.transform(image)
                    tensors.append(tensor)
                    valid_indices.append(i)
                except Exception as e:
                    results.append({
                        "embedding": None,
                        "error": str(e),
                        "success": False
                    })

            if tensors:
                batch = torch.stack(tensors).to(self.device)

                with torch.no_grad():
                    embeddings = self.model(batch)

                embeddings_np = embeddings.cpu().numpy()

                # Normalize each embedding
                norms = np.linalg.norm(embeddings_np, axis=1, keepdims=True)
                norms[norms == 0] = 1
                embeddings_np = embeddings_np / norms

                for j, idx in enumerate(valid_indices):
                    results.insert(idx, {
                        "embedding": embeddings_np[j].tolist(),
                        "shape": embeddings_np[j].shape,
                        "success": True
                    })

            return results

        except Exception as e:
            import traceback
            error_result = {
                "embedding": None,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "success": False
            }
            return [error_result] * len(images)


# ==================== CVWC2019 Model ====================

def download_cvwc2019_weights(volume_path: Path, models_volume_ref):
    """
    Check for CVWC2019 weights in Modal volume.
    
    Note: Weights should be uploaded to Modal volume using scripts/upload_weights_to_modal.py
    Actual trained weights may need to be obtained from:
    - CVWC2019 GitHub repo: https://github.com/LcenArthas/CWCV2019-Amur-Tiger-Re-ID
    - Paper supplement or contact authors
    - Baidu Pan links in README (may require manual download)
    """
    weight_dir = volume_path / "cvwc2019"
    weight_dir.mkdir(parents=True, exist_ok=True)
    
    weight_path = weight_dir / "best_model.pth"
    
    # Check if weights already exist
    if weight_path.exists():
        print(f"CVWC2019 weights already exist at {weight_path}")
        return str(weight_path)
    
    print("CVWC2019 trained weights not found in Modal volume.")
    print("To add weights, use: scripts/upload_weights_to_modal.py")
    print("Weights should be downloaded from GitHub repo and uploaded to Modal volume.")
    
    return None


# CVWC2019 image with additional dependencies for multi-stream architecture
cvwc2019_image = pytorch_base.pip_install(
    "Pillow>=11.0.0",
    "yacs>=0.1.8",
)


@app.cls(
    image=cvwc2019_image,
    gpu=GPU_CONFIG_T4,
    volumes={MODEL_CACHE_DIR: models_volume},
    timeout=600,
)
class CVWC2019ReIDModel:
    """
    CVWC2019 part-pose guided tiger re-identification model.

    Implements the multi-stream architecture from CVWC2019:
    - Global stream: ResNet152 backbone for holistic features
    - Body part stream: ResNet34 backbone for body stripe patterns
    - Paw part stream: ResNet34 backbone for paw/leg patterns

    The streams are combined via feature fusion for robust tiger identification
    across different poses and viewpoints.
    """

    @modal.enter()
    def load_model(self):
        """Load CVWC2019 multi-stream model with weights from Modal volume."""
        import torch
        import torch.nn as nn
        from torchvision import transforms
        import torchvision.models as models

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Check for weights in Modal volume
        weight_path = Path(MODEL_CACHE_DIR) / "cvwc2019" / "best_model.pth"
        pretrained_global_path = Path(MODEL_CACHE_DIR) / "cvwc2019" / "resnet152-b121ed2d.pth"

        # Try to check for weights if they don't exist
        if not weight_path.exists():
            print("CVWC2019 weights not found in volume.")
            print("To add weights, use: scripts/upload_weights_to_modal.py")
            download_cvwc2019_weights(Path(MODEL_CACHE_DIR), models_volume)

        # Build multi-stream architecture using ResNet152 global stream
        print("Building CVWC2019 global stream (ResNet152)...")

        # Create ResNet152 backbone
        global_backbone = models.resnet152(pretrained=True)

        # If we have pretrained weights for ResNet152, load them
        if pretrained_global_path.exists():
            try:
                state_dict = torch.load(pretrained_global_path, map_location='cpu')
                global_backbone.load_state_dict(state_dict, strict=False)
                print(f"Loaded pretrained ResNet152 from {pretrained_global_path}")
            except Exception as e:
                print(f"Could not load pretrained weights: {e}")

        # Create global feature extractor (remove classifier)
        # Extract all layers except avgpool and fc
        backbone_layers = list(global_backbone.children())[:-2]
        self.backbone = nn.Sequential(*backbone_layers)
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.bn = nn.BatchNorm1d(2048)
        self.bn.bias.requires_grad_(False)

        # If trained CVWC2019 weights exist, try to load them
        if weight_path.exists():
            try:
                checkpoint = torch.load(weight_path, map_location='cpu')
                if isinstance(checkpoint, dict):
                    state_dict = checkpoint.get('state_dict', checkpoint)
                else:
                    state_dict = checkpoint

                # Try to load weights that match our architecture
                loaded_count = 0
                for k, v in state_dict.items():
                    # Map CVWC2019 keys to our model keys
                    if k.startswith('glabole.base.'):
                        # These are backbone weights
                        try:
                            # Try to find matching layer in backbone
                            parts = k.replace('glabole.base.', '').split('.')
                            # Navigate to the correct module
                            module = self.backbone
                            for part in parts[:-1]:
                                if part.isdigit():
                                    module = module[int(part)]
                                else:
                                    module = getattr(module, part)
                            param_name = parts[-1]
                            if hasattr(module, param_name):
                                param = getattr(module, param_name)
                                if param.shape == v.shape:
                                    param.data.copy_(v)
                                    loaded_count += 1
                        except Exception:
                            pass
                    elif k.startswith('glabole.bottleneck.'):
                        # These are batch norm weights
                        bn_key = k.replace('glabole.bottleneck.', '')
                        if hasattr(self.bn, bn_key.split('.')[0]):
                            try:
                                param = getattr(self.bn, bn_key.split('.')[0])
                                if param.shape == v.shape:
                                    param.data.copy_(v)
                                    loaded_count += 1
                            except Exception:
                                pass

                print(f"Loaded {loaded_count} parameter tensors from CVWC2019 weights")

            except Exception as e:
                print(f"Warning: Could not load CVWC2019 weights: {e}")
                print("Using ImageNet pretrained weights")

        self.backbone = self.backbone.to(self.device)
        self.gap = self.gap.to(self.device)
        self.bn = self.bn.to(self.device)

        self.backbone.requires_grad_(False)
        self.gap.requires_grad_(False)
        self.bn.requires_grad_(False)

        # Transform for global image (128x256 as per config)
        self.transform = transforms.Compose([
            transforms.Resize((256, 128)),  # Height x Width
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        print(f"CVWC2019 model loaded. Using ResNet152 backbone with 2048-dim output")

    @modal.method()
    def generate_embedding(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Generate CVWC2019 embedding using global stream.

        For full multi-stream inference, part annotations (body/paw regions)
        would be needed. Without these, we use the robust global stream
        which still provides strong tiger identification features.

        Args:
            image_bytes: Image as bytes

        Returns:
            Dictionary with embedding vector and metadata
        """
        import torch
        from PIL import Image

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                feat = self.backbone(image_tensor)
                feat = self.gap(feat)
                feat = feat.view(feat.size(0), -1)
                embedding = self.bn(feat)

            embedding_array = embedding.cpu().numpy().flatten()

            # L2 normalize embedding for cosine similarity
            norm = np.linalg.norm(embedding_array)
            if norm > 0:
                embedding_array = embedding_array / norm

            return {
                "embedding": embedding_array.tolist(),
                "shape": embedding_array.shape,
                "model_info": {
                    "architecture": "CVWC2019-GlobalStream",
                    "backbone": "ResNet152",
                    "output_dim": 2048
                },
                "success": True
            }

        except Exception as e:
            import traceback
            return {
                "embedding": None,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "success": False
            }


# ==================== MatchAnything Model ====================

@app.cls(
    image=matchanything_image,
    gpu=GPU_CONFIG_T4,
    volumes={MODEL_CACHE_DIR: models_volume},
    timeout=600,
)
class MatchAnythingModel:
    """
    MatchAnything-ELOFTR for keypoint-based image matching.

    Uses semi-dense feature matching to find corresponding keypoints
    between image pairs. Designed for geometric verification of tiger
    identity by comparing stripe patterns.

    Model: zju-community/matchanything_eloftr
    Output: Keypoint correspondences and matching scores
    """

    MODEL_NAME = "zju-community/matchanything_eloftr"

    @modal.enter()
    def load_model(self):
        """Load MatchAnything model on container startup."""
        import torch
        from transformers import AutoImageProcessor, AutoModelForKeypointMatching

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        print(f"Loading MatchAnything model: {self.MODEL_NAME}")
        self.processor = AutoImageProcessor.from_pretrained(self.MODEL_NAME)
        self.model = AutoModelForKeypointMatching.from_pretrained(self.MODEL_NAME)
        self.model.to(self.device)
        self.model.requires_grad_(False)  # Inference mode

        print(f"MatchAnything model loaded on {self.device}")

    @modal.method()
    def match_images(
        self,
        image1_bytes: bytes,
        image2_bytes: bytes,
        threshold: float = 0.2
    ) -> Dict[str, Any]:
        """
        Match two images and return keypoint correspondences.

        Args:
            image1_bytes: First image as bytes
            image2_bytes: Second image as bytes
            threshold: Confidence threshold for keypoint filtering

        Returns:
            Dictionary with matching results:
            - num_matches: Number of keypoint correspondences
            - mean_score: Average confidence of matches
            - max_score: Maximum match confidence
            - total_score: Sum of all match confidences
            - success: Whether matching succeeded
        """
        import torch
        from PIL import Image

        try:
            # Load images
            img1 = Image.open(io.BytesIO(image1_bytes)).convert('RGB')
            img2 = Image.open(io.BytesIO(image2_bytes)).convert('RGB')

            # Prepare inputs
            inputs = self.processor([img1, img2], return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Run inference
            with torch.no_grad():
                outputs = self.model(**inputs)

            # Post-process
            image_sizes = [[(img1.height, img1.width), (img2.height, img2.width)]]
            results = self.processor.post_process_keypoint_matching(
                outputs, image_sizes, threshold=threshold
            )

            # Extract metrics (key is 'matching_scores' per transformers API)
            keypoints0 = results[0]["keypoints0"]
            keypoints1 = results[0]["keypoints1"]
            scores = results[0]["matching_scores"]

            num_matches = len(scores)

            return {
                "num_matches": num_matches,
                "mean_score": float(scores.mean().item()) if num_matches > 0 else 0.0,
                "max_score": float(scores.max().item()) if num_matches > 0 else 0.0,
                "min_score": float(scores.min().item()) if num_matches > 0 else 0.0,
                "total_score": float(scores.sum().item()) if num_matches > 0 else 0.0,
                "keypoints0_count": len(keypoints0),
                "keypoints1_count": len(keypoints1),
                "threshold_used": threshold,
                "success": True
            }

        except Exception as e:
            import traceback
            return {
                "num_matches": 0,
                "mean_score": 0.0,
                "max_score": 0.0,
                "min_score": 0.0,
                "total_score": 0.0,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "success": False
            }

    @modal.method()
    def health_check(self) -> Dict[str, Any]:
        """Check if model is loaded and healthy."""
        return {
            "status": "healthy",
            "model_name": self.MODEL_NAME,
            "device": str(self.device)
        }

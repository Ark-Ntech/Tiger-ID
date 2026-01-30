"""
Modal application for Tiger ID ML model inference.

This module provides serverless GPU compute for all ML models:
- TigerReID: Tiger re-identification embeddings
- MegaDetector: Animal detection in images
- RAPID: Re-identification model
- WildlifeTools: MegaDescriptor/WildFusion embeddings
- CVWC2019: Part-pose guided tiger re-identification
- OmniVinci: Video analysis (NVIDIA API)

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

omnivinci_image = pytorch_base.pip_install(
    "transformers>=4.46.0",
    "accelerate>=0.34.0",
    "Pillow>=11.0.0",
    "av>=11.0.0",
    "librosa>=0.10.0",
    "soundfile>=0.12.0",
    "einops",  # Required by OmniVinci
    "openai-whisper",  # Required by OmniVinci for audio
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


# ==================== OmniVinci Model ====================

@app.cls(
    image=omnivinci_image,
    gpu=GPU_CONFIG_A100,  # OmniVinci needs a powerful GPU
    volumes={MODEL_CACHE_DIR: models_volume},
    timeout=900,  # Longer timeout for video processing
)
class OmniVinciModel:
    """
    OmniVinci video analysis using NVIDIA's open-source model.
    
    Model: https://huggingface.co/nvidia/omnivinci
    GitHub: https://github.com/NVlabs/OmniVinci
    License: Apache 2.0
    """
    
    @modal.enter()
    def load_model(self):
        """Load OmniVinci model from HuggingFace."""
        from transformers import AutoProcessor, AutoModel, AutoConfig
        import torch
        
        print("Loading OmniVinci model from HuggingFace...")
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = "nvidia/omnivinci"
        
        # Load model configuration
        self.config = AutoConfig.from_pretrained(
            self.model_path,
            trust_remote_code=True
        )
        
        # Load the model
        self.model = AutoModel.from_pretrained(
            self.model_path,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # Load processor
        self.processor = AutoProcessor.from_pretrained(
            self.model_path,
            trust_remote_code=True
        )
        
        # Set default generation config
        self.generation_config = self.model.default_generation_config
        self.generation_config.update({
            "max_new_tokens": 1024,
            "max_length": 99999999
        })
        
        # Configure video/audio settings
        self.model.config.load_audio_in_video = True
        self.processor.config.load_audio_in_video = True
        self.model.config.num_video_frames = 128
        self.processor.config.num_video_frames = 128
        self.model.config.audio_chunk_length = "max_3600"
        self.processor.config.audio_chunk_length = "max_3600"
        
        print("OmniVinci model loaded successfully!")
    
    @modal.method()
    def analyze_video(
        self, 
        video_bytes: bytes,
        prompt: str = "Assess the video, followed by a detailed description of its video and audio contents.",
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze video using OmniVinci model with optional agentic tool calling.
        
        Args:
            video_bytes: Video as bytes
            prompt: Analysis prompt
            tools: Optional list of available tools for agentic calling
            tool_callback_url: Optional URL to call back for tool execution
            
        Returns:
            Dictionary with analysis results and any tool calls
        """
        import tempfile
        import os
        
        try:
            # Save video bytes to temporary file (OmniVinci needs file path)
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
                tmp_file.write(video_bytes)
                video_path = tmp_file.name
            
            try:
                # Enhance prompt with tool information if tools are provided
                enhanced_prompt = prompt
                if tools:
                    tool_descriptions = "\n".join([
                        f"- {tool.get('name', 'unknown')}: {tool.get('description', 'No description')}"
                        for tool in tools
                    ])
                    enhanced_prompt = f"""{prompt}

Available Tools (you can request to use these by describing what you need):
{tool_descriptions}

If you need to use a tool, describe what you want to do and I will execute it for you."""
                
                # Prepare conversation
                # For text-only queries, we can use just text without video
                # OmniVinci can handle text-only input
                if len(video_bytes) < 100:  # Minimal video (placeholder) - treat as text-only
                    conversation = [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": enhanced_prompt}
                        ]
                    }]
                else:
                    conversation = [{
                        "role": "user",
                        "content": [
                            {"type": "video", "video": video_path},
                            {"type": "text", "text": enhanced_prompt}
                        ]
                    }]
                
                # Apply chat template
                text = self.processor.apply_chat_template(
                    conversation,
                    tokenize=False,
                    add_generation_prompt=True
                )
                
                # Process inputs
                inputs = self.processor([text])
                
                # Generate response
                output_ids = self.model.generate(
                    input_ids=inputs.input_ids,
                    media=getattr(inputs, 'media', None),
                    media_config=getattr(inputs, 'media_config', None),
                    generation_config=self.generation_config,
                )
                
                # Decode output
                response = self.processor.tokenizer.batch_decode(
                    output_ids,
                    skip_special_tokens=True
                )[0]
                
                result = {
                    "analysis": response,
                    "prompt": prompt,
                    "success": True
                }
                
                # Check if response contains tool requests
                # OmniVinci may request tools in natural language
                # We'll parse these and return them for execution
                if tools and tool_callback_url:
                    # Simple pattern matching for tool requests
                    # In production, this could use structured output or function calling
                    tool_requests = []
                    response_lower = response.lower()
                    for tool in tools:
                        tool_name = tool.get('name', '').lower()
                        if tool_name in response_lower:
                            tool_requests.append({
                                "tool": tool.get('name'),
                                "reason": "Requested in analysis",
                                "arguments": {}  # Would be parsed from response
                            })
                    
                    if tool_requests:
                        result["tool_requests"] = tool_requests
                        result["tool_callback_url"] = tool_callback_url
                
                return result
                
            finally:
                # Clean up temporary file
                if os.path.exists(video_path):
                    os.unlink(video_path)
            
        except Exception as e:
            import traceback
            error_type = type(e).__name__
            error_msg = str(e)
            tb = traceback.format_exc()
            
            # Log detailed error
            print(f"OmniVinci error ({error_type}): {error_msg}")
            print(f"Traceback:\n{tb}")
            
            # Provide more specific error messages
            if "CUDA" in error_msg or "cuda" in error_msg.lower():
                error_msg = f"GPU/CUDA error: {error_msg}. Check GPU availability and configuration."
            elif "out of memory" in error_msg.lower() or "OOM" in error_msg:
                error_msg = f"Out of memory: {error_msg}. Video may be too large or GPU memory insufficient."
            elif "timeout" in error_msg.lower():
                error_msg = f"Processing timeout: {error_msg}. Video may be too long."
            elif "model" in error_msg.lower() and ("not found" in error_msg.lower() or "load" in error_msg.lower()):
                error_msg = f"Model loading error: {error_msg}. Check model files and configuration."
            elif "processor" in error_msg.lower() or "tokenizer" in error_msg.lower():
                error_msg = f"Processing error: {error_msg}. Check model processor configuration."
            elif "video" in error_msg.lower() and ("format" in error_msg.lower() or "codec" in error_msg.lower()):
                error_msg = f"Video format error: {error_msg}. Unsupported video format or codec."
            
            return {
                "analysis": None,
                "error": error_msg,
                "error_type": error_type,
                "traceback": tb,
                "success": False
            }
    
    @modal.method()
    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str = "Analyze this image in detail and describe what you see."
    ) -> Dict[str, Any]:
        """
        Analyze an image using OmniVinci's omni-modal understanding.
        
        Based on example_mini_image.py from OmniVinci GitHub repository.
        Provides detailed visual analysis beyond pattern matching.
        
        Args:
            image_bytes: Image as bytes
            prompt: Analysis prompt  
            
        Returns:
            Dictionary with detailed analysis
        """
        from PIL import Image
        import tempfile
        import os
        
        try:
            # Save image to temporary file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                tmp_file.write(image_bytes)
                image_path = tmp_file.name
            
            try:
                # Prepare conversation with image
                # OmniVinci handles images similarly to videos
                conversation = [{
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image_path},
                        {"type": "text", "text": prompt}
                    ]
                }]
                
                # Apply chat template
                text = self.processor.apply_chat_template(
                    conversation,
                    tokenize=False,
                    add_generation_prompt=True
                )
                
                # Process inputs
                inputs = self.processor([text])
                
                # Generate response
                output_ids = self.model.generate(
                    input_ids=inputs.input_ids,
                    media=getattr(inputs, 'media', None),
                    media_config=getattr(inputs, 'media_config', None),
                    generation_config=self.generation_config,
                )
                
                # Decode output
                response = self.processor.tokenizer.batch_decode(
                    output_ids,
                    skip_special_tokens=True
                )[0]
                
                print(f"OmniVinci image analysis completed: {len(response)} characters")
                
                return {
                    "analysis": response,
                    "prompt": prompt,
                    "success": True
                }
            
            finally:
                # Clean up temp file
                if os.path.exists(image_path):
                    os.unlink(image_path)
        
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"OmniVinci image analysis error: {e}")
            print(f"Traceback: {error_trace}")
            return {
                "analysis": None,
                "error": str(e),
                "traceback": error_trace,
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


@app.cls(
    image=tiger_reid_image,
    gpu=GPU_CONFIG_T4,
    volumes={MODEL_CACHE_DIR: models_volume},
    timeout=600,
)
class CVWC2019ReIDModel:
    """CVWC2019 part-pose guided tiger re-identification model."""
    
    @modal.enter()
    def load_model(self):
        """Load CVWC2019 model with weights from Modal volume."""
        import torch
        import torchvision.models as models
        from torchvision import transforms
        import sys
        import os
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Check for weights in Modal volume
        weight_path = Path(MODEL_CACHE_DIR) / "cvwc2019" / "best_model.pth"
        
        # Try to check for weights if they don't exist
        if not weight_path.exists():
            print("CVWC2019 weights not found in volume.")
            print("To add weights, use: scripts/upload_weights_to_modal.py")
            download_cvwc2019_weights(Path(MODEL_CACHE_DIR), models_volume)
        
        # For now, use ResNet50 as base architecture
        # TODO: Replace with actual CVWC2019 part-pose architecture when weights are available
        # The full architecture requires:
        # - Global stream (ResNet152 backbone)
        # - Part body stream (ResNet34 backbone)
        # - Part paw stream (ResNet34 backbone)
        # - Pipeline to combine features
        # 
        # To implement full architecture:
        # 1. Add data/models/cvwc2019 to Modal image
        # 2. Import from data.models.cvwc2019.modeling import build_model
        # 3. Build model with proper config
        
        # Simplified version: Use ResNet50 with ImageNet pretrained
        # This will be replaced with actual CVWC2019 architecture when weights are available
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
                print(f"Loaded CVWC2019 weights from {weight_path}")
            except Exception as e:
                print(f"Warning: Could not load CVWC2019 weights: {e}")
                print("Using ImageNet pretrained weights instead")
        
        self.model = self.model.to(self.device)
        self.model.eval()
        
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    @modal.method()
    def generate_embedding(self, image_bytes: bytes) -> Dict[str, Any]:
        """Generate CVWC2019 embedding."""
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


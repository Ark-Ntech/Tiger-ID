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

# Create Modal images with dependencies
tiger_reid_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch>=2.3.0,<2.10.0",
        "torchvision>=0.18.0,<0.25.0",
        "Pillow>=11.0.0",
        "numpy>=1.26.0,<2.0.0",
    )
)

megadetector_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch>=2.3.0,<2.10.0",
        "torchvision>=0.18.0,<0.25.0",
        "Pillow>=11.0.0",
        "numpy>=1.26.0,<2.0.0",
        "ultralytics",
    )
)

wildlife_tools_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")  # Install git first
    .pip_install(
        "torch>=2.3.0,<2.10.0",
        "torchvision>=0.18.0,<0.25.0",
        "Pillow>=11.0.0",
        "numpy>=1.26.0,<2.0.0",
        "timm",
        "git+https://github.com/WildlifeDatasets/wildlife-tools",
    )
)

omnivinci_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch>=2.3.0,<2.10.0",
        "transformers>=4.46.0",
        "accelerate>=0.34.0",
        "Pillow>=11.0.0",
        "numpy>=1.26.0,<2.0.0",
        "av>=11.0.0",  # For video processing
        "librosa>=0.10.0",  # For audio processing
        "soundfile>=0.12.0",
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
        
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            
            # Generate embedding
            embedding = self.extractor([np.array(image)])
            
            return {
                "embedding": embedding[0].tolist(),
                "shape": embedding[0].shape,
                "success": True
            }
            
        except Exception as e:
            return {
                "embedding": None,
                "error": str(e),
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


# ==================== RAPID ReID Model ====================

@app.cls(
    image=tiger_reid_image,
    gpu=GPU_CONFIG_T4,
    volumes={MODEL_CACHE_DIR: models_volume},
    timeout=600,
)
class RAPIDReIDModel:
    """RAPID re-identification model."""
    
    @modal.enter()
    def load_model(self):
        """Load RAPID model."""
        import torch
        import torchvision.models as models
        from torchvision import transforms
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load model (placeholder with ResNet50 pretrained)
        # TODO: Add RAPID model when official weights are available
        self.model = models.resnet50(pretrained=True)
        self.model.fc = torch.nn.Identity()
        
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
        """Load CVWC2019 model."""
        import torch
        import torchvision.models as models
        from torchvision import transforms
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load model (placeholder with ResNet50 pretrained)
        # TODO: Add CVWC2019 model when official weights are available
        self.model = models.resnet50(pretrained=True)
        self.model.fc = torch.nn.Identity()
        
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



# ==================== Hermes-3-Llama-3.1-8B Chat Orchestrator ====================

hermes_chat_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch>=2.3.0",
        "transformers>=4.46.0",
        "accelerate>=0.34.2",
        "bitsandbytes>=0.44.1",  # For 8-bit quantization
    )
)


@app.cls(
    image=hermes_chat_image,
    gpu=GPU_CONFIG_T4,  # Hermes-3-8B runs efficiently on T4
    volumes={MODEL_CACHE_DIR: models_volume},
    timeout=300,
    scaledown_window=300,  # Renamed from container_idle_timeout
)
class HermesChatModel:
    """Hermes-3-Llama-3.1-8B chat orchestrator with native tool calling."""
    
    @modal.enter()
    def load_model(self):
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
        
        model_id = "NousResearch/Hermes-3-Llama-3.1-8B"
        print(f"Loading Hermes-3 chat model: {model_id}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_id, cache_dir=MODEL_CACHE_DIR, trust_remote_code=True
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, cache_dir=MODEL_CACHE_DIR, torch_dtype=torch.float16,
            device_map="auto", load_in_8bit=True, trust_remote_code=True
        )
        self.model.eval()
        print("Hermes-3 model loaded successfully")
    
    @modal.method()
    def chat(self, message: str, tools: Optional[List[Dict[str, Any]]] = None,
             conversation_history: Optional[List[Dict[str, str]]] = None,
             max_tokens: int = 2048, temperature: float = 0.7) -> Dict[str, Any]:
        import torch, json, re
        try:
            messages = conversation_history or []
            if tools:
                tool_desc = "\n".join([f"- {t.get('name')}: {t.get('description')}" for t in tools[:20]])
                system_content = f"You are an AI assistant for tiger conservation. Tools: {tool_desc}. Use JSON for tool calls: {{\"tool_call\": {{\"name\": \"x\", \"arguments\": {{}}}}}}"
                messages = [{"role": "system", "content": system_content}] + messages
            messages.append({"role": "user", "content": message})
            text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=4096).to(self.model.device)
            with torch.no_grad():
                output_ids = self.model.generate(**inputs, max_new_tokens=max_tokens, temperature=temperature,
                                                  do_sample=temperature > 0, pad_token_id=self.tokenizer.eos_token_id)
            response_text = self.tokenizer.decode(output_ids[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            tool_calls = []
            if tools and "tool_call" in response_text:
                try:
                    json_match = re.search(r'\{["\']tool_call["\']\s*:\s*\{.*?\}\s*\}', response_text, re.DOTALL)
                    if json_match:
                        tool_call_data = json.loads(json_match.group())
                        tool_calls.append(tool_call_data.get("tool_call"))
                        response_text = response_text[:json_match.start()] + response_text[json_match.end():]
                        response_text = response_text.strip()
                except: pass
            return {"response": response_text, "tool_calls": tool_calls, "success": True, "model": "Hermes-3-Llama-3.1-8B"}
        except Exception as e:
            import traceback
            return {"response": None, "tool_calls": [], "error": str(e), "error_type": type(e).__name__,
                    "traceback": traceback.format_exc(), "success": False}

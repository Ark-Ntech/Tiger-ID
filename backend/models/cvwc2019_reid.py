"""CVWC2019 Amur Tiger Re-ID integration

Part-pose guided approach for tiger re-identification from CVWC 2019 workshop.
Paper: https://openaccess.thecvf.com/content_ICCVW_2019/papers/CVWC/Liu_Part-Pose_Guided_Amur_Tiger_Re-Identification_ICCVW_2019_paper.pdf
"""

from typing import Optional, Dict, Any, List
import sys
import io
from pathlib import Path
import numpy as np
from PIL import Image
import torch
import torchvision.transforms as transforms

from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)

# Add CVWC2019 to path if available
CVWC2019_PATH = Path(__file__).parent.parent.parent.parent / "data" / "models" / "cvwc2019"
if CVWC2019_PATH.exists():
    sys.path.insert(0, str(CVWC2019_PATH))


class CVWC2019ReIDModel:
    """Wrapper for CVWC2019 part-pose guided tiger Re-ID model"""
    
    def __init__(
        self, 
        model_path: Optional[str] = None,
        config_file: Optional[str] = None,
        device: str = "cuda",
        num_classes: int = 92  # Default ATRW has 92 tigers
    ):
        """
        Initialize CVWC2019 Re-ID model
        
        Args:
            model_path: Path to model checkpoint (required)
            config_file: Path to YAML config file (defaults to tiger.yml)
            device: Device to run model on (cuda or cpu)
            num_classes: Number of classes (default: 92 for ATRW)
        """
        settings = get_settings()
        self.model_path = model_path or settings.models.cvwc2019.path
        self.config_file = config_file or (
            str(CVWC2019_PATH / "configs" / "tiger.yml") if CVWC2019_PATH.exists() else None
        )
        self.device = device
        self.num_classes = num_classes
        self.model = None
        self.eval_model = None
        self.cfg = None
        self.similarity_threshold = settings.models.cvwc2019.similarity_threshold
        
    def load_model(self):
        """Load the CVWC2019 model"""
        if self.model is not None:
            return
        
        try:
            if not CVWC2019_PATH.exists():
                logger.warning("CVWC2019 repository not found at expected path")
                raise ImportError("CVWC2019 repository not found")
            
            if not os.path.exists(self.model_path):
                logger.warning(f"CVWC2019 model weights not found at {self.model_path}")
                logger.info("Please download trained weights and place them in the model_path")
                raise FileNotFoundError(f"Model weights not found: {self.model_path}")
            
            try:
                from config import cfg
                from modeling import build_model
                
                # Load config
                if self.config_file and os.path.exists(self.config_file):
                    cfg.merge_from_file(self.config_file)
                else:
                    logger.warning(f"Config file not found: {self.config_file}, using defaults")
                
                # Configure for inference
                cfg.MODEL.PRETRAIN_CHOICE = 'self'
                cfg.TEST.WEIGHT = self.model_path
                cfg.MODEL.DEVICE = self.device
                cfg.MODEL.DEVICE_ID = '0' if self.device == 'cuda' else ''
                cfg.IS_DEMO = True
                cfg.freeze()
                
                self.cfg = cfg
                
                logger.info(f"Loading CVWC2019 part-pose guided Re-ID model from {self.model_path}")
                
                # Build model
                self.model, self.eval_model = build_model(cfg, self.num_classes)
                
                # Load weights
                if self.device == 'cuda':
                    self.model.load_param(self.model_path)
                else:
                    self.model.load_param(self.model_path, cpu=True)
                
                self.model.eval()
                self.eval_model.eval()
                
                if self.device == 'cuda':
                    self.model = self.model.to(self.device)
                    self.eval_model = self.eval_model.to(self.device)
                
                logger.info("CVWC2019 model loaded successfully")
                return
                
            except ImportError as e:
                logger.warning(f"Could not import CVWC2019 modules: {e}")
                logger.info("CVWC2019 requires PyTorch 1.0.1 and specific dependencies")
                raise
            except Exception as e:
                logger.warning(f"Failed to load CVWC2019 model: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Failed to load CVWC2019 model: {e}")
            raise
    
    def _preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """
        Preprocess image for CVWC2019 model
        
        Args:
            image: PIL Image
            
        Returns:
            Preprocessed image tensor
        """
        # Default transforms from CVWC2019 config
        # Size: typically 128x256 or 256x512 depending on model
        size = self.cfg.INPUT.SIZE_TEST if self.cfg else [128, 256]
        
        transform = transforms.Compose([
            transforms.Resize(size),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return transform(image)
    
    def generate_embedding(self, image_data: bytes) -> Optional[np.ndarray]:
        """
        Generate embedding for an image using part-pose guided approach
        
        Args:
            image_data: Image bytes
            
        Returns:
            Embedding vector (numpy array) or None if failed
        """
        if self.model is None:
            self.load_model()
        
        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Preprocess image
            img_tensor = self._preprocess_image(image)
            
            # For part-pose guided model, we need body and paw images too
            # For simplicity, we use the same image for all streams
            # In production, you would extract body and paw regions separately
            img_body = img_tensor.clone()
            img_part = img_tensor.clone()
            
            # Create batch
            img_batch = img_tensor.unsqueeze(0).to(self.device)
            img_body_batch = img_body.unsqueeze(0).to(self.device)
            img_part_batch = img_part.unsqueeze(0).to(self.device)
            
            # Extract features
            with torch.no_grad():
                if hasattr(self.eval_model, 'forward'):
                    # Use eval model (global stream) for feature extraction
                    _, global_feature = self.eval_model(img_batch)
                    feature = global_feature.cpu().numpy()[0]
                else:
                    # Fallback to full model
                    output = self.model(img_batch, img_body_batch, img_part_batch)
                    # Extract global feature (4th element in output)
                    if len(output) >= 4:
                        global_feature = output[3]  # global_feature
                        feature = global_feature.cpu().numpy()[0]
                    else:
                        feature = output[0].cpu().numpy()[0]
            
            return feature
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def compare_embeddings(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compare two embeddings and return similarity score using cosine similarity
        
        Args:
            embedding1: First embedding vector (numpy array)
            embedding2: Second embedding vector (numpy array)
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            # Normalize embeddings
            from sklearn.preprocessing import normalize
            
            embedding1 = embedding1.reshape(1, -1)
            embedding2 = embedding2.reshape(1, -1)
            
            embedding1_norm = normalize(embedding1, norm='l2')
            embedding2_norm = normalize(embedding2, norm='l2')
            
            # Compute cosine similarity
            similarity = np.dot(embedding1_norm, embedding2_norm.T)[0, 0]
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to compare embeddings: {e}")
            return 0.0


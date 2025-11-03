"""Siamese network for tiger stripe re-identification"""

import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision.models import resnet50
from PIL import Image
import numpy as np
from typing import Optional, List, Tuple
import io

from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)


class SiameseNetwork(nn.Module):
    """Siamese network for tiger re-identification"""
    
    def __init__(self, embedding_dim: int = 512):
        super(SiameseNetwork, self).__init__()
        # Use ResNet50 as backbone
        resnet = resnet50(pretrained=True)
        # Remove final fully connected layer
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])
        
        # Add embedding layer
        self.embedding = nn.Sequential(
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(2048, embedding_dim),
            nn.BatchNorm1d(embedding_dim),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(embedding_dim, embedding_dim)
        )
        
        # Normalize embeddings
        self.normalize = nn.functional.normalize
    
    def forward(self, x):
        """Forward pass"""
        features = self.backbone(x)
        embedding = self.embedding(features)
        embedding = self.normalize(embedding, p=2, dim=1)
        return embedding


class TigerReIDModel:
    """Tiger stripe re-identification model using Siamese network"""
    
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize tiger re-ID model
        
        Args:
            model_path: Path to model checkpoint
            device: Device to run model on (cuda or cpu). If None, auto-detects.
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        settings = get_settings()
        self.model_path = model_path or settings.models.reid_path
        self.embedding_dim = settings.models.reid_embedding_dim
        self.model = SiameseNetwork(embedding_dim=self.embedding_dim)
        self.model.to(device)
        self.model.eval()
        
        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # Horizontal flip for left/right flank support
        self.flip_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(p=1.0),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    async def load_model(self):
        """Load the re-ID model"""
        try:
            if os.path.exists(self.model_path):
                logger.info("Loading re-ID model from path", path=self.model_path)
                checkpoint = torch.load(self.model_path, map_location=self.device)
                self.model.load_state_dict(checkpoint['model_state_dict'])
                self.model.eval()
            else:
                logger.warning("Re-ID model not found, using untrained model", path=self.model_path)
                # Model will use pretrained ResNet50 features but won't be fine-tuned
                
        except Exception as e:
            logger.error("Failed to load re-ID model", error=str(e))
            raise
    
    async def generate_embedding(
        self,
        image: Image.Image,
        use_flip: bool = False
    ) -> np.ndarray:
        """
        Generate embedding for a tiger image
        
        Args:
            image: PIL Image of tiger
            use_flip: Whether to also use horizontally flipped version
            
        Returns:
            Embedding vector (numpy array)
        """
        if not hasattr(self.model, 'forward'):
            await self.load_model()
        
        try:
            # Apply transform
            if use_flip:
                # Try both original and flipped
                tensor = self.transform(image).unsqueeze(0).to(self.device)
                flip_tensor = self.flip_transform(image).unsqueeze(0).to(self.device)
                
                with torch.no_grad():
                    embedding1 = self.model(tensor)
                    embedding2 = self.model(flip_tensor)
                    # Average embeddings
                    embedding = (embedding1 + embedding2) / 2
            else:
                tensor = self.transform(image).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    embedding = self.model(tensor)
            
            # Convert to numpy
            embedding_np = embedding.cpu().numpy().flatten()
            
            # Normalize
            embedding_np = embedding_np / np.linalg.norm(embedding_np)
            
            return embedding_np
            
        except Exception as e:
            logger.error("Error generating embedding", error=str(e))
            raise
    
    async def generate_embedding_from_bytes(self, image_bytes: bytes) -> np.ndarray:
        """Generate embedding from image bytes"""
        image = Image.open(io.BytesIO(image_bytes))
        return await self.generate_embedding(image)
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1)
        """
        # Cosine similarity
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        return float(similarity)


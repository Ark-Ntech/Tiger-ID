"""WildlifeTools integration for tiger re-identification

WildlifeTools provides training and inference tooling for wildlife Re-ID models
including MegaDescriptor and WildFusion models.
"""

from typing import Optional, Dict, Any, List, Union
import sys
import io
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image
import torch
import torchvision.transforms as T

from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)

# Add WildlifeTools to path if available
WILDLIFETOOLS_PATH = Path(__file__).parent.parent.parent.parent / "data" / "models" / "wildlife-tools"
if WILDLIFETOOLS_PATH.exists():
    sys.path.insert(0, str(WILDLIFETOOLS_PATH))


class WildlifeToolsReIDModel:
    """Wrapper for WildlifeTools Re-ID models (MegaDescriptor/WildFusion)"""
    
    def __init__(
        self, 
        model_name: Optional[str] = None,
        model_type: str = "megadescriptor",
        device: str = "cuda",
        batch_size: int = 128
    ):
        """
        Initialize WildlifeTools Re-ID model
        
        Args:
            model_name: HuggingFace model name (e.g., "hf-hub:BVRA/MegaDescriptor-L-384")
                       Defaults based on model_type
            model_type: Model type ("megadescriptor" or "wildfusion")
            device: Device to run model on (cuda or cpu)
            batch_size: Batch size for feature extraction
        """
        self.model_name = model_name
        self.model_type = model_type
        self.device = device
        self.batch_size = batch_size
        self.extractor = None
        settings = get_settings()
        self.similarity_threshold = settings.models.wildlife_tools.similarity_threshold
        
        # Default model names based on type
        if self.model_name is None:
            if model_type == "megadescriptor":
                # Default to MegaDescriptor-L-384 for best performance
                self.model_name = "hf-hub:BVRA/MegaDescriptor-L-384"
            else:
                self.model_name = "hf-hub:BVRA/MegaDescriptor-L-384"
        
    def load_model(self):
        """Load the WildlifeTools model"""
        if self.extractor is not None:
            return
        
        try:
            if WILDLIFETOOLS_PATH.exists():
                try:
                    import timm
                    from wildlife_tools.features import DeepFeatures
                    from wildlife_tools.similarity import CosineSimilarity
                    from wildlife_tools.inference import KnnClassifier
                    
                    logger.info(f"Loading WildlifeTools {self.model_type} model: {self.model_name}")
                    
                    # Load model from HuggingFace via timm
                    backbone = timm.create_model(
                        self.model_name,
                        num_classes=0,  # Remove classification head, get features
                        pretrained=True
                    )
                    
                    # Create feature extractor
                    self.extractor = DeepFeatures(
                        model=backbone,
                        batch_size=self.batch_size,
                        device=self.device
                    )
                    
                    # Store similarity and classifier classes for later use
                    self.CosineSimilarity = CosineSimilarity
                    self.KnnClassifier = KnnClassifier
                    
                    logger.info("WildlifeTools model loaded successfully")
                    return
                    
                except ImportError as e:
                    logger.warning(f"Could not import WildlifeTools: {e}")
                    logger.info("Try installing: pip install git+https://github.com/WildlifeDatasets/wildlife-tools")
                    raise
                except Exception as e:
                    logger.warning(f"Failed to load WildlifeTools model: {e}")
                    raise
            else:
                logger.warning("WildlifeTools repository not found at expected path")
                raise ImportError("WildlifeTools repository not found")
                
        except Exception as e:
            logger.error(f"Failed to load WildlifeTools model: {e}")
            raise
    
    def _create_dataset_from_image(self, image: Image.Image, label: str = "query") -> Any:
        """
        Create ImageDataset from a single PIL Image
        
        Args:
            image: PIL Image
            label: Label for the image
            
        Returns:
            ImageDataset instance
        """
        try:
            from wildlife_tools.data import ImageDataset
            
            # Create transform
            transform = T.Compose([
                T.Resize([384, 384]),  # Match MegaDescriptor-L-384 input size
                T.ToTensor(),
                T.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225))
            ])
            
            # Create metadata DataFrame
            metadata = pd.DataFrame({
                "path": ["temp"],  # Path not used for single image
                "identity": [label]
            })
            
            # Create custom dataset that returns the image
            class SingleImageDataset(ImageDataset):
                def __getitem__(self, idx):
                    if self.transform is not None:
                        return self.transform(image), self.labels[idx]
                    return image, self.labels[idx]
            
            return SingleImageDataset(metadata, root=None, transform=transform)
            
        except Exception as e:
            logger.error(f"Failed to create dataset from image: {e}")
            raise
    
    def generate_embedding(self, image_data: bytes) -> Optional[np.ndarray]:
        """
        Generate embedding for an image
        
        Args:
            image_data: Image bytes
            
        Returns:
            Embedding vector (numpy array) or None if failed
        """
        if self.extractor is None:
            self.load_model()
        
        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_data))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Create dataset
            dataset = self._create_dataset_from_image(image)
            
            # Extract features
            feature_dataset = self.extractor(dataset)
            
            # Return features as numpy array
            if len(feature_dataset.features.shape) > 1:
                return feature_dataset.features[0]  # Return first (and only) feature vector
            return feature_dataset.features
            
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
            if self.extractor is None:
                self.load_model()
            
            # Ensure embeddings are 2D arrays (1, n_features)
            if embedding1.ndim == 1:
                embedding1 = embedding1.reshape(1, -1)
            if embedding2.ndim == 1:
                embedding2 = embedding2.reshape(1, -1)
            
            # Create FeatureDatasets
            from wildlife_tools.data import FeatureDataset
            import pandas as pd
            
            query_dataset = FeatureDataset(
                metadata=pd.DataFrame({"identity": ["query"]}),
                features=embedding1
            )
            database_dataset = FeatureDataset(
                metadata=pd.DataFrame({"identity": ["database"]}),
                features=embedding2
            )
            
            # Compute cosine similarity
            similarity = self.CosineSimilarity()(query_dataset, database_dataset)
            
            # Return similarity score (single value)
            return float(similarity[0, 0])
            
        except Exception as e:
            logger.error(f"Failed to compare embeddings: {e}")
            return 0.0
    
    def identify(self, query_embedding: np.ndarray, database_embeddings: List[np.ndarray], database_labels: List[str], k: int = 1) -> tuple:
        """
        Identify a query embedding against a database using k-NN
        
        Args:
            query_embedding: Query embedding vector
            database_embeddings: List of database embedding vectors
            database_labels: List of labels corresponding to database embeddings
            k: Number of nearest neighbors to consider
            
        Returns:
            Tuple of (predicted_label, similarity_score)
        """
        try:
            if self.extractor is None:
                self.load_model()
            
            # Convert to numpy arrays
            query_features = np.array([query_embedding]) if query_embedding.ndim == 1 else query_embedding
            db_features = np.array(database_embeddings)
            
            # Ensure correct shapes
            if query_features.ndim == 1:
                query_features = query_features.reshape(1, -1)
            
            # Create FeatureDatasets
            from wildlife_tools.data import FeatureDataset
            import pandas as pd
            
            query_dataset = FeatureDataset(
                metadata=pd.DataFrame({"identity": ["query"]}),
                features=query_features
            )
            database_dataset = FeatureDataset(
                metadata=pd.DataFrame({"identity": database_labels}),
                features=db_features
            )
            
            # Compute similarity
            similarity = self.CosineSimilarity()(query_dataset, database_dataset)
            
            # Use k-NN classifier
            classifier = self.KnnClassifier(
                database_labels=np.array(database_labels),
                k=k,
                return_scores=True
            )
            
            predictions, scores = classifier(similarity)
            
            return str(predictions[0]), float(scores[0])
            
        except Exception as e:
            logger.error(f"Failed to identify: {e}")
            return None, 0.0


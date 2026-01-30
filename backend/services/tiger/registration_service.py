"""Tiger registration service.

Handles registering new tigers with images and embeddings.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import UploadFile

from backend.utils.logging import get_logger
from backend.config.settings import get_settings
from backend.database.models import Tiger, TigerImage
from backend.database.vector_search import store_embedding
from backend.models.detection import TigerDetectionModel
from backend.models.interfaces.base_reid_model import BaseReIDModel
from backend.repositories.tiger_repository import TigerRepository

logger = get_logger(__name__)


class TigerRegistrationService:
    """Service for registering new tigers."""

    def __init__(
        self,
        db: Session,
        tiger_repo: Optional[TigerRepository] = None,
        detection_model: Optional[TigerDetectionModel] = None
    ):
        """Initialize registration service.

        Args:
            db: Database session
            tiger_repo: Optional tiger repository (creates default if not provided)
            detection_model: Optional detection model (creates default if not provided)
        """
        self.db = db
        self.settings = get_settings()
        self.tiger_repo = tiger_repo or TigerRepository(db)
        self.detection_model = detection_model or TigerDetectionModel()

        # Initialize available models
        self._available_models: Dict[str, type] = {}
        self._initialize_available_models()

    def _initialize_available_models(self):
        """Initialize available RE-ID models."""
        from backend.models.reid import TigerReIDModel

        self._available_models = {
            'tiger_reid': TigerReIDModel
        }

        try:
            from backend.models.wildlife_tools import WildlifeToolsReIDModel
            self._available_models['wildlife_tools'] = WildlifeToolsReIDModel
        except ImportError:
            pass

        try:
            from backend.models.cvwc2019_reid import CVWC2019ReIDModel
            self._available_models['cvwc2019'] = CVWC2019ReIDModel
        except ImportError:
            pass

        try:
            from backend.models.rapid_reid import RAPIDReIDModel
            self._available_models['rapid'] = RAPIDReIDModel
        except ImportError:
            pass

    def _get_model(self, model_name: Optional[str] = None) -> BaseReIDModel:
        """Get model instance by name."""
        if model_name is None:
            model_name = 'wildlife_tools'

        if model_name not in self._available_models:
            raise ValueError(f"Model '{model_name}' not available")

        model_class = self._available_models[model_name]
        return model_class()

    async def register_new_tiger(
        self,
        name: str,
        alias: Optional[str],
        images: List[UploadFile],
        notes: Optional[str],
        model_name: Optional[str],
        user_id: UUID
    ) -> Dict[str, Any]:
        """Register a new tiger with images.

        Args:
            name: Tiger name
            alias: Tiger alias/identifier
            images: List of image files
            notes: Additional notes
            model_name: Model to use for embedding generation
            user_id: User ID who registered the tiger

        Returns:
            Dictionary with created tiger information
        """
        logger.info(
            f"Registering new tiger: {name} (alias: {alias}) "
            f"with {len(images)} images"
        )

        # Create tiger record
        tiger = Tiger(
            tiger_id=uuid4(),
            name=name,
            alias=alias,
            status="active",
            notes=notes,
            tags=["user-registered"]
        )

        self.db.add(tiger)
        self.db.flush()  # Get ID without committing

        # Process images
        image_paths = []
        for idx, image_file in enumerate(images):
            try:
                processed_path = await self._process_registration_image(
                    tiger=tiger,
                    image_file=image_file,
                    index=idx,
                    model_name=model_name,
                    user_id=user_id
                )
                if processed_path:
                    image_paths.append(processed_path)
            except Exception as e:
                logger.error(
                    f"Error processing image {image_file.filename}: {e}",
                    exc_info=True
                )
                continue

        # Commit all changes
        self.db.commit()
        self.db.refresh(tiger)

        logger.info(
            f"Successfully registered tiger {tiger.tiger_id} "
            f"with {len(image_paths)} images"
        )

        return {
            "tiger_id": str(tiger.tiger_id),
            "name": tiger.name,
            "alias": tiger.alias,
            "image_count": len(image_paths),
            "images": image_paths
        }

    async def _process_registration_image(
        self,
        tiger: Tiger,
        image_file: UploadFile,
        index: int,
        model_name: Optional[str],
        user_id: UUID
    ) -> Optional[str]:
        """Process a single image for tiger registration.

        Args:
            tiger: Tiger being registered
            image_file: Image file to process
            index: Image index
            model_name: Model for embedding
            user_id: User ID

        Returns:
            Image path if successful, None otherwise
        """
        from PIL import Image
        import io

        # Read image
        image_bytes = await image_file.read()
        await image_file.seek(0)

        # Detect tiger in image
        detection_result = await self.detection_model.detect(image_bytes)

        if not detection_result.get("detections"):
            logger.warning(
                f"No tiger detected in image {image_file.filename}, skipping"
            )
            return None

        # Extract tiger crop
        tiger_crop = detection_result["detections"][0].get("crop")

        # Convert crop to bytes if needed
        if hasattr(tiger_crop, 'save'):
            buffer = io.BytesIO()
            tiger_crop.save(buffer, format='JPEG')
            tiger_crop_bytes = buffer.getvalue()
        else:
            tiger_crop_bytes = tiger_crop

        # Save image to storage
        storage_dir = Path("data/storage/tigers") / str(tiger.tiger_id)
        storage_dir.mkdir(parents=True, exist_ok=True)

        image_filename = f"{index}_{image_file.filename}"
        image_path = storage_dir / image_filename

        with open(image_path, "wb") as f:
            f.write(image_bytes)

        # Generate embedding using selected model
        reid_model = self._get_model(model_name)

        if hasattr(reid_model, 'generate_embedding_from_bytes'):
            embedding = await reid_model.generate_embedding_from_bytes(tiger_crop_bytes)
        else:
            image_obj = Image.open(io.BytesIO(tiger_crop_bytes))
            embedding = await reid_model.generate_embedding(image_obj)

        # Create TigerImage record
        tiger_image = TigerImage(
            tiger_id=tiger.tiger_id,
            image_path=str(image_path),
            uploaded_by=user_id,
            meta_data={
                "original_filename": image_file.filename,
                "model_used": model_name or "wildlife_tools",
                "registered_by": str(user_id)
            }
        )

        self.db.add(tiger_image)
        self.db.flush()

        # Store embedding in vector database
        if embedding is not None:
            store_embedding(
                self.db,
                tiger_id=str(tiger.tiger_id),
                image_id=str(tiger_image.image_id),
                embedding=embedding
            )

        logger.info(
            f"Processed image {index + 1} for tiger {tiger.tiger_id}"
        )

        return str(image_path)

    async def add_image_to_tiger(
        self,
        tiger_id: UUID,
        image_file: UploadFile,
        model_name: Optional[str],
        user_id: UUID
    ) -> Dict[str, Any]:
        """Add a new image to an existing tiger.

        Args:
            tiger_id: UUID of the tiger
            image_file: Image file to add
            model_name: Model for embedding
            user_id: User ID

        Returns:
            Dictionary with added image information
        """
        tiger = self.tiger_repo.get_by_id(tiger_id)
        if not tiger:
            raise ValueError(f"Tiger {tiger_id} not found")

        images = self.tiger_repo.get_images(tiger_id)
        next_index = len(images)

        image_path = await self._process_registration_image(
            tiger=tiger,
            image_file=image_file,
            index=next_index,
            model_name=model_name,
            user_id=user_id
        )

        self.db.commit()

        return {
            "tiger_id": str(tiger_id),
            "image_path": image_path,
            "total_images": next_index + 1
        }

"""
Model testing API routes.

Endpoints for model testing, evaluation, and benchmarking.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import json

from backend.database import get_db
from backend.auth.auth import get_current_user
from backend.services.model_evaluation_service import ModelEvaluationService
from backend.services.model_comparison_service import ModelComparisonService
from backend.services.tiger_service import TigerService
from backend.utils.response_models import SuccessResponse
from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)

router = APIRouter(prefix="/models", tags=["models"])

# Initialize services
evaluation_service = ModelEvaluationService()
comparison_service = ModelComparisonService()


@router.post("/test")
async def test_model(
    images: List[UploadFile] = File(...),
    model_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Test a model on uploaded images.
    
    Returns embedding generation results and performance metrics.
    """
    try:
        if len(images) == 0:
            raise HTTPException(
                status_code=400,
                detail="At least one image is required"
            )
        
        if len(images) > 20:
            raise HTTPException(
                status_code=400,
                detail="Maximum 20 images per test request"
            )
        
        # Validate file types and sizes
        for image in images:
            if image.content_type and not image.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type for {image.filename}: {image.content_type}. Only image files are allowed."
                )
            image_bytes = await image.read()
            if len(image_bytes) > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {image.filename} exceeds 10MB limit"
                )
            await image.seek(0)
        
        tiger_service = TigerService(db)
        
        # Special models that don't need to be in TigerService (detection only)
        special_models = ["megadetector"]

        if model_name:
            # Check if it's a special model or in available models
            if model_name not in tiger_service.get_available_models() and model_name not in special_models:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model '{model_name}' not available. Available: {', '.join(tiger_service.get_available_models() + special_models)}"
                )

            # Handle special models
            if model_name == "megadetector":
                raise HTTPException(
                    status_code=400,
                    detail="MegaDetector is a detection model. Use the detection endpoint instead."
                )
        
        # Use default model if not specified
        if not model_name:
            model_name = "tiger_reid"
        
        model = tiger_service._get_model(model_name)
        
        # Process images
        results = []
        for image in images:
            try:
                image_bytes = await image.read()
                from PIL import Image
                import io
                image_obj = Image.open(io.BytesIO(image_bytes))
                
                # Generate embedding
                if hasattr(model, 'generate_embedding_from_bytes'):
                    embedding = await model.generate_embedding_from_bytes(image_bytes)
                else:
                    embedding = await model.generate_embedding(image_obj)
                
                results.append({
                    "filename": image.filename,
                    "success": embedding is not None,
                    "embedding_shape": list(embedding.shape) if embedding is not None else None
                })
            except Exception as e:
                logger.error(f"Error processing {image.filename}: {e}")
                results.append({
                    "filename": image.filename,
                    "success": False,
                    "error": str(e)
                })
        
        return SuccessResponse(data={
            "model": model_name,
            "total_images": len(images),
            "results": results
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/evaluate")
async def evaluate_model(
    query_images: List[UploadFile] = File(...),
    gallery_images: List[UploadFile] = File(...),
    model_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Evaluate a model on query and gallery images.
    
    Returns Rank-1 accuracy, mAP, CMC curve, and performance metrics.
    """
    try:
        tiger_service = TigerService(db)
        
        if model_name and model_name not in tiger_service.get_available_models():
            raise HTTPException(
                status_code=400,
                detail=f"Model '{model_name}' not available"
            )
        
        if not model_name:
            model_name = "tiger_reid"
        
        model = tiger_service._get_model(model_name)
        
        model = tiger_service._get_model(model_name)

        # Generate query embeddings
        import numpy as np
        from PIL import Image
        import io
        import time

        query_embeddings = []
        query_filenames = []
        for img in query_images:
            try:
                image_bytes = await img.read()
                image_obj = Image.open(io.BytesIO(image_bytes))

                if hasattr(model, 'generate_embedding_from_bytes'):
                    embedding = await model.generate_embedding_from_bytes(image_bytes)
                else:
                    embedding = await model.generate_embedding(image_obj)

                if embedding is not None:
                    query_embeddings.append(embedding)
                    query_filenames.append(img.filename)
            except Exception as e:
                logger.warning(f"Failed to process query image {img.filename}: {e}")

        # Generate gallery embeddings
        gallery_embeddings = []
        gallery_filenames = []
        for img in gallery_images:
            try:
                image_bytes = await img.read()
                image_obj = Image.open(io.BytesIO(image_bytes))

                if hasattr(model, 'generate_embedding_from_bytes'):
                    embedding = await model.generate_embedding_from_bytes(image_bytes)
                else:
                    embedding = await model.generate_embedding(image_obj)

                if embedding is not None:
                    gallery_embeddings.append(embedding)
                    gallery_filenames.append(img.filename)
            except Exception as e:
                logger.warning(f"Failed to process gallery image {img.filename}: {e}")

        if not query_embeddings or not gallery_embeddings:
            raise HTTPException(
                status_code=400,
                detail="No valid embeddings could be generated from the images"
            )

        # Compute similarity matrix (cosine similarity)
        query_matrix = np.vstack(query_embeddings)
        gallery_matrix = np.vstack(gallery_embeddings)

        # Normalize for cosine similarity
        query_norm = query_matrix / (np.linalg.norm(query_matrix, axis=1, keepdims=True) + 1e-8)
        gallery_norm = gallery_matrix / (np.linalg.norm(gallery_matrix, axis=1, keepdims=True) + 1e-8)

        similarity_matrix = np.dot(query_norm, gallery_norm.T)

        # Get top matches for each query
        top_matches = []
        for i, query_name in enumerate(query_filenames):
            similarities = similarity_matrix[i]
            sorted_indices = np.argsort(-similarities)
            matches = [
                {"gallery_image": gallery_filenames[j], "similarity": float(similarities[j])}
                for j in sorted_indices[:5]
            ]
            top_matches.append({
                "query_image": query_name,
                "top_matches": matches
            })

        return SuccessResponse(data={
            "model": model_name,
            "query_count": len(query_embeddings),
            "gallery_count": len(gallery_embeddings),
            "embedding_dim": query_matrix.shape[1],
            "results": top_matches,
            "note": "For mAP/CMC evaluation, provide ground truth labels via /models/benchmark"
        })
        
    except Exception as e:
        logger.error(f"Error evaluating model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/compare")
async def compare_models(
    query_images: List[UploadFile] = File(...),
    gallery_images: List[UploadFile] = File(...),
    model_names: Optional[str] = Form(None),  # Comma-separated list
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Compare multiple models on same query and gallery images.
    
    Returns comparison results with best model selection.
    """
    try:
        tiger_service = TigerService(db)
        
        # Parse model names
        if model_names:
            requested_models = [m.strip() for m in model_names.split(",")]
        else:
            requested_models = tiger_service.get_available_models()
        
        # Validate models
        available_models = tiger_service.get_available_models()
        invalid_models = [m for m in requested_models if m not in available_models]
        if invalid_models:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid models: {invalid_models}. Available: {available_models}"
            )
        
        # Read images into memory once
        import numpy as np
        from PIL import Image
        import io
        import time

        query_bytes_list = []
        for img in query_images:
            query_bytes_list.append((img.filename, await img.read()))

        gallery_bytes_list = []
        for img in gallery_images:
            gallery_bytes_list.append((img.filename, await img.read()))

        # Compare models
        model_results = {}
        for model_name in requested_models:
            try:
                model = tiger_service._get_model(model_name)
                start_time = time.time()

                # Generate embeddings
                query_embeddings = []
                gallery_embeddings = []

                for filename, img_bytes in query_bytes_list:
                    try:
                        image_obj = Image.open(io.BytesIO(img_bytes))
                        if hasattr(model, 'generate_embedding_from_bytes'):
                            embedding = await model.generate_embedding_from_bytes(img_bytes)
                        else:
                            embedding = await model.generate_embedding(image_obj)
                        if embedding is not None:
                            query_embeddings.append(embedding)
                    except Exception as e:
                        logger.warning(f"Model {model_name} failed on query {filename}: {e}")

                for filename, img_bytes in gallery_bytes_list:
                    try:
                        image_obj = Image.open(io.BytesIO(img_bytes))
                        if hasattr(model, 'generate_embedding_from_bytes'):
                            embedding = await model.generate_embedding_from_bytes(img_bytes)
                        else:
                            embedding = await model.generate_embedding(image_obj)
                        if embedding is not None:
                            gallery_embeddings.append(embedding)
                    except Exception as e:
                        logger.warning(f"Model {model_name} failed on gallery {filename}: {e}")

                total_time = time.time() - start_time

                if query_embeddings and gallery_embeddings:
                    query_matrix = np.vstack(query_embeddings)
                    gallery_matrix = np.vstack(gallery_embeddings)

                    # Compute average similarity
                    query_norm = query_matrix / (np.linalg.norm(query_matrix, axis=1, keepdims=True) + 1e-8)
                    gallery_norm = gallery_matrix / (np.linalg.norm(gallery_matrix, axis=1, keepdims=True) + 1e-8)
                    similarity_matrix = np.dot(query_norm, gallery_norm.T)

                    model_results[model_name] = {
                        "success": True,
                        "query_processed": len(query_embeddings),
                        "gallery_processed": len(gallery_embeddings),
                        "embedding_dim": query_matrix.shape[1],
                        "avg_similarity": float(np.mean(similarity_matrix)),
                        "max_similarity": float(np.max(similarity_matrix)),
                        "min_similarity": float(np.min(similarity_matrix)),
                        "processing_time_seconds": round(total_time, 3)
                    }
                else:
                    model_results[model_name] = {
                        "success": False,
                        "error": "Failed to generate embeddings"
                    }

            except Exception as e:
                logger.error(f"Error comparing model {model_name}: {e}")
                model_results[model_name] = {
                    "success": False,
                    "error": str(e)
                }

        # Determine best model by processing success and speed
        successful_models = {k: v for k, v in model_results.items() if v.get("success")}
        best_model = None
        if successful_models:
            best_model = min(successful_models.keys(), key=lambda k: successful_models[k]["processing_time_seconds"])

        return SuccessResponse(data={
            "models_compared": requested_models,
            "results": model_results,
            "best_model": best_model,
            "note": "Best model determined by processing speed among successful models"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/benchmark")
async def benchmark_model(
    images: List[UploadFile] = File(...),
    model_name: Optional[str] = Form(None),
    num_runs: int = Form(5),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Benchmark model performance (latency, throughput, memory).
    
    Returns performance metrics including inference time statistics.
    """
    try:
        if num_runs < 1 or num_runs > 20:
            raise HTTPException(
                status_code=400,
                detail="num_runs must be between 1 and 20"
            )
        
        tiger_service = TigerService(db)
        
        if model_name and model_name not in tiger_service.get_available_models():
            raise HTTPException(
                status_code=400,
                detail=f"Model '{model_name}' not available"
            )
        
        if not model_name:
            model_name = "tiger_reid"
        
        model = tiger_service._get_model(model_name)
        
        # Save images temporarily for benchmarking
        import tempfile
        import shutil
        temp_dir = Path(tempfile.mkdtemp())
        image_paths = []
        
        try:
            for img in images:
                temp_path = temp_dir / img.filename
                with open(temp_path, 'wb') as f:
                    content = await img.read()
                    f.write(content)
                image_paths.append(temp_path)
            
            # Run benchmark
            benchmark_results = evaluation_service.benchmark_model_performance(
                model=model,
                model_name=model_name,
                test_images=image_paths,
                num_runs=num_runs
            )
            
            return SuccessResponse(data=benchmark_results)
            
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error benchmarking model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/available")
async def get_available_models(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get list of available models with Modal metadata.
    Returns the same structure as /api/v1/modal/models for frontend compatibility.
    """
    try:
        tiger_service = TigerService(db)
        available_models = tiger_service.get_available_models()
        
        # Model metadata with Modal GPU information (same as modal_routes.py)
        model_info = {
            "tiger_reid": {
                "name": "TigerReID",
                "description": "Tiger re-identification using ResNet50",
                "gpu": "T4",
                "backend": "Modal",
                "embedding_dim": 2048,
                "type": "reid"
            },
            "wildlife_tools": {
                "name": "WildlifeTools",
                "description": "MegaDescriptor embeddings",
                "gpu": "A100-40GB",
                "backend": "Modal",
                "embedding_dim": 1536,
                "type": "reid"
            },
            "rapid": {
                "name": "RAPID",
                "description": "Real-time Animal Pattern ReID",
                "gpu": "T4",
                "backend": "Modal",
                "embedding_dim": 2048,
                "type": "reid"
            },
            "cvwc2019": {
                "name": "CVWC2019",
                "description": "Part-pose guided tiger ReID",
                "gpu": "T4",
                "backend": "Modal",
                "embedding_dim": 2048,
                "type": "reid"
            },
            "megadetector": {
                "name": "MegaDetector",
                "description": "Animal detection v5",
                "gpu": "T4",
                "backend": "Modal",
                "type": "detection"
            },
            "transreid": {
                "name": "TransReID",
                "description": "Vision Transformer ReID (ViT-Base)",
                "gpu": "T4",
                "backend": "Modal",
                "embedding_dim": 768,
                "type": "reid"
            }
        }

        # Filter to only available models
        models = {
            name: info for name, info in model_info.items()
            if name in available_models or name in ["megadetector", "transreid"]
        }
        
        return SuccessResponse(
            message="Models retrieved successfully",
            data={
                "models": models,
                "default": "tiger_reid"
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting available models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


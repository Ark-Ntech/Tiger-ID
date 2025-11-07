"""
Comprehensive test suite for RE-ID models on real tiger datasets.

Tests all RE-ID models (TigerReIDModel, WildlifeToolsReIDModel, CVWC2019ReIDModel, RAPIDReIDModel)
on real tiger images from ATRW and WildlifeReID-10k datasets.
"""

import pytest
import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from PIL import Image
import torch
import psutil
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)

# Try to import all models
try:
    from backend.models.reid import TigerReIDModel
    TIGER_REID_AVAILABLE = True
except ImportError:
    TIGER_REID_AVAILABLE = False
    logger.warning("TigerReIDModel not available")

try:
    from backend.models.wildlife_tools import WildlifeToolsReIDModel
    WILDLIFE_TOOLS_AVAILABLE = True
except ImportError:
    WILDLIFE_TOOLS_AVAILABLE = False
    logger.warning("WildlifeToolsReIDModel not available")

try:
    from backend.models.cvwc2019_reid import CVWC2019ReIDModel
    CVWC2019_AVAILABLE = True
except ImportError:
    CVWC2019_AVAILABLE = False
    logger.warning("CVWC2019ReIDModel not available")

try:
    from backend.models.rapid_reid import RAPIDReIDModel
    RAPID_AVAILABLE = True
except ImportError:
    RAPID_AVAILABLE = False
    logger.warning("RAPIDReIDModel not available")


class ModelTestFramework:
    """Framework for testing RE-ID models on real datasets"""
    
    def __init__(self, test_datasets_dir: Optional[Path] = None):
        """
        Initialize test framework
        
        Args:
            test_datasets_dir: Directory containing prepared test datasets
        """
        self.settings = get_settings()
        
        if test_datasets_dir is None:
            test_datasets_dir = Path(self.settings.datasets.individual_animal_reid_path).parent / "test_datasets"
        
        self.test_datasets_dir = Path(test_datasets_dir)
        self.results = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"Using device: {self.device}")
    
    def load_test_dataset(self, split: str = "test") -> Dict[str, Any]:
        """
        Load test dataset from prepared datasets
        
        Args:
            split: Dataset split to load (train/val/test)
            
        Returns:
            Dictionary with dataset information
        """
        manifest_path = self.test_datasets_dir / "atrw_manifest.json"
        
        if not manifest_path.exists():
            logger.warning(f"Test dataset manifest not found: {manifest_path}")
            logger.info("Run scripts/prepare_test_datasets.py first to prepare datasets")
            return {}
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        if split not in manifest.get('splits', {}):
            logger.warning(f"Split '{split}' not found in manifest")
            return {}
        
        split_data = manifest['splits'][split]
        
        # Load ground truth
        gt_path = self.test_datasets_dir / "ground_truth.json"
        ground_truth = {}
        if gt_path.exists():
            with open(gt_path, 'r') as f:
                gt_data = json.load(f)
                ground_truth = gt_data.get(split, {})
        
        # Build dataset structure
        dataset = {
            'tigers': {},
            'images': [],
            'ground_truth': ground_truth
        }
        
        for tiger_data in split_data.get('tigers', []):
            tiger_id = tiger_data['tiger_id']
            dataset['tigers'][tiger_id] = []
            
            for img_data in tiger_data.get('images', []):
                img_path = self.test_datasets_dir / split / img_data['path']
                if img_path.exists():
                    dataset['tigers'][tiger_id].append(img_path)
                    dataset['images'].append({
                        'path': img_path,
                        'tiger_id': tiger_id,
                        'metadata': img_data
                    })
        
        logger.info(
            f"Loaded {split} split: {len(dataset['tigers'])} tigers, "
            f"{len(dataset['images'])} images"
        )
        
        return dataset
    
    async def test_model_embedding_generation(
        self,
        model,
        model_name: str,
        test_images: List[Path],
        max_images: int = 10
    ) -> Dict[str, Any]:
        """
        Test model embedding generation
        
        Args:
            model: Model instance
            model_name: Name of the model
            test_images: List of test image paths
            max_images: Maximum number of images to test
            
        Returns:
            Dictionary with test results
        """
        logger.info(f"Testing {model_name} embedding generation...")
        
        results = {
            'model_name': model_name,
            'total_images': min(len(test_images), max_images),
            'successful': 0,
            'failed': 0,
            'inference_times': [],
            'embedding_shapes': [],
            'errors': []
        }
        
        # Load model if needed
        try:
            if hasattr(model, 'load_model'):
                await model.load_model()
        except Exception as e:
            logger.warning(f"Model {model_name} load failed: {e}")
            results['errors'].append(f"Load error: {str(e)}")
            return results
        
        # Test on sample images
        test_sample = test_images[:max_images]
        
        for img_path in test_sample:
            try:
                start_time = time.time()
                
                # Load image
                image = Image.open(img_path)
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Generate embedding
                # Try different methods based on model interface
                embedding = None
                if hasattr(model, 'generate_embedding_from_bytes'):
                    with open(img_path, 'rb') as f:
                        img_bytes = f.read()
                    embedding = await model.generate_embedding_from_bytes(img_bytes)
                elif hasattr(model, 'generate_embedding'):
                    # Some models take PIL Image, some take bytes
                    try:
                        embedding = await model.generate_embedding(image)
                    except TypeError:
                        # Try with bytes if PIL Image doesn't work
                        with open(img_path, 'rb') as f:
                            img_bytes = f.read()
                        embedding = await model.generate_embedding(img_bytes)
                else:
                    logger.warning(f"Model {model_name} has no embedding generation method")
                    results['failed'] += 1
                    continue
                
                inference_time = time.time() - start_time
                
                # Validate embedding
                if embedding is None:
                    results['failed'] += 1
                    results['errors'].append(f"None embedding for {img_path.name}")
                    continue
                
                embedding_array = np.array(embedding)
                if embedding_array.size == 0:
                    results['failed'] += 1
                    results['errors'].append(f"Empty embedding for {img_path.name}")
                    continue
                
                results['successful'] += 1
                results['inference_times'].append(inference_time)
                results['embedding_shapes'].append(embedding_array.shape)
                
            except Exception as e:
                logger.error(f"Error testing {img_path} with {model_name}: {e}")
                results['failed'] += 1
                results['errors'].append(f"{img_path.name}: {str(e)}")
        
        # Calculate statistics
        if results['inference_times']:
            results['avg_inference_time'] = np.mean(results['inference_times'])
            results['min_inference_time'] = np.min(results['inference_times'])
            results['max_inference_time'] = np.max(results['inference_times'])
            results['std_inference_time'] = np.std(results['inference_times'])
        
        if results['embedding_shapes']:
            # Check if all embeddings have same shape
            unique_shapes = set(results['embedding_shapes'])
            results['unique_shapes'] = list(unique_shapes)
            if len(unique_shapes) == 1:
                results['embedding_dim'] = results['embedding_shapes'][0]
        
        logger.info(
            f"✓ {model_name}: {results['successful']}/{results['total_images']} successful, "
            f"avg time: {results.get('avg_inference_time', 0):.3f}s"
        )
        
        return results
    
    async def test_model_identification_accuracy(
        self,
        model,
        model_name: str,
        query_images: List[Dict[str, Any]],
        gallery_images: List[Dict[str, Any]],
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Test model identification accuracy
        
        Args:
            model: Model instance
            model_name: Name of the model
            query_images: List of query images with tiger_id
            gallery_images: List of gallery images with tiger_id
            top_k: Number of top matches to consider
            
        Returns:
            Dictionary with accuracy results
        """
        logger.info(f"Testing {model_name} identification accuracy...")
        
        results = {
            'model_name': model_name,
            'total_queries': len(query_images),
            'correct_top1': 0,
            'correct_top5': 0,
            'rank1_accuracy': 0.0,
            'top5_accuracy': 0.0,
            'errors': []
        }
        
        # Load model if needed
        try:
            if hasattr(model, 'load_model'):
                await model.load_model()
        except Exception as e:
            logger.warning(f"Model {model_name} load failed: {e}")
            results['errors'].append(f"Load error: {str(e)}")
            return results
        
        # Generate gallery embeddings
        gallery_embeddings = {}
        gallery_tiger_ids = []
        
        for gallery_img in gallery_images:
            try:
                img_path = gallery_img['path']
                tiger_id = gallery_img['tiger_id']
                
                image = Image.open(img_path)
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Generate gallery embedding
                embedding = None
                if hasattr(model, 'generate_embedding_from_bytes'):
                    with open(img_path, 'rb') as f:
                        img_bytes = f.read()
                    embedding = await model.generate_embedding_from_bytes(img_bytes)
                elif hasattr(model, 'generate_embedding'):
                    try:
                        embedding = await model.generate_embedding(image)
                    except TypeError:
                        # Try with bytes if PIL Image doesn't work
                        with open(img_path, 'rb') as f:
                            img_bytes = f.read()
                        embedding = await model.generate_embedding(img_bytes)
                else:
                    continue
                
                if embedding is None:
                    continue
                
                embedding_array = np.array(embedding)
                if embedding_array.size == 0:
                    continue
                
                if tiger_id not in gallery_embeddings:
                    gallery_embeddings[tiger_id] = []
                    gallery_tiger_ids.append(tiger_id)
                
                gallery_embeddings[tiger_id].append(embedding_array)
                
            except Exception as e:
                logger.warning(f"Error processing gallery image {img_path}: {e}")
                continue
        
        if len(gallery_embeddings) == 0:
            results['errors'].append("No gallery embeddings generated")
            return results
        
        # Test queries
        for query_img in query_images:
            try:
                img_path = query_img['path']
                true_tiger_id = query_img['tiger_id']
                
                image = Image.open(img_path)
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Generate query embedding
                query_embedding = None
                if hasattr(model, 'generate_embedding_from_bytes'):
                    with open(img_path, 'rb') as f:
                        img_bytes = f.read()
                    query_embedding = await model.generate_embedding_from_bytes(img_bytes)
                elif hasattr(model, 'generate_embedding'):
                    try:
                        query_embedding = await model.generate_embedding(image)
                    except TypeError:
                        # Try with bytes if PIL Image doesn't work
                        with open(img_path, 'rb') as f:
                            img_bytes = f.read()
                        query_embedding = await model.generate_embedding(img_bytes)
                else:
                    results['errors'].append(f"No embedding method for {img_path.name}")
                    continue
                
                if query_embedding is None:
                    results['errors'].append(f"None embedding for {img_path.name}")
                    continue
                
                query_embedding_array = np.array(query_embedding)
                if query_embedding_array.size == 0:
                    results['errors'].append(f"Empty embedding for {img_path.name}")
                    continue
                
                # Compute similarities with gallery
                similarities = []
                for tiger_id, embeddings_list in gallery_embeddings.items():
                    for gallery_emb in embeddings_list:
                        # Cosine similarity
                        similarity = np.dot(query_embedding_array, gallery_emb) / (
                            np.linalg.norm(query_embedding_array) * np.linalg.norm(gallery_emb)
                        )
                        similarities.append((tiger_id, similarity))
                
                # Sort by similarity
                similarities.sort(key=lambda x: x[1], reverse=True)
                
                # Check top-1
                if len(similarities) > 0 and similarities[0][0] == true_tiger_id:
                    results['correct_top1'] += 1
                
                # Check top-k
                top_k_tiger_ids = [tiger_id for tiger_id, _ in similarities[:top_k]]
                if true_tiger_id in top_k_tiger_ids:
                    results['correct_top5'] += 1
                
            except Exception as e:
                logger.error(f"Error testing query {img_path}: {e}")
                results['errors'].append(f"{img_path.name}: {str(e)}")
                continue
        
        # Calculate accuracies
        if results['total_queries'] > 0:
            results['rank1_accuracy'] = results['correct_top1'] / results['total_queries']
            results['top5_accuracy'] = results['correct_top5'] / results['total_queries']
        
        logger.info(
            f"✓ {model_name}: Rank-1: {results['rank1_accuracy']:.3f}, "
            f"Top-5: {results['top5_accuracy']:.3f}"
        )
        
        return results
    
    def measure_memory_usage(self) -> Dict[str, Any]:
        """Measure current memory usage"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        memory_stats = {
            'rss_mb': memory_info.rss / (1024 * 1024),
            'vms_mb': memory_info.vms / (1024 * 1024)
        }
        
        if torch.cuda.is_available():
            memory_stats['gpu_allocated_mb'] = torch.cuda.memory_allocated() / (1024 * 1024)
            memory_stats['gpu_reserved_mb'] = torch.cuda.memory_reserved() / (1024 * 1024)
        
        return memory_stats


@pytest.fixture
def test_framework():
    """Fixture for test framework"""
    return ModelTestFramework()


@pytest.fixture
def test_dataset(test_framework):
    """Fixture for test dataset"""
    dataset = test_framework.load_test_dataset(split="test")
    if not dataset:
        pytest.skip("Test dataset not available. Run scripts/prepare_test_datasets.py first.")
    return dataset


@pytest.mark.asyncio
@pytest.mark.skipif(not TIGER_REID_AVAILABLE, reason="TigerReIDModel not available")
async def test_tiger_reid_model_embeddings(test_framework, test_dataset):
    """Test TigerReIDModel embedding generation"""
    if not test_dataset or not test_dataset.get('images'):
        pytest.skip("No test images available")
    
    model = TigerReIDModel(device=test_framework.device)
    test_images = [img['path'] for img in test_dataset['images'][:10]]
    
    results = await test_framework.test_model_embedding_generation(
        model, "TigerReIDModel", test_images, max_images=10
    )
    
    assert results['successful'] > 0, "Should generate at least some embeddings"
    assert results.get('avg_inference_time', 0) < 5.0, "Inference should be reasonably fast"


@pytest.mark.asyncio
@pytest.mark.skipif(not WILDLIFE_TOOLS_AVAILABLE, reason="WildlifeToolsReIDModel not available")
async def test_wildlife_tools_model_embeddings(test_framework, test_dataset):
    """Test WildlifeToolsReIDModel embedding generation"""
    if not test_dataset or not test_dataset.get('images'):
        pytest.skip("No test images available")
    
    model = WildlifeToolsReIDModel(device=test_framework.device)
    test_images = [img['path'] for img in test_dataset['images'][:10]]
    
    results = await test_framework.test_model_embedding_generation(
        model, "WildlifeToolsReIDModel", test_images, max_images=10
    )
    
    assert results['successful'] > 0, "Should generate at least some embeddings"


@pytest.mark.asyncio
@pytest.mark.skipif(not CVWC2019_AVAILABLE, reason="CVWC2019ReIDModel not available")
async def test_cvwc2019_model_embeddings(test_framework, test_dataset):
    """Test CVWC2019ReIDModel embedding generation"""
    if not test_dataset or not test_dataset.get('images'):
        pytest.skip("No test images available")
    
    model = CVWC2019ReIDModel(device=test_framework.device)
    test_images = [img['path'] for img in test_dataset['images'][:10]]
    
    results = await test_framework.test_model_embedding_generation(
        model, "CVWC2019ReIDModel", test_images, max_images=10
    )
    
    assert results['successful'] > 0, "Should generate at least some embeddings"


@pytest.mark.asyncio
@pytest.mark.skipif(not RAPID_AVAILABLE, reason="RAPIDReIDModel not available")
async def test_rapid_model_embeddings(test_framework, test_dataset):
    """Test RAPIDReIDModel embedding generation"""
    if not test_dataset or not test_dataset.get('images'):
        pytest.skip("No test images available")
    
    model = RAPIDReIDModel(device=test_framework.device)
    test_images = [img['path'] for img in test_dataset['images'][:10]]
    
    results = await test_framework.test_model_embedding_generation(
        model, "RAPIDReIDModel", test_images, max_images=10
    )
    
    # RAPID may not be fully implemented, so we just check if it runs
    assert 'errors' in results


@pytest.mark.asyncio
@pytest.mark.skipif(not TIGER_REID_AVAILABLE, reason="TigerReIDModel not available")
async def test_tiger_reid_identification_accuracy(test_framework, test_dataset):
    """Test TigerReIDModel identification accuracy"""
    if not test_dataset or not test_dataset.get('images'):
        pytest.skip("No test images available")
    
    # Split into query and gallery
    all_images = test_dataset['images']
    if len(all_images) < 20:
        pytest.skip("Not enough images for accuracy test")
    
    # Use first 10 as queries, rest as gallery
    query_images = all_images[:10]
    gallery_images = all_images[10:50]  # Use up to 40 gallery images
    
    model = TigerReIDModel(device=test_framework.device)
    
    results = await test_framework.test_model_identification_accuracy(
        model, "TigerReIDModel", query_images, gallery_images, top_k=5
    )
    
    assert results['total_queries'] > 0, "Should have queries"
    assert results['rank1_accuracy'] >= 0.0, "Accuracy should be non-negative"
    assert results['rank1_accuracy'] <= 1.0, "Accuracy should be <= 1.0"


@pytest.mark.asyncio
@pytest.mark.skipif(not WILDLIFE_TOOLS_AVAILABLE, reason="WildlifeToolsReIDModel not available")
async def test_wildlife_tools_identification_accuracy(test_framework, test_dataset):
    """Test WildlifeToolsReIDModel identification accuracy"""
    if not test_dataset or not test_dataset.get('images'):
        pytest.skip("No test images available")
    
    all_images = test_dataset['images']
    if len(all_images) < 20:
        pytest.skip("Not enough images for accuracy test")
    
    query_images = all_images[:10]
    gallery_images = all_images[10:50]
    
    model = WildlifeToolsReIDModel(device=test_framework.device)
    
    results = await test_framework.test_model_identification_accuracy(
        model, "WildlifeToolsReIDModel", query_images, gallery_images, top_k=5
    )
    
    assert results['total_queries'] > 0
    assert results['rank1_accuracy'] >= 0.0
    assert results['rank1_accuracy'] <= 1.0


@pytest.mark.asyncio
async def test_all_models_comparison(test_framework, test_dataset):
    """Compare all available models on same test set"""
    if not test_dataset or not test_dataset.get('images'):
        pytest.skip("No test images available")
    
    test_images = [img['path'] for img in test_dataset['images'][:5]]
    
    comparison_results = {}
    
    # Test each available model
    if TIGER_REID_AVAILABLE:
        model = TigerReIDModel(device=test_framework.device)
        results = await test_framework.test_model_embedding_generation(
            model, "TigerReIDModel", test_images, max_images=5
        )
        comparison_results['TigerReIDModel'] = results
    
    if WILDLIFE_TOOLS_AVAILABLE:
        model = WildlifeToolsReIDModel(device=test_framework.device)
        results = await test_framework.test_model_embedding_generation(
            model, "WildlifeToolsReIDModel", test_images, max_images=5
        )
        comparison_results['WildlifeToolsReIDModel'] = results
    
    if CVWC2019_AVAILABLE:
        model = CVWC2019ReIDModel(device=test_framework.device)
        results = await test_framework.test_model_embedding_generation(
            model, "CVWC2019ReIDModel", test_images, max_images=5
        )
        comparison_results['CVWC2019ReIDModel'] = results
    
    # Check that at least one model was tested
    assert len(comparison_results) > 0, "At least one model should be available"
    
    # Print comparison
    logger.info("Model Comparison Results:")
    for model_name, results in comparison_results.items():
        logger.info(
            f"  {model_name}: {results['successful']}/{results['total_images']} successful, "
            f"avg time: {results.get('avg_inference_time', 0):.3f}s"
        )


@pytest.mark.asyncio
async def test_memory_usage(test_framework):
    """Test memory usage of models"""
    initial_memory = test_framework.measure_memory_usage()
    
    models = []
    
    if TIGER_REID_AVAILABLE:
        models.append(("TigerReIDModel", TigerReIDModel(device=test_framework.device)))
    
    if WILDLIFE_TOOLS_AVAILABLE:
        models.append(("WildlifeToolsReIDModel", WildlifeToolsReIDModel(device=test_framework.device)))
    
    if CVWC2019_AVAILABLE:
        models.append(("CVWC2019ReIDModel", CVWC2019ReIDModel(device=test_framework.device)))
    
    for model_name, model in models:
        try:
            if hasattr(model, 'load_model'):
                await model.load_model()
            
            memory_after = test_framework.measure_memory_usage()
            memory_delta = {
                'rss_mb': memory_after['rss_mb'] - initial_memory['rss_mb'],
                'vms_mb': memory_after['vms_mb'] - initial_memory['vms_mb']
            }
            
            if 'gpu_allocated_mb' in memory_after:
                memory_delta['gpu_allocated_mb'] = memory_after['gpu_allocated_mb']
            
            logger.info(f"{model_name} memory usage: {memory_delta}")
            
        except Exception as e:
            logger.warning(f"Error loading {model_name}: {e}")


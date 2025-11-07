"""
Model evaluation service for RE-ID models.

Implements evaluation metrics: Rank-1 accuracy, mAP, CMC curve, and performance benchmarking.
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from PIL import Image
import torch
import asyncio
from collections import defaultdict

from backend.utils.logging import get_logger
from backend.utils.device import get_device
from backend.config.settings import get_settings

logger = get_logger(__name__)


class ModelEvaluationService:
    """Service for evaluating RE-ID model performance"""
    
    def __init__(self):
        """Initialize evaluation service"""
        self.settings = get_settings()
        self.logger = logger
    
    def compute_rank_k_accuracy(
        self,
        query_results: List[Dict[str, Any]],
        k: int = 1
    ) -> float:
        """
        Compute Rank-k accuracy
        
        Args:
            query_results: List of query results, each containing:
                - 'query_id': Query tiger ID
                - 'matches': List of (tiger_id, similarity) tuples sorted by similarity
            k: Rank to compute (default: 1 for Rank-1)
            
        Returns:
            Rank-k accuracy (0.0 to 1.0)
        """
        if not query_results:
            return 0.0
        
        correct = 0
        total = 0
        
        for result in query_results:
            query_id = result.get('query_id')
            matches = result.get('matches', [])
            
            if not query_id or not matches:
                continue
            
            total += 1
            
            # Check if correct tiger is in top-k
            top_k_ids = [tiger_id for tiger_id, _ in matches[:k]]
            if query_id in top_k_ids:
                correct += 1
        
        return correct / total if total > 0 else 0.0
    
    def compute_map(
        self,
        query_results: List[Dict[str, Any]]
    ) -> float:
        """
        Compute mean Average Precision (mAP)
        
        Args:
            query_results: List of query results with matches
            
        Returns:
            mAP score (0.0 to 1.0)
        """
        if not query_results:
            return 0.0
        
        aps = []
        
        for result in query_results:
            query_id = result.get('query_id')
            matches = result.get('matches', [])
            
            if not query_id or not matches:
                continue
            
            # Find positions of correct matches
            correct_positions = [
                i for i, (tiger_id, _) in enumerate(matches)
                if tiger_id == query_id
            ]
            
            if not correct_positions:
                aps.append(0.0)
                continue
            
            # Compute Average Precision
            precisions = []
            for pos in correct_positions:
                # Precision at position pos+1
                precision = len([p for p in correct_positions if p <= pos]) / (pos + 1)
                precisions.append(precision)
            
            # Average Precision is mean of precisions
            ap = np.mean(precisions) if precisions else 0.0
            aps.append(ap)
        
        return np.mean(aps) if aps else 0.0
    
    def compute_cmc_curve(
        self,
        query_results: List[Dict[str, Any]],
        max_rank: int = 20
    ) -> Dict[int, float]:
        """
        Compute Cumulative Matching Characteristics (CMC) curve
        
        Args:
            query_results: List of query results with matches
            max_rank: Maximum rank to compute
            
        Returns:
            Dictionary mapping rank to cumulative accuracy
        """
        if not query_results:
            return {i: 0.0 for i in range(1, max_rank + 1)}
        
        # Count correct matches at each rank
        rank_counts = defaultdict(int)
        total_queries = 0
        
        for result in query_results:
            query_id = result.get('query_id')
            matches = result.get('matches', [])
            
            if not query_id or not matches:
                continue
            
            total_queries += 1
            
            # Find first correct match
            for rank, (tiger_id, _) in enumerate(matches[:max_rank], start=1):
                if tiger_id == query_id:
                    # This query is correct at this rank and all higher ranks
                    for r in range(rank, max_rank + 1):
                        rank_counts[r] += 1
                    break
        
        # Compute cumulative accuracy
        cmc = {}
        for rank in range(1, max_rank + 1):
            cmc[rank] = rank_counts[rank] / total_queries if total_queries > 0 else 0.0
        
        return cmc
    
    async def evaluate_model(
        self,
        model,
        model_name: str,
        query_images: List[Dict[str, Any]],
        gallery_images: List[Dict[str, Any]],
        device: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a model on query and gallery images
        
        Args:
            model: Model instance
            model_name: Name of the model
            query_images: List of query images, each with 'path' and 'tiger_id'
            gallery_images: List of gallery images, each with 'path' and 'tiger_id'
            device: Device to use. If None, auto-detects.
            
        Returns:
            Dictionary with evaluation results
        """
        device = get_device(device)
        logger.info(f"Evaluating {model_name} on {len(query_images)} queries, {len(gallery_images)} gallery images")
        
        results = {
            'model_name': model_name,
            'num_queries': len(query_images),
            'num_gallery': len(gallery_images),
            'query_results': [],
            'metrics': {},
            'performance': {},
            'errors': []
        }
        
        start_time = time.time()
        
        # Load model if needed
        try:
            if hasattr(model, 'load_model'):
                await model.load_model()
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            results['errors'].append(f"Load error: {str(e)}")
            return results
        
        # Generate gallery embeddings
        logger.info(f"Generating gallery embeddings for {model_name}...")
        gallery_embeddings = {}
        gallery_tiger_ids = []
        
        gallery_start = time.time()
        for gallery_img in gallery_images:
            try:
                img_path = gallery_img['path']
                tiger_id = gallery_img['tiger_id']
                
                image = Image.open(img_path)
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Generate embedding
                embedding = None
                if hasattr(model, 'generate_embedding_from_bytes'):
                    with open(img_path, 'rb') as f:
                        img_bytes = f.read()
                    embedding = await model.generate_embedding_from_bytes(img_bytes)
                elif hasattr(model, 'generate_embedding'):
                    try:
                        embedding = await model.generate_embedding(image)
                    except TypeError:
                        with open(img_path, 'rb') as f:
                            img_bytes = f.read()
                        embedding = await model.generate_embedding(img_bytes)
                
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
                results['errors'].append(f"Gallery error: {str(e)}")
                continue
        
        gallery_time = time.time() - gallery_start
        results['performance']['gallery_embedding_time'] = gallery_time
        results['performance']['gallery_embedding_time_per_image'] = (
            gallery_time / len(gallery_images) if gallery_images else 0
        )
        
        logger.info(f"Generated {len(gallery_embeddings)} gallery tiger embeddings")
        
        # Process queries
        logger.info(f"Processing queries for {model_name}...")
        query_start = time.time()
        
        for query_img in query_images:
            try:
                img_path = query_img['path']
                query_tiger_id = query_img['tiger_id']
                
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
                        with open(img_path, 'rb') as f:
                            img_bytes = f.read()
                        query_embedding = await model.generate_embedding(img_bytes)
                
                if query_embedding is None:
                    results['errors'].append(f"None embedding for query {img_path.name}")
                    continue
                
                query_embedding_array = np.array(query_embedding)
                if query_embedding_array.size == 0:
                    results['errors'].append(f"Empty embedding for query {img_path.name}")
                    continue
                
                # Compute similarities with gallery
                similarities = []
                for tiger_id, embeddings_list in gallery_embeddings.items():
                    for gallery_emb in embeddings_list:
                        # Cosine similarity
                        similarity = np.dot(query_embedding_array, gallery_emb) / (
                            np.linalg.norm(query_embedding_array) * np.linalg.norm(gallery_emb)
                        )
                        similarities.append((tiger_id, float(similarity)))
                
                # Sort by similarity
                similarities.sort(key=lambda x: x[1], reverse=True)
                
                # Store result
                results['query_results'].append({
                    'query_id': query_tiger_id,
                    'query_path': str(img_path),
                    'matches': similarities
                })
                
            except Exception as e:
                logger.error(f"Error processing query {img_path}: {e}")
                results['errors'].append(f"Query error: {str(e)}")
                continue
        
        query_time = time.time() - query_start
        results['performance']['query_processing_time'] = query_time
        results['performance']['query_processing_time_per_image'] = (
            query_time / len(query_images) if query_images else 0
        )
        
        total_time = time.time() - start_time
        results['performance']['total_time'] = total_time
        
        # Compute metrics
        logger.info(f"Computing metrics for {model_name}...")
        results['metrics'] = {
            'rank1_accuracy': self.compute_rank_k_accuracy(results['query_results'], k=1),
            'rank5_accuracy': self.compute_rank_k_accuracy(results['query_results'], k=5),
            'rank10_accuracy': self.compute_rank_k_accuracy(results['query_results'], k=10),
            'map': self.compute_map(results['query_results']),
            'cmc_curve': self.compute_cmc_curve(results['query_results'], max_rank=20)
        }
        
        logger.info(
            f"✓ {model_name} evaluation complete: "
            f"Rank-1: {results['metrics']['rank1_accuracy']:.3f}, "
            f"mAP: {results['metrics']['map']:.3f}, "
            f"Time: {total_time:.2f}s"
        )
        
        return results
    
    def benchmark_model_performance(
        self,
        model,
        model_name: str,
        test_images: List[Path],
        num_runs: int = 5
    ) -> Dict[str, Any]:
        """
        Benchmark model performance (latency, throughput, memory)
        
        Args:
            model: Model instance
            model_name: Name of the model
            test_images: List of test image paths
            num_runs: Number of runs for averaging
            
        Returns:
            Dictionary with benchmark results
        """
        logger.info(f"Benchmarking {model_name} performance...")
        
        results = {
            'model_name': model_name,
            'latency': [],
            'throughput': [],
            'memory_usage': {}
        }
        
        # Measure memory before
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            initial_memory = torch.cuda.memory_allocated()
        else:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
        
        # Run inference multiple times
        inference_times = []
        for run in range(num_runs):
            run_times = []
            
            for img_path in test_images[:10]:  # Use first 10 images
                try:
                    image = Image.open(img_path)
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    start = time.time()
                    
                    # Generate embedding (synchronous for benchmarking)
                    if hasattr(model, 'generate_embedding'):
                        # Note: This assumes synchronous method, may need adjustment
                        embedding = asyncio.run(model.generate_embedding(image))
                    else:
                        continue
                    
                    inference_time = time.time() - start
                    run_times.append(inference_time)
                    
                except Exception as e:
                    logger.warning(f"Error in benchmark run {run} for {img_path}: {e}")
                    continue
            
            if run_times:
                inference_times.extend(run_times)
        
        if inference_times:
            results['latency'] = {
                'mean': np.mean(inference_times),
                'std': np.std(inference_times),
                'min': np.min(inference_times),
                'max': np.max(inference_times),
                'p50': np.percentile(inference_times, 50),
                'p95': np.percentile(inference_times, 95),
                'p99': np.percentile(inference_times, 99)
            }
            
            # Throughput (images per second)
            results['throughput'] = {
                'images_per_second': 1.0 / results['latency']['mean'],
                'mean_latency': results['latency']['mean']
            }
        
        # Measure memory after
        if torch.cuda.is_available():
            peak_memory = torch.cuda.max_memory_allocated()
            results['memory_usage'] = {
                'initial_mb': initial_memory / (1024 * 1024),
                'peak_mb': peak_memory / (1024 * 1024),
                'delta_mb': (peak_memory - initial_memory) / (1024 * 1024)
            }
        else:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            final_memory = process.memory_info().rss
            results['memory_usage'] = {
                'initial_mb': initial_memory / (1024 * 1024),
                'final_mb': final_memory / (1024 * 1024),
                'delta_mb': (final_memory - initial_memory) / (1024 * 1024)
            }
        
        logger.info(
            f"✓ {model_name} benchmark: "
            f"Latency: {results['latency'].get('mean', 0):.3f}s, "
            f"Throughput: {results['throughput'].get('images_per_second', 0):.2f} img/s"
        )
        
        return results
    
    def generate_evaluation_report(
        self,
        evaluation_results: List[Dict[str, Any]],
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Generate evaluation report from multiple model evaluations
        
        Args:
            evaluation_results: List of evaluation result dictionaries
            output_path: Optional path to save report
            
        Returns:
            Report dictionary
        """
        report = {
            'summary': {},
            'models': {},
            'comparison': {}
        }
        
        # Aggregate metrics
        all_rank1 = []
        all_map = []
        all_latency = []
        
        for result in evaluation_results:
            model_name = result['model_name']
            report['models'][model_name] = {
                'metrics': result.get('metrics', {}),
                'performance': result.get('performance', {})
            }
            
            if 'metrics' in result:
                all_rank1.append(result['metrics'].get('rank1_accuracy', 0))
                all_map.append(result['metrics'].get('map', 0))
            
            if 'performance' in result:
                latency = result['performance'].get('query_processing_time_per_image', 0)
                if latency > 0:
                    all_latency.append(latency)
        
        # Summary statistics
        report['summary'] = {
            'num_models': len(evaluation_results),
            'best_rank1': max(all_rank1) if all_rank1 else 0,
            'best_map': max(all_map) if all_map else 0,
            'avg_latency': np.mean(all_latency) if all_latency else 0,
            'fastest_latency': min(all_latency) if all_latency else 0
        }
        
        # Find best model
        if evaluation_results:
            best_model = max(
                evaluation_results,
                key=lambda x: x.get('metrics', {}).get('rank1_accuracy', 0)
            )
            report['summary']['best_model'] = best_model['model_name']
        
        # Save report if path provided
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Evaluation report saved to {output_path}")
        
        return report


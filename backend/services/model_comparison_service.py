"""
Model comparison service for RE-ID models.

Runs multiple models on same query images, compares results, and selects best model.
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from PIL import Image
import asyncio

from backend.utils.logging import get_logger
from backend.utils.device import get_device
from backend.config.settings import get_settings
from backend.services.model_evaluation_service import ModelEvaluationService

logger = get_logger(__name__)


class ModelComparisonService:
    """Service for comparing multiple RE-ID models"""
    
    def __init__(self):
        """Initialize comparison service"""
        self.settings = get_settings()
        self.logger = logger
        self.evaluation_service = ModelEvaluationService()
    
    async def compare_models(
        self,
        models: Dict[str, Any],
        query_images: List[Dict[str, Any]],
        gallery_images: List[Dict[str, Any]],
        device: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple models on same query and gallery images
        
        Args:
            models: Dictionary mapping model names to model instances
            query_images: List of query images with 'path' and 'tiger_id'
            gallery_images: List of gallery images with 'path' and 'tiger_id'
            device: Device to use. If None, auto-detects.
            
        Returns:
            Dictionary with comparison results
        """
        device = get_device(device)
        logger.info(f"Comparing {len(models)} models on {len(query_images)} queries")
        
        comparison_results = {
            'models': {},
            'query_results': {},
            'summary': {},
            'best_model': None,
            'ensemble_results': None
        }
        
        # Evaluate each model
        model_results = {}
        for model_name, model in models.items():
            logger.info(f"Evaluating {model_name}...")
            try:
                result = await self.evaluation_service.evaluate_model(
                    model, model_name, query_images, gallery_images, device
                )
                model_results[model_name] = result
                comparison_results['models'][model_name] = {
                    'metrics': result.get('metrics', {}),
                    'performance': result.get('performance', {}),
                    'errors': result.get('errors', [])
                }
            except Exception as e:
                logger.error(f"Error evaluating {model_name}: {e}")
                comparison_results['models'][model_name] = {
                    'error': str(e)
                }
        
        # Compare metrics
        if model_results:
            comparison_results['summary'] = self._compare_metrics(model_results)
            comparison_results['best_model'] = self._select_best_model(model_results)
        
        # Generate ensemble predictions
        if len(model_results) > 1:
            comparison_results['ensemble_results'] = await self._generate_ensemble_predictions(
                models, query_images, gallery_images, device
            )
        
        logger.info(f"✓ Model comparison complete. Best model: {comparison_results.get('best_model')}")
        
        return comparison_results
    
    def _compare_metrics(
        self,
        model_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare metrics across models
        
        Args:
            model_results: Dictionary mapping model names to evaluation results
            
        Returns:
            Comparison summary
        """
        summary = {
            'rank1_accuracy': {},
            'map': {},
            'latency': {},
            'best_rank1': None,
            'best_map': None,
            'fastest': None
        }
        
        rank1_scores = {}
        map_scores = {}
        latency_scores = {}
        
        for model_name, result in model_results.items():
            metrics = result.get('metrics', {})
            performance = result.get('performance', {})
            
            rank1 = metrics.get('rank1_accuracy', 0)
            map_score = metrics.get('map', 0)
            latency = performance.get('query_processing_time_per_image', 0)
            
            rank1_scores[model_name] = rank1
            map_scores[model_name] = map_score
            if latency > 0:
                latency_scores[model_name] = latency
        
        # Find best models
        if rank1_scores:
            summary['best_rank1'] = max(rank1_scores.items(), key=lambda x: x[1])
            summary['rank1_accuracy'] = rank1_scores
        
        if map_scores:
            summary['best_map'] = max(map_scores.items(), key=lambda x: x[1])
            summary['map'] = map_scores
        
        if latency_scores:
            summary['fastest'] = min(latency_scores.items(), key=lambda x: x[1])
            summary['latency'] = latency_scores
        
        return summary
    
    def _select_best_model(
        self,
        model_results: Dict[str, Dict[str, Any]],
        metric: str = 'rank1_accuracy'
    ) -> Optional[str]:
        """
        Select best model based on metric
        
        Args:
            model_results: Dictionary mapping model names to evaluation results
            metric: Metric to use for selection (default: 'rank1_accuracy')
            
        Returns:
            Name of best model
        """
        best_model = None
        best_score = -1
        
        for model_name, result in model_results.items():
            metrics = result.get('metrics', {})
            score = metrics.get(metric, 0)
            
            if score > best_score:
                best_score = score
                best_model = model_name
        
        return best_model
    
    async def _generate_ensemble_predictions(
        self,
        models: Dict[str, Any],
        query_images: List[Dict[str, Any]],
        gallery_images: List[Dict[str, Any]],
        device: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate ensemble predictions from multiple models
        
        Args:
            models: Dictionary mapping model names to model instances
            query_images: List of query images
            gallery_images: List of gallery images
            device: Device to use
            
        Returns:
            Ensemble prediction results
        """
        logger.info("Generating ensemble predictions...")
        
        ensemble_results = {
            'method': 'weighted_average',
            'query_results': [],
            'metrics': {}
        }
        
        # Get individual model predictions
        model_predictions = {}
        
        for model_name, model in models.items():
            try:
                result = await self.evaluation_service.evaluate_model(
                    model, model_name, query_images, gallery_images, device
                )
                model_predictions[model_name] = result.get('query_results', [])
            except Exception as e:
                logger.warning(f"Error getting predictions from {model_name}: {e}")
                continue
        
        if not model_predictions:
            return None
        
        # Combine predictions for each query
        num_queries = len(query_images)
        for query_idx in range(num_queries):
            query_img = query_images[query_idx]
            query_id = query_img['tiger_id']
            
            # Collect matches from all models
            all_matches = {}
            
            for model_name, predictions in model_predictions.items():
                if query_idx < len(predictions):
                    query_result = predictions[query_idx]
                    matches = query_result.get('matches', [])
                    
                    # Weight matches by model's rank1 accuracy (if available)
                    # For now, use equal weights
                    weight = 1.0 / len(model_predictions)
                    
                    for tiger_id, similarity in matches:
                        if tiger_id not in all_matches:
                            all_matches[tiger_id] = 0.0
                        all_matches[tiger_id] += similarity * weight
            
            # Sort by combined similarity
            combined_matches = sorted(
                all_matches.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            ensemble_results['query_results'].append({
                'query_id': query_id,
                'query_path': str(query_img['path']),
                'matches': [(tid, float(sim)) for tid, sim in combined_matches]
            })
        
        # Compute ensemble metrics
        ensemble_results['metrics'] = {
            'rank1_accuracy': self.evaluation_service.compute_rank_k_accuracy(
                ensemble_results['query_results'], k=1
            ),
            'rank5_accuracy': self.evaluation_service.compute_rank_k_accuracy(
                ensemble_results['query_results'], k=5
            ),
            'map': self.evaluation_service.compute_map(ensemble_results['query_results'])
        }
        
        logger.info(
            f"✓ Ensemble: Rank-1: {ensemble_results['metrics']['rank1_accuracy']:.3f}, "
            f"mAP: {ensemble_results['metrics']['map']:.3f}"
        )
        
        return ensemble_results
    
    async def select_model_for_scenario(
        self,
        models: Dict[str, Any],
        scenario: str,
        query_images: List[Dict[str, Any]],
        gallery_images: List[Dict[str, Any]],
        device: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Select best model for a specific scenario
        
        Args:
            models: Dictionary mapping model names to model instances
            scenario: Scenario type ('accuracy', 'speed', 'balanced')
            query_images: List of query images
            gallery_images: List of gallery images
            device: Device to use. If None, auto-detects.
            
        Returns:
            Selected model information
        """
        logger.info(f"Selecting best model for scenario: {scenario}")
        
        # Evaluate all models
        comparison = await self.compare_models(models, query_images, gallery_images, device)
        
        if not comparison.get('models'):
            return {'error': 'No models evaluated successfully'}
        
        # Select based on scenario
        if scenario == 'accuracy':
            best_model = comparison.get('best_model')
            metric = 'rank1_accuracy'
        elif scenario == 'speed':
            # Find fastest model
            fastest = comparison.get('summary', {}).get('fastest')
            if fastest:
                best_model = fastest[0]
                metric = 'latency'
            else:
                best_model = comparison.get('best_model')
                metric = 'rank1_accuracy'
        else:  # balanced
            # Use weighted score: accuracy * 0.7 + (1/latency) * 0.3
            best_model = None
            best_score = -1
            
            for model_name, model_data in comparison.get('models', {}).items():
                metrics = model_data.get('metrics', {})
                performance = model_data.get('performance', {})
                
                rank1 = metrics.get('rank1_accuracy', 0)
                latency = performance.get('query_processing_time_per_image', 0)
                
                if latency > 0:
                    speed_score = 1.0 / latency
                else:
                    speed_score = 0
                
                balanced_score = rank1 * 0.7 + speed_score * 0.3
                
                if balanced_score > best_score:
                    best_score = balanced_score
                    best_model = model_name
            
            metric = 'balanced'
        
        result = {
            'scenario': scenario,
            'selected_model': best_model,
            'metric': metric,
            'comparison': comparison
        }
        
        logger.info(f"✓ Selected {best_model} for scenario {scenario}")
        
        return result
    
    def store_comparison_results(
        self,
        comparison_results: Dict[str, Any],
        output_path: Path
    ) -> None:
        """
        Store comparison results to file
        
        Args:
            comparison_results: Comparison results dictionary
            output_path: Path to save results
        """
        import json
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(comparison_results, f, indent=2)
        
        logger.info(f"Comparison results saved to {output_path}")


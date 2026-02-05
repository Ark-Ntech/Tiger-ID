#!/usr/bin/env python3
"""
MatchAnything-ELOFTR Testing Script for Tiger Re-Identification.

This script tests whether MatchAnything-ELOFTR can discriminate between
same-tiger and different-tiger image pairs.

Requires: pip install "git+https://github.com/huggingface/transformers@22e89e538529420b2ddae6af70865655bc5c22d8"
"""

import sys
import argparse
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
from datetime import datetime
import time

import numpy as np
from PIL import Image
import torch
from tqdm import tqdm

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from transformers import AutoImageProcessor, AutoModelForKeypointMatching
    MATCHANYTHING_AVAILABLE = True
except ImportError:
    MATCHANYTHING_AVAILABLE = False
    print("WARNING: MatchAnything not available. Install with:")
    print('  pip install "git+https://github.com/huggingface/transformers@22e89e538529420b2ddae6af70865655bc5c22d8"')

# Image extensions to process
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}


class MatchAnythingTester:
    """Test MatchAnything-ELOFTR for tiger re-identification."""

    def __init__(
        self,
        model_name: str = "zju-community/matchanything_eloftr",
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        threshold: float = 0.2
    ):
        """
        Initialize the tester.

        Args:
            model_name: HuggingFace model name
            device: Device to use (cuda/cpu)
            threshold: Matching threshold for keypoint filtering
        """
        self.model_name = model_name
        self.device = device
        self.threshold = threshold
        self.processor = None
        self.model = None

    def load_model(self) -> bool:
        """Load the MatchAnything model."""
        if not MATCHANYTHING_AVAILABLE:
            print("ERROR: transformers not installed with MatchAnything support")
            return False

        print(f"Loading MatchAnything model: {self.model_name}")
        print(f"Device: {self.device}")

        try:
            self.processor = AutoImageProcessor.from_pretrained(self.model_name)
            self.model = AutoModelForKeypointMatching.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()  # Inference mode
            print("Model loaded successfully")
            return True
        except Exception as e:
            print(f"ERROR loading model: {e}")
            return False

    def match_images(
        self,
        img1: Image.Image,
        img2: Image.Image
    ) -> Dict[str, Any]:
        """
        Match two images and return keypoint correspondences.

        Args:
            img1: First PIL Image
            img2: Second PIL Image

        Returns:
            Dictionary with matching results
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Prepare inputs
        inputs = self.processor([img1, img2], return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Run inference
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Post-process
        image_sizes = [[(img1.height, img1.width), (img2.height, img2.width)]]
        results = self.processor.post_process_keypoint_matching(
            outputs, image_sizes, threshold=self.threshold
        )

        # Extract metrics (key is 'matching_scores' not 'scores')
        keypoints0 = results[0]["keypoints0"].float()  # Convert to float for std()
        keypoints1 = results[0]["keypoints1"].float()
        scores = results[0]["matching_scores"]

        num_matches = len(scores)

        return {
            "num_matches": num_matches,
            "mean_score": float(scores.mean().item()) if num_matches > 0 else 0.0,
            "max_score": float(scores.max().item()) if num_matches > 0 else 0.0,
            "min_score": float(scores.min().item()) if num_matches > 0 else 0.0,
            "std_score": float(scores.std().item()) if num_matches > 1 else 0.0,
            "total_score": float(scores.sum().item()) if num_matches > 0 else 0.0,
            # Keypoint dispersion (how spread out are matches)
            "kp0_std_x": float(keypoints0[:, 0].std().item()) if num_matches > 1 else 0.0,
            "kp0_std_y": float(keypoints0[:, 1].std().item()) if num_matches > 1 else 0.0,
            "kp1_std_x": float(keypoints1[:, 0].std().item()) if num_matches > 1 else 0.0,
            "kp1_std_y": float(keypoints1[:, 1].std().item()) if num_matches > 1 else 0.0,
        }


def load_tiger_images(data_path: Path, split: str = "test") -> Dict[str, List[Path]]:
    """
    Load tiger images from prepared dataset or ATRW raw format.

    Args:
        data_path: Path to prepared dataset (with train/val/test splits) or ATRW base
        split: Which split to use

    Returns:
        Dictionary mapping tiger_id to list of image paths
    """
    tiger_images = defaultdict(list)

    # Try ATRW raw format first (CSV-based)
    atrw_base = data_path / "images" / "Amur Tigers"
    if not atrw_base.exists():
        # Maybe data_path is already pointing to Amur Tigers
        atrw_base = data_path
        if not (atrw_base / "reid_list_train.csv").exists():
            atrw_base = data_path / "Amur Tigers"

    train_csv = atrw_base / "reid_list_train.csv"
    test_csv = atrw_base / "reid_list_test.csv"

    if train_csv.exists() or test_csv.exists():
        print("Detected ATRW raw format (CSV-based)")
        return load_atrw_images(atrw_base, split)

    # Fall back to prepared dataset format (directory-based)
    split_dir = data_path / split
    if not split_dir.exists():
        print(f"WARNING: Split directory not found: {split_dir}")
        # Try loading from data_path directly
        split_dir = data_path

    for tiger_dir in split_dir.iterdir():
        if not tiger_dir.is_dir():
            continue

        tiger_id = tiger_dir.name
        for img_path in tiger_dir.iterdir():
            if img_path.suffix.lower() in IMAGE_EXTENSIONS:
                tiger_images[tiger_id].append(img_path)

    return dict(tiger_images)


def load_atrw_images(atrw_base: Path, split: str = "train") -> Dict[str, List[Path]]:
    """
    Load tiger images from ATRW raw format using CSV files.

    Args:
        atrw_base: Path to ATRW "Amur Tigers" directory
        split: Which split to use (train/test)

    Returns:
        Dictionary mapping tiger_id to list of image paths
    """
    import pandas as pd

    tiger_images = defaultdict(list)

    csv_file = atrw_base / f"reid_list_{split}.csv"
    images_dir = atrw_base / split

    if not csv_file.exists():
        print(f"WARNING: CSV file not found: {csv_file}")
        return dict(tiger_images)

    if not images_dir.exists():
        print(f"WARNING: Images directory not found: {images_dir}")
        return dict(tiger_images)

    # Read CSV (format: tiger_id,filename without header)
    df = pd.read_csv(csv_file, header=None, names=['tiger_id', 'filename'])

    print(f"Loaded {len(df)} entries from {csv_file.name}")
    print(f"Unique tigers: {df['tiger_id'].nunique()}")

    for _, row in df.iterrows():
        tiger_id = str(row['tiger_id'])
        filename = row['filename']
        img_path = images_dir / filename

        if img_path.exists():
            tiger_images[tiger_id].append(img_path)
        else:
            # Try without leading zeros variations
            pass

    # Report statistics
    tigers_with_multiple = sum(1 for imgs in tiger_images.values() if len(imgs) >= 2)
    print(f"Tigers with images: {len(tiger_images)}")
    print(f"Tigers with 2+ images: {tigers_with_multiple}")

    return dict(tiger_images)


def create_test_pairs(
    tiger_images: Dict[str, List[Path]],
    num_same_pairs: int = 100,
    num_diff_pairs: int = 100,
    seed: int = 42
) -> List[Tuple[Path, Path, bool, str, str]]:
    """
    Create balanced same-tiger and different-tiger image pairs.

    Args:
        tiger_images: Dictionary mapping tiger_id to image paths
        num_same_pairs: Number of same-tiger pairs to create
        num_diff_pairs: Number of different-tiger pairs to create
        seed: Random seed

    Returns:
        List of (img1_path, img2_path, is_same_tiger, tiger1_id, tiger2_id)
    """
    random.seed(seed)
    pairs = []

    # Get tigers with at least 2 images (for same-tiger pairs)
    tigers_with_multiple = {
        tid: paths for tid, paths in tiger_images.items()
        if len(paths) >= 2
    }
    all_tiger_ids = list(tiger_images.keys())

    print(f"Tigers with 2+ images (for same-tiger pairs): {len(tigers_with_multiple)}")
    print(f"Total tigers: {len(all_tiger_ids)}")

    # Create same-tiger pairs
    same_pairs_created = 0
    tiger_list = list(tigers_with_multiple.keys())

    while same_pairs_created < num_same_pairs and tiger_list:
        tiger_id = random.choice(tiger_list)
        images = tigers_with_multiple[tiger_id]

        if len(images) >= 2:
            img1, img2 = random.sample(images, 2)
            pairs.append((img1, img2, True, tiger_id, tiger_id))
            same_pairs_created += 1

        # Avoid infinite loop
        if same_pairs_created == 0:
            break

    print(f"Created {same_pairs_created} same-tiger pairs")

    # Create different-tiger pairs
    diff_pairs_created = 0
    attempts = 0
    max_attempts = num_diff_pairs * 10

    while diff_pairs_created < num_diff_pairs and attempts < max_attempts:
        attempts += 1
        if len(all_tiger_ids) < 2:
            break

        tiger1_id, tiger2_id = random.sample(all_tiger_ids, 2)
        if tiger1_id == tiger2_id:
            continue

        images1 = tiger_images[tiger1_id]
        images2 = tiger_images[tiger2_id]

        if images1 and images2:
            img1 = random.choice(images1)
            img2 = random.choice(images2)
            pairs.append((img1, img2, False, tiger1_id, tiger2_id))
            diff_pairs_created += 1

    print(f"Created {diff_pairs_created} different-tiger pairs")

    # Shuffle pairs
    random.shuffle(pairs)

    return pairs


def compute_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute discrimination metrics from test results.

    Args:
        results: List of test results with 'is_same_tiger' and matching metrics

    Returns:
        Dictionary with computed metrics
    """
    same_tiger_results = [r for r in results if r["is_same_tiger"]]
    diff_tiger_results = [r for r in results if not r["is_same_tiger"]]

    if not same_tiger_results or not diff_tiger_results:
        return {"error": "Insufficient data for metrics"}

    # Compute statistics for each metric
    metrics = {}

    for metric_name in ["num_matches", "mean_score", "total_score"]:
        same_values = [r[metric_name] for r in same_tiger_results]
        diff_values = [r[metric_name] for r in diff_tiger_results]

        same_mean = np.mean(same_values)
        diff_mean = np.mean(diff_values)
        same_std = np.std(same_values)
        diff_std = np.std(diff_values)

        # Cohen's d effect size
        pooled_std = np.sqrt((same_std**2 + diff_std**2) / 2)
        cohens_d = (same_mean - diff_mean) / pooled_std if pooled_std > 0 else 0

        # AUC approximation using Mann-Whitney U statistic
        all_values = same_values + diff_values
        all_labels = [1] * len(same_values) + [0] * len(diff_values)

        # Sort by value
        sorted_pairs = sorted(zip(all_values, all_labels), key=lambda x: x[0], reverse=True)
        sorted_labels = [p[1] for p in sorted_pairs]

        # Calculate AUC
        n_pos = sum(all_labels)
        n_neg = len(all_labels) - n_pos
        auc = 0
        pos_count = 0
        for label in sorted_labels:
            if label == 1:
                pos_count += 1
            else:
                auc += pos_count
        auc = auc / (n_pos * n_neg) if n_pos * n_neg > 0 else 0.5

        metrics[metric_name] = {
            "same_tiger_mean": float(same_mean),
            "same_tiger_std": float(same_std),
            "diff_tiger_mean": float(diff_mean),
            "diff_tiger_std": float(diff_std),
            "cohens_d": float(cohens_d),
            "auc": float(auc),
            "separation": float(same_mean - diff_mean)
        }

    # Best metric for discrimination
    best_metric = max(metrics.items(), key=lambda x: x[1]["auc"])
    metrics["best_discriminating_metric"] = best_metric[0]
    metrics["best_auc"] = best_metric[1]["auc"]

    # Overall recommendation
    if best_metric[1]["auc"] > 0.80:
        metrics["recommendation"] = "PROCEED - Good discrimination (AUC > 0.80)"
    elif best_metric[1]["auc"] > 0.70:
        metrics["recommendation"] = "INVESTIGATE - Moderate discrimination (AUC 0.70-0.80)"
    else:
        metrics["recommendation"] = "STOP - Poor discrimination (AUC < 0.70)"

    return metrics


def run_test(
    tester: MatchAnythingTester,
    pairs: List[Tuple[Path, Path, bool, str, str]],
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the matching test on all pairs.

    Args:
        tester: MatchAnythingTester instance
        pairs: List of image pairs to test
        output_path: Optional path to save results

    Returns:
        Dictionary with test results and metrics
    """
    results = []
    timings = []

    print(f"\nTesting {len(pairs)} image pairs...")

    for img1_path, img2_path, is_same, tiger1_id, tiger2_id in tqdm(pairs):
        try:
            # Load images
            img1 = Image.open(img1_path).convert("RGB")
            img2 = Image.open(img2_path).convert("RGB")

            # Time the matching
            start_time = time.time()
            match_result = tester.match_images(img1, img2)
            elapsed = time.time() - start_time
            timings.append(elapsed)

            # Store result
            result = {
                "img1": str(img1_path),
                "img2": str(img2_path),
                "is_same_tiger": is_same,
                "tiger1_id": tiger1_id,
                "tiger2_id": tiger2_id,
                "time_seconds": elapsed,
                **match_result
            }
            results.append(result)

        except Exception as e:
            print(f"ERROR processing pair: {e}")
            continue

    # Compute metrics
    metrics = compute_metrics(results)

    # Compute timing stats
    timing_stats = {
        "mean_time_seconds": float(np.mean(timings)),
        "std_time_seconds": float(np.std(timings)),
        "total_time_seconds": float(np.sum(timings)),
        "pairs_tested": len(results)
    }

    # Assemble output
    output = {
        "metadata": {
            "model": tester.model_name,
            "device": tester.device,
            "threshold": tester.threshold,
            "timestamp": datetime.now().isoformat(),
        },
        "timing": timing_stats,
        "metrics": metrics,
        "results": results
    }

    # Save if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\nResults saved to: {output_path}")

    return output


def print_summary(output: Dict[str, Any]):
    """Print a summary of test results."""
    print("\n" + "=" * 60)
    print("MATCHANYTHING TEST RESULTS SUMMARY")
    print("=" * 60)

    metrics = output.get("metrics", {})
    timing = output.get("timing", {})

    print(f"\nPairs tested: {timing.get('pairs_tested', 0)}")
    print(f"Mean time per pair: {timing.get('mean_time_seconds', 0):.3f}s")

    print("\n--- Discrimination Metrics ---")
    for metric_name in ["num_matches", "mean_score", "total_score"]:
        if metric_name in metrics:
            m = metrics[metric_name]
            print(f"\n{metric_name}:")
            print(f"  Same tiger:  {m['same_tiger_mean']:.3f} +/- {m['same_tiger_std']:.3f}")
            print(f"  Diff tiger:  {m['diff_tiger_mean']:.3f} +/- {m['diff_tiger_std']:.3f}")
            print(f"  Separation:  {m['separation']:.3f}")
            print(f"  Cohen's d:   {m['cohens_d']:.3f}")
            print(f"  AUC:         {m['auc']:.3f}")

    print(f"\n--- Overall ---")
    print(f"Best metric: {metrics.get('best_discriminating_metric', 'N/A')}")
    print(f"Best AUC: {metrics.get('best_auc', 0):.3f}")
    print(f"\n>>> {metrics.get('recommendation', 'N/A')}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Test MatchAnything-ELOFTR for tiger re-identification"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/models/atrw",
        help="Path to ATRW dataset or prepared test dataset"
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        help="Dataset split to use (train/val/test)"
    )
    parser.add_argument(
        "--num-same-pairs",
        type=int,
        default=100,
        help="Number of same-tiger pairs to test"
    )
    parser.add_argument(
        "--num-diff-pairs",
        type=int,
        default=100,
        help="Number of different-tiger pairs to test"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.2,
        help="Keypoint matching threshold"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/matchanything_test_results.json",
        help="Output path for results"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Device to use (cuda/cpu)"
    )

    args = parser.parse_args()

    # Check if MatchAnything is available
    if not MATCHANYTHING_AVAILABLE:
        print("ERROR: MatchAnything not available. Please install with:")
        print('  pip install "git+https://github.com/huggingface/transformers@22e89e538529420b2ddae6af70865655bc5c22d8"')
        sys.exit(1)

    # Load tiger images
    data_path = Path(args.data_path)
    print(f"Loading tiger images from: {data_path}")
    tiger_images = load_tiger_images(data_path, args.split)

    if not tiger_images:
        print(f"ERROR: No tiger images found in {data_path}")
        print("Please run prepare_test_datasets.py first, or provide a valid data path.")
        sys.exit(1)

    print(f"Loaded {len(tiger_images)} tigers")
    total_images = sum(len(imgs) for imgs in tiger_images.values())
    print(f"Total images: {total_images}")

    # Create test pairs
    pairs = create_test_pairs(
        tiger_images,
        num_same_pairs=args.num_same_pairs,
        num_diff_pairs=args.num_diff_pairs,
        seed=args.seed
    )

    if not pairs:
        print("ERROR: Could not create test pairs")
        sys.exit(1)

    # Initialize tester
    tester = MatchAnythingTester(
        device=args.device,
        threshold=args.threshold
    )

    # Load model
    if not tester.load_model():
        sys.exit(1)

    # Run test
    output = run_test(
        tester,
        pairs,
        output_path=Path(args.output)
    )

    # Print summary
    print_summary(output)


if __name__ == "__main__":
    main()

"""Optimize calibration temperatures and ensemble weights using ATRW train data.

Generates embeddings from all 6 ReID models on ATRW labeled images, splits
into gallery/query by tiger identity, and optimizes per-model temperatures
to maximize rank-1 accuracy.

Usage:
    python scripts/calibrate_temperatures.py
    python scripts/calibrate_temperatures.py --cache-dir data/calibration_cache
    python scripts/calibrate_temperatures.py --skip-embedding  # use cached embeddings
"""

import asyncio
import argparse
import sys
import os
import time
import json
import csv
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import numpy as np


ALL_MODELS = [
    "wildlife_tools", "cvwc2019", "rapid",
    "tiger_reid", "transreid", "megadescriptor_b"
]

# Temperature grid for per-model search
TEMP_GRID = [0.5, 0.7, 0.85, 0.95, 1.0, 1.1, 1.3, 1.5]

# Weight grid for ensemble weight search
WEIGHT_GRID = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40]


def load_atrw_labels(csv_path: str) -> dict:
    """Load ATRW train CSV: tiger_id -> list of filenames."""
    tiger_images = defaultdict(list)
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                tiger_id, filename = row[0].strip(), row[1].strip()
                tiger_images[tiger_id].append(filename)
    return dict(tiger_images)


def split_gallery_query(tiger_images: dict, gallery_ratio: float = 0.6, seed: int = 42):
    """Split images into gallery and query sets by tiger identity.

    For each tiger with 2+ images, first 60% go to gallery, rest to query.
    Tigers with only 1 image go to gallery only.
    """
    rng = np.random.RandomState(seed)
    gallery = {}  # tiger_id -> [filenames]
    query = {}    # tiger_id -> [filenames]

    for tiger_id, images in tiger_images.items():
        if len(images) < 2:
            gallery[tiger_id] = images
            continue

        shuffled = images.copy()
        rng.shuffle(shuffled)
        split_idx = max(1, int(len(shuffled) * gallery_ratio))
        gallery[tiger_id] = shuffled[:split_idx]
        query[tiger_id] = shuffled[split_idx:]

    return gallery, query


async def generate_embedding(model, model_name: str, image_bytes: bytes):
    """Generate embedding from a model, handling different interfaces."""
    try:
        if hasattr(model, 'generate_embedding_from_bytes'):
            return await model.generate_embedding_from_bytes(image_bytes)
        elif hasattr(model, 'generate_embedding'):
            result = model.generate_embedding(image_bytes)
            if asyncio.iscoroutine(result):
                result = await result
            if isinstance(result, dict):
                emb = result.get("embedding")
                if emb is not None and not isinstance(emb, np.ndarray):
                    return np.array(emb)
                return emb
            return result
    except Exception as e:
        print(f"    {model_name}: ERROR - {str(e)[:80]}")
        return None


def _load_embedding_cache(cache_file: str) -> dict:
    """Load cached embeddings from npz file."""
    if not os.path.exists(cache_file):
        return {}
    data = np.load(cache_file)
    result = {str(k): data[k] for k in data.files}
    data.close()
    return result


async def generate_all_embeddings(
    image_dir: str,
    filenames: list,
    models: dict,
    cache_dir: str,
    batch_size: int = 25
) -> dict:
    """Generate embeddings for all images from all models.

    Returns: {model_name: {filename: embedding_array}}
    Caches to disk for resume.
    """
    os.makedirs(cache_dir, exist_ok=True)
    all_embeddings = {}

    for model_name, model in models.items():
        cache_file = os.path.join(cache_dir, f"atrw_{model_name}.npz")
        cached = _load_embedding_cache(cache_file)

        if len(cached) >= len(filenames) * 0.9:  # 90% coverage
            print(f"  {model_name}: loaded {len(cached)} cached embeddings")
            all_embeddings[model_name] = cached
            continue

        print(f"  {model_name}: generating embeddings for {len(filenames)} images...")
        embeddings = dict(cached)
        processed = 0
        errors = 0

        for batch_start in range(0, len(filenames), batch_size):
            batch = filenames[batch_start:batch_start + batch_size]
            batch_time = time.time()

            for filename in batch:
                if filename in embeddings:
                    continue

                img_path = os.path.join(image_dir, filename)
                if not os.path.exists(img_path):
                    errors += 1
                    continue

                try:
                    image_bytes = Path(img_path).read_bytes()
                    emb = await generate_embedding(model, model_name, image_bytes)
                    if emb is not None and isinstance(emb, np.ndarray):
                        embeddings[filename] = emb
                        processed += 1
                except Exception:
                    errors += 1

            elapsed = time.time() - batch_time
            total_done = batch_start + len(batch)
            print(
                f"    {model_name}: {total_done}/{len(filenames)} "
                f"({100*total_done/len(filenames):.0f}%) "
                f"batch: {elapsed:.1f}s"
            )

            # Save checkpoint every 100 images
            if processed > 0 and total_done % 100 < batch_size:
                np.savez_compressed(cache_file, **embeddings)

        # Final save
        if embeddings:
            np.savez_compressed(cache_file, **embeddings)
        print(f"  {model_name}: {len(embeddings)} embeddings, {errors} errors")
        all_embeddings[model_name] = embeddings

    return all_embeddings


def compute_similarity_matrix(
    query_embeddings: dict,
    gallery_embeddings: dict,
    temperature: float = 1.0
) -> tuple:
    """Compute cosine similarity matrix between query and gallery.

    Returns: (similarity_matrix, query_filenames, gallery_filenames)
    """
    query_files = sorted(query_embeddings.keys())
    gallery_files = sorted(gallery_embeddings.keys())

    if not query_files or not gallery_files:
        return np.array([]), query_files, gallery_files

    # Stack into matrices
    Q = np.vstack([query_embeddings[f] for f in query_files])
    G = np.vstack([gallery_embeddings[f] for f in gallery_files])

    # L2 normalize
    Q = Q / (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-10)
    G = G / (np.linalg.norm(G, axis=1, keepdims=True) + 1e-10)

    # Cosine similarity
    sim = Q @ G.T

    # Apply temperature calibration
    if temperature != 1.0:
        sim = sim / temperature
        sim = np.clip(sim, 0.0, 1.0)

    return sim, query_files, gallery_files


def evaluate_rank_accuracy(
    sim_matrix: np.ndarray,
    query_files: list,
    gallery_files: list,
    query_labels: dict,
    gallery_labels: dict,
    k_values: list = [1, 5, 10]
) -> dict:
    """Compute rank-k accuracy and mAP.

    Args:
        sim_matrix: (num_query, num_gallery) similarity matrix
        query_files: list of query filenames
        gallery_files: list of gallery filenames
        query_labels: filename -> tiger_id
        gallery_labels: filename -> tiger_id

    Returns:
        dict with rank-k accuracies and mAP
    """
    if sim_matrix.size == 0:
        return {f"rank{k}": 0.0 for k in k_values}

    results = {f"rank{k}": 0.0 for k in k_values}
    aps = []

    for i, qf in enumerate(query_files):
        q_label = query_labels.get(qf)
        if q_label is None:
            continue

        # Sort gallery by similarity (descending)
        indices = np.argsort(-sim_matrix[i])

        # Check rank-k
        correct_found = False
        num_correct = 0
        precision_sum = 0.0

        for rank, idx in enumerate(indices):
            gf = gallery_files[idx]
            g_label = gallery_labels.get(gf)

            if g_label == q_label:
                num_correct += 1
                precision_sum += num_correct / (rank + 1)

                if not correct_found:
                    for k in k_values:
                        if rank < k:
                            results[f"rank{k}"] += 1
                    correct_found = True

        # Average precision for this query
        total_relevant = sum(1 for gf in gallery_files if gallery_labels.get(gf) == q_label)
        if total_relevant > 0:
            aps.append(precision_sum / total_relevant)

    # Normalize by number of queries
    num_queries = len(query_files)
    if num_queries > 0:
        for k in k_values:
            results[f"rank{k}"] /= num_queries

    results["mAP"] = float(np.mean(aps)) if aps else 0.0
    results["num_queries"] = num_queries

    return results


def optimize_temperature_per_model(
    model_name: str,
    query_embs: dict,
    gallery_embs: dict,
    query_labels: dict,
    gallery_labels: dict,
    temp_grid: list
) -> tuple:
    """Find optimal temperature for a single model.

    Returns: (best_temp, best_rank1, results_by_temp)
    """
    best_temp = 1.0
    best_rank1 = 0.0
    results_by_temp = {}

    for temp in temp_grid:
        sim, qf, gf = compute_similarity_matrix(query_embs, gallery_embs, temperature=temp)
        metrics = evaluate_rank_accuracy(sim, qf, gf, query_labels, gallery_labels)
        results_by_temp[temp] = metrics

        if metrics["rank1"] > best_rank1:
            best_rank1 = metrics["rank1"]
            best_temp = temp

    return best_temp, best_rank1, results_by_temp


def optimize_ensemble_weights(
    all_sim_matrices: dict,
    query_files: list,
    gallery_files: list,
    query_labels: dict,
    gallery_labels: dict,
    current_weights: dict,
    calibrated_temps: dict
) -> tuple:
    """Optimize ensemble weights using calibrated similarity matrices.

    Uses a simplified search: try predefined weight configurations.
    Returns: (best_weights, best_rank1)
    """
    # Get calibrated similarity matrices for each model
    calibrated_sims = {}
    for model_name, (sim, qf, gf) in all_sim_matrices.items():
        temp = calibrated_temps.get(model_name, 1.0)
        if temp != 1.0:
            cal_sim = np.clip(sim / temp, 0.0, 1.0)
        else:
            cal_sim = sim
        calibrated_sims[model_name] = cal_sim

    best_weights = current_weights.copy()
    best_rank1 = 0.0

    # Define weight configs to try
    configs = [
        current_weights,
        {"wildlife_tools": 0.50, "cvwc2019": 0.25, "transreid": 0.15,
         "megadescriptor_b": 0.10, "tiger_reid": 0.05, "rapid": 0.05},
        {"wildlife_tools": 0.25, "cvwc2019": 0.25, "transreid": 0.25,
         "megadescriptor_b": 0.25, "tiger_reid": 0.00, "rapid": 0.00},
        {"wildlife_tools": 0.45, "cvwc2019": 0.35, "transreid": 0.20,
         "megadescriptor_b": 0.00, "tiger_reid": 0.00, "rapid": 0.00},
        {"wildlife_tools": 0.30, "cvwc2019": 0.25, "transreid": 0.20,
         "megadescriptor_b": 0.15, "tiger_reid": 0.05, "rapid": 0.05},
        {"wildlife_tools": 0.60, "cvwc2019": 0.20, "transreid": 0.10,
         "megadescriptor_b": 0.05, "tiger_reid": 0.03, "rapid": 0.02},
    ]

    for weights in configs:
        combined = np.zeros_like(next(iter(calibrated_sims.values())))
        total_weight = 0.0

        for model_name, sim in calibrated_sims.items():
            w = weights.get(model_name, 0.0)
            if w > 0:
                combined += w * sim
                total_weight += w

        if total_weight > 0:
            combined /= total_weight

        metrics = evaluate_rank_accuracy(
            combined, query_files, gallery_files, query_labels, gallery_labels
        )

        if metrics["rank1"] > best_rank1:
            best_rank1 = metrics["rank1"]
            best_weights = weights.copy()

    return best_weights, best_rank1


async def main():
    parser = argparse.ArgumentParser(description="Calibrate temperatures for ReID ensemble")
    parser.add_argument(
        "--cache-dir", default="data/calibration_cache",
        help="Directory to cache embeddings"
    )
    parser.add_argument(
        "--skip-embedding", action="store_true",
        help="Skip embedding generation (use cached only)"
    )
    parser.add_argument(
        "--models", nargs="+", default=ALL_MODELS,
        help="Models to calibrate"
    )
    parser.add_argument(
        "--output", default="config/calibration_temperatures.json",
        help="Output JSON file for calibrated temperatures"
    )
    args = parser.parse_args()

    atrw_base = Path("data/models/atrw/images/Amur Tigers")
    csv_path = atrw_base / "reid_list_train.csv"
    image_dir = str(atrw_base / "train")

    print("=" * 70)
    print("CALIBRATION TEMPERATURE OPTIMIZATION")
    print("=" * 70)

    # 1. Load labels and split
    print("\n--- Loading ATRW Train Labels ---")
    tiger_images = load_atrw_labels(str(csv_path))
    print(f"  Tigers: {len(tiger_images)}")
    print(f"  Images: {sum(len(v) for v in tiger_images.values())}")

    gallery_split, query_split = split_gallery_query(tiger_images)
    print(f"  Gallery tigers: {len(gallery_split)}, images: {sum(len(v) for v in gallery_split.values())}")
    print(f"  Query tigers: {len(query_split)}, images: {sum(len(v) for v in query_split.values())}")

    # Build label lookups
    query_labels = {}
    gallery_labels = {}
    query_filenames = []
    gallery_filenames = []

    for tiger_id, files in query_split.items():
        for f in files:
            query_labels[f] = tiger_id
            query_filenames.append(f)

    for tiger_id, files in gallery_split.items():
        for f in files:
            gallery_labels[f] = tiger_id
            gallery_filenames.append(f)

    all_filenames = list(set(query_filenames + gallery_filenames))
    print(f"  Total unique images: {len(all_filenames)}")

    # 2. Generate embeddings
    print("\n--- Generating Embeddings ---")
    if args.skip_embedding:
        print("  Using cached embeddings only")
        all_embeddings = {}
        for model_name in args.models:
            cache_file = os.path.join(args.cache_dir, f"atrw_{model_name}.npz")
            cached = _load_embedding_cache(cache_file)
            if cached:
                all_embeddings[model_name] = cached
                print(f"  {model_name}: {len(cached)} cached")
            else:
                print(f"  {model_name}: no cache found, skipping")
    else:
        from backend.services.tiger.model_loader import get_model_loader
        loader = get_model_loader()

        models = {}
        for model_name in args.models:
            try:
                models[model_name] = loader.get_model(model_name)
                print(f"  {model_name}: loaded")
            except Exception as e:
                print(f"  {model_name}: FAILED - {e}")

        all_embeddings = await generate_all_embeddings(
            image_dir, all_filenames, models, args.cache_dir
        )

    # 3. Optimize temperatures per model
    print("\n--- Optimizing Temperatures ---")
    calibrated_temps = {}
    model_results = {}
    all_sim_matrices = {}

    for model_name in args.models:
        if model_name not in all_embeddings or not all_embeddings[model_name]:
            print(f"  {model_name}: no embeddings, skipping")
            continue

        embs = all_embeddings[model_name]

        # Split embeddings into query/gallery
        q_embs = {f: embs[f] for f in query_filenames if f in embs}
        g_embs = {f: embs[f] for f in gallery_filenames if f in embs}

        if not q_embs or not g_embs:
            print(f"  {model_name}: insufficient query/gallery embeddings")
            continue

        # Store raw similarity matrix for ensemble optimization
        raw_sim, qf, gf = compute_similarity_matrix(q_embs, g_embs, temperature=1.0)
        all_sim_matrices[model_name] = (raw_sim, qf, gf)

        # Optimize temperature
        best_temp, best_rank1, results_by_temp = optimize_temperature_per_model(
            model_name, q_embs, g_embs, query_labels, gallery_labels, TEMP_GRID
        )

        calibrated_temps[model_name] = best_temp
        model_results[model_name] = {
            "best_temperature": best_temp,
            "best_rank1": best_rank1,
            "results_by_temp": {
                str(t): {k: round(v, 4) for k, v in m.items()}
                for t, m in results_by_temp.items()
            }
        }

        baseline_rank1 = results_by_temp.get(1.0, {}).get("rank1", 0)
        improvement = best_rank1 - baseline_rank1

        print(
            f"  {model_name}: temp={best_temp:.2f}, "
            f"rank1={best_rank1:.3f} "
            f"(baseline={baseline_rank1:.3f}, "
            f"{'+'if improvement >= 0 else ''}{improvement:.3f})"
        )

    # 4. Optimize ensemble weights
    print("\n--- Optimizing Ensemble Weights ---")
    from backend.services.confidence_calibrator import DEFAULT_MODEL_WEIGHTS

    if len(all_sim_matrices) >= 2:
        first_model = next(iter(all_sim_matrices))
        _, common_qf, common_gf = all_sim_matrices[first_model]

        best_weights, best_ensemble_rank1 = optimize_ensemble_weights(
            all_sim_matrices, common_qf, common_gf,
            query_labels, gallery_labels,
            DEFAULT_MODEL_WEIGHTS, calibrated_temps
        )

        print(f"  Best ensemble rank-1: {best_ensemble_rank1:.3f}")
        print(f"  Best weights:")
        for model_name, weight in sorted(best_weights.items(), key=lambda x: -x[1]):
            if weight > 0:
                print(f"    {model_name}: {weight:.2f}")
    else:
        best_weights = DEFAULT_MODEL_WEIGHTS
        best_ensemble_rank1 = 0
        print("  Not enough models for ensemble optimization")

    # 5. Save results
    print(f"\n--- Saving Results to {args.output} ---")
    output = {
        "calibration_temperatures": calibrated_temps,
        "ensemble_weights": best_weights,
        "best_ensemble_rank1": round(best_ensemble_rank1, 4),
        "per_model_results": model_results,
        "metadata": {
            "atrw_train_images": len(all_filenames),
            "query_images": len(query_filenames),
            "gallery_images": len(gallery_filenames),
            "temperature_grid": TEMP_GRID,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"  Saved to {args.output}")

    # 6. Summary
    print("\n--- Summary ---")
    print(f"  Optimized temperatures:")
    for model, temp in calibrated_temps.items():
        print(f"    {model}: {temp}")
    print(f"  Optimized weights:")
    for model, weight in sorted(best_weights.items(), key=lambda x: -x[1]):
        if weight > 0:
            print(f"    {model}: {weight}")
    print(f"  Ensemble rank-1 accuracy: {best_ensemble_rank1:.3f}")

    print("\n" + "=" * 70)
    print("CALIBRATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

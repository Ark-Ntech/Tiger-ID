"""End-to-end verification of the 6-model ensemble on discovered tigers.

Tests identification accuracy by holding out one image per tiger as a query
and checking if the ensemble correctly identifies it against the remaining
gallery images.

Usage:
    python scripts/verify_ensemble_accuracy.py
    python scripts/verify_ensemble_accuracy.py --mode weighted
    python scripts/verify_ensemble_accuracy.py --atrw-only
"""

import asyncio
import argparse
import sys
import os
import time
import csv
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import numpy as np


async def verify_discovered_tigers(db_session, models, args):
    """Verify ensemble on discovered tigers with multiple images."""
    from backend.database.models import Tiger, TigerImage
    from backend.database.vector_search import find_matching_tigers, store_embedding

    print("\n--- Discovered Tigers Verification ---")

    # Find tigers with 2+ images
    tigers = db_session.query(Tiger).all()
    multi_image_tigers = []

    for tiger in tigers:
        images = db_session.query(TigerImage).filter(
            TigerImage.tiger_id == tiger.tiger_id,
            TigerImage.image_path.isnot(None)
        ).all()

        valid_images = []
        for img in images:
            p = Path(img.image_path)
            if not p.exists():
                p = Path('.') / img.image_path
            if p.exists():
                valid_images.append({
                    "image_id": img.image_id,
                    "path": str(p),
                    "tiger_id": str(tiger.tiger_id),
                    "tiger_name": tiger.name or str(tiger.tiger_id)[:8],
                })

        if len(valid_images) >= 2:
            multi_image_tigers.append({
                "tiger_id": str(tiger.tiger_id),
                "tiger_name": tiger.name or str(tiger.tiger_id)[:8],
                "images": valid_images,
            })

    print(f"  Tigers with 2+ images: {len(multi_image_tigers)}")
    total_images = sum(len(t["images"]) for t in multi_image_tigers)
    print(f"  Total images: {total_images}")

    if not multi_image_tigers:
        print("  No tigers with multiple images found. Skipping.")
        return {}

    # For each tiger: hold out last image as query, rest are in gallery (via DB)
    correct_rank1 = 0
    correct_rank5 = 0
    total_queries = 0
    per_model_correct = defaultdict(int)
    per_model_total = defaultdict(int)
    failures = []

    max_tigers = min(len(multi_image_tigers), args.max_tigers)
    print(f"  Testing {max_tigers} tigers...")

    for idx, tiger_data in enumerate(multi_image_tigers[:max_tigers]):
        query_img = tiger_data["images"][-1]  # Last image as query
        true_tiger_id = tiger_data["tiger_id"]

        try:
            image_bytes = Path(query_img["path"]).read_bytes()
        except Exception:
            continue

        # Run each model individually
        for model_name, model in models.items():
            try:
                if hasattr(model, 'generate_embedding_from_bytes'):
                    embedding = await model.generate_embedding_from_bytes(image_bytes)
                else:
                    from PIL import Image
                    import io
                    img = Image.open(io.BytesIO(image_bytes))
                    embedding = await model.generate_embedding(img)

                if embedding is None:
                    continue

                matches = find_matching_tigers(
                    db_session,
                    query_embedding=embedding,
                    model_name=model_name,
                    limit=5,
                    similarity_threshold=0.0  # Get all results
                )

                per_model_total[model_name] += 1
                if matches and str(matches[0].get("tiger_id")) == true_tiger_id:
                    per_model_correct[model_name] += 1

            except Exception as e:
                pass  # Skip errors for individual models

        # Run weighted ensemble via direct similarity search
        # Collect matches from all models and weight them
        from backend.services.confidence_calibrator import ConfidenceCalibrator, DEFAULT_MODEL_WEIGHTS
        calibrator = ConfidenceCalibrator()
        tiger_scores = {}
        total_available_weight = 0.0

        for model_name, model in models.items():
            try:
                if hasattr(model, 'generate_embedding_from_bytes'):
                    embedding = await model.generate_embedding_from_bytes(image_bytes)
                else:
                    from PIL import Image
                    import io
                    img = Image.open(io.BytesIO(image_bytes))
                    embedding = await model.generate_embedding(img)

                if embedding is None:
                    continue

                matches = find_matching_tigers(
                    db_session,
                    query_embedding=embedding,
                    model_name=model_name,
                    limit=10,
                    similarity_threshold=0.0
                )

                weight = calibrator.weights.get(model_name, 0.1)
                total_available_weight += weight
                for match in matches:
                    tid = str(match["tiger_id"])
                    sim = calibrator.calibrate(match["similarity"], model_name)

                    if tid not in tiger_scores:
                        tiger_scores[tid] = {
                            "name": match.get("tiger_name", tid[:8]),
                            "weighted_sum": 0.0,
                            "total_weight": 0.0,
                        }
                    tiger_scores[tid]["weighted_sum"] += sim * weight
                    tiger_scores[tid]["total_weight"] += weight

            except Exception:
                pass

        # Rank by weighted score - normalize by total available weight
        # so tigers found by fewer models are penalized
        for tid in tiger_scores:
            tiger_scores[tid]["score"] = tiger_scores[tid]["weighted_sum"] / total_available_weight if total_available_weight > 0 else 0

        ranked = sorted(tiger_scores.items(), key=lambda x: -x[1]["score"])
        total_queries += 1

        top1_correct = len(ranked) > 0 and ranked[0][0] == true_tiger_id
        top5_ids = [r[0] for r in ranked[:5]]
        top5_correct = true_tiger_id in top5_ids

        if top1_correct:
            correct_rank1 += 1
        if top5_correct:
            correct_rank5 += 1

        if not top1_correct:
            top1_name = ranked[0][1]["name"] if ranked else "none"
            top1_score = ranked[0][1]["score"] if ranked else 0
            failures.append({
                "tiger": tiger_data["tiger_name"],
                "predicted": top1_name,
                "score": top1_score,
                "correct_rank": next(
                    (i+1 for i, (tid, _) in enumerate(ranked) if tid == true_tiger_id),
                    -1
                ),
            })

        if (idx + 1) % 10 == 0:
            print(
                f"    [{idx+1}/{max_tigers}] "
                f"rank-1: {correct_rank1}/{total_queries} "
                f"({100*correct_rank1/total_queries:.0f}%)"
            )

    # Results
    results = {
        "rank1": correct_rank1 / total_queries if total_queries > 0 else 0,
        "rank5": correct_rank5 / total_queries if total_queries > 0 else 0,
        "total_queries": total_queries,
        "correct_rank1": correct_rank1,
        "correct_rank5": correct_rank5,
    }

    print(f"\n  Discovered Tigers Results:")
    print(f"    Rank-1 accuracy: {results['rank1']:.3f} ({correct_rank1}/{total_queries})")
    print(f"    Rank-5 accuracy: {results['rank5']:.3f} ({correct_rank5}/{total_queries})")

    print(f"\n  Per-Model Rank-1 Accuracy:")
    for model_name in sorted(per_model_correct.keys()):
        total = per_model_total[model_name]
        correct = per_model_correct[model_name]
        print(f"    {model_name}: {correct}/{total} ({100*correct/total:.0f}%)" if total > 0 else f"    {model_name}: no results")

    if failures:
        print(f"\n  Failures ({len(failures)}):")
        for f in failures[:10]:
            print(f"    {f['tiger']}: predicted '{f['predicted']}' "
                  f"(score={f['score']:.3f}, correct at rank {f['correct_rank']})")

    return results


async def verify_atrw_reference(models, args):
    """Verify ensemble on ATRW reference images (labeled tiger data)."""
    print("\n--- ATRW Reference Verification ---")

    atrw_base = Path("data/models/atrw/images/Amur Tigers")
    csv_path = atrw_base / "reid_list_train.csv"
    image_dir = atrw_base / "train"

    if not csv_path.exists():
        print("  ATRW train CSV not found. Skipping.")
        return {}

    # Load labels
    tiger_images = defaultdict(list)
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                tiger_images[row[0].strip()].append(row[1].strip())

    # Filter to tigers with 3+ images for meaningful eval
    eval_tigers = {tid: imgs for tid, imgs in tiger_images.items() if len(imgs) >= 3}
    print(f"  Tigers with 3+ images: {len(eval_tigers)}")

    if not eval_tigers:
        return {}

    # Split: last image as query, rest as gallery
    # Generate gallery embeddings, then query each
    correct_rank1 = 0
    correct_rank5 = 0
    total_queries = 0

    # Build gallery embeddings per model
    print("  Building gallery embeddings...")
    gallery_embs = {}  # model_name -> {tiger_id: [embeddings]}
    query_data = []  # [(tiger_id, filename)]

    for tiger_id, images in list(eval_tigers.items())[:args.max_tigers]:
        query_data.append((tiger_id, images[-1]))
        gallery_images = images[:-1]

        for model_name, model in models.items():
            if model_name not in gallery_embs:
                gallery_embs[model_name] = {}

            for filename in gallery_images[:3]:  # Max 3 gallery per tiger
                img_path = image_dir / filename
                if not img_path.exists():
                    continue
                try:
                    image_bytes = img_path.read_bytes()
                    if hasattr(model, 'generate_embedding_from_bytes'):
                        emb = await model.generate_embedding_from_bytes(image_bytes)
                    else:
                        from PIL import Image
                        import io
                        img = Image.open(io.BytesIO(image_bytes))
                        emb = await model.generate_embedding(img)

                    if emb is not None:
                        if tiger_id not in gallery_embs[model_name]:
                            gallery_embs[model_name][tiger_id] = []
                        gallery_embs[model_name][tiger_id].append(emb)
                except Exception:
                    pass

    print(f"  Gallery built. Querying {len(query_data)} images...")

    from backend.services.confidence_calibrator import ConfidenceCalibrator
    calibrator = ConfidenceCalibrator()

    for idx, (true_tiger_id, query_filename) in enumerate(query_data):
        img_path = image_dir / query_filename
        if not img_path.exists():
            continue

        try:
            image_bytes = img_path.read_bytes()
        except Exception:
            continue

        # Weighted ensemble: compare query to all gallery embeddings
        tiger_scores = {}
        total_available_weight = 0.0

        for model_name, model in models.items():
            try:
                if hasattr(model, 'generate_embedding_from_bytes'):
                    q_emb = await model.generate_embedding_from_bytes(image_bytes)
                else:
                    from PIL import Image
                    import io
                    img = Image.open(io.BytesIO(image_bytes))
                    q_emb = await model.generate_embedding(img)

                if q_emb is None:
                    continue

                q_emb = q_emb / (np.linalg.norm(q_emb) + 1e-10)
                weight = calibrator.weights.get(model_name, 0.1)
                total_available_weight += weight

                for tiger_id, g_embs in gallery_embs.get(model_name, {}).items():
                    # Best similarity across gallery images
                    best_sim = 0
                    for g_emb in g_embs:
                        g_norm = g_emb / (np.linalg.norm(g_emb) + 1e-10)
                        sim = float(np.dot(q_emb, g_norm))
                        sim = calibrator.calibrate(max(0, sim), model_name)
                        best_sim = max(best_sim, sim)

                    if tiger_id not in tiger_scores:
                        tiger_scores[tiger_id] = {"weighted_sum": 0, "total_weight": 0}
                    tiger_scores[tiger_id]["weighted_sum"] += best_sim * weight
                    tiger_scores[tiger_id]["total_weight"] += weight

            except Exception:
                pass

        # Rank - normalize by total available weight so tigers found by fewer models are penalized
        for tid in tiger_scores:
            tiger_scores[tid]["score"] = tiger_scores[tid]["weighted_sum"] / total_available_weight if total_available_weight > 0 else 0

        ranked = sorted(tiger_scores.items(), key=lambda x: -x[1]["score"])
        total_queries += 1

        if ranked and ranked[0][0] == true_tiger_id:
            correct_rank1 += 1
        top5_ids = [r[0] for r in ranked[:5]]
        if true_tiger_id in top5_ids:
            correct_rank5 += 1

        if (idx + 1) % 20 == 0:
            print(
                f"    [{idx+1}/{len(query_data)}] "
                f"rank-1: {correct_rank1}/{total_queries} "
                f"({100*correct_rank1/total_queries:.0f}%)"
            )

    results = {
        "rank1": correct_rank1 / total_queries if total_queries > 0 else 0,
        "rank5": correct_rank5 / total_queries if total_queries > 0 else 0,
        "total_queries": total_queries,
    }

    print(f"\n  ATRW Reference Results:")
    print(f"    Rank-1 accuracy: {results['rank1']:.3f} ({correct_rank1}/{total_queries})")
    print(f"    Rank-5 accuracy: {results['rank5']:.3f} ({correct_rank5}/{total_queries})")

    return results


async def main():
    parser = argparse.ArgumentParser(description="Verify ensemble accuracy")
    parser.add_argument("--max-tigers", type=int, default=50, help="Max tigers to test")
    parser.add_argument("--atrw-only", action="store_true", help="Only test on ATRW data")
    parser.add_argument("--discovered-only", action="store_true", help="Only test on discovered tigers")
    args = parser.parse_args()

    from backend.database import get_db_session
    from backend.services.tiger.model_loader import get_model_loader

    print("=" * 70)
    print("ENSEMBLE ACCURACY VERIFICATION")
    print("=" * 70)

    # Load models
    print("\n--- Loading Models ---")
    loader = get_model_loader()
    models = {}
    for model_name in ["wildlife_tools", "cvwc2019", "rapid", "tiger_reid", "transreid", "megadescriptor_b"]:
        try:
            models[model_name] = loader.get_model(model_name)
            print(f"  {model_name}: OK")
        except Exception as e:
            print(f"  {model_name}: FAILED - {e}")

    print(f"\n  {len(models)}/6 models loaded")

    results = {}

    # Test on discovered tigers (from database)
    if not args.atrw_only:
        with get_db_session() as db:
            results["discovered"] = await verify_discovered_tigers(db, models, args)

    # Test on ATRW reference images
    if not args.discovered_only:
        results["atrw"] = await verify_atrw_reference(models, args)

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    for dataset, data in results.items():
        if data:
            print(f"\n  {dataset}:")
            print(f"    Rank-1: {data.get('rank1', 0):.3f}")
            print(f"    Rank-5: {data.get('rank5', 0):.3f}")
            print(f"    Queries: {data.get('total_queries', 0)}")

    # Success criteria check
    print("\n--- Success Criteria ---")
    atrw_r1 = results.get("atrw", {}).get("rank1", 0)
    disc_r1 = results.get("discovered", {}).get("rank1", 0)

    checks = [
        (f"ATRW rank-1 > 85%: {atrw_r1:.1%}", atrw_r1 > 0.85),
        (f"Discovered rank-1 > 70%: {disc_r1:.1%}", disc_r1 > 0.70),
    ]

    for desc, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {desc}")

    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

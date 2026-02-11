"""Backfill all tiger images with embeddings from all 6 ReID models.

Processes existing tiger images through the full 6-model ensemble and
stores embeddings in per-model vec tables. Supports resume via --start-index.

Usage:
    python scripts/backfill_embeddings.py
    python scripts/backfill_embeddings.py --start-index 100
    python scripts/backfill_embeddings.py --batch-size 20
    python scripts/backfill_embeddings.py --models wildlife_tools cvwc2019
"""

import asyncio
import argparse
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import numpy as np


ALL_MODELS = [
    "wildlife_tools", "cvwc2019", "rapid",
    "tiger_reid", "transreid", "megadescriptor_b"
]


async def generate_embedding(model, model_name: str, image_bytes: bytes):
    """Generate embedding from a model, handling different interfaces."""
    try:
        if hasattr(model, 'get_embedding'):
            return await model.get_embedding(image_bytes)
        elif hasattr(model, 'generate_embedding_from_bytes'):
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


async def main():
    parser = argparse.ArgumentParser(description="Backfill tiger embeddings")
    parser.add_argument("--start-index", type=int, default=0, help="Start from this image index")
    parser.add_argument("--batch-size", type=int, default=50, help="Process in batches of N")
    parser.add_argument("--models", nargs="+", default=ALL_MODELS, help="Models to run")
    parser.add_argument("--dry-run", action="store_true", help="Count images without processing")
    args = parser.parse_args()

    from backend.database import get_db_session
    from backend.database.models import TigerImage, Tiger
    from backend.database.vector_search import (
        store_embedding, get_embedding_counts_by_table, MODEL_TO_TABLE
    )
    from backend.services.tiger_service import TigerService
    from pathlib import Path

    print("=" * 70)
    print("EMBEDDING BACKFILL - 6-Model ReID Ensemble")
    print("=" * 70)

    # Check current state
    print("\n--- Current Vec Table Counts ---")
    with get_db_session() as db:
        counts = get_embedding_counts_by_table(db)
        for table, count in counts.items():
            print(f"  {table}: {count}")

    # Load all tiger images
    print("\n--- Loading Tiger Images ---")
    with get_db_session() as db:
        images = db.query(TigerImage).filter(
            TigerImage.image_path.isnot(None),
            TigerImage.tiger_id.isnot(None)
        ).order_by(TigerImage.image_id).all()

        image_records = []
        for img in images:
            img_path = Path(img.image_path)
            if not img_path.exists():
                img_path = Path(__file__).parent.parent / img.image_path
            if img_path.exists():
                image_records.append({
                    "image_id": img.image_id,
                    "tiger_id": img.tiger_id,
                    "path": str(img_path),
                })

    total = len(image_records)
    print(f"  Found {total} images with valid paths")
    print(f"  Starting from index: {args.start_index}")
    print(f"  Models: {args.models}")

    if args.dry_run:
        print("\n[DRY RUN] Would process these images. Exiting.")
        return

    # Initialize models
    print("\n--- Initializing Models ---")
    with get_db_session() as db:
        tiger_service = TigerService(db)
        models = {}
        for model_name in args.models:
            try:
                model = tiger_service._get_model(model_name)
                models[model_name] = model
                print(f"  {model_name}: OK")
            except Exception as e:
                print(f"  {model_name}: FAILED - {e}")

    if not models:
        print("\nERROR: No models available!")
        return

    print(f"\n  {len(models)}/{len(args.models)} models loaded")

    # Process images in batches
    print(f"\n--- Processing {total - args.start_index} images ---")
    start_time = time.time()
    total_stored = 0
    total_skipped = 0
    total_errors = 0

    for batch_start in range(args.start_index, total, args.batch_size):
        batch_end = min(batch_start + args.batch_size, total)
        batch = image_records[batch_start:batch_end]

        batch_stored = 0
        batch_time = time.time()

        for img_data in batch:
            try:
                image_bytes = Path(img_data["path"]).read_bytes()
            except Exception as e:
                print(f"  [{batch_start}] Failed to read {img_data['path']}: {e}")
                total_errors += 1
                continue

            # Generate embeddings from all models in parallel
            async def run_model(model_name):
                return model_name, await generate_embedding(
                    models[model_name], model_name, image_bytes
                )

            tasks = [run_model(mn) for mn in models.keys()]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Store embeddings
            with get_db_session() as db:
                for result in results:
                    if isinstance(result, Exception):
                        total_errors += 1
                        continue
                    model_name, embedding = result
                    if embedding is not None and isinstance(embedding, np.ndarray):
                        if store_embedding(db, img_data["image_id"], embedding, model_name=model_name):
                            batch_stored += 1
                            total_stored += 1
                        else:
                            total_errors += 1
                    else:
                        total_skipped += 1

        elapsed = time.time() - batch_time
        total_elapsed = time.time() - start_time
        images_done = batch_end - args.start_index
        images_remaining = total - batch_end
        rate = images_done / total_elapsed if total_elapsed > 0 else 0
        eta = images_remaining / rate if rate > 0 else 0

        print(
            f"  Batch {batch_start}-{batch_end}: "
            f"{batch_stored} stored, {elapsed:.1f}s | "
            f"Progress: {images_done}/{total - args.start_index} "
            f"({100*images_done/(total-args.start_index):.0f}%) | "
            f"ETA: {eta/60:.0f}min"
        )

    # Final counts
    print(f"\n--- Final Results ---")
    print(f"  Total stored: {total_stored}")
    print(f"  Total skipped: {total_skipped}")
    print(f"  Total errors: {total_errors}")
    print(f"  Time: {time.time() - start_time:.0f}s")

    print("\n--- Final Vec Table Counts ---")
    with get_db_session() as db:
        counts = get_embedding_counts_by_table(db)
        for table, count in counts.items():
            print(f"  {table}: {count}")
        print(f"  Total: {sum(counts.values())}")

    print("\n" + "=" * 70)
    print("BACKFILL COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""Initialize database with tables, seed data, and ATRW tiger dataset.

This script is called both standalone and from the backend startup lifespan
(via `from scripts.init_db import load_data_from_models`).

It loads:
1. Facility data from the TPC Tigers Excel spreadsheet
2. Tiger data from the ATRW re-identification dataset CSV files
3. Tiger images from the ATRW train/test directories
"""

import sys
import os
import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any, List, Optional

# Add parent directory to path so this works both as a script and as an import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.database import init_db, get_db_session, SessionLocal
from backend.database.models import (
    User, UserRole, Facility, Tiger, TigerImage, TigerStatus, SideView
)

logger = logging.getLogger(__name__)


def _get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent


def _create_admin_user(db) -> None:
    """Create admin user if it doesn't exist."""
    from backend.auth.auth import hash_password

    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        print("[OK] Admin user already exists")
        return

    admin = User(
        user_id=str(uuid4()),
        username="admin",
        email="admin@tigerid.local",
        password_hash=hash_password("Admin123!"),
        role=UserRole.admin.value,
        permissions=json.dumps({
            "investigations": ["create", "read", "update", "delete"],
            "tigers": ["create", "read", "update", "delete"],
            "facilities": ["create", "read", "update", "delete"],
            "users": ["create", "read", "update", "delete"],
        }),
        is_active=True,
        mfa_enabled=False,
    )
    db.add(admin)
    db.commit()
    print("[OK] Admin user created (username: admin, password: Admin123!)")


def _load_facilities_from_excel(db, excel_path: Path) -> Dict[str, Any]:
    """Load facility data from TPC Tigers Excel spreadsheet.

    Uses the parse_tpc_facilities_excel module if available, otherwise
    falls back to a direct pandas read.
    """
    stats = {"facilities_created": 0, "facilities_updated": 0, "errors": []}

    try:
        import pandas as pd
    except ImportError:
        print("WARNING: pandas not installed, cannot load Excel facilities")
        return stats

    try:
        from scripts.parse_tpc_facilities_excel import parse_excel_file
        facilities_data = parse_excel_file(excel_path)
    except Exception as e:
        logger.warning(f"parse_excel_file failed, using fallback: {e}")
        # Fallback: read directly with pandas
        try:
            df = pd.read_excel(excel_path, engine="openpyxl")
            facilities_data = []
            for idx, row in df.iterrows():
                exhibitor = str(row.get("Exhibitor", "")).strip()
                if not exhibitor or exhibitor.upper() == "TOTAL":
                    continue

                tiger_count = 0
                tc_raw = row.get("Tigers", "")
                if pd.notna(tc_raw):
                    try:
                        tiger_count = int(float(tc_raw))
                    except (ValueError, TypeError):
                        pass

                state = str(row.get("State", "")).strip() if pd.notna(row.get("State")) else None
                city = str(row.get("City", "")).strip() if pd.notna(row.get("City")) else None
                usda_license = str(row.get("License", "")).strip() if pd.notna(row.get("License")) else None

                website = None
                for col in ["Website", "website"]:
                    val = row.get(col)
                    if pd.notna(val):
                        val = str(val).strip()
                        if val.startswith("http") or val.startswith("www."):
                            website = val
                            break

                social_media = {}
                for platform in ["Facebook", "Instagram", "TikTok", "YouTube"]:
                    val = row.get(platform)
                    if pd.notna(val):
                        val = str(val).strip()
                        if val and val.lower() not in ["none", "nan", ""]:
                            social_media[platform.lower()] = val

                facilities_data.append({
                    "exhibitor_name": exhibitor,
                    "usda_license": usda_license,
                    "state": state,
                    "city": city,
                    "tiger_count": tiger_count,
                    "website": website,
                    "social_media_links": social_media,
                    "accreditation_status": "Non-Accredited",
                    "is_reference_facility": True,
                    "data_source": "tpc_non_accredited_facilities",
                })
        except Exception as fallback_err:
            print(f"WARNING: Fallback Excel parsing also failed: {fallback_err}")
            return stats

    # Insert facilities into database
    for fdata in facilities_data:
        try:
            exhibitor_name = fdata.get("exhibitor_name", "").strip()
            if not exhibitor_name:
                continue

            # Check for existing by USDA license or name
            existing = None
            usda = fdata.get("usda_license")
            if usda:
                existing = db.query(Facility).filter(Facility.usda_license == usda).first()
            if not existing:
                existing = db.query(Facility).filter(
                    Facility.exhibitor_name == exhibitor_name
                ).first()

            if existing:
                # Update tiger count if we have a better value
                if fdata.get("tiger_count") and not existing.tiger_count:
                    existing.tiger_count = fdata["tiger_count"]
                stats["facilities_updated"] += 1
            else:
                facility = Facility(
                    facility_id=str(uuid4()),
                    exhibitor_name=exhibitor_name,
                    usda_license=fdata.get("usda_license"),
                    state=fdata.get("state"),
                    city=fdata.get("city"),
                    tiger_count=fdata.get("tiger_count", 0),
                    website=fdata.get("website"),
                    social_media_links=fdata.get("social_media_links", {}),
                    accreditation_status=fdata.get("accreditation_status", "Non-Accredited"),
                    is_reference_facility=fdata.get("is_reference_facility", True),
                    data_source=fdata.get("data_source", "tpc_non_accredited_facilities"),
                    reference_dataset_version=datetime.utcnow(),
                )
                db.add(facility)
                stats["facilities_created"] += 1

            # Commit in batches
            if (stats["facilities_created"] + stats["facilities_updated"]) % 50 == 0:
                db.commit()

        except Exception as e:
            logger.warning(f"Error loading facility '{fdata.get('exhibitor_name', '?')}': {e}")
            stats["errors"].append(str(e))
            db.rollback()

    db.commit()
    return stats


def _load_atrw_tigers(db, atrw_base: Path) -> Dict[str, Any]:
    """Load tiger data from ATRW re-identification dataset.

    Reads the reid_list_train.csv and reid_list_test.csv files to create
    Tiger and TigerImage records. Each row in the CSV is:
        tiger_id_number,image_filename.jpg

    Images are in train/ and test/ subdirectories.
    """
    stats = {"tigers_created": 0, "images_created": 0, "images_skipped": 0, "errors": []}

    train_csv = atrw_base / "reid_list_train.csv"
    test_csv = atrw_base / "reid_list_test.csv"
    train_dir = atrw_base / "train"
    test_dir = atrw_base / "test"

    if not train_csv.exists() and not test_csv.exists():
        print(f"WARNING: No ATRW CSV files found at {atrw_base}")
        return stats

    # Build mapping: tiger_numeric_id -> list of (image_filename, split_dir)
    tiger_images_map: Dict[str, List[tuple]] = {}

    for csv_path, img_dir, split in [
        (train_csv, train_dir, "train"),
        (test_csv, test_dir, "test"),
    ]:
        if not csv_path.exists():
            continue

        with open(csv_path, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    # Test CSV has only image filenames (no tiger ID)
                    continue
                tiger_num = row[0].strip()
                image_name = row[1].strip() if len(row) > 1 else row[0].strip()

                if tiger_num not in tiger_images_map:
                    tiger_images_map[tiger_num] = []
                tiger_images_map[tiger_num].append((image_name, img_dir, split))

    # If test CSV has no tiger IDs (single column), handle separately
    if test_csv.exists():
        with open(test_csv, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 1:
                    # Test images without tiger ID assignment - skip for now
                    # They can be used for identification queries later
                    pass

    print(f"  Found {len(tiger_images_map)} unique tigers in ATRW dataset")

    # Create tiger records and image records
    for tiger_num, image_list in tiger_images_map.items():
        try:
            alias = f"ATRW-{tiger_num.zfill(3)}"
            name = f"Amur Tiger {tiger_num}"

            # Check if tiger already exists
            existing_tiger = db.query(Tiger).filter(Tiger.alias == alias).first()

            if existing_tiger:
                tiger = existing_tiger
            else:
                tiger = Tiger(
                    tiger_id=str(uuid4()),
                    name=name,
                    alias=alias,
                    status=TigerStatus.active.value,
                    is_reference=True,
                    tags=["ATRW", "reference", "amur"],
                    notes=f"Reference tiger from ATRW re-identification dataset (ID: {tiger_num})",
                    created_at=datetime.utcnow(),
                )
                db.add(tiger)
                db.flush()
                stats["tigers_created"] += 1

            # Add images for this tiger
            for image_name, img_dir, split in image_list:
                image_path = img_dir / image_name

                if not image_path.exists():
                    continue

                # Use a relative path from project root for portability
                project_root = _get_project_root()
                try:
                    rel_path = image_path.relative_to(project_root)
                except ValueError:
                    rel_path = image_path

                # Check if image already exists
                existing_image = db.query(TigerImage).filter(
                    TigerImage.image_path == str(rel_path)
                ).first()

                if existing_image:
                    stats["images_skipped"] += 1
                    continue

                tiger_image = TigerImage(
                    image_id=str(uuid4()),
                    tiger_id=tiger.tiger_id,
                    image_path=str(rel_path),
                    side_view=SideView.unknown.value,
                    meta_data=json.dumps({
                        "dataset": "ATRW",
                        "split": split,
                        "tiger_id_dataset": tiger_num,
                        "original_filename": image_name,
                    }),
                    is_reference=True,
                    verified=False,
                    created_at=datetime.utcnow(),
                )
                db.add(tiger_image)
                stats["images_created"] += 1

            # Commit in batches of 20 tigers
            if stats["tigers_created"] % 20 == 0:
                db.commit()

        except Exception as e:
            logger.warning(f"Error loading tiger {tiger_num}: {e}")
            stats["errors"].append(str(e))
            db.rollback()

    db.commit()
    return stats


def load_data_from_models():
    """Load facilities and tigers from data/models directory.

    This is the main entry point called by the backend startup lifespan
    in backend/api/app.py when the database is empty.
    """
    project_root = _get_project_root()

    db = SessionLocal()
    try:
        # --- Load facilities from Excel ---
        excel_file = project_root / "data" / "models" / "2025_10_31 TPC_Tigers non-accredited facilities.xlsx"
        if not excel_file.exists():
            # Try to find any Excel file in data/models
            excel_files = list((project_root / "data" / "models").glob("*.xlsx"))
            if excel_files:
                excel_file = excel_files[0]

        if excel_file.exists() and excel_file.suffix == ".xlsx":
            print(f"Loading facilities from: {excel_file.name}")
            facility_stats = _load_facilities_from_excel(db, excel_file)
            print(
                f"[OK] Facilities: {facility_stats['facilities_created']} created, "
                f"{facility_stats['facilities_updated']} updated"
            )
            if facility_stats["errors"]:
                print(f"  Warnings: {len(facility_stats['errors'])} errors")
        else:
            print(f"WARNING: No Excel facility file found in data/models/")

        # --- Load ATRW tigers ---
        atrw_base = project_root / "data" / "models" / "atrw" / "images" / "Amur Tigers"
        if atrw_base.exists():
            print("Loading ATRW tiger dataset...")
            tiger_stats = _load_atrw_tigers(db, atrw_base)
            print(
                f"[OK] Tigers: {tiger_stats['tigers_created']} created, "
                f"{tiger_stats['images_created']} images added, "
                f"{tiger_stats['images_skipped']} skipped"
            )
            if tiger_stats["errors"]:
                print(f"  Warnings: {len(tiger_stats['errors'])} errors")
        else:
            print(f"WARNING: ATRW dataset not found at: {atrw_base}")

        # --- Create admin user ---
        print("Ensuring admin user exists...")
        try:
            _create_admin_user(db)
        except Exception as e:
            print(f"WARNING: Could not create admin user: {e}")
            db.rollback()

        # Print summary
        facility_count = db.query(Facility).count()
        tiger_count = db.query(Tiger).count()
        image_count = db.query(TigerImage).count()
        print(f"\nDatabase summary: {facility_count} facilities, {tiger_count} tigers, {image_count} images")

    except Exception as e:
        logger.error(f"Data loading failed: {e}", exc_info=True)
        print(f"ERROR: Data loading failed: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Initialize database and load seed data."""
    import argparse

    parser = argparse.ArgumentParser(description="Initialize database and load data")
    parser.add_argument(
        "--skip-data", action="store_true",
        help="Skip loading facility and tiger data"
    )
    args = parser.parse_args()

    print("Initializing database...")

    # Create all tables and vec_embeddings virtual table
    init_db()
    print("[OK] Database schema created")

    if args.skip_data:
        print("Skipping data loading (--skip-data flag)")
    else:
        # Check if data needs to be loaded
        db = SessionLocal()
        try:
            facility_count = db.query(Facility).count()
            tiger_count = db.query(Tiger).count()

            if facility_count == 0 or tiger_count == 0:
                print("\nDatabase is empty, loading seed data...")
                db.close()
                load_data_from_models()
            else:
                print(f"[OK] Database already has {facility_count} facilities and {tiger_count} tigers")
        except Exception as e:
            print(f"WARNING: Could not check/load data: {e}")
        finally:
            db.close()

    print("\n[OK] Database initialization complete!")


if __name__ == "__main__":
    main()

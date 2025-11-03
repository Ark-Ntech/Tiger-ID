# Dataset Ingestion Guide

This document describes how datasets are automatically ingested into the Tiger ID database.

## Overview

The Tiger ID system automatically loads datasets from `data/models/` and `data/datasets/` directories into the database, creating Tiger and TigerImage records for use in identification and matching.

## Supported Datasets

### 1. **ATRW (Amur Tiger Re-identification in the Wild)**
- **Location**: `data/models/atrw/`
- **Structure**: `images/{tiger_id}/` containing images for each tiger
- **Format**: Images organized by tiger ID directories
- **Tigers**: 92 individual tigers

### 2. **MetaWild**
- **Location**: `data/datasets/metawild/`
- **Structure**: Various - adapts to directory structure
- **Format**: Images with identity information in path or metadata

### 3. **Wildlife Datasets Library**
- **Location**: `data/datasets/wildlife-datasets/`
- **Structure**: Uses wildlife-datasets Python library format
- **Format**: DataFrames with identity and path columns
- **Requires**: `wildlife-datasets` Python package

### 4. **Individual Animal Re-ID Datasets**
- **Location**: `data/datasets/individual-animal-reid/`
- **Structure**: CSV files with metadata
- **Format**: CSV files with columns: identity, image_path (or similar)

## Automatic Ingestion

### On Startup (Docker)

Set environment variable to enable automatic ingestion on container startup:

```bash
INGEST_DATASETS_ON_STARTUP=true
```

This runs in the background and doesn't block application startup.

### Scheduled (Celery Beat)

Dataset ingestion runs automatically via Celery Beat:
- **Schedule**: Daily at 3 AM UTC
- **Behavior**: Only ingests new images (skips existing)
- **Task**: `ingest_datasets`

To disable scheduled ingestion, remove or comment out the task in `backend/jobs/data_sync_jobs.py`.

## Manual Ingestion

### Using the Script

```bash
# Ingest all datasets
python scripts/ingest_datasets.py --dataset all

# Ingest specific dataset
python scripts/ingest_datasets.py --dataset atrw

# Dry run (no database changes)
python scripts/ingest_datasets.py --dataset all --dry-run

# Force re-ingestion (overwrite existing)
python scripts/ingest_datasets.py --dataset all --force
```

### During Database Initialization

```bash
# Initialize database and ingest datasets
python scripts/init_db.py --ingest-datasets

# With dry run
python scripts/init_db.py --ingest-datasets --ingest-datasets-dry-run
```

### Using Celery Task

```python
from backend.jobs.data_sync_jobs import ingest_datasets_task

# Queue ingestion task
result = ingest_datasets_task.delay(
    dataset='all',
    skip_existing=True
)
```

## What Gets Created

### Tiger Records
- **Name**: Generated from dataset source (e.g., "ATRW Tiger 001")
- **Alias**: Dataset-specific tiger ID
- **Status**: Set to "active"
- **Tags**: Includes dataset source name
- **Notes**: Import metadata

### TigerImage Records
- **tiger_id**: Links to Tiger record
- **image_path**: Absolute path to image file
- **metadata**: Includes dataset source, tiger ID, source path
- **verified**: Set to `false` (requires manual verification)
- **embedding**: Not generated during ingestion (see below)

## Image Embeddings

**Important**: Dataset ingestion creates TigerImage records but does NOT generate embeddings automatically. Embeddings are required for similarity search.

To generate embeddings for ingested images:

```bash
# Process all images without embeddings
python scripts/process_images.py --generate-embeddings

# Or use Re-ID service directly
# (embeddings are generated on-demand during identification)
```

## Idempotency

The ingestion process is idempotent:
- Skips images that already exist (by `image_path`)
- Updates Tiger records if they exist (by alias or name)
- Can be run multiple times safely

## Configuration

### Environment Variables

```bash
# Enable ingestion on startup
INGEST_DATASETS_ON_STARTUP=false

# Dataset paths (from settings.yaml)
ATRW_DATASET_PATH=./data/models/atrw/
METAWILD_DATASET_PATH=./data/datasets/metawild/
WILDLIFE_DATASETS_PATH=./data/datasets/wildlife-datasets/
INDIVIDUAL_ANIMAL_REID_PATH=./data/datasets/individual-animal-reid/
```

### Dataset Paths

Dataset paths are configured in:
- `config/settings.yaml`
- Environment variables (takes precedence)
- `backend/config/settings.py` (defaults)

## Troubleshooting

### Dataset Not Found

```
Warning: Dataset path does not exist: ./data/models/atrw
```

**Solution**: Ensure dataset is downloaded and placed in correct directory.

### No Images Found

```
Warning: No images found in MetaWild dataset
```

**Solution**: Check dataset structure matches expected format. Review dataset-specific ingestion code.

### Import Errors

```
Error: wildlife-datasets library not available
```

**Solution**: Install required package:
```bash
pip install wildlife-datasets
```

### Database Connection Errors

Ensure database is initialized and accessible:
```bash
python scripts/init_db.py
```

## Statistics

After ingestion, check statistics:

```python
from backend.database import get_db_session
from backend.database.models import Tiger, TigerImage

with get_db_session() as session:
    tiger_count = session.query(Tiger).count()
    image_count = session.query(TigerImage).count()
    print(f"Tigers: {tiger_count}, Images: {image_count}")
```

## Best Practices

1. **Initial Setup**: Run ingestion after downloading datasets
2. **Production**: Use scheduled Celery task for regular updates
3. **Development**: Use `--dry-run` to test without changes
4. **Verification**: Always verify ingested images before use
5. **Embeddings**: Generate embeddings after ingestion for best performance

## Dataset Formats

### ATRW Format
```
atrw/
├── images/
│   ├── tiger_001/
│   │   ├── image1.jpg
│   │   └── image2.jpg
│   └── tiger_002/
│       └── image1.jpg
└── annotations/
```

### MetaWild Format
```
metawild/
├── identity_1/
│   └── image.jpg
└── identity_2/
    └── image.jpg
```

### CSV Format (Individual Animal Re-ID)
```csv
identity,image_path
tiger_001,images/tiger_001/img1.jpg
tiger_001,images/tiger_001/img2.jpg
tiger_002,images/tiger_002/img1.jpg
```

## See Also

- [Models Configuration](MODELS_CONFIGURATION.md)
- [API Documentation](API.md)
- [Deployment Guide](DEPLOYMENT.md)


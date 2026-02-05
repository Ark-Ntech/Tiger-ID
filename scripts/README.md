# Scripts

Utility scripts for Tiger ID setup, data management, and maintenance.

## Database Scripts

| Script | Purpose |
|--------|---------|
| `init_db.py` | Initialize database schema and indexes |
| `populate_production_db.py` | Load production tiger data |
| `create_admin_user.py` | Create admin user account |
| `check_data.py` | Verify database contents |
| `validate_production_data.py` | Validate data integrity |

## Model Scripts

| Script | Purpose |
|--------|---------|
| `download_models.py` | Download all ML model weights |
| `download_model_weights.py` | Download specific model weights |
| `upload_weights_to_modal.py` | Upload weights to Modal volumes |
| `init_models.py` | Initialize model configurations |

## Dataset Scripts

| Script | Purpose |
|--------|---------|
| `ingest_atrw.py` | Ingest ATRW tiger dataset |
| `ingest_datasets.py` | Batch dataset ingestion |
| `download_datasets.py` | Download public datasets |
| `prepare_test_datasets.py` | Prepare test data |

## Data Processing

| Script | Purpose |
|--------|---------|
| `process_images.py` | Image preprocessing |
| `generate_reference_embeddings.py` | Generate gallery embeddings |
| `geocode_facilities.py` | Batch geocode facility addresses |
| `parse_tpc_facilities_excel.py` | Parse USDA facility data |
| `assign_facility_associations.py` | Link tigers to facilities |

## Startup Scripts

| Script | Purpose |
|--------|---------|
| `start_tiger_id.ps1` | PowerShell startup script |
| `setup.sh` | Bash setup script |

## Usage Examples

### Initial Setup

```bash
# Initialize database
python scripts/init_db.py

# Create admin user
python scripts/create_admin_user.py

# Load tiger data
python scripts/populate_production_db.py
```

### Model Setup

```bash
# Download all models
python scripts/download_models.py --model all

# Generate embeddings for gallery
python scripts/generate_reference_embeddings.py
```

### Data Management

```bash
# Ingest ATRW dataset
python scripts/ingest_atrw.py --path data/models/atrw/

# Validate data
python scripts/validate_production_data.py
```

## Related Documentation

- `../docs/DATABASE_SETUP.md` - Database configuration
- `../docs/MODELS_CONFIGURATION.md` - Model setup
- `../docs/DEPLOYMENT.md` - Deployment guide

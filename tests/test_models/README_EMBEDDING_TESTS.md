# Model Embedding Dimension Tests

## Overview

This test suite ensures that model wrapper `embedding_dim` properties match the values defined in `model_registry.py`. This prevents runtime errors where embedding dimensions mismatch between model outputs and storage/comparison operations.

## Test File

**Location**: `tests/test_models/test_embedding_dimensions.py`

## What Gets Tested

### 1. Individual Model Verification (`TestEmbeddingDimensionsMatchRegistry`)

Each ReID model wrapper is tested to verify its `embedding_dim` property matches the registry:

| Model | Expected Dimension | Registry Key |
|-------|-------------------|--------------|
| WildlifeToolsReIDModel | 1536 | `wildlife_tools` |
| CVWC2019ReIDModel | 2048 | `cvwc2019_reid` |
| TigerReIDModel | 2048 | `tiger_reid` |
| TransReIDModel | 768 | `transreid` |
| MegaDescriptorBReIDModel | 1024 | `megadescriptor_b` |
| RAPIDReIDModel | 2048 | `rapid_reid` |

### 2. Registry Completeness (`TestRegistryCompleteness`)

- Verifies all expected ReID models are present in the registry
- Ensures all ReID models have non-None, positive integer embedding dimensions

### 3. Dimension Value Validation (`TestEmbeddingDimensionValues`)

Validates that each model has the correct dimension value based on its architecture:

- `wildlife_tools`: 1536 (MegaDescriptor-L-384 with Swin-Large)
- `cvwc2019_reid`: 2048 (global stream output)
- `tiger_reid`: 2048 (ResNet50 base)
- `transreid`: 768 (ViT-Base)
- `megadescriptor_b`: 1024 (Swin-Base)
- `rapid_reid`: 2048 (ResNet50-based)

### 4. Ensemble Consistency (`TestConsistencyAcrossEnsemble`)

- Verifies the ensemble uses models with diverse embedding dimensions (at least 3 unique dimensions)
- Validates registry config structure is consistent across all ReID models

## Running the Tests

```bash
# Run all embedding dimension tests
pytest tests/test_models/test_embedding_dimensions.py -v

# Run specific test class
pytest tests/test_models/test_embedding_dimensions.py::TestEmbeddingDimensionsMatchRegistry -v

# Run with coverage
pytest tests/test_models/test_embedding_dimensions.py --cov=backend.models --cov=backend.infrastructure.modal
```

## Test Results

All 16 tests pass:

- 6 individual model dimension verifications
- 2 registry completeness checks
- 6 dimension value validations
- 2 ensemble consistency tests

## Why These Tests Matter

### Prevents Runtime Errors

Without these tests, mismatches between model wrapper `embedding_dim` and registry values cause:
- Vector storage errors (wrong dimension in database)
- Similarity computation failures (incompatible embeddings)
- Ensemble voting failures (dimension mismatches across models)

### Recent Fixes

These tests caught and prevented regression of:
1. **WildlifeTools**: Was incorrectly set to 2048, should be 1536
2. **CVWC2019**: Was incorrectly set to 3072, should be 2048

### Continuous Integration

These tests should run on every PR to prevent dimension mismatches from being merged.

## Fixing a Test Failure

If a test fails:

1. **Determine the source of truth**:
   - Check model architecture documentation
   - Verify actual output from Modal inference
   - Confirm with model research papers

2. **Update both locations**:
   - Model wrapper property in `backend/models/`
   - Registry value in `backend/infrastructure/modal/model_registry.py`

3. **Update related tests**:
   - Fix mock embeddings in model-specific test files (e.g., `test_wildlife_tools.py`)
   - Ensure embedding shapes match in all test assertions

## Related Files

- `backend/infrastructure/modal/model_registry.py` - Source of truth for dimensions
- `backend/models/*.py` - Model wrappers with `embedding_dim` properties
- `tests/test_models/test_wildlife_tools.py` - Updated to use 1536-dim
- `tests/test_models/test_cvwc2019_reid.py` - Updated to use 2048-dim

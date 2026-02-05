# Services

Business logic layer for Tiger ID.

## Service Categories

### Tiger Identification

| Service | Purpose |
|---------|---------|
| `tiger_service.py` | Core tiger CRUD operations |
| `tiger/identification_service.py` | Tiger ReID orchestration |
| `tiger/ensemble_strategy.py` | Ensemble strategy implementations |
| `embedding_service.py` | Embedding generation |
| `model_comparison_service.py` | Model comparison and evaluation |
| `confidence_calibrator.py` | Temperature-based score calibration |
| `reranking_service.py` | K-reciprocal re-ranking |

### Investigation

| Service | Purpose |
|---------|---------|
| `investigation_service.py` | Investigation management |
| `investigation2_task_runner.py` | Workflow task execution |
| `evidence_compilation_service.py` | Evidence gathering |

### Discovery Pipeline

| Service | Purpose |
|---------|---------|
| `discovery_scheduler.py` | Crawl scheduling |
| `facility_crawler_service.py` | Web crawling with rate limiting |
| `image_pipeline_service.py` | Image deduplication (SHA256) |

### Web Intelligence

| Service | Purpose |
|---------|---------|
| `web_search_service.py` | Multi-provider web search |
| `image_search_service.py` | Reverse image search |
| `news_monitoring_service.py` | News article monitoring |
| `lead_generation_service.py` | Lead discovery |

### External Integration

| Service | Purpose |
|---------|---------|
| `modal_client.py` | Modal GPU client |
| `usda_service.py` | USDA license validation |
| `youtube_client.py` | YouTube data extraction |
| `meta_client.py` | Meta/Facebook data |

### Infrastructure

| Service | Purpose |
|---------|---------|
| `notification_service.py` | User notifications |
| `event_service.py` | Event broadcasting |
| `metrics_service.py` | System metrics |

## Ensemble Strategies

The tiger identification system uses a 6-model ensemble with configurable strategies:

| Strategy | Description |
|----------|-------------|
| `StaggeredEnsembleStrategy` | Sequential with early exit |
| `ParallelEnsembleStrategy` | All models, majority voting |
| `WeightedEnsembleStrategy` | Weighted scoring + re-ranking |
| `VerifiedEnsembleStrategy` | Geometric verification |

## Key Patterns

### Service Factory

```python
from backend.services.factory import get_service

tiger_service = get_service('tiger')
identification_service = get_service('identification')
```

### Async Operations

Most services use async methods:

```python
async def identify_tiger(image_path: str):
    service = IdentificationService()
    result = await service.identify(image_path)
    return result
```

## Related Documentation

- `../../docs/ENSEMBLE_STRATEGIES.md` - Ensemble details
- `../../docs/DISCOVERY_PIPELINE.md` - Discovery pipeline
- `../../docs/ARCHITECTURE.md` - System architecture

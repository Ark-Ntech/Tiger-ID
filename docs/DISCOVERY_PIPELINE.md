# Continuous Tiger Discovery Pipeline

This document describes the automated tiger discovery system that continuously monitors facility websites for new tiger images and integrates with the Investigation 2.0 workflow.

---

## Table of Contents

- [Overview](#overview)
- [Data Flow Diagram](#data-flow-diagram)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Rate Limiting](#rate-limiting)
- [Auto-Investigation Triggering](#auto-investigation-triggering)
- [Verification Queue Workflow](#verification-queue-workflow)
- [API Endpoints](#api-endpoints)
- [JS-Heavy Site Detection](#js-heavy-site-detection)
- [Image Deduplication](#image-deduplication)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Overview

The discovery pipeline provides two pathways for tiger identification:

1. **Auto-Discovery Pipeline**: Continuous crawler monitors TPC facility websites, discovers new tiger images, processes them through ML, and optionally triggers full investigations.

2. **User Upload Pipeline**: Users upload tiger images directly, which go through Investigation 2.0 workflow and into the verification queue.

Both pathways converge at the **Verification Queue** where human reviewers approve or reject identified tigers before they become confirmed records.

### Key Features

- **Continuous monitoring** of facility websites without manual intervention
- **Intelligent JS detection** for SPA/React sites requiring Playwright rendering
- **GPU compute savings** through SHA256 content-hash deduplication
- **Quality gates** prevent low-quality images from triggering investigations
- **Rate limiting** prevents investigation spam while catching important discoveries
- **Human-in-the-loop** verification for all identified tigers

---

## Data Flow Diagram

```
                           DISCOVERY PIPELINE
    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                 │
    │  ┌─────────────┐     ┌────────────────┐     ┌───────────────┐  │
    │  │  Facility   │────▶│  Image         │────▶│ Investigation │  │
    │  │  Crawler    │     │  Pipeline      │     │ Trigger       │  │
    │  │             │     │                │     │ Service       │  │
    │  │ - DuckDuckGo│     │ - Deduplicate  │     │               │  │
    │  │ - Playwright│     │ - Quality Check│     │ - Quality Gate│  │
    │  │ - HTTP      │     │ - MegaDetector │     │ - Rate Limit  │  │
    │  └─────────────┘     │ - 6-Model ReID │     │ - Per-Facility│  │
    │        │             │ - Match/Create │     └───────────────┘  │
    │        │             └────────────────┘            │           │
    │        │                    │                      │           │
    │        │           NEW TIGERS CREATED              │           │
    │        │                    │                      │           │
    │        │                    ▼                      ▼           │
    │        │            ┌─────────────────────────────────┐        │
    │        │            │    Investigation 2.0 Workflow   │        │
    │        │            │                                 │        │
    │        │            │  1. Upload & Parse (EXIF)       │        │
    │        │            │  2. Reverse Image Search        │        │
    │        │            │  3. Tiger Detection             │        │
    │        │            │  4. Stripe Analysis (6 models)  │        │
    │        │            │  5. Report Generation           │        │
    │        │            │  6. Complete                    │        │
    │        │            └─────────────────────────────────┘        │
    │        │                          │                            │
    └────────│──────────────────────────│────────────────────────────┘
             │                          │
             │                          │
             │    ┌─────────────────────┘
             │    │
             │    │   USER UPLOAD PIPELINE
             │    │   ┌──────────────────────────────────────────┐
             │    │   │                                          │
             │    │   │  ┌──────────────┐    ┌────────────────┐  │
             │    │   │  │ User Upload  │───▶│ Investigation  │  │
             │    │   │  │              │    │ 2.0 Workflow   │  │
             │    │   │  │ - Web UI     │    │                │  │
             │    │   │  │ - API        │    │ (Same as above)│  │
             │    │   │  └──────────────┘    └────────────────┘  │
             │    │   │                              │           │
             │    │   └──────────────────────────────│───────────┘
             │    │                                  │
             ▼    ▼                                  ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    VERIFICATION QUEUE                        │
    │                                                              │
    │  ┌─────────────────────────────────────────────────────────┐│
    │  │ Pending Review                                          ││
    │  │                                                         ││
    │  │  Priority: HIGH (user uploads, high-confidence auto)    ││
    │  │  Priority: MEDIUM (standard auto-discoveries)           ││
    │  │  Priority: LOW (low-confidence discoveries)             ││
    │  │                                                         ││
    │  │  Source: user_upload | auto_discovery                   ││
    │  │  Status: pending | in_review | approved | rejected      ││
    │  └─────────────────────────────────────────────────────────┘│
    │                          │                                   │
    │              ┌───────────┴───────────┐                      │
    │              ▼                       ▼                      │
    │       ┌───────────┐           ┌───────────┐                 │
    │       │  APPROVE  │           │  REJECT   │                 │
    │       │           │           │           │                 │
    │       │ → Tiger   │           │ → Tiger   │                 │
    │       │   Verified│           │   Deleted │                 │
    │       └───────────┘           └───────────┘                 │
    └─────────────────────────────────────────────────────────────┘
```

---

## Architecture

### Core Services

| Service | File | Purpose |
|---------|------|---------|
| FacilityCrawlerService | `backend/services/facility_crawler_service.py` | Web crawling with rate limiting |
| ImagePipelineService | `backend/services/image_pipeline_service.py` | Deduplication and ML processing |
| InvestigationTriggerService | `backend/services/investigation_trigger_service.py` | Auto-investigation quality gates and rate limiting |
| DiscoveryScheduler | `backend/services/discovery_scheduler.py` | Scheduling and orchestration |
| VerificationService | `backend/services/verification_service.py` | Verification queue management |
| Investigation2Workflow | `backend/agents/investigation2_workflow.py` | LangGraph investigation workflow |

### Service Interaction Flow

```
FacilityCrawlerService
         │
         │ DiscoveredImage[]
         ▼
ImagePipelineService
         │
         │ ProcessedTiger (is_new, detection_confidence, quality_score)
         │
         ├──────────────────────────────────────────────┐
         │ (if new tiger)                               │
         ▼                                              │
InvestigationTriggerService                             │
         │                                              │
         │ should_trigger_investigation()               │
         │   ├── Quality gate (min_quality_score)       │
         │   ├── Confidence gate (min_detection_conf)   │
         │   ├── Global rate limit (max_per_hour)       │
         │   ├── Per-facility rate limit (1hr interval) │
         │   └── Duplicate check (content_hash)         │
         │                                              │
         ▼ (if passes all gates)                        │
Investigation2Workflow                                  │
         │                                              │
         │ (async, background)                          │
         │                                              │
         ▼                                              │
VerificationQueue ◀─────────────────────────────────────┘
```

---

## Configuration

All auto-discovery settings are in `config/settings.yaml`.

### Auto-Investigation Section

```yaml
auto_investigation:
  # Master switch for auto-triggered investigations
  enabled: ${AUTO_INVESTIGATION_ENABLED:-true}

  # Quality gates - higher thresholds than pipeline to reduce noise
  min_quality_score: ${AUTO_INVESTIGATION_MIN_QUALITY:-60.0}  # 0-100 scale
  min_detection_confidence: ${AUTO_INVESTIGATION_MIN_CONFIDENCE:-0.85}  # 0-1 scale

  # Rate limiting to prevent investigation spam
  max_per_hour: ${AUTO_INVESTIGATION_MAX_PER_HOUR:-5}
  min_facility_interval_seconds: ${AUTO_INVESTIGATION_FACILITY_INTERVAL:-3600}  # 1 hour

  # Async behavior
  always_async: true  # Auto-investigations always run in background
  use_duckduckgo_deep_research: true  # Use free DuckDuckGo (not Claude web search)

  # Priority mapping based on detection confidence
  priority_mapping:
    high: 0.95
    medium: 0.85
    low: 0.70
```

### Verification Queue Section

```yaml
verification_queue:
  # All tigers go to pending review - both auto-discoveries AND user uploads
  user_uploads_status: "pending"
  auto_discovery_status: "pending"
  require_human_review: true

  # Priority defaults by source
  user_upload_priority: "medium"
  auto_discovery_high_confidence_priority: "high"  # >= 85% confidence
  auto_discovery_default_priority: "medium"
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTO_INVESTIGATION_ENABLED` | `true` | Master switch for auto-investigations |
| `AUTO_INVESTIGATION_MIN_QUALITY` | `60.0` | Minimum image quality score (0-100) |
| `AUTO_INVESTIGATION_MIN_CONFIDENCE` | `0.85` | Minimum MegaDetector confidence (0-1) |
| `AUTO_INVESTIGATION_MAX_PER_HOUR` | `5` | Maximum auto-investigations per hour |
| `AUTO_INVESTIGATION_FACILITY_INTERVAL` | `3600` | Seconds between investigations for same facility |

---

## Rate Limiting

The system implements multiple layers of rate limiting to prevent abuse and conserve resources.

### Crawling Rate Limits

Per-domain request throttling for web crawling:

| Setting | Value | Description |
|---------|-------|-------------|
| Base interval | 2 seconds | Minimum time between requests to same domain |
| Max backoff | 60 seconds | Maximum wait time after repeated errors |
| Recovery rate | 0.9x multiplier | Gradual backoff reduction on success |

HTTP status codes that trigger backoff:
- `429` - Too Many Requests
- `503` - Service Unavailable
- `520-524` - Cloudflare errors

### Auto-Investigation Rate Limits

| Limit Type | Default | Purpose |
|------------|---------|---------|
| Global limit | 5/hour | Prevents investigation spam across all facilities |
| Per-facility limit | 1 hour between | Prevents same facility from flooding queue |

**Why These Limits Exist:**

1. **Prevent Investigation Spam**: Without limits, a single facility with many tiger images could trigger dozens of investigations in minutes.

2. **Conserve Resources**: Each investigation uses Claude API calls, DuckDuckGo searches, and Modal GPU compute. Rate limiting ensures sustainable resource usage.

3. **Human Review Bottleneck**: Investigators can only review so many tigers per day. Rate limiting prevents the queue from growing faster than it can be processed.

4. **Quality Over Quantity**: By limiting investigations, the system prioritizes high-quality, high-confidence discoveries that are more likely to be genuine.

---

## Auto-Investigation Triggering

When the ImagePipelineService processes a new tiger, it calls `InvestigationTriggerService.should_trigger_investigation()` to determine if a full investigation should run.

### Quality Gates

```python
# All gates must pass for auto-investigation to trigger
1. Quality Gate:      quality_score >= 60.0 (configurable)
2. Confidence Gate:   detection_confidence >= 0.85 (configurable)
3. Global Rate Limit: auto_investigations_last_hour < 5 (configurable)
4. Facility Rate:     time_since_last_facility_investigation >= 3600s
5. Duplicate Check:   content_hash not already investigated
```

### Priority Determination

Investigation priority is calculated from detection confidence and quality score:

```python
combined_score = (detection_confidence * 100 + quality_score) / 2

if combined_score >= 90:
    priority = "high"
elif combined_score >= 75:
    priority = "medium"
else:
    priority = "low"
```

### Fire-and-Forget Pattern

Auto-investigations use a fire-and-forget pattern to avoid blocking the discovery pipeline:

```python
# ImagePipelineService._maybe_trigger_auto_investigation()
# This queues the investigation and returns immediately
await self._trigger_service.trigger_investigation(
    tiger_image=processed_tiger.tiger_image,
    image_bytes=image_bytes,
    facility=facility,
    detection_confidence=processed_tiger.detection_confidence,
    quality_score=quality.score
)
# Discovery pipeline continues immediately without waiting
```

---

## Verification Queue Workflow

All identified tigers go to the verification queue for human review.

### Queue Entry Sources

| Source | Initial Status | Default Priority | Notes |
|--------|----------------|------------------|-------|
| User Upload | `pending` | `medium` | Direct uploads via UI/API |
| Auto-Discovery (high conf) | `pending` | `high` | >= 85% detection confidence |
| Auto-Discovery (standard) | `pending` | `medium` | < 85% detection confidence |

### Queue Statuses

| Status | Description |
|--------|-------------|
| `pending` | Awaiting human review |
| `in_review` | Assigned to a reviewer |
| `approved` | Tiger verified and confirmed |
| `rejected` | Tiger rejected (false positive, duplicate, etc.) |

### Review Process

1. **Queue Display**: Reviewers see pending items sorted by priority (high → medium → low) and creation date.

2. **Assignment**: Reviewer clicks to assign themselves, status changes to `in_review`.

3. **Review**: Reviewer examines:
   - Source image and crops
   - Detection confidence
   - ReID match candidates
   - Investigation report (if available)
   - Facility information

4. **Decision**:
   - **Approve**: Tiger becomes verified, linked to confirmed identity
   - **Reject**: Tiger record marked as rejected with notes

### Queue Priority Rules

```python
# Priority order (highest to lowest)
priority_order = {
    "critical": 0,  # Reserved for urgent cases
    "high": 1,      # User uploads, high-confidence auto
    "medium": 2,    # Standard discoveries
    "low": 3        # Low-confidence discoveries
}

# Sort by priority first, then by creation date
queue = sorted(items, key=lambda x: (priority_order[x.priority], x.created_at))
```

---

## API Endpoints

### Discovery Pipeline Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/discovery/status` | Get scheduler status and statistics |
| `POST` | `/api/v1/discovery/start` | Start the discovery scheduler |
| `POST` | `/api/v1/discovery/stop` | Stop the discovery scheduler |
| `POST` | `/api/v1/discovery/crawl/facility/{facility_id}` | Trigger crawl for specific facility |
| `POST` | `/api/v1/discovery/crawl/all` | Trigger full crawl (background) |
| `GET` | `/api/v1/discovery/stats` | Get comprehensive discovery statistics |
| `GET` | `/api/v1/discovery/queue` | Get facilities pending crawl |
| `GET` | `/api/v1/discovery/history` | Get crawl history records |
| `POST` | `/api/v1/discovery/research/{facility_id}` | Run deep research on facility |

### Verification Queue

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/verification/tasks` | Get verification queue items |

### Example: Get Discovery Statistics

```bash
curl -X GET http://localhost:8000/api/v1/discovery/stats \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "facilities": {
    "total": 150,
    "reference": 120,
    "crawled": 85,
    "with_website": 95,
    "pending_crawl": 35
  },
  "tigers": {
    "total": 450,
    "discovered": 120,
    "reference": 330,
    "real": 120
  },
  "images": {
    "total": 1200,
    "discovered": 400,
    "verified": 250
  },
  "scheduler": {
    "running": true,
    "enabled": true,
    "total_crawls": 85,
    "last_crawl": "2026-02-04T10:30:00Z"
  },
  "tools_used": [
    "duckduckgo (free)",
    "playwright (local)",
    "opencv (local)",
    "modal_gpu (existing)"
  ]
}
```

### Example: Start Discovery Scheduler

```bash
curl -X POST http://localhost:8000/api/v1/discovery/start \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "status": "started",
  "message": "Discovery scheduler started (FREE tools only)",
  "tools_used": [
    "duckduckgo_search",
    "playwright_crawling",
    "opencv_quality",
    "modal_gpu_reid"
  ]
}
```

---

## JS-Heavy Site Detection

Modern facility websites often use JavaScript frameworks that require browser rendering.

### Detection Indicators

Sites are classified as JavaScript-heavy if they contain **2 or more** indicators:

**Framework markers:**
- `react`, `angular`, `vue`
- `__next_data__` (Next.js)
- `ng-app` (Angular)

**Lazy loading:**
- `loading="lazy"`
- `data-src=`
- `lazyload`

**Hydration:**
- `hydrate`
- `createRoot`
- `window.__NUXT__`

### Playwright Fallback

When JS-heavy site detected:
1. Launch headless Chromium via Playwright
2. Wait for page to fully render
3. Scroll page to trigger lazy-loaded images
4. Extract `data-src`, `data-lazy-src` attributes
5. Visit up to 5 gallery pages per site

---

## Image Deduplication

SHA256 content hashing prevents redundant GPU processing.

### Process

```
Download Image → Compute SHA256 → Check DB → Skip or Process
```

### Database Schema

| Column | Type | Description |
|--------|------|-------------|
| `content_hash` | VARCHAR(64) | SHA256 hash of image content |
| `is_duplicate_of` | UUID FK | Reference to original image |

### Benefits

- **GPU savings**: Duplicate images skip ML inference entirely
- **Storage efficiency**: Track duplicates without storing twice
- **Audit trail**: Know which images are duplicates of which

---

## Deployment

### Prerequisites

```bash
# Install Playwright
pip install playwright>=1.40.0

# Install browser binaries
playwright install chromium

# Or via Docker (add to Dockerfile):
RUN pip install playwright && playwright install chromium --with-deps
```

### Resource Requirements

| Resource | Requirement |
|----------|-------------|
| Disk (Chromium) | ~500MB |
| RAM per browser | 200-500MB |
| Recommendation | Run discovery workers on dedicated containers |

### Docker Compose Example

```yaml
services:
  discovery_worker:
    build: .
    environment:
      - PLAYWRIGHT_ENABLED=true
      - PLAYWRIGHT_HEADLESS=true
      - RATE_LIMIT_BASE_INTERVAL=2.0
      - RATE_LIMIT_MAX_BACKOFF=60.0
      - IMAGE_DEDUPLICATION_ENABLED=true
      - AUTO_INVESTIGATION_ENABLED=true
      - AUTO_INVESTIGATION_MAX_PER_HOUR=5
    volumes:
      - discovery_data:/app/data/storage/discovered
    deploy:
      resources:
        limits:
          memory: 2G

volumes:
  discovery_data:
```

### Database Initialization

Image deduplication schema is created automatically on startup. To verify:

```bash
# Check content_hash column exists
sqlite3 data/tiger_id.db ".schema tiger_images" | grep content_hash

# Re-initialize if needed
python -c "from backend.database import init_db; init_db()"
```

---

## Troubleshooting

### Auto-Investigations Not Triggering

**Check 1: Is auto-investigation enabled?**
```bash
# Check settings.yaml
grep -A5 "auto_investigation:" config/settings.yaml

# Or environment variable
echo $AUTO_INVESTIGATION_ENABLED
```

**Check 2: Quality thresholds too high?**
```bash
# Current thresholds from settings
grep "min_quality_score\|min_detection_confidence" config/settings.yaml

# Consider lowering if too few investigations trigger:
# min_quality_score: 50.0 (from 60.0)
# min_detection_confidence: 0.80 (from 0.85)
```

**Check 3: Rate limits reached?**
```bash
# Check recent auto-investigations in database
sqlite3 data/tiger_id.db \
  "SELECT COUNT(*) FROM investigations
   WHERE source='auto_discovery'
   AND created_at > datetime('now', '-1 hour')"

# If >= 5, wait for rate limit to reset or increase max_per_hour
```

**Check 4: Per-facility rate limit?**
```bash
# Check last investigation for specific facility
sqlite3 data/tiger_id.db \
  "SELECT created_at FROM investigations
   WHERE source='auto_discovery'
   AND related_facilities LIKE '%<facility_id>%'
   ORDER BY created_at DESC LIMIT 1"
```

### Verification Queue Not Populating

**Check 1: Are tigers being created?**
```bash
# Check recent tiger creations
sqlite3 data/tiger_id.db \
  "SELECT COUNT(*) FROM tigers
   WHERE discovered_at > datetime('now', '-1 day')"
```

**Check 2: Is verification queue table populated?**
```bash
# Check verification_queue table
sqlite3 data/tiger_id.db \
  "SELECT entity_type, source, status, COUNT(*)
   FROM verification_queue
   GROUP BY entity_type, source, status"
```

**Check 3: Check for errors in logs**
```bash
# Search for verification queue errors
grep -i "verification" logs/backend.log | tail -50
```

### Playwright Not Working

```bash
# Verify Playwright installation
python -c "from playwright.sync_api import sync_playwright; print('OK')"

# Reinstall browser
playwright install chromium --with-deps
```

### Rate Limiting Too Aggressive

Adjust environment variables:
```env
RATE_LIMIT_BASE_INTERVAL=1.0  # Reduce from 2.0
RATE_LIMIT_MAX_BACKOFF=30.0   # Reduce from 60.0
```

### Images Not Being Processed

1. Check if hash already exists in database:
```bash
sqlite3 data/tiger_id.db \
  "SELECT image_id, content_hash FROM tiger_images
   WHERE content_hash = '<hash>'"
```

2. Verify image passes quality check (score >= 40)
3. Check MegaDetector is detecting tigers (confidence >= 0.5)
4. Review logs for ML pipeline errors:
```bash
grep -i "embedding\|detection\|quality" logs/backend.log | tail -50
```

### High Memory Usage

- Reduce concurrent browser instances
- Increase container memory limit
- Use `PLAYWRIGHT_HEADLESS=true`

### Duplicate Detection Not Working

Verify content_hash column exists:
```bash
sqlite3 data/tiger_id.db ".schema tiger_images" | grep content_hash
```

If missing, re-run database initialization:
```bash
python -c "from backend.database import init_db; init_db()"
```

---

## Related Documentation

- [Architecture Overview](./ARCHITECTURE.md) - System architecture with discovery flow diagrams
- [Ensemble Strategies](./ENSEMBLE_STRATEGIES.md) - 6-model ensemble details
- [Models Configuration](./MODELS_CONFIGURATION.md) - Model weights and dimensions
- [Deployment Guide](./DEPLOYMENT.md) - General deployment instructions
- [Investigation 2.0](./ARCHITECTURE.md#investigation-20-workflow) - LangGraph workflow phases

---

*Last Updated: February 2026*

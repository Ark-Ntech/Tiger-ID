# Auto-Discovery Integration Tests

## Overview

Comprehensive integration tests for the auto-discovery to investigation pipeline in `test_autodiscovery_integration.py`.

## Test Coverage

### ✅ Passing Tests (3/9)

1. **test_user_upload_adds_to_verification_queue** - Verifies user-uploaded tigers are added to VerificationQueue with correct attributes
2. **test_auto_discovery_adds_to_verification_queue** - Verifies auto-discovered tigers are queued for human review
3. **test_investigation_trigger_criteria** - Validates quality/confidence thresholds and rate limiting logic

### ⚠️ Tests Requiring Async Mock Fixes (6/9)

The following tests have correct structure and assertions but need async mock improvements:

4. **test_pipeline_triggers_investigation** - Tests ImagePipelineService triggers investigation for high-quality discoveries
5. **test_pipeline_respects_rate_limits** - Validates rate limiting prevents excessive investigations
6. **test_completed_investigation_links_to_source** - Tests investigation results link back to source tiger
7. **test_image_deduplication_prevents_duplicates** - Verifies content hash deduplication
8. **test_low_quality_images_rejected** - Tests quality gate rejects poor images before ML processing
9. **test_no_investigation_for_existing_matches** - Verifies matching existing tigers doesn't trigger investigation

## Pipeline Flow Tested

```
Auto-Discovery → Image Pipeline → Investigation Trigger → Investigation Workflow → Verification Queue
                                                                                           ↓
                                                                               Update Source Tiger
```

### Key Components Tested

1. **ImagePipelineService**
   - Image download and quality assessment
   - Tiger detection (MegaDetector)
   - Embedding generation (6-model ensemble)
   - Database matching
   - Deduplication via SHA256 content hash
   - Investigation triggering logic

2. **InvestigationTriggerService**
   - Quality threshold enforcement (min 60.0)
   - Detection confidence threshold (min 0.85)
   - Global rate limiting (max 5/hour)
   - Per-facility rate limiting (1 hour cooldown)
   - Duplicate prevention

3. **Investigation2Workflow**
   - Source tiger linkage
   - VerificationQueue population
   - Investigation completion tracking

4. **Database Models**
   - Tiger (with discovery tracking)
   - TigerImage (with content_hash deduplication)
   - Investigation (with source tracking)
   - VerificationQueue (with priority/status)

## Test Architecture

### Fixtures

- **test_engine** - In-memory SQLite database
- **db_session** - Test database session with rollback
- **test_facility** - Sample wildlife facility
- **sample_tiger_image** - Mock JPEG image bytes
- **discovered_image** - DiscoveredImage dataclass instance
- **mock_tiger_service** - Mocked tiger detection/ReID models

### Mocking Strategy

- **External Services**: Modal GPU inference, web APIs
- **Database**: Real SQLite in-memory (not mocked)
- **File I/O**: Mocked image downloads
- **Settings**: Mocked configuration values

## Issues Discovered

### Bug in investigation2_workflow.py

The `_link_investigation_to_source_tiger` method attempts to JSON load/dump tags:

```python
existing_tags = json.loads(tiger.tags) if tiger.tags else []
tiger.tags = json.dumps(existing_tags)
```

However, the `Tiger` model uses `JSONEncodedValue` which already handles serialization:

```python
tags = Column(JSONList())  # Auto-serializes to/from JSON
```

**Fix Required**: Remove manual JSON handling in workflow to work with JSONEncodedValue.

## Running Tests

### Run All Tests
```bash
pytest tests/test_integration/test_autodiscovery_integration.py -v
```

### Run Specific Test
```bash
pytest tests/test_integration/test_autodiscovery_integration.py::test_user_upload_adds_to_verification_queue -v
```

### Run With Detailed Output
```bash
pytest tests/test_integration/test_autodiscovery_integration.py -xvs
```

## Next Steps

### To Fix Failing Tests

1. **Improve Async Mocking**
   - Use `AsyncMock()` correctly for `session.get()` context manager
   - Ensure `__aenter__` and `__aexit__` are properly mocked
   - Mock `TigerService` detection/embedding methods as async

2. **Fix Workflow Bug**
   - Update `_link_investigation_to_source_tiger` to work with JSONEncodedValue
   - Remove manual `json.loads/dumps` for tags field
   - Test with both JSON strings and lists

3. **Add More Coverage**
   - Test facility rate limiting across different facilities
   - Test concurrent image processing
   - Test investigation completion callbacks
   - Test error handling and recovery

## Test Data Flow

### Successful Auto-Investigation Trigger

```
1. Crawler discovers image → DiscoveredImage
2. ImagePipeline downloads & assesses quality (>60)
3. MegaDetector finds tiger (confidence >0.85)
4. No duplicate found (content_hash check)
5. No strong match (similarity <90%)
6. Rate limits not exceeded
7. InvestigationTriggerService creates Investigation
8. Investigation queued for background processing
9. Source tiger updated with tags/notes
10. Tiger added to VerificationQueue
```

### Rejection Cases

- **Quality < 60**: Rejected at quality gate (no ML processing)
- **Confidence < 0.85**: Rejected at detection threshold
- **Duplicate hash**: Skipped (already processed)
- **Strong match >90%**: Existing tiger updated (no investigation)
- **Rate limit hit**: Queued for later processing
- **Facility cooldown**: Wait for facility-specific timeout

## Database Schema Requirements

The tests verify these fields exist:

### Tiger
- `is_reference` (Boolean) - True for ATRW data, False for real tigers
- `discovered_at` (DateTime) - When tiger was discovered
- `discovered_by_investigation_id` (String) - Investigation that found tiger
- `discovery_confidence` (Float) - ML confidence in discovery
- `tags` (JSONList) - Auto-serialized tags

### TigerImage
- `content_hash` (String) - SHA256 for deduplication
- `is_reference` (Boolean) - Reference vs. real tiger
- `discovered_by_investigation_id` (String) - Source investigation

### Investigation
- `source` (String) - "user_upload" or "auto_discovery"
- `source_tiger_id` (String) - Tiger that triggered auto-investigation
- `source_image_id` (String) - Image that triggered auto-investigation

### VerificationQueue
- `entity_type` (String) - "tiger", "facility", etc.
- `source` (String) - "user_upload" or "auto_discovery"
- `priority` (String) - "low", "medium", "high"
- `status` (String) - "pending", "in_review", "approved", "rejected"
- `requires_human_review` (Boolean) - Always True for discoveries

## Success Criteria

When all tests pass, the system guarantees:

1. **No duplicate processing** - SHA256 hash prevents reprocessing same image
2. **Quality filtering** - Only high-quality images (>60 score) processed
3. **Confidence filtering** - Only high-confidence detections (>0.85) trigger investigations
4. **Rate limiting** - Maximum 5 auto-investigations per hour
5. **Facility throttling** - Minimum 1 hour between investigations for same facility
6. **Human review** - All discoveries queued for verification
7. **Audit trail** - Source tigers updated with investigation references
8. **Source tracking** - Investigations tagged with source (auto vs. user)

## Related Files

- `backend/services/image_pipeline_service.py` - Main discovery processing
- `backend/services/investigation_trigger_service.py` - Auto-investigation logic
- `backend/agents/investigation2_workflow.py` - Investigation workflow
- `backend/database/models.py` - Data models
- `backend/services/facility_crawler_service.py` - Web crawler

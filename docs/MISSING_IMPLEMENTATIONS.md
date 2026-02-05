# Missing Implementations and Required Components

This document lists items that still need to be implemented or configured for the Tiger ID application.

**Last Updated**: February 2026

---

## Recently Completed (2026-02)

The following major improvements have been completed:

### ML/Ops Improvements
- **6-Model Ensemble** - Wildlife-Tools, CVWC2019, TransReID, MegaDescriptor-B, TigerReID, RAPID
- **CVWC2019 Fix** - Corrected to use ResNet152 backbone (was placeholder ResNet50)
- **TransReID** - Added ViT-Base model (768-dim embeddings)
- **MegaDescriptor-B** - Added fast variant (1024-dim embeddings)
- **OmniVinci** - Removed (didn't work for tiger re-ID)
- **RerankingService** - K-reciprocal re-ranking implementation
- **ConfidenceCalibrator** - Temperature scaling for cross-model normalization
- **WeightedEnsembleStrategy** - Combines weights, calibration, re-ranking
- **VerifiedEnsembleStrategy** - Geometric verification using MatchAnything ELOFTR keypoint matching
  - Parallel verification of top-k candidates
  - Adaptive weighting based on ReID confidence spread
  - Sigmoid normalization for match counts
  - Multi-gallery image support (up to 3 per tiger)
  - Side-view preference for gallery selection
  - Verification status thresholds (insufficient_matches, low_confidence, verified, high_confidence)
- **Multi-view Fusion** - Quality-weighted embedding fusion

### MCP Servers
- **Sequential Thinking Server** - Reasoning chain management
- **Image Analysis Server** - Quality assessment, manipulation detection (OpenCV)
- **Deep Research Server** - Iterative DuckDuckGo research
- **Report Generation Server** - Multi-audience reports

### Skills System
- `/synthesize-evidence` - Weighted evidence combination
- `/explain-reasoning` - Chain-of-thought reasoning
- `/investigate-facility` - Deep facility research
- `/generate-report` - Multi-audience reports
- `/assess-image` - Image quality advisor

### Discovery System Enhancements
- **Rate Limiting** - Per-domain tracking with exponential backoff in `facility_crawler_service.py`
  - Tracks request history per domain
  - Exponential backoff on HTTP 429, 503, 520-524
  - Gradual recovery (0.9x multiplier) on success
  - 2-second base interval, 60-second max backoff
- **Image Deduplication** - SHA256 content hashing in `image_pipeline_service.py`
  - Content hash computed before ML processing (saves GPU compute)
  - `content_hash` column in tiger_images table
  - `is_duplicate_of` self-referential FK for tracking duplicates
- **Playwright Crawling** - Auto-detection and JS rendering in `facility_crawler_service.py`
  - Detects JS-heavy sites via `JS_HEAVY_INDICATORS` (React, Vue, Angular, lazy loading)
  - Threshold: 2+ indicators triggers Playwright fallback
  - Scrolls pages to trigger lazy-loaded images
  - Extracts `data-src`, `data-lazy-src` attributes
  - Visits up to 5 gallery pages per site

### Frontend Updates
- **Investigation2Methodology** - Enhanced with expand/collapse, color-coding
- **Audience Selector** - Law Enforcement, Conservation, Internal, Public
- **ReportDownload** - Multi-format export (Markdown, PDF, JSON)
- **Image Quality Badge** - Shows quality score from Image Analysis MCP
- **Verification Tab** - Displays geometric verification results with detailed score breakdowns
- **VerifiedCandidate Types** - TypeScript types for verification data
- **Verification Badges** - Color-coded status indicators (high_confidence, verified, low_confidence)
- **Dark Mode** - Full dark mode support with 530+ `dark:` class occurrences across 18 frontend files

### Backend Features
- **Email Service** - SMTP configuration and email utilities (`backend/utils/email.py`)
- **Reference Data Upload UI** - Tigers page with upload modal (`frontend/src/pages/Tigers.tsx`)
- **Template Functionality** - Template creation dialog (`frontend/src/components/templates/CreateTemplateDialog.tsx`)
- **Backend Test Suite** - 88 test files in `tests/` directory covering services, middleware, routes, and utilities

### Infrastructure Fixes
- **Modal Client Dimension Fixes** - Corrected embedding dimensions:
  - CVWC2019Client: 3072 → 2048 (matches ResNet152 output)
  - WildlifeToolsClient: 2048 → 1536 (matches MegaDescriptor-L-384)
- **TransReIDClient** - New Modal client for TransReID (768-dim ViT-Base)
- **MegaDescriptorBClient** - New Modal client for MegaDescriptor-B (1024-dim)
- **MockResponseProvider** - Fixed default dimensions, added megadescriptor_b_embedding
- **WebSocket Implementation** - Full WebSocket support with auth and investigation rooms

### Database Architecture
- **SQLite with sqlite-vec** - Direct SQLAlchemy model-based schema (no Alembic migrations)
- **Vector Search** - Approximate nearest neighbor search for tiger re-identification
- **Single docker-compose.yml** - Simplified deployment (removed quickstart and dev variants)

### Configuration
- **`.env.example`** - Comprehensive environment template (200+ lines)
- **Model Preloading** - Implemented, enable with `MODEL_PRELOAD_ON_STARTUP=true`

### Medium Severity Audit Fixes (2026-02)
- **Error Message Sanitization** - WebSocket errors sanitized to prevent information disclosure
- **Modal Configuration** - Workspace/app names now configurable via `MODAL_WORKSPACE`, `MODAL_APP_NAME`
- **Discovery Query Optimization** - Reduced dashboard queries from 12+ to 4 using SQLAlchemy CASE expressions
- **Model Testing Endpoints** - `/evaluate` and `/compare` endpoints fully implemented
- **Audience Parameter** - Investigation 2.0 launch accepts `audience` parameter for report targeting
- **Temperature Calibration Bounds** - MIN_TEMPERATURE (0.1), MAX_TEMPERATURE (5.0) enforced
- **Gateway Timeout Prevention** - Modal client tracks total timeout (90s) to prevent 502/504 errors
- **Image Load Timeout** - Gallery image loading has 10s timeout to prevent hangs
- **HTTP Session Cleanup** - ImagePipelineService implements async context manager for proper cleanup
- **WebSocket Reconnection** - Frontend auto-reconnects with exponential backoff (5 attempts, 1s base, 30s max)
- **TypeScript Type Safety** - Replaced generic `any` types with proper Investigation2 types in API

---

## Data & Model Issues

*Last Verified: February 2026*

### Tiger Data Issue
**Problem:** No tiger images may be loaded into the database
- **Location:** `scripts/populate_production_db.py`
- **Root Cause:** ATRW images directory may be empty - dataset needs to be downloaded
- **Solution Required:**
  1. Download ATRW dataset from https://lila.science/datasets/atrw or Kaggle
  2. Extract images to `data/models/atrw/images/` with tiger ID subdirectories

### Model Weights
**Status:** Some models may need weights downloaded
- **TigerReID** - `./data/models/tiger_reid_model.pth` (needs training or download)
- **TransReID** - `./data/models/transreid/vit_base.pth` (needs download)
- **MegaDescriptor-B** - `./data/models/megadescriptor-b/` (needs download)
- **Wildlife-Tools** - May auto-download from HuggingFace

**Solution:** Run `python scripts/download_models.py --model all`

---

## Configuration & Setup

*Last Verified: February 2026*

### 1. Environment Configuration
- **`.env.example` file** - ✅ EXISTS - Comprehensive template (200+ lines)
  - Required: `SECRET_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL` (SQLite)
  - Optional: API keys for external services
  - Model configuration variables
  - Anthropic API key for Claude integration

### 2. External API Integrations
These require API keys:
- **Anthropic API** - Required for Claude (MCP servers, skills, reports)
- **Firecrawl API** - Web scraping (optional, DuckDuckGo works without)
- **YouTube Data API** - Video search (optional)
- **Meta/Facebook Graph API** - Social media search (optional)

### 3. Database Initialization
- **Schema** - Managed via SQLAlchemy models directly (no Alembic migrations required)
- **ATRW Dataset** - Tiger images and embeddings need to be populated
- **Facility Data** - Import from Excel using `/api/v1/facilities/import-excel`
- **Initial Embeddings** - Run embedding generation for gallery tigers

---

## Pending Features

*Last Verified: February 2026*

### Testing
- **Backend Tests** - ✅ 88 test files in `tests/` directory with pytest
- **Frontend Tests** - Basic component tests exist; expansion recommended
- **E2E Tests** - Skeleton only (Playwright configured in `frontend/e2e/`)

---

## Nice-to-Have Enhancements

*Last Verified: February 2026*

### Performance
- **Model Caching** - Verify model caching works properly
- **Database Query Optimization** - Indexes for embeddings
- **Frontend Code Splitting** - Lazy loading components
- **CDN Integration** - For static assets

### User Experience
- **Keyboard Shortcuts** - Power user features
- **Drag and Drop** - Enhanced file upload
- **Progress Indicators** - Better feedback during processing

### Integrations
- **USDA API** - Facility data sync
- **CITES API** - Trade records sync

### Accessibility
- **ARIA Labels** - Screen reader support
- **Keyboard Navigation** - Full keyboard support
- **Color Contrast** - WCAG compliance

---

## Implementation Priority

### High Priority (Required for Basic Functionality)
1. ~~Environment configuration (`.env.example`)~~ ✅ Done
2. Model weights download (auto-download from HuggingFace for most models)
3. Database population (tiger images from ATRW dataset)
4. Anthropic API key configuration

### Medium Priority (Full Functionality)
1. ~~WebSocket implementation~~ ✅ Done
2. ~~Email service~~ ✅ Done
3. ~~Backend tests~~ ✅ Done (88 test files)
4. Frontend test expansion

### Low Priority (Enhancements)
1. Performance optimization
2. Accessibility improvements
3. External API integrations (YouTube, Meta)
4. ~~Dark mode~~ ✅ Done

---

## Verification Checklist

*Last Verified: February 2026*

### Core Functionality
- [x] Backend starts without errors (`uvicorn main:app --reload`)
- [x] Frontend builds and runs (`npm run dev`)
- [x] Database tables created correctly
- [ ] Investigation 2.0 workflow runs end-to-end
- [ ] 6-model ensemble produces results
- [ ] Reports generate in all formats

### Models
- [ ] MegaDetector loads and detects tigers
- [ ] Wildlife-Tools generates embeddings
- [ ] CVWC2019 generates embeddings
- [ ] TransReID generates embeddings
- [ ] MegaDescriptor-B generates embeddings
- [ ] TigerReID generates embeddings
- [ ] RAPID generates embeddings

### MCP Servers
- [ ] Sequential Thinking tracks reasoning
- [ ] Image Analysis returns quality metrics
- [ ] Deep Research returns web results
- [ ] Report Generation produces formatted output

### Skills
- [ ] /synthesize-evidence combines sources
- [ ] /explain-reasoning documents methodology
- [ ] /investigate-facility researches facilities
- [ ] /generate-report creates audience-specific reports
- [ ] /assess-image advises on quality

### Frontend
- [x] Investigation 2.0 page loads
- [x] Results display with methodology
- [x] Audience selector works
- [x] Report download produces files
- [x] Image quality badge shows
- [x] Dark mode works

---

## Quick Start Checklist

1. **Clone and Install**
   ```bash
   git clone <repo>
   cd tiger-id
   pip install -r requirements.txt
   cd frontend && npm install
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Download Models**
   ```bash
   python scripts/download_models.py --model all
   ```

4. **Initialize Database**
   ```bash
   # Database schema is created automatically via SQLAlchemy on first run
   python -c "from backend.database import init_db; init_db()"
   python scripts/populate_production_db.py
   ```

5. **Deploy to Modal (for GPU inference)**
   ```bash
   modal deploy backend/modal_app.py
   ```

6. **Run Application**
   ```bash
   # Terminal 1: Backend
   cd backend && uvicorn main:app --reload

   # Terminal 2: Frontend
   cd frontend && npm run dev
   ```

---

*This document is updated as features are completed. Check git history for changes.*

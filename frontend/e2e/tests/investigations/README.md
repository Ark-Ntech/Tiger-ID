# Investigation E2E Tests

Comprehensive end-to-end tests for the Investigation 2.0 workflow using Playwright.

## Test Coverage

### Image Upload (6 tests)
- ✓ Display upload zone on initial load
- ✓ Upload image via file input
- ✓ Show image preview after upload
- ✓ Support drag and drop upload
- ✓ Reject invalid file types
- ✓ Allow replacing uploaded image

### Context Form (6 tests)
- ✓ Accept location input
- ✓ Accept date input
- ✓ Accept notes input
- ✓ Submit investigation with complete context
- ✓ Allow launching investigation without optional context
- ✓ Enable launch button after image upload

### Investigation Launch (2 tests)
- ✓ Start investigation when launch button is clicked
- ✓ Disable launch button during investigation

### Progress Display (4 tests)
- ✓ Display progress timeline with all 6 phases
- ✓ Show activity feed with progress updates
- ✓ Update phase status as investigation progresses
- ✓ Show current phase as running

### Model Progress Grid (4 tests)
- ✓ Display model progress grid during stripe_analysis phase
- ✓ Show all 6 models in progress grid
- ✓ Show progress percentage for each model
- ✓ Update model progress in real-time

### Results Display (6 tests)
- ✓ Show results section after completion
- ✓ Display tab navigation (Overview/Detection/Matching/Verification/Methodology)
- ✓ Switch between result tabs
- ✓ Display match cards with results
- ✓ Show confidence scores on match cards
- ✓ Show model attribution on match cards

### Match Card Interactions (3 tests)
- ✓ Click match card to view details
- ✓ Select multiple matches for comparison
- ✓ Open comparison drawer for selected matches

### Filters and Search (4 tests)
- ✓ Filter matches by confidence level
- ✓ Filter matches by model
- ✓ Filter matches by facility
- ✓ Clear all filters

### Report Generation (5 tests)
- ✓ Display report section after completion
- ✓ Show audience selector for report (law_enforcement/conservation/internal/public)
- ✓ Regenerate report for different audience
- ✓ Download investigation report
- ✓ Download report in different formats (PDF/JSON)

### Methodology Tracking (4 tests)
- ✓ Display methodology tab
- ✓ Show ensemble strategy details
- ✓ Display model weights in methodology
- ✓ Show processing timeline in methodology

### Error Handling (3 tests)
- ✓ Display error state on investigation failure
- ✓ Allow retry after error
- ✓ Handle network timeout gracefully

### Detection Results (3 tests)
- ✓ Show detection tab with bounding boxes
- ✓ Display detection count
- ✓ Show confidence for each detection

### Overview Tab (3 tests)
- ✓ Show investigation summary
- ✓ Display key metrics in overview
- ✓ Show top matches preview

### Verification Tab (2 tests)
- ✓ Show verification comparison view
- ✓ Display side-by-side image comparison

## Total: 55 E2E Tests

## Running Tests

### All Investigation Tests
```bash
npm run test:e2e -- investigation.spec.ts
```

### Specific Test Suite
```bash
npm run test:e2e -- investigation.spec.ts -g "Image Upload"
```

### Single Test
```bash
npm run test:e2e -- investigation.spec.ts -g "should upload image via file input"
```

### Debug Mode
```bash
npm run test:e2e -- investigation.spec.ts --debug
```

### Headed Mode (See Browser)
```bash
npm run test:e2e -- investigation.spec.ts --headed
```

## Test Architecture

### Page Object Model
Tests use the `Investigation2Page` class (`frontend/e2e/pages/investigations/investigation2.page.ts`) which provides:
- Clean locator abstractions
- Reusable action methods
- Assertion helpers
- Progress tracking utilities

### MSW Mocking
Backend responses are mocked using Mock Service Worker (MSW) handlers:
- `investigationsHandlers` from `frontend/e2e/mocks/handlers/investigations.handlers.ts`
- Simulates investigation workflow phases
- Simulates model progress updates
- Handles file uploads, report generation, and downloads

### Test Factories
Data factories generate realistic test data:
- `investigationFactory` creates investigation objects with various states
- Supports building pending, running, completed, and error states
- Generates realistic match data with confidence scores

## Test Fixtures

Place test images in `frontend/e2e/fixtures/`:
- `tiger.jpg` - Primary test image
- `tiger2.jpg` - Secondary test image for replacement tests

Tests will gracefully skip if fixtures are missing.

## Data Test IDs

All components use `data-testid` attributes for reliable element selection:

### Upload Section
- `investigation-upload-zone`
- `investigation-image-preview`
- `investigation-location-input`
- `investigation-date-input`
- `investigation-notes-input`
- `investigation-launch-button`

### Progress Section
- `investigation-progress-timeline`
- `model-progress-grid`
- `investigation-activity-feed`
- `activity-item`

### Results Section
- `investigation-results`
- `investigation-tab-nav`
- `results-tab-overview`
- `results-tab-detection`
- `results-tab-matching`
- `results-tab-verification`
- `results-tab-methodology`

### Match Cards
- `match-card`
- `match-confidence`
- `match-model`
- `comparison-drawer`
- `compare-selected-button`

### Filters
- `confidence-filter`
- `model-filter`
- `facility-filter`
- `clear-filters-button`

### Report
- `investigation-report`
- `report-audience-select`
- `report-regenerate-button`
- `report-download-button`
- `report-format-select`

### Methodology
- `methodology-content`
- `ensemble-strategy`
- `model-weight-{model_name}`
- `processing-timeline`

### Detection
- `detection-visualization`
- `detection-count`
- `detection-item`
- `detection-confidence`

### Overview
- `investigation-summary`
- `total-matches`
- `detection-count`
- `confidence-level`
- `top-matches`

### Verification
- `verification-content`
- `query-image`
- `match-image`

### Error State
- `error-state`
- `error-state-retry`

## CI/CD Integration

Tests are configured for CI environments:
- 2 retries on failure
- Serial execution (1 worker) in CI
- HTML report generation
- Trace on first retry
- Cross-browser testing (Chromium, Firefox, WebKit)

## Performance Considerations

- Tests use MSW to mock API responses (fast, no network delay)
- Progress simulation runs at accelerated speed for testing
- Timeouts are generous (120s for completion) to handle CI load
- File uploads use small test fixtures (< 5MB)

## Troubleshooting

### Tests Timing Out
- Increase timeout in test: `await investigationPage.waitForCompletion(180000)`
- Check MSW handlers are properly simulating progress

### Elements Not Found
- Verify `data-testid` attributes match in React components
- Check element visibility with `--headed` mode
- Use `page.pause()` to debug interactively

### File Upload Failures
- Ensure test fixtures exist in `frontend/e2e/fixtures/`
- Check file paths are correct (absolute paths from `__dirname`)
- Verify file input is visible before upload

### Flaky Tests
- Add explicit waits: `await page.waitForTimeout(500)`
- Use Playwright's auto-waiting: `await expect(element).toBeVisible()`
- Check for race conditions in MSW progress simulation

## Future Enhancements

- Add visual regression testing with Playwright screenshots
- Test WebSocket real-time updates more thoroughly
- Add accessibility (a11y) testing with axe-core
- Test keyboard navigation through investigation workflow
- Add performance testing (Lighthouse CI integration)

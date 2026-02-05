# Investigation E2E Test Suite - Summary

## Overview

Created comprehensive E2E tests for the Investigation 2.0 workflow covering all major user interactions and system behaviors.

## Files Created

### Test Files
- `investigation.spec.ts` - Main test suite (55 tests across 15 describe blocks)
- `README.md` - Comprehensive documentation of test coverage and usage

### Helper Files
- `fixtures.ts` - Fixture management utilities with auto-generation of minimal test images

### Updated Files
- `../fixtures/README.md` - Updated documentation for test fixtures

## Test Coverage Summary

### 55 Total E2E Tests

| Category | Tests | Description |
|----------|-------|-------------|
| Image Upload | 6 | Upload, preview, drag-drop, validation, replacement |
| Context Form | 6 | Location, date, notes, submission |
| Investigation Launch | 2 | Launch button, state management |
| Progress Display | 4 | Timeline, phases, activity feed |
| Model Progress Grid | 4 | 6-model parallel progress tracking |
| Results Display | 6 | Tabs, match cards, confidence scores |
| Match Card Interactions | 3 | Click, select, compare |
| Filters and Search | 4 | Confidence, model, facility filters |
| Report Generation | 5 | Audience selection, regeneration, download |
| Methodology Tracking | 4 | Ensemble details, weights, timeline |
| Error Handling | 3 | Error state, retry, network timeout |
| Detection Results | 3 | Bounding boxes, detection count |
| Overview Tab | 3 | Summary, metrics, top matches |
| Verification Tab | 2 | Comparison view, side-by-side images |

## Architecture Highlights

### Page Object Model
Uses `Investigation2Page` class providing:
- Clean locator abstractions via getters
- Reusable action methods (uploadImage, fillContext, launchInvestigation)
- Assertion helpers (expectImageUploaded, expectInProgress, expectCompleted)
- Progress tracking utilities (getPhaseStatus, waitForPhase, getModelProgress)

### MSW Mocking
Backend responses mocked with:
- Simulated workflow phases (6-phase investigation pipeline)
- Realistic progress updates with polling
- Model progress simulation during stripe_analysis
- File upload handling
- Report generation and download simulation

### Fixture Management
Auto-generates minimal valid JPEG files if real images not present:
- `ensureFixtures()` creates 1x1 pixel valid JPEGs
- Tests gracefully handle missing fixtures
- Easy to replace with real tiger images

### Data-Driven Testing
Uses `investigationFactory` for test data:
- Realistic investigation objects
- Various states (pending, running, completed, error)
- Match data with confidence scores
- Top matches with model attribution

## Test Execution

### Run All Tests
```bash
npm run test:e2e -- investigation.spec.ts
```

### Run Specific Suite
```bash
npm run test:e2e -- investigation.spec.ts -g "Image Upload"
```

### Debug Mode
```bash
npm run test:e2e -- investigation.spec.ts --debug
```

### Headed Mode
```bash
npm run test:e2e -- investigation.spec.ts --headed
```

## Key Test Scenarios

### Happy Path
1. Upload tiger image
2. Fill context form (location, date, notes)
3. Launch investigation
4. Monitor progress through 6 phases
5. View model progress grid during stripe_analysis
6. Review results across all tabs
7. Filter matches by confidence/model/facility
8. Select matches for comparison
9. Generate and download report

### Edge Cases
- Invalid file type upload
- Missing optional context fields
- Network timeout handling
- Investigation error and retry
- Empty match results
- Filter combinations
- Multiple report audiences
- Different download formats

### Error Scenarios
- Investigation failure with error state
- Retry after failure
- Network timeout handling
- Missing fixtures (graceful degradation)

## Data Test IDs Used

All components use consistent `data-testid` attributes for reliable selection:

### Critical Test IDs
- `investigation-upload-zone`
- `investigation-image-preview`
- `investigation-launch-button`
- `investigation-progress-timeline`
- `model-progress-grid`
- `investigation-results`
- `investigation-tab-nav`
- `match-card`
- `comparison-drawer`
- `report-download-button`

## Test Reliability Features

### Auto-Waiting
Playwright's built-in auto-waiting ensures tests don't fail due to timing:
- `await expect(element).toBeVisible()` waits automatically
- Generous timeouts (120s for completion) handle CI load
- Progress simulation at accelerated speed

### Error Recovery
Tests handle common failure scenarios:
- Missing fixtures (auto-generated or skipped)
- Network delays (mocked with MSW)
- Element visibility checks with retries
- Proper cleanup between tests

### Cross-Browser
Configured for testing on:
- Chromium (Chrome/Edge)
- Firefox
- WebKit (Safari)

## Performance Considerations

- MSW mocking eliminates network latency
- Small test fixtures (< 1KB minimal JPEGs)
- Parallel test execution (except CI)
- Fast progress simulation
- No actual ML model inference

## Future Enhancements

Potential additions for comprehensive coverage:

1. Visual Regression Testing
   - Screenshot comparison for UI consistency
   - Detect unintended visual changes

2. Accessibility Testing
   - axe-core integration for a11y checks
   - Keyboard navigation testing

3. Performance Testing
   - Lighthouse CI integration
   - Performance budgets

4. WebSocket Testing
   - Real-time update verification
   - Connection handling

5. Mobile Testing
   - Responsive design verification
   - Touch interactions

## Integration with CI/CD

Tests are CI-ready:
- 2 retries on failure
- Serial execution in CI (1 worker)
- HTML report generation
- Trace on first retry
- Environment-specific configuration

## Maintenance Notes

### When to Update Tests

1. New UI Components
   - Add corresponding test cases
   - Update Page Object Model locators

2. API Changes
   - Update MSW handlers
   - Adjust response shapes

3. Workflow Changes
   - Update phase names/count
   - Adjust progress expectations

4. New Features
   - Add new describe blocks
   - Create feature-specific tests

### Common Issues

1. Element Not Found
   - Verify `data-testid` in component
   - Check visibility timing
   - Use `--headed` mode to debug

2. Timing Issues
   - Increase timeout for slow operations
   - Add explicit waits if needed
   - Check MSW handler delays

3. Fixture Issues
   - Ensure fixtures directory exists
   - Check file paths are absolute
   - Replace minimal JPEGs with real images

## Test Quality Metrics

### Coverage
- All major user flows covered
- Edge cases tested
- Error scenarios handled

### Reliability
- No hard-coded waits (except for MSW simulation)
- Proper element selection with test IDs
- Graceful failure handling

### Maintainability
- Page Object Model abstraction
- Reusable helpers
- Clear test descriptions
- Comprehensive documentation

### Performance
- Fast execution (< 5 min for full suite with MSW)
- Parallel execution where possible
- Minimal fixture size

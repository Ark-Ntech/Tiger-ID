# Facility Detail Tests - Quick Start Guide

## Prerequisites

### 1. Start Backend API
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 2. Start Frontend Dev Server
```bash
cd frontend
npm run dev
```

### 3. Verify Test User Exists
Ensure test user credentials are configured:
- Username: `testuser`
- Password: `testpassword`

Or set custom credentials in `.env`:
```bash
TEST_USER_EMAIL=your-test-user
TEST_USER_PASSWORD=your-test-password
```

## Running Tests

### Quick Run (Headless)
```bash
cd frontend
npx playwright test tests/facilities/facility-detail
```

### See Browser Actions (Headed)
```bash
npx playwright test tests/facilities/facility-detail --headed
```

### Interactive Debugging (UI Mode)
```bash
npx playwright test tests/facilities/facility-detail --ui
```

### Run Single Test
```bash
npx playwright test tests/facilities/facility-detail -g "should display facility detail page"
```

### Generate Report
```bash
npx playwright test tests/facilities/facility-detail
npx playwright show-report
```

## Test Scenarios

### 10 Core Tests
1. ✅ View facility detail page with info
2. ✅ Facility map shows location
3. ✅ Crawl history timeline shows events
4. ✅ Timeline event details expand
5. ✅ Tiger gallery shows tigers
6. ✅ Gallery view mode toggle
7. ✅ Group by tiger toggle
8. ✅ Click tiger navigates
9. ✅ Edit facility info
10. ✅ Start manual crawl

### 10+ Additional Tests
- Discovery status display
- Metadata and timestamps
- Links and social media
- Accreditation badges
- Close detail panel
- Loading states
- Empty states
- Mobile responsive
- Filter functionality
- Show more events
- Quality indicators
- Navigation flow

## Expected Results

### All Passing ✅
Tests should pass when:
- Backend API is running
- Frontend dev server is running
- Test user can authenticate
- At least 1 facility exists in database

### Partial Pass (OK) ⚠️
Some tests may skip when:
- No facilities in database (empty state tests pass)
- Facility has no tigers (empty gallery tests pass)
- Facility has no crawl history (empty timeline tests pass)
- Optional fields missing (edit/crawl buttons conditional)

### Failures to Investigate ❌
- Authentication failures
- Network errors
- Missing `data-testid` attributes
- Component rendering errors

## Troubleshooting

### "Timeout waiting for web server"
```bash
# Start frontend manually first
cd frontend && npm run dev

# Then run tests with existing server
npx playwright test tests/facilities/facility-detail
```

### "Element not found"
- Check that components have proper `data-testid` attributes
- See README.md for full list of required test IDs

### "Authentication failed"
- Verify test user exists in database
- Check credentials in `.env` or test file

### "Map not loading"
- Wait longer for Leaflet to initialize
- Check for JavaScript console errors
- Verify facility has valid lat/long coordinates

## Quick Debug Commands

### View test in slow motion
```bash
npx playwright test tests/facilities/facility-detail --headed --debug
```

### Generate trace for debugging
```bash
npx playwright test tests/facilities/facility-detail --trace on
```

### View trace file
```bash
npx playwright show-trace trace.zip
```

### Screenshot on failure
```bash
# Automatic in CI
# Check test-results/ directory for screenshots
```

## File Locations

- **Tests**: `frontend/e2e/tests/facilities/facility-detail.spec.ts`
- **Documentation**: `frontend/e2e/tests/facilities/README.md`
- **Summary**: `frontend/e2e/tests/facilities/FACILITY_DETAIL_TEST_SUMMARY.md`
- **Auth Helper**: `frontend/e2e/helpers/auth.ts`

## Component Files

- **Timeline**: `frontend/src/components/facilities/CrawlHistoryTimeline.tsx`
- **Gallery**: `frontend/src/components/facilities/FacilityTigerGallery.tsx`
- **Map**: `frontend/src/components/facilities/FacilityMapView.tsx`
- **Filters**: `frontend/src/components/facilities/FacilityFilters.tsx`
- **Facilities Page**: `frontend/src/pages/Facilities.tsx`

## Need Help?

1. Check `README.md` for detailed documentation
2. See `FACILITY_DETAIL_TEST_SUMMARY.md` for architecture overview
3. Review Playwright docs: https://playwright.dev
4. Check component source code for test ID implementation

---

**Quick Test**: `npx playwright test tests/facilities/facility-detail --headed -g "should display facility detail page"`

This will run just the first test with the browser visible so you can see what's happening.

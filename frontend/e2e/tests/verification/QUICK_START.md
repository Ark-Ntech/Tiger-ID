# Verification Queue E2E Tests - Quick Start Guide

## Prerequisites

1. Install dependencies (if not already done):
```bash
cd frontend
npm install
```

2. Install Playwright browsers:
```bash
npx playwright install
```

3. Ensure backend API is running on `http://localhost:8000`:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

4. Ensure frontend dev server is running on `http://localhost:5173`:
```bash
cd frontend
npm run dev
```

## Running Tests

### Quick Run (All Verification Tests)
```bash
cd frontend
npx playwright test tests/verification/verification.spec.ts
```

**Expected output:**
```
Running 38 tests using 4 workers
  38 passed (5.2s)
```

### Run Specific Test Suite

#### Filtering Tests Only
```bash
npx playwright test tests/verification/verification.spec.ts -g "Filtering"
```

#### Selection Tests Only
```bash
npx playwright test tests/verification/verification.spec.ts -g "Item Selection"
```

#### Bulk Actions Tests Only
```bash
npx playwright test tests/verification/verification.spec.ts -g "Bulk Actions"
```

#### Pagination Tests Only
```bash
npx playwright test tests/verification/verification.spec.ts -g "Pagination"
```

### Visual Test Modes

#### Headed Mode (See Browser)
Watch tests execute in real browser:
```bash
npx playwright test tests/verification/verification.spec.ts --headed
```

#### UI Mode (Interactive)
Interactive test runner with time-travel debugging:
```bash
npx playwright test tests/verification/verification.spec.ts --ui
```

#### Debug Mode (Step Through)
Step through test execution:
```bash
npx playwright test tests/verification/verification.spec.ts --debug
```

### Browser-Specific Runs

#### Chrome Only
```bash
npx playwright test tests/verification/verification.spec.ts --project=chromium
```

#### Firefox Only
```bash
npx playwright test tests/verification/verification.spec.ts --project=firefox
```

#### Safari Only
```bash
npx playwright test tests/verification/verification.spec.ts --project=webkit
```

## Test Results

### View HTML Report
After tests complete:
```bash
npx playwright show-report
```

### Generate Report Manually
```bash
npx playwright test tests/verification/verification.spec.ts --reporter=html
npx playwright show-report
```

## Debugging Failed Tests

### Take Screenshots
Screenshots are automatically captured on failure and saved to:
```
frontend/test-results/
```

### View Trace
If a test fails, view detailed trace:
```bash
npx playwright show-trace test-results/<test-name>/trace.zip
```

### Run Single Test
Debug specific failing test:
```bash
npx playwright test tests/verification/verification.spec.ts -g "should approve individual item" --debug
```

## Test Coverage Checklist

Verify all scenarios are passing:

- [ ] View queue - Page loads with pending items
- [ ] Filter by status - Status dropdown filters correctly
- [ ] Filter by confidence - High/medium/low confidence filters work
- [ ] Filter by entity type - Tiger/facility filters work
- [ ] Select items - Individual checkboxes can be selected
- [ ] Select all - Select-all checkbox works
- [ ] Bulk approve - Multiple items can be approved at once
- [ ] Bulk reject - Multiple items can be rejected at once
- [ ] Individual approve - Single item approve button works
- [ ] Individual reject - Single item reject button works
- [ ] Comparison overlay - View button opens comparison modal
- [ ] Model agreement badge - Badge shows correct model consensus
- [ ] Pagination - Next/previous navigation works

## Common Issues

### Issue: Tests fail with "Authentication required"
**Solution**: Ensure login helper is working and test user exists:
```bash
# Check auth helper
cat frontend/e2e/helpers/auth.ts

# Verify test credentials in .env
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=password123
```

### Issue: Tests fail with "Network timeout"
**Solution**: Ensure backend API is running:
```bash
# Check backend status
curl http://localhost:8000/health

# Restart backend if needed
cd backend
uvicorn main:app --reload --port 8000
```

### Issue: Tests fail with "Element not found"
**Solution**: Verify selectors match actual page:
```bash
# Run test in headed mode to inspect page
npx playwright test tests/verification/verification.spec.ts --headed --debug
```

### Issue: Intermittent failures
**Solution**: Check for race conditions, increase timeout:
```typescript
test.setTimeout(60000) // 60 seconds
```

## Mock Data vs Real API

Tests use mocked API responses by default. To run against real API:

1. Comment out `page.route()` calls in tests
2. Ensure backend has test data:
```bash
# Seed test data
python backend/scripts/seed_verification_queue.py
```

3. Run tests:
```bash
npx playwright test tests/verification/verification.spec.ts
```

## Test Data Factories

Tests use factory functions for consistent data:

### Available Factories
- `createVerificationQueue(count)` - Create N queue items
- `createHighConfidenceItem(overrides)` - High confidence item (>90%)
- `createLowConfidenceItem(overrides)` - Low confidence item (<70%)
- `createFacilityVerificationItem(overrides)` - Facility entity

### Example Usage in Tests
```typescript
const mockItems = createVerificationQueue(5)
const highConfItem = createHighConfidenceItem({
  entity_name: 'Rajah',
  confidence: 0.95
})
```

## Performance Tips

### Run Tests Faster
```bash
# Use fewer workers for stability
npx playwright test tests/verification/verification.spec.ts --workers=1

# Skip browser downloads (if already installed)
npx playwright test --no-install

# Run specific tests only
npx playwright test -g "should approve"
```

### Parallel Execution
```bash
# Use all CPU cores (default)
npx playwright test tests/verification/verification.spec.ts

# Limit to 2 workers
npx playwright test tests/verification/verification.spec.ts --workers=2
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Verification Tests
  run: npx playwright test tests/verification/verification.spec.ts
  working-directory: ./frontend
  env:
    CI: true
```

### GitLab CI
```yaml
verification-tests:
  script:
    - cd frontend
    - npx playwright test tests/verification/verification.spec.ts
  artifacts:
    when: always
    paths:
      - frontend/playwright-report/
```

## Next Steps

After verifying all tests pass:

1. Review test coverage report
2. Add custom tests for specific edge cases
3. Integrate into CI/CD pipeline
4. Set up scheduled test runs
5. Configure alerts for test failures

## Resources

- **Full Test File**: `frontend/e2e/tests/verification/verification.spec.ts`
- **Page Object**: `frontend/e2e/pages/verification/verification-queue.page.ts`
- **Test Summary**: `frontend/e2e/tests/verification/TEST_SUMMARY.md`
- **Playwright Docs**: https://playwright.dev/docs/intro
- **Project E2E Docs**: `frontend/e2e/README.md`

## Support

For issues or questions:
1. Check `frontend/e2e/README.md` for troubleshooting
2. Review Playwright documentation
3. Inspect browser console in headed mode
4. Check test-results directory for screenshots/traces

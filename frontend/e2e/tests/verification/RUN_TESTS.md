# Quick Test Execution Guide

## Run All Verification Tests

```bash
cd frontend
npm run test:e2e -- e2e/tests/verification/verification.spec.ts
```

## Run Specific Test Suites

### Filtering Tests
```bash
npm run test:e2e -- e2e/tests/verification/verification.spec.ts -g "Filtering"
```

### Bulk Actions Tests
```bash
npm run test:e2e -- e2e/tests/verification/verification.spec.ts -g "Bulk Actions"
```

### Individual Actions Tests
```bash
npm run test:e2e -- e2e/tests/verification/verification.spec.ts -g "Individual Item Actions"
```

### Comparison Overlay Tests
```bash
npm run test:e2e -- e2e/tests/verification/verification.spec.ts -g "Comparison Overlay"
```

### Pagination Tests
```bash
npm run test:e2e -- e2e/tests/verification/verification.spec.ts -g "Pagination"
```

### Model Agreement Badge Tests
```bash
npm run test:e2e -- e2e/tests/verification/verification.spec.ts -g "Model Agreement Badge"
```

## Debug Mode

Run with headed browser and paused execution:
```bash
npm run test:e2e -- e2e/tests/verification/verification.spec.ts --debug
```

## Watch Mode

Automatically rerun tests on file changes:
```bash
npm run test:e2e -- e2e/tests/verification/verification.spec.ts --watch
```

## Generate HTML Report

```bash
npm run test:e2e -- e2e/tests/verification/verification.spec.ts --reporter=html
```

Then open `playwright-report/index.html` in a browser.

## Run in Different Browsers

### Chromium (default)
```bash
npm run test:e2e -- e2e/tests/verification/verification.spec.ts --project=chromium
```

### Firefox
```bash
npm run test:e2e -- e2e/tests/verification/verification.spec.ts --project=firefox
```

### WebKit (Safari)
```bash
npm run test:e2e -- e2e/tests/verification/verification.spec.ts --project=webkit
```

## Run Single Test

```bash
npm run test:e2e -- e2e/tests/verification/verification.spec.ts -g "should approve individual item"
```

## Common Options

- `--headed` - Run with visible browser
- `--debug` - Run in debug mode with Playwright Inspector
- `--ui` - Run in UI mode (interactive)
- `--trace on` - Record trace for debugging
- `--workers=1` - Run tests serially (no parallelization)
- `--retries=2` - Retry failed tests up to 2 times

## Test Coverage Summary

Total Tests: **32 scenarios across 10 test suites**

1. Page Load and Initial State: 4 tests
2. Filtering: 4 tests
3. Item Selection: 3 tests
4. Bulk Actions: 3 tests
5. Individual Item Actions: 3 tests
6. Comparison Overlay: 4 tests
7. Model Agreement Badge: 3 tests
8. Pagination: 5 tests
9. Real-time Updates: 1 test
10. Accessibility: 2 tests

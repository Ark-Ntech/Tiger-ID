# Playwright CI/CD Configuration

Comprehensive guide to the Playwright test configuration for Tiger ID, including sharding, parallel execution, and CI/CD optimization.

## Configuration Overview

**File**: `frontend/playwright.config.ts`

### Key Features

1. **Multi-browser Testing**: Chromium, Firefox, WebKit
2. **Sharding Support**: 4 shards for parallel CI execution
3. **Smart Retries**: 2 retries in CI, 0 locally
4. **Parallel Workers**: 4 workers in CI, 50% CPU locally
5. **Timeouts**: 30s test timeout, 10s expect timeout
6. **Reporters**: JUnit XML + HTML for CI, line + HTML for local
7. **Artifacts**: Screenshots on failure, video/trace on first retry
8. **Global Setup**: Single authentication for all tests
9. **Configurable Base URL**: Via `BASE_URL` environment variable

## Running Tests

### Local Development

```bash
# Run all tests
npm run test:e2e

# Run with UI
npm run test:e2e:ui

# Run headed (see browser)
npm run test:e2e:headed

# Run specific test file
npm run test:e2e auth-flow

# Run specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### CI/CD Execution

#### Single Machine (No Sharding)

```bash
# Run all tests on one machine
CI=1 npx playwright test
```

#### Parallel Sharding (4 Shards)

Run these commands in parallel on different CI jobs/machines:

```bash
# Job 1
CI=1 npx playwright test --shard=1/4

# Job 2
CI=1 npx playwright test --shard=2/4

# Job 3
CI=1 npx playwright test --shard=3/4

# Job 4
CI=1 npx playwright test --shard=4/4
```

Each shard will run approximately 25% of the tests.

#### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci
          npx playwright install --with-deps

      - name: Start backend
        run: |
          cd backend
          pip install -r requirements.txt
          uvicorn main:app --host 0.0.0.0 --port 8000 &
          sleep 10

      - name: Run Playwright tests
        run: |
          cd frontend
          npx playwright test --shard=${{ matrix.shard }}/4
        env:
          CI: true
          BASE_URL: http://localhost:5173
          API_URL: http://localhost:8000

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results-${{ matrix.shard }}
          path: frontend/test-results/
          retention-days: 7

      - name: Upload HTML report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report-${{ matrix.shard }}
          path: frontend/playwright-report/
          retention-days: 7
```

## Configuration Details

### Test Timeouts

```typescript
timeout: 30000,              // 30s per test
expect: { timeout: 10000 },  // 10s per assertion
use: {
  actionTimeout: 30000,      // 30s per action (click, fill, etc.)
  navigationTimeout: 30000,  // 30s for page navigation
}
```

### Retry Strategy

```typescript
retries: process.env.CI ? 2 : 0
```

- **CI**: Tests retry 2 times on failure (3 total attempts)
- **Local**: Tests do not retry (fail immediately)

### Worker Configuration

```typescript
workers: process.env.CI ? 4 : '50%'
```

- **CI**: 4 parallel workers (matches shard count)
- **Local**: 50% of available CPUs

### Reporters

#### CI Environment
```typescript
[
  ['junit', { outputFile: 'test-results/junit.xml' }],  // For CI integration
  ['html', { outputFolder: 'playwright-report', open: 'never' }],  // HTML report
  ['list']  // Console output
]
```

#### Local Environment
```typescript
[
  ['line'],  // Concise console output
  ['html', { outputFolder: 'playwright-report', open: 'on-failure' }]  // Opens browser on failure
]
```

### Artifact Capture

```typescript
screenshot: 'only-on-failure',  // Screenshot when test fails
video: 'on-first-retry',        // Video on first retry only
trace: 'on-first-retry',        // Trace on first retry only
```

Artifacts are saved to `test-results/` directory.

## Global Setup

**File**: `frontend/e2e/global.setup.ts`

The global setup runs once before all tests to:

1. **Verify Backend**: Check that API is available at `API_URL`
2. **Authenticate Users**: Login as admin, analyst, and viewer
3. **Save Auth States**: Store authentication in `.auth/` directory
4. **Initialize Data**: Create test data if needed

### Auth State Reuse

Authenticated states are saved and reused across all test files and browser projects:

```
.auth/
├── admin.json    # Admin user authentication
├── analyst.json  # Analyst user authentication
└── viewer.json   # Viewer user authentication
```

Tests load these states via:

```typescript
use: {
  storageState: '.auth/admin.json',
}
```

### Auth State Caching

Auth states are cached for 1 hour. If an auth file exists and is less than 1 hour old, it will be reused instead of re-authenticating.

## Browser Projects

### Configured Browsers

1. **Chromium** (Chrome/Edge)
   - Uses Desktop Chrome device profile
   - Loads admin auth state

2. **Firefox**
   - Uses Desktop Firefox device profile
   - Loads admin auth state

3. **WebKit** (Safari)
   - Uses Desktop Safari device profile
   - Loads admin auth state

### Project Dependencies

All browser projects depend on the `setup` project, which runs `global.setup.ts`.

```typescript
projects: [
  { name: 'setup', testMatch: /.*\.setup\.ts/ },
  { name: 'chromium', dependencies: ['setup'], ... },
  { name: 'firefox', dependencies: ['setup'], ... },
  { name: 'webkit', dependencies: ['setup'], ... },
]
```

## Environment Variables

### Required

- `BASE_URL` - Frontend URL (default: `http://localhost:5173`)
- `API_URL` - Backend API URL (default: `http://localhost:8000`)

### Optional

- `CI` - Set to `true` to enable CI mode (retries, workers, reporters)
- `PLAYWRIGHT_HTML_OPEN` - Override HTML report behavior

### Setting Variables

```bash
# Local
export BASE_URL=http://localhost:3000
export API_URL=http://localhost:8000

# CI
CI=1 BASE_URL=https://staging.tiger-id.com npx playwright test
```

## Sharding Strategy

### Why Sharding?

Sharding distributes tests across multiple machines to:
- Reduce total test execution time
- Parallelize across CI runners
- Improve CI/CD pipeline speed

### How It Works

1. Playwright divides tests into 4 roughly equal groups
2. Each shard runs independently on a different machine
3. Results are collected separately
4. Total time ≈ (sequential time) / 4

### Optimal Shard Count

- **4 shards** is the default (matches worker count)
- Increase if you have more CI runners available
- Decrease for smaller test suites

### Sharding Commands

```bash
# Local testing of shards
npm run test:e2e:shard1
npm run test:e2e:shard2
npm run test:e2e:shard3
npm run test:e2e:shard4

# Or directly
npx playwright test --shard=1/4
npx playwright test --shard=2/4
npx playwright test --shard=3/4
npx playwright test --shard=4/4
```

## Output Directories

```
frontend/
├── test-results/         # Test artifacts (screenshots, videos, traces)
│   ├── junit.xml         # JUnit XML report (CI only)
│   └── [test-artifacts]  # Per-test artifacts
├── playwright-report/    # HTML test report
│   └── index.html        # View in browser
└── .auth/                # Authenticated storage states
    ├── admin.json
    ├── analyst.json
    └── viewer.json
```

### Viewing Reports

```bash
# Open HTML report in browser
npm run test:e2e:report

# Or directly
npx playwright show-report
```

## Debugging

### Local Debugging

```bash
# Run with UI mode (recommended)
npm run test:e2e:ui

# Run headed (see browser)
npm run test:e2e:headed

# Debug specific test
npx playwright test auth-flow --debug

# Run in slow motion
npx playwright test --slow-mo=1000
```

### CI Debugging

1. Download test artifacts from CI
2. Extract to `test-results/`
3. View trace files:

```bash
npx playwright show-trace test-results/[test-name]/trace.zip
```

4. View screenshots in `test-results/`

### Common Issues

#### Backend Not Available

```
❌ Could not reach backend API
```

**Solution**: Start backend server before running tests

```bash
cd backend
uvicorn main:app --reload --port 8000
```

#### Authentication Failed

```
❌ Failed to authenticate user admin: No token found in storage
```

**Solution**: Check that login page is accessible and credentials are correct in `e2e/data/factories/user.factory.ts`

#### Timeout Errors

```
Timeout 30000ms exceeded
```

**Solution**:
- Increase timeout in config: `timeout: 60000`
- Or for specific test: `test.setTimeout(60000)`
- Check if app is slow or hanging

## Best Practices

### Writing Sharding-Compatible Tests

1. **Make tests independent**: Don't rely on order or other tests
2. **Use global setup**: Share auth states, don't login in every test
3. **Clean up after tests**: Reset state or use unique identifiers
4. **Avoid race conditions**: Don't share test data between shards

### Test Organization

```typescript
// Good: Independent tests
test('create tiger', async ({ page }) => {
  const uniqueName = `Tiger-${Date.now()}`;
  // Test creates unique tiger
});

// Bad: Depends on other tests
test('edit tiger', async ({ page }) => {
  // Assumes "Tiger-1" exists from another test
  await page.goto('/tigers/Tiger-1/edit');
});
```

### Performance Tips

1. **Reuse auth states** (already configured)
2. **Use page fixtures** instead of logging in per test
3. **Minimize network requests** in tests
4. **Use waitForLoadState** strategically
5. **Avoid unnecessary waits** (use Playwright auto-waiting)

## Troubleshooting

### Tests Pass Locally But Fail in CI

Check:
- Environment variables are set correctly in CI
- Backend is running and accessible
- CI has enough resources (memory, CPU)
- Timeouts may need to be increased for slower CI machines

### Shards Have Uneven Runtime

This is normal due to test complexity variation. Playwright tries to distribute evenly by test count, not runtime. Consider:
- Breaking up long tests into smaller ones
- Using more shards if some take significantly longer

### Global Setup Runs Multiple Times

When using sharding, each shard runs global setup. The auth state caching (1-hour TTL) helps reduce redundant authentication.

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Sharding Guide](https://playwright.dev/docs/test-sharding)
- [CI/CD Guide](https://playwright.dev/docs/ci)
- [Best Practices](https://playwright.dev/docs/best-practices)

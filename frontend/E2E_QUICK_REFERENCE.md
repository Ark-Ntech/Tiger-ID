# E2E Testing Quick Reference

Quick commands and common tasks for Playwright E2E testing in Tiger ID.

## Quick Start

```bash
# Run all tests
npm run test:e2e

# Run with UI (recommended for development)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed
```

## Running Tests

### All Tests
```bash
npm run test:e2e                    # All tests, all browsers
npm run test:e2e -- --project=chromium  # Chromium only
npm run test:e2e -- --project=firefox   # Firefox only
npm run test:e2e -- --project=webkit    # WebKit only
```

### Specific Test Files
```bash
npm run test:e2e:auth              # Authentication tests
npm run test:e2e:investigation     # Investigation tests
npm run test:e2e:tiger             # Tiger management tests
npm run test:e2e:facility          # Facility tests
npm run test:e2e:verification      # Verification tests
npm run test:e2e:discovery         # Discovery tests
```

### Debugging
```bash
npm run test:e2e:ui                # UI mode (best for debugging)
npm run test:e2e:headed            # See browser while testing
npx playwright test --debug        # Step-by-step debugging
npx playwright test --debug auth-flow  # Debug specific test
```

### Sharding (for CI or parallel local runs)
```bash
npm run test:e2e:shard1            # Run shard 1/4
npm run test:e2e:shard2            # Run shard 2/4
npm run test:e2e:shard3            # Run shard 3/4
npm run test:e2e:shard4            # Run shard 4/4
```

## Viewing Reports

```bash
npm run test:e2e:report            # Open HTML report
npx playwright show-report         # Alternative command
npx playwright show-trace path/to/trace.zip  # View trace file
```

## Common Tasks

### Test Specific Functionality
```bash
# Test by grep pattern
npx playwright test -g "login"
npx playwright test -g "create tiger"
npx playwright test -g "upload image"

# Test specific file
npx playwright test e2e/auth-flow.spec.ts
```

### Run Tests with Different Settings
```bash
# Slow motion (helpful for watching tests)
npx playwright test --slow-mo=1000

# Specific browser
npx playwright test --project=chromium

# Multiple browsers
npx playwright test --project=chromium --project=firefox

# Update snapshots (for visual tests)
npm run test:e2e:visual:update
```

### Environment Variables
```bash
# Custom base URL
BASE_URL=http://localhost:3000 npm run test:e2e

# Custom API URL
API_URL=http://localhost:8080 npm run test:e2e

# Both
BASE_URL=http://staging.tiger-id.com API_URL=http://api.staging.tiger-id.com npm run test:e2e
```

## CI/CD Usage

### GitHub Actions
```yaml
# Single machine (no sharding)
- run: npx playwright test
  env:
    CI: true

# With sharding (4 parallel jobs)
strategy:
  matrix:
    shard: [1, 2, 3, 4]
steps:
  - run: npx playwright test --shard=${{ matrix.shard }}/4
    env:
      CI: true
```

### GitLab CI
```yaml
test:e2e:
  parallel: 4
  script:
    - npx playwright test --shard=${CI_NODE_INDEX}/${CI_NODE_TOTAL}
  variables:
    CI: "true"
```

## File Locations

```
frontend/
├── playwright.config.ts           # Main configuration
├── e2e/                           # Test files
│   ├── global.setup.ts            # Global setup (auth)
│   ├── global.teardown.ts         # Global teardown
│   ├── auth-flow.spec.ts          # Auth tests
│   ├── investigation-flow.spec.ts # Investigation tests
│   └── ...                        # Other test files
├── .auth/                         # Auth states (gitignored)
│   ├── admin.json
│   ├── analyst.json
│   └── viewer.json
├── test-results/                  # Test artifacts (gitignored)
│   ├── junit.xml                  # JUnit report (CI)
│   └── [test-artifacts]           # Screenshots, videos, traces
└── playwright-report/             # HTML report (gitignored)
    └── index.html                 # Open this in browser
```

## Troubleshooting

### Backend Not Available
```bash
# Start backend first
cd backend
uvicorn main:app --reload --port 8000

# Then run tests in another terminal
cd frontend
npm run test:e2e
```

### Authentication Fails
```bash
# Clear auth cache
rm -rf .auth/*

# Run tests again (will re-authenticate)
npm run test:e2e
```

### Tests Timeout
```bash
# Increase timeout for slow machines
PLAYWRIGHT_TIMEOUT=60000 npm run test:e2e
```

### View Failure Details
```bash
# After test failure, open HTML report
npm run test:e2e:report

# View trace file (most detailed)
npx playwright show-trace test-results/[test-name]/trace.zip
```

### Clean Start
```bash
# Remove all generated files
rm -rf .auth test-results playwright-report

# Run tests fresh
npm run test:e2e
```

## Configuration Details

### Timeouts
- **Test timeout**: 30 seconds per test
- **Action timeout**: 30 seconds per action (click, fill, etc.)
- **Assertion timeout**: 10 seconds per expect()
- **Navigation timeout**: 30 seconds for page loads

### Retries
- **Local**: 0 retries (fail fast)
- **CI**: 2 retries (3 total attempts)

### Workers
- **Local**: 50% of CPUs
- **CI**: 4 workers (matches shard count)

### Artifacts
- **Screenshots**: Captured on failure
- **Videos**: Captured on first retry only
- **Traces**: Captured on first retry only

## Best Practices

### Writing Tests
```typescript
import { test, expect } from '@playwright/test';

test('descriptive test name', async ({ page }) => {
  // Arrange: Setup test state
  await page.goto('/tigers');

  // Act: Perform action
  await page.getByRole('button', { name: 'Add Tiger' }).click();

  // Assert: Verify result
  await expect(page).toHaveURL(/\/tigers\/new/);
});
```

### Using Auth States
```typescript
// Use admin auth (default)
test.use({ storageState: '.auth/admin.json' });

// Use analyst auth
test.use({ storageState: '.auth/analyst.json' });

// Use viewer auth
test.use({ storageState: '.auth/viewer.json' });
```

### Waiting for Elements
```typescript
// Good: Use Playwright auto-waiting
await page.getByText('Tiger created').click();

// Good: Wait for specific state
await page.waitForLoadState('networkidle');

// Bad: Arbitrary wait
await page.waitForTimeout(5000);  // Avoid this!
```

## Help & Resources

- **Documentation**: `frontend/PLAYWRIGHT_CI_CONFIG.md`
- **Test examples**: `frontend/e2e/examples/`
- **Playwright docs**: https://playwright.dev
- **Report issues**: Check `test-results/` and `playwright-report/`

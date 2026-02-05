# Playwright Configuration Tests

Comprehensive unit tests for Playwright CI/CD configuration and global setup logic.

## Overview

These tests validate the Playwright configuration for CI/CD compatibility, ensuring proper sharding support, retry logic, and authentication setup.

## Test Files

### `playwright-config.test.ts`

Tests for `playwright.config.ts` configuration values and conditional logic.

**Coverage: 55 tests**

| Test Suite | Tests | Description |
|------------|-------|-------------|
| Browser Projects | 4 | Validates 3-browser setup (Chromium, Firefox, WebKit) with dependencies |
| Retry Configuration | 4 | Tests CI vs local retry logic (2 in CI, 0 local) |
| Worker Configuration | 3 | Validates parallel execution (4 workers CI, 50% local) |
| Timeout Configuration | 5 | Tests test, expect, action, and navigation timeouts (30s/10s) |
| Reporter Configuration | 6 | JUnit + HTML in CI, line + HTML locally |
| Screenshot/Video | 6 | Validates capture on failure and first retry only |
| Base URL | 3 | Tests environment variable override support |
| Global Setup/Teardown | 3 | Validates file references |
| Test Organization | 5 | Tests directory, parallel execution, forbidOnly in CI |
| Sharding Support | 3 | Validates 4-shard compatibility |
| Visual Regression | 2 | Tests snapshot comparison thresholds |
| Web Server | 5 | Validates dev server configuration |
| Device Configuration | 2 | Tests Playwright device presets |
| Project Dependencies | 2 | Validates setup project runs first |
| Auth State | 3 | Tests consistent auth state paths |

### `global-setup.test.ts`

Tests for `e2e/global.setup.ts` authentication and setup logic.

**Coverage: 43 tests**

| Test Suite | Tests | Description |
|------------|-------|-------------|
| Auth Directory | 2 | Validates .auth directory creation |
| Environment Variables | 4 | Tests BASE_URL and API_URL handling |
| Auth State Caching | 3 | Tests 1-hour cache logic |
| Token Verification | 5 | Tests localStorage, auth_token, sessionStorage detection |
| URL Verification | 4 | Tests post-login navigation detection |
| Storage State Paths | 4 | Validates admin/analyst/viewer auth paths |
| Error Screenshots | 3 | Tests error screenshot path generation |
| Health Check URLs | 3 | Validates backend health endpoint construction |
| HTTP Response Validation | 3 | Tests status code handling |
| Browser Configuration | 2 | Tests headless mode settings |
| Test Credentials | 3 | Validates user credential structure |
| Form Selectors | 3 | Tests flexible input selector strategy |
| Wait Strategies | 2 | Validates timeout values |
| API Endpoints | 2 | Tests endpoint URL construction |

## Running Tests

```bash
# Run all configuration tests
npm run test -- e2e/__tests__/ --run

# Run specific test file
npm run test -- e2e/__tests__/playwright-config.test.ts --run
npm run test -- e2e/__tests__/global-setup.test.ts --run

# Run with coverage
npm run test -- e2e/__tests__/ --coverage

# Watch mode for development
npm run test -- e2e/__tests__/ --watch
```

## Key Configuration Features Tested

### 1. **Sharding Support** ✅
- Supports `--shard=1/4` syntax
- 4 workers in CI match 4-shard configuration
- Tests distributed across multiple browser projects

### 2. **Retry Logic** ✅
- CI: 2 retries (3 total attempts)
- Local: 0 retries (1 attempt)
- Environment-aware configuration

### 3. **Browser Coverage** ✅
- Chromium (Chrome/Edge)
- Firefox
- WebKit (Safari)
- All share authenticated state from setup project

### 4. **Timeout Configuration** ✅
- Test timeout: 30 seconds
- Expect timeout: 10 seconds
- Action timeout: 30 seconds
- Navigation timeout: 30 seconds

### 5. **CI/CD Reporters** ✅
- CI: JUnit XML + HTML report + list
- Local: Line + HTML (opens on failure)
- JUnit output: `test-results/junit.xml`

### 6. **Artifact Capture** ✅
- Screenshots: Only on failure
- Videos: On first retry only
- Traces: On first retry only
- Optimized for storage efficiency

### 7. **Authentication Setup** ✅
- Global setup authenticates 3 users once
- Auth states cached for 1 hour
- States saved to `.auth/*.json`
- All tests start authenticated

### 8. **Base URL Configuration** ✅
- Default: `http://localhost:5173`
- Override via `BASE_URL` environment variable
- API URL: `http://localhost:8000` (or `API_URL` env var)

## Test Quality Metrics

- **Total Tests**: 98
- **Pass Rate**: 100%
- **Execution Time**: ~3 seconds
- **Coverage**: Configuration logic and setup flow

## Continuous Integration

These tests ensure the Playwright configuration works correctly in CI/CD pipelines:

```yaml
# Example CI configuration
- name: Run E2E tests (shard 1/4)
  run: npx playwright test --shard=1/4

- name: Run E2E tests (shard 2/4)
  run: npx playwright test --shard=2/4

- name: Run E2E tests (shard 3/4)
  run: npx playwright test --shard=3/4

- name: Run E2E tests (shard 4/4)
  run: npx playwright test --shard=4/4
```

## Error Handling

Global setup includes comprehensive error handling:

1. **Backend Availability Check**: Fails fast if API not running
2. **Authentication Verification**: Checks for tokens in multiple storage locations
3. **URL Verification**: Ensures successful navigation away from login
4. **Screenshot on Error**: Captures page state when authentication fails
5. **Cache Validation**: Reuses recent auth states to speed up test runs

## Environment Variables

Configuration supports the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CI` | `false` | Enables CI-specific settings (retries, workers, reporters) |
| `BASE_URL` | `http://localhost:5173` | Frontend application URL |
| `API_URL` | `http://localhost:8000` | Backend API URL |

## Best Practices

These tests validate adherence to Playwright best practices:

- ✅ Global setup for authentication (avoid repeated logins)
- ✅ Storage state reuse across tests
- ✅ Environment-aware configuration
- ✅ Optimized artifact capture (storage efficiency)
- ✅ Sharding support for parallel CI execution
- ✅ Flexible selectors for robustness
- ✅ Health checks before test execution
- ✅ Reasonable timeout values

## Maintenance

When updating configuration:

1. Update `playwright.config.ts` or `global.setup.ts`
2. Run configuration tests: `npm run test -- e2e/__tests__/ --run`
3. Verify all tests pass before committing
4. Update this README if adding new test coverage

## Related Documentation

- [Playwright Configuration](https://playwright.dev/docs/test-configuration)
- [Test Sharding](https://playwright.dev/docs/test-sharding)
- [Global Setup](https://playwright.dev/docs/test-global-setup-teardown)
- [CI Configuration](https://playwright.dev/docs/ci)

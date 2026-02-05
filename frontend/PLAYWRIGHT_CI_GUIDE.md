# Playwright CI/CD Configuration Guide

Complete guide for running Playwright E2E tests in CI/CD pipelines with sharding support.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration Overview](#configuration-overview)
- [Local Testing](#local-testing)
- [CI/CD Setup](#cicd-setup)
- [Sharding](#sharding)
- [Authentication](#authentication)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

```bash
# Install dependencies
npm ci

# Install Playwright browsers
npx playwright install --with-deps
```

### Run Tests Locally

```bash
# Run all tests
npm run test:e2e

# Run in UI mode (recommended for development)
npm run test:e2e:ui

# Run specific browser
npx playwright test --project=chromium

# Run specific test file
npx playwright test auth-flow

# Run in headed mode (see browser)
npm run test:e2e:headed
```

### Run with Sharding

```bash
# Sequential execution (all 4 shards)
npm run test:e2e:sharded

# Parallel execution (faster)
npm run test:e2e:sharded:parallel

# Run specific shard manually
npm run test:e2e:shard2
```

## Configuration Overview

### `playwright.config.ts` Features

| Feature | CI Value | Local Value | Description |
|---------|----------|-------------|-------------|
| **Retries** | 2 | 0 | Retry failed tests in CI |
| **Workers** | 1 | CPU count | Parallel execution |
| **Timeout** | 30s | 30s | Per-test timeout |
| **Expect Timeout** | 10s | 10s | Assertion timeout |
| **Screenshots** | On failure | On failure | Capture screenshots |
| **Video** | First retry | First retry | Record video |
| **Trace** | First retry | First retry | Collect trace |
| **Reporter** | JUnit + HTML | Line + HTML | Test reporting |

### Environment Variables

Create `.env` file in `frontend/` directory:

```bash
# Base URL for tests (optional)
BASE_URL=http://localhost:5173

# Backend API URL (optional)
API_URL=http://localhost:8000

# Test user credentials (recommended)
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=password123

# CI mode (set automatically in CI environments)
CI=true
```

## Local Testing

### Running Tests

```bash
# Run all tests
npm run test:e2e

# Run with UI mode (interactive debugging)
npm run test:e2e:ui

# Run specific test suite
npm run test:e2e:auth          # Authentication tests
npm run test:e2e:investigation # Investigation workflow
npm run test:e2e:tiger         # Tiger management
npm run test:e2e:facility      # Facility management
npm run test:e2e:verification  # Verification queue
npm run test:e2e:discovery     # Discovery pipeline

# Run specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# Debug specific test
npx playwright test auth-flow --debug

# Run in headed mode
npm run test:e2e:headed
```

### Viewing Reports

```bash
# Generate and view HTML report
npm run test:e2e:report

# View specific trace
npx playwright show-trace test-results/trace.zip
```

### Running Sharded Tests Locally

```bash
# Sequential execution (one shard after another)
npm run test:e2e:sharded

# Parallel execution (all shards at once)
npm run test:e2e:sharded:parallel

# Run specific shard
npm run test:e2e:shard1   # Shard 1/4
npm run test:e2e:shard2   # Shard 2/4
npm run test:e2e:shard3   # Shard 3/4
npm run test:e2e:shard4   # Shard 4/4

# Or use the helper script
node run-sharded-tests.js --shard=2/4
```

## CI/CD Setup

### GitHub Actions

Create `.github/workflows/e2e-tests.yml`:

```yaml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    timeout-minutes: 60
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        shardIndex: [1, 2, 3, 4]
        shardTotal: [4]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 18
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci
        working-directory: ./frontend

      - name: Install Playwright
        run: npx playwright install --with-deps
        working-directory: ./frontend

      - name: Run tests
        run: npx playwright test --shard=${{ matrix.shardIndex }}/${{ matrix.shardTotal }}
        working-directory: ./frontend
        env:
          CI: true
          BASE_URL: http://localhost:5173
          API_URL: http://localhost:8000

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: blob-report-${{ matrix.shardIndex }}
          path: frontend/blob-report/
          retention-days: 1

  merge-reports:
    if: always()
    needs: [test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci
        working-directory: ./frontend

      - name: Download reports
        uses: actions/download-artifact@v4
        with:
          path: frontend/all-blob-reports
          pattern: blob-report-*
          merge-multiple: true

      - name: Merge reports
        run: npx playwright merge-reports --reporter html ./all-blob-reports
        working-directory: ./frontend

      - uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 30
```

### GitLab CI

Create `.gitlab-ci.yml`:

```yaml
e2e-tests:
  stage: test
  image: mcr.microsoft.com/playwright:v1.40.0-focal
  parallel: 4
  script:
    - cd frontend
    - npm ci
    - npx playwright test --shard=$CI_NODE_INDEX/$CI_NODE_TOTAL
  artifacts:
    when: always
    paths:
      - frontend/playwright-report/
      - frontend/test-results/
    reports:
      junit: frontend/test-results/junit.xml
  only:
    - main
    - merge_requests
```

### CircleCI

Create `.circleci/config.yml`:

```yaml
version: 2.1

jobs:
  e2e-tests:
    docker:
      - image: mcr.microsoft.com/playwright:v1.40.0-focal
    parallelism: 4
    steps:
      - checkout
      - restore_cache:
          keys:
            - v1-deps-{{ checksum "frontend/package-lock.json" }}
      - run:
          name: Install dependencies
          command: cd frontend && npm ci
      - save_cache:
          key: v1-deps-{{ checksum "frontend/package-lock.json" }}
          paths:
            - frontend/node_modules
      - run:
          name: Run tests
          command: |
            cd frontend
            SHARD="$((${CIRCLE_NODE_INDEX} + 1))/${CIRCLE_NODE_TOTAL}"
            npx playwright test --shard=$SHARD
      - store_artifacts:
          path: frontend/playwright-report
      - store_test_results:
          path: frontend/test-results

workflows:
  version: 2
  test:
    jobs:
      - e2e-tests
```

### Jenkins

```groovy
pipeline {
    agent any

    stages {
        stage('E2E Tests') {
            parallel {
                stage('Shard 1/4') {
                    steps {
                        sh 'cd frontend && npm ci'
                        sh 'cd frontend && npx playwright install --with-deps'
                        sh 'cd frontend && npx playwright test --shard=1/4'
                    }
                }
                stage('Shard 2/4') {
                    steps {
                        sh 'cd frontend && npm ci'
                        sh 'cd frontend && npx playwright install --with-deps'
                        sh 'cd frontend && npx playwright test --shard=2/4'
                    }
                }
                stage('Shard 3/4') {
                    steps {
                        sh 'cd frontend && npm ci'
                        sh 'cd frontend && npx playwright install --with-deps'
                        sh 'cd frontend && npx playwright test --shard=3/4'
                    }
                }
                stage('Shard 4/4') {
                    steps {
                        sh 'cd frontend && npm ci'
                        sh 'cd frontend && npx playwright install --with-deps'
                        sh 'cd frontend && npx playwright test --shard=4/4'
                    }
                }
            }
        }
    }

    post {
        always {
            publishHTML([
                reportDir: 'frontend/playwright-report',
                reportFiles: 'index.html',
                reportName: 'Playwright Report'
            ])
            archiveArtifacts artifacts: 'frontend/test-results/**/*', allowEmptyArchive: true
        }
    }
}
```

## Sharding

Sharding splits tests across multiple machines for parallel execution.

### How Sharding Works

1. **Test Distribution**: Playwright splits test files into N groups
2. **Parallel Execution**: Each shard runs independently on separate machines
3. **Report Merging**: Results are merged into single HTML report

### Benefits

- **Faster Execution**: 4 shards = ~4x faster
- **Resource Efficiency**: Distribute load across machines
- **Cost Optimization**: Reduce CI/CD pipeline time

### Shard Count Recommendations

| Total Tests | Recommended Shards | Execution Time (approx) |
|-------------|-------------------|-------------------------|
| < 50 tests | 1-2 shards | 5-10 minutes |
| 50-100 tests | 2-4 shards | 10-20 minutes |
| 100-200 tests | 4-6 shards | 15-30 minutes |
| > 200 tests | 6-8 shards | 20-40 minutes |

### Manual Sharding

```bash
# Run shard 1 of 4
npx playwright test --shard=1/4

# Run shard 2 of 4
npx playwright test --shard=2/4

# Run shard 3 of 4
npx playwright test --shard=3/4

# Run shard 4 of 4
npx playwright test --shard=4/4
```

### Merging Shard Reports

```bash
# After all shards complete, merge reports
npx playwright merge-reports --reporter html ./all-blob-reports

# View merged report
npx playwright show-report
```

## Authentication

### Global Setup

Tests use global setup to authenticate once before all tests:

1. `global.setup.ts` - Authenticates and saves state
2. `.auth/user.json` - Stores authenticated session
3. All tests reuse this session (no repeated logins)

### Test Credentials

Set credentials via environment variables or `.env`:

```bash
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=password123
```

### CI Secrets

Store credentials as CI secrets:

**GitHub Actions:**
```yaml
env:
  TEST_USER_EMAIL: ${{ secrets.TEST_USER_EMAIL }}
  TEST_USER_PASSWORD: ${{ secrets.TEST_USER_PASSWORD }}
```

**GitLab CI:**
```yaml
variables:
  TEST_USER_EMAIL: $TEST_USER_EMAIL
  TEST_USER_PASSWORD: $TEST_USER_PASSWORD
```

## Troubleshooting

### Tests Timeout

**Problem**: Tests fail with timeout errors

**Solutions**:
```typescript
// Increase timeout in specific test
test('slow test', async ({ page }) => {
  test.setTimeout(60000); // 60 seconds
  // test code
});

// Increase timeout in config
timeout: 60000, // in playwright.config.ts
```

### Authentication Fails

**Problem**: Global setup cannot authenticate

**Solutions**:
1. Verify test credentials exist in database
2. Check `BASE_URL` and `API_URL` are correct
3. Ensure backend is running before tests
4. Check authentication endpoint is accessible

### Flaky Tests

**Problem**: Tests pass/fail inconsistently

**Solutions**:
```typescript
// Add proper waits
await page.waitForSelector('[data-testid="results"]');

// Use auto-waiting assertions
await expect(page.locator('[data-testid="results"]')).toBeVisible();

// Avoid hard timeouts
// BAD: await page.waitForTimeout(5000);
// GOOD: await page.waitForSelector('[data-testid="results"]');
```

### Sharding Issues

**Problem**: Some shards fail, others pass

**Solutions**:
1. Check for test interdependencies
2. Ensure tests are isolated
3. Verify test data is not shared between shards
4. Check for race conditions in parallel execution

### Screenshot/Video Not Captured

**Problem**: No artifacts generated on failure

**Solutions**:
1. Verify `outputDir` exists: `test-results/`
2. Check CI artifact upload configuration
3. Ensure `screenshot: 'only-on-failure'` in config
4. Verify `video: 'retain-on-failure'` in config

### Report Not Merging

**Problem**: Cannot merge sharded reports

**Solutions**:
```bash
# Ensure blob-report mode is enabled
npx playwright test --reporter=blob

# Check all shard reports exist
ls -la all-blob-reports/

# Merge with verbose output
npx playwright merge-reports --reporter html ./all-blob-reports
```

## Best Practices

### 1. Use Data Test IDs

```typescript
// Good
await page.locator('[data-testid="submit-button"]').click();

// Bad (brittle)
await page.locator('.btn.btn-primary').click();
```

### 2. Wait for Elements

```typescript
// Good
await page.waitForSelector('[data-testid="results"]');
await expect(page.locator('[data-testid="results"]')).toBeVisible();

// Bad
await page.waitForTimeout(5000);
```

### 3. Keep Tests Independent

```typescript
// Each test should set up its own state
test('create tiger', async ({ page }) => {
  await page.goto('/tigers/new');
  // test code
});

// Don't rely on previous test state
```

### 4. Clean Up After Tests

```typescript
test.afterEach(async ({ page }) => {
  // Clean up test data
  await page.request.delete('/api/test-data');
});
```

### 5. Use Page Object Model

```typescript
// Good: Encapsulate page interactions
class TigerListPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/tigers');
  }

  async searchTiger(name: string) {
    await this.page.fill('[data-testid="search"]', name);
  }
}
```

## Additional Resources

- [Playwright Documentation](https://playwright.dev)
- [Playwright CI Guide](https://playwright.dev/docs/ci)
- [Playwright Sharding](https://playwright.dev/docs/test-sharding)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)

## Support

For issues or questions:
1. Check logs in `test-results/` directory
2. View HTML report: `npm run test:e2e:report`
3. Run with `--debug` flag for step-by-step execution
4. Check CI/CD pipeline logs for detailed error messages

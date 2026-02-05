# Tiger ID E2E Test Suite

Comprehensive Playwright end-to-end tests for the Tiger ID application.

## Test Suites

### 1. Authentication Flow (`auth-flow.spec.ts`)
Tests user authentication and authorization flows:
- Login page display and validation
- Invalid credential handling
- Successful login and token storage
- Protected route access control
- Logout functionality
- Session persistence across reloads

**Key Tests:**
- `should display login page with correct elements`
- `should successfully login with valid credentials and store token`
- `should redirect to login when accessing protected route without auth`
- `should logout successfully and clear token`

### 2. Investigation Flow (`investigation-flow.spec.ts`)
Tests the Investigation 2.0 workflow:
- File upload and validation
- 6-phase investigation workflow tracking
- WebSocket real-time updates
- Results display and confidence scores
- Ensemble visualization
- Report generation and download
- Error handling

**Key Tests:**
- `should display Investigation 2.0 page with upload capability`
- `should show investigation phases during processing`
- `should handle WebSocket connection for real-time updates`
- `should display investigation results after completion`

### 3. Tiger Management (`tiger-management.spec.ts`)
Tests tiger database management:
- Tiger list display
- Search and filter functionality
- Pagination
- Tiger detail page navigation
- Image display
- Metadata and history
- New tiger registration

**Key Tests:**
- `should display tigers list page`
- `should navigate to tiger detail page when clicking a tiger`
- `should have upload functionality for new tigers`
- `should show tiger identification history`

### 3a. Tiger Detail Page (`tests/tigers/tiger-detail.spec.ts`)
Comprehensive tests for individual tiger detail pages:
- Tiger information display (name, ID, status, metadata)
- Image gallery functionality and lightbox navigation
- Image quality indicators and badges
- Identification timeline with events and timestamps
- Related investigations panel and navigation
- Edit tiger functionality (name, notes)
- Delete tiger with confirmation
- Facility navigation and links
- Quick actions (launch investigation, back to list)
- Error handling for non-existent tigers

**Key Tests:**
- `should display tiger detail page with basic information`
- `should display tiger image gallery`
- `should open lightbox when clicking image`
- `should display identification timeline section`
- `should show investigations involving this tiger`
- `should navigate to investigation detail when clicking investigation`
- `should enable editing mode when clicking edit`
- `should show confirmation dialog when deleting tiger`
- `should navigate to facility detail when clicking facility link`

### 4. Facility Management (`facility-management.spec.ts`)
Tests facility database management:
- Facility list display
- Search and location filtering
- Map visualization (Leaflet)
- Associated tigers display
- Facility detail pages
- Discovery status tracking
- Contact information display

**Key Tests:**
- `should display facilities list page`
- `should show facility location on map`
- `should display tigers associated with facility`
- `should display facility discovery status`

### 4b. Facility Detail Page (`tests/facilities/facility-detail.spec.ts`)
Comprehensive tests for the Facility Detail page:
- Page loading and facility information display
- Map visualization with facility location
- Crawl history timeline with event details
- Tiger gallery with view modes and grouping
- Edit functionality and manual crawl triggers
- Discovery status monitoring
- Navigation and error handling
- Mobile-responsive design

**Key Tests:**
- `should display facility detail page with complete information`
- `should display crawl history timeline for facility`
- `should display tiger gallery for facility`
- `should allow triggering manual crawl for facility`
- `should display discovery status for facility`

See `tests/facilities/README.md` for detailed documentation.

### 5. Verification Queue (`verification-flow.spec.ts`)
Tests the verification workflow:
- Queue display and statistics
- Filtering by status and confidence
- Match comparison visualization
- Approve/reject actions
- Ensemble model results
- Stripe pattern comparison
- Bulk actions

**Key Tests:**
- `should show verification statistics`
- `should filter verification items by status`
- `should approve a verification item`
- `should display ensemble model results`

### 6. Discovery Pipeline (`discovery-flow.spec.ts`)
Tests the automated discovery system:
- Pipeline status monitoring
- Start/stop controls
- Facility monitoring list
- Crawl history and timeline
- Rate limiting information
- Deduplication statistics
- Browser automation status
- Schedule configuration

**Key Tests:**
- `should show discovery pipeline status`
- `should have start discovery button`
- `should show crawl history/timeline`
- `should display deduplication statistics`

### 7. Visual Regression Tests (`visual.spec.ts`)
Tests visual consistency across the application using Playwright screenshots:
- Authentication pages (login, password reset)
- Dashboard layouts (light/dark mode)
- Tiger management pages
- Investigation workflows
- Discovery pipeline
- Facility management
- Verification queue
- Template management
- Component states (empty, error, loading, modal)
- Responsive layouts (desktop, tablet, mobile)
- Badge and card variations

**Key Tests:**
- `login page - light mode - desktop`
- `dashboard - full layout - dark mode`
- `tigers list - grid view - light mode`
- `investigation - upload state - dark mode`
- `empty state - dark mode`
- `error state - with details expanded`
- `modal - light mode`
- `responsive layouts - tablet/mobile`

**Full Documentation:** See [VISUAL_REGRESSION_TESTING.md](./VISUAL_REGRESSION_TESTING.md) for complete guide.

## Running Tests

### Run all tests
```bash
npm run test:e2e
```

### Run specific test suite
```bash
npx playwright test auth-flow
npx playwright test investigation-flow
npx playwright test tiger-management
npx playwright test tests/tigers/tiger-detail
npx playwright test facility-management
npx playwright test verification-flow
npx playwright test discovery-flow
npx playwright test visual
npx playwright test accessibility
```

### Run visual regression tests
```bash
# Run all visual tests
npm run test:e2e:visual

# Update baseline snapshots
npm run test:e2e:visual:update

# Run visual tests in UI mode
npm run test:e2e:visual:ui

# Run specific visual test
npx playwright test visual -g "login page"
```

### Run tests in headed mode (see browser)
```bash
npx playwright test --headed
```

### Run tests in specific browser
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### Run tests in UI mode (interactive)
```bash
npx playwright test --ui
```

### Run tests and generate report
```bash
npx playwright test
npx playwright show-report
```

### Run tests with sharding (parallel execution across multiple machines)
```bash
# Machine 1: Run shard 1 of 4
npx playwright test --shard=1/4

# Machine 2: Run shard 2 of 4
npx playwright test --shard=2/4

# Machine 3: Run shard 3 of 4
npx playwright test --shard=3/4

# Machine 4: Run shard 4 of 4
npx playwright test --shard=4/4
```

### Merge sharded reports
```bash
# After running sharded tests, merge the results
npx playwright merge-reports --reporter html ./all-blob-reports
```

## Test Configuration

Configuration is in `playwright.config.ts`:
- **Base URL**: Configurable via `BASE_URL` env var (default: http://localhost:5173)
- **Browsers**: Chromium, Firefox, WebKit
- **Parallel execution**: Enabled (1 worker in CI, all CPUs locally)
- **Retries**: 2 in CI, 0 locally
- **Timeouts**: 30s test timeout, 10s expect timeout
- **Trace**: On first retry only
- **Screenshots**: On failure only
- **Video**: On first retry only (retained on failure)
- **Reporters**:
  - **CI**: JUnit XML + HTML + list
  - **Local**: Line + HTML (opens on failure)
- **Web server**: Auto-starts dev server
- **Global setup**: `global.setup.ts` - Creates authenticated state before all tests
- **Auth setup**: `auth.setup.ts` - Logs in once and saves state to `.auth/user.json`

### Environment Variables

```bash
# Base URL for tests (default: http://localhost:5173)
BASE_URL=http://localhost:5173

# Backend API URL (default: http://localhost:8000)
API_URL=http://localhost:8000

# Test user credentials
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=password123

# CI mode (enables retries and optimizations)
CI=true
```

## Test Helpers

### Authentication Helper (`helpers/auth.ts`)
Provides reusable authentication functions:
- `login(page, username, password)` - Login to application
- `logout(page)` - Logout from application
- `isAuthenticated(page)` - Check authentication status
- `clearAuth(page)` - Clear authentication state

Usage:
```typescript
import { login, logout } from './helpers/auth'

test('my test', async ({ page }) => {
  await login(page)
  // ... test code ...
  await logout(page)
})
```

## Test Fixtures

Test fixtures are in `fixtures/`:
- `test.txt` - Sample text file for invalid file type testing
- `test-tiger.jpg` - Sample tiger image (add manually)
- `test-tiger-2.jpg` - Second tiger image (add manually)

## Best Practices

1. **Use data-testid attributes** for reliable selectors
2. **Use waitForTimeout sparingly** - prefer waiting for specific elements
3. **Clean up after tests** - logout, clear state
4. **Make tests independent** - don't rely on test execution order
5. **Use Page Object Model** for complex pages (future enhancement)
6. **Mock external services** when possible to avoid flakiness
7. **Test error states** not just happy paths

## Debugging

### Debug specific test
```bash
npx playwright test auth-flow --debug
```

### View test trace
```bash
npx playwright show-trace trace.zip
```

### Take screenshots on failure
Tests automatically capture screenshots on failure in `test-results/`

## CI/CD Integration

### Basic CI Configuration

Tests are optimized for CI with:
- **Retries**: 2 attempts per test
- **Workers**: Sequential execution (workers: 1) for stability
- **Reporters**: JUnit XML + HTML report + list output
- **Artifacts**: Screenshots, videos, traces on failure
- **Web server**: Automatic startup and teardown

### GitHub Actions Example

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
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci
        working-directory: ./frontend

      - name: Install Playwright Browsers
        run: npx playwright install --with-deps
        working-directory: ./frontend

      - name: Run Playwright tests
        run: npx playwright test
        working-directory: ./frontend
        env:
          CI: true
          BASE_URL: http://localhost:5173
          API_URL: http://localhost:8000

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 30

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: frontend/test-results/
          retention-days: 30
```

### Sharded CI Configuration (Parallel Execution)

Run tests across 4 parallel jobs for faster execution:

```yaml
name: E2E Tests (Sharded)

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

      - name: Install dependencies
        run: npm ci
        working-directory: ./frontend

      - name: Install Playwright Browsers
        run: npx playwright install --with-deps
        working-directory: ./frontend

      - name: Run Playwright tests
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

      - name: Download blob reports from artifacts
        uses: actions/download-artifact@v4
        with:
          path: frontend/all-blob-reports
          pattern: blob-report-*
          merge-multiple: true

      - name: Merge into HTML Report
        run: npx playwright merge-reports --reporter html ./all-blob-reports
        working-directory: ./frontend

      - uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 30
```

### GitLab CI Example

```yaml
e2e-tests:
  stage: test
  image: mcr.microsoft.com/playwright:v1.40.0-focal
  script:
    - cd frontend
    - npm ci
    - npx playwright test
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

### CircleCI Example

```yaml
version: 2.1

jobs:
  e2e-tests:
    docker:
      - image: mcr.microsoft.com/playwright:v1.40.0-focal
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
          name: Run E2E tests
          command: cd frontend && npx playwright test
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

### 7. Accessibility Tests (`tests/accessibility/accessibility.spec.ts`)
Tests WCAG 2.0/2.1 Level A and AA compliance using axe-core:
- Color contrast requirements
- Form labels and validation
- Keyboard navigation
- Screen reader compatibility
- Modal focus trapping
- Image alt text
- Semantic HTML structure
- ARIA attributes

**Key Tests:**
- `should not have accessibility violations` (for each page)
- `should have proper ARIA labels and focus trapping` (modals)
- `should meet color contrast requirements`
- `Generate accessibility report for all critical pages`

See `tests/accessibility/README.md` for detailed documentation.

## Future Enhancements

- [x] Add visual regression testing with Playwright snapshots
- [ ] Implement Page Object Model for complex workflows
- [ ] Add API mocking with MSW (Mock Service Worker)
- [ ] Add performance testing with Lighthouse
- [x] Add accessibility testing with axe-core
- [ ] Add database seeding for consistent test data
- [x] Add cross-browser screenshot comparisons
- [ ] Implement test data factories
- [ ] Integrate Percy or Chromatic for cloud-based visual regression
- [ ] Add visual regression tests to CI/CD pipeline
- [ ] Create visual regression baselines per environment

## Troubleshooting

### Tests failing with "Timeout"
- Increase timeout in test: `test.setTimeout(60000)`
- Check if dev server is running
- Verify backend API is accessible

### Tests failing with "Element not found"
- Add `await page.waitForSelector()` before interacting
- Use more specific selectors
- Check if element is in shadow DOM

### Authentication tests failing
- Verify test credentials exist in database
- Check if auth token is properly stored
- Ensure CORS is configured for localhost

### Flaky tests
- Add proper waits instead of `waitForTimeout`
- Ensure test data is isolated
- Check for race conditions in async operations

### 7. Dashboard (`tests/dashboard/dashboard.spec.ts`)
Tests the main dashboard page:
- Page load with all sections
- Quick stats grid (tigers, facilities, ID rate, pending verifications)
- Stats with trend indicators
- Time range selector (7d/30d/90d buttons)
- Refresh button functionality
- Subagent activity panel and pool utilization
- Recent investigations table
- Investigation row click navigation
- Geographic map visualization
- Analytics tabs (7 tabs: Investigations, Evidence & Verification, Geographic, Tigers, Facilities, Agent Performance, Model Performance)
- Charts rendering (line charts, pie charts, bar charts)
- Responsive behavior (mobile/tablet/desktop)
- Navigation from stat cards
- Error handling and empty states

**Key Tests:**
- should display dashboard page with all sections
- should display quick stats grid with all stat cards
- should change time range when clicking buttons
- should refresh data when clicking refresh button
- should display subagent activity panel
- should navigate to investigation when clicking row
- should display geographic map card
- should switch between analytics tabs
- should render line chart without errors
- should display model performance tab content

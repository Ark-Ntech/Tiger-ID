# Running Visual Regression Tests

Quick guide to running visual regression tests for the Tiger ID application.

## Prerequisites

```bash
# Install dependencies (if not already done)
cd frontend
npm install

# Install Playwright browsers
npx playwright install --with-deps
```

## Quick Start

### Run All Visual Tests
```bash
npm run test:e2e:visual
```

### Run in Interactive UI Mode
```bash
npm run test:e2e:visual:ui
```

### Run with Visible Browser
```bash
npm run test:e2e:visual:headed
```

### Update Baseline Snapshots
```bash
npm run test:e2e:visual:update
```

## Step-by-Step: First Time Setup

### 1. Generate Initial Baselines

First time running visual tests? Generate baseline snapshots:

```bash
# Make sure backend and frontend are running
cd backend
uvicorn main:app --reload --port 8000

# In another terminal, start frontend
cd frontend
npm run dev

# In a third terminal, generate baselines
cd frontend
npm run test:e2e:visual:update
```

This will:
- Run all 87+ visual tests
- Capture screenshots of each page/component
- Save baselines to `e2e/tests/visual/__snapshots__/`
- Take about 3-5 minutes

### 2. Verify Baselines Generated

Check that snapshots were created:

```bash
ls e2e/tests/visual/__snapshots__/
```

You should see files like:
- `login-light-desktop.png`
- `dashboard-dark.png`
- `tigers-list-light.png`
- etc.

### 3. Run Tests Against Baselines

Now run tests to compare current UI against baselines:

```bash
npm run test:e2e:visual
```

All tests should pass (green) if UI hasn't changed.

## Common Workflows

### Workflow 1: Checking for Visual Regressions

**Use Case:** Before merging a PR, verify no unintended visual changes.

```bash
# 1. Checkout the PR branch
git checkout feature-branch

# 2. Run visual tests
npm run test:e2e:visual

# 3. Review results
npm run test:e2e:report
```

If tests fail:
- Open `playwright-report/index.html` in browser
- Review screenshots showing differences
- If changes are unintended, fix the CSS/component
- If changes are intentional, update baselines (see Workflow 2)

### Workflow 2: Updating Baselines After UI Changes

**Use Case:** You made intentional UI changes and need to update baselines.

```bash
# 1. Make your UI changes
# ... edit components, CSS, etc. ...

# 2. Update affected baselines
npm run test:e2e:visual:update

# 3. Review the changes
git diff e2e/tests/visual/__snapshots__/

# 4. If changes look good, commit them
git add e2e/tests/visual/__snapshots__/
git commit -m "Update visual regression baselines for [component]"
```

### Workflow 3: Adding New Visual Tests

**Use Case:** You added a new page/component and want to add visual tests.

```bash
# 1. Edit visual.spec.ts to add new test
code e2e/tests/visual/visual.spec.ts

# 2. Add your test following existing patterns:
test('new-page - light mode', async ({ page }) => {
  await page.setViewportSize(VIEWPORTS.desktop)
  await page.goto('/new-page')
  await waitForPageLoad(page)

  const screenshot = await page.screenshot({
    path: 'screenshots/visual/new-page/new-page-light.png',
    fullPage: true
  })
  expect(screenshot).toMatchSnapshot('new-page-light.png')
})

# 3. Generate baseline for new test
npm run test:e2e:visual:update -- -g "new-page"

# 4. Verify test passes
npm run test:e2e:visual -- -g "new-page"

# 5. Commit
git add e2e/tests/visual/
git commit -m "Add visual regression test for new page"
```

### Workflow 4: Debugging Failed Visual Tests

**Use Case:** Tests are failing and you need to understand why.

```bash
# 1. Run failing test in UI mode
npm run test:e2e:visual:ui

# 2. Or run specific test in headed mode
npx playwright test tests/visual -g "failing test name" --headed

# 3. Or run with debug inspector
npx playwright test tests/visual -g "failing test name" --debug

# 4. View detailed report
npm run test:e2e:report
```

In the UI mode:
- Click on failed test
- View side-by-side comparison of expected vs actual
- See pixel difference overlay
- Review trace timeline

### Workflow 5: Testing Specific Component

**Use Case:** You changed a specific component and want to test only related visuals.

```bash
# Test only dashboard
npm run test:e2e:visual -- -g "Dashboard"

# Test only authentication pages
npm run test:e2e:visual -- -g "Authentication"

# Test only tiger management
npm run test:e2e:visual -- -g "Tigers"

# Test only dark mode
npm run test:e2e:visual -- -g "dark mode"

# Test only mobile views
npm run test:e2e:visual -- -g "mobile"
```

### Workflow 6: Testing Before Release

**Use Case:** Final visual check before production release.

```bash
# 1. Run full visual suite on all browsers
npm run test:e2e:visual

# 2. Generate comprehensive report
npm run test:e2e:report

# 3. Review all screenshots in screenshots/visual/
open screenshots/visual/

# 4. Check for any unexpected differences
# Review test-results/ if any tests failed

# 5. Sign off on visual consistency
```

## Test Organization

### By Feature
```bash
# Authentication
npx playwright test tests/visual -g "Authentication"

# Dashboard & Analytics
npx playwright test tests/visual -g "Dashboard"

# Tiger Management
npx playwright test tests/visual -g "Tigers"

# Investigation Workflows
npx playwright test tests/visual -g "Investigation"

# Discovery Pipeline
npx playwright test tests/visual -g "Discovery"

# Facilities
npx playwright test tests/visual -g "Facilities"

# Verification Queue
npx playwright test tests/visual -g "Verification"

# Templates
npx playwright test tests/visual -g "Templates"
```

### By Component Type
```bash
# All empty states
npx playwright test tests/visual -g "Empty State"

# All error states
npx playwright test tests/visual -g "Error State"

# All modals
npx playwright test tests/visual -g "Modal"

# All loading states
npx playwright test tests/visual -g "Loading"

# All badges
npx playwright test tests/visual -g "Badge"

# All cards
npx playwright test tests/visual -g "Card"
```

### By Theme
```bash
# All light mode tests
npx playwright test tests/visual -g "light mode"

# All dark mode tests
npx playwright test tests/visual -g "dark mode"
```

### By Viewport
```bash
# All desktop tests
npx playwright test tests/visual -g "desktop"

# All tablet tests
npx playwright test tests/visual -g "tablet"

# All mobile tests
npx playwright test tests/visual -g "mobile"

# All responsive tests
npx playwright test tests/visual -g "Responsive"
```

## Understanding Test Results

### Test Passes (Green ✓)
```
✓ tests/visual/visual.spec.ts:67 › login page - light mode - desktop
```
- Screenshot matches baseline
- No visual changes detected
- All good!

### Test Fails (Red ✗)
```
✗ tests/visual/visual.spec.ts:67 › login page - light mode - desktop
  Error: Screenshot comparison failed:
  1234 pixels (ratio 0.012 of all image pixels) are different.
```
- Screenshot doesn't match baseline
- Visual changes detected
- Review diff in report

### Where to Find Results

1. **Console Output**: Basic pass/fail info
2. **HTML Report**: `playwright-report/index.html`
   - Side-by-side comparisons
   - Pixel difference overlays
   - Test timeline
3. **Screenshots**: `screenshots/visual/`
   - Organized by feature
   - Latest screenshots from test run
4. **Test Results**: `test-results/`
   - Diff images showing differences
   - Trace files for debugging
5. **Baselines**: `e2e/tests/visual/__snapshots__/`
   - Expected screenshots

## Troubleshooting

### "Screenshot comparison failed"

**Problem:** Test fails with pixel differences.

**Solution:**
1. View report: `npm run test:e2e:report`
2. Check if change is intentional
3. If yes: `npm run test:e2e:visual:update`
4. If no: Fix the CSS/component

### "Timeout waiting for page load"

**Problem:** Test times out during `waitForPageLoad()`.

**Solution:**
1. Check if backend is running
2. Check if frontend is running
3. Increase timeout in test
4. Check network tab for failed requests

### "Element not found"

**Problem:** Test can't find element to screenshot.

**Solution:**
1. Check if element exists on page
2. Verify data-testid or selector
3. Add wait before checking element
4. Run in headed mode to see page

### "Images not loading"

**Problem:** Screenshots show missing images.

**Solution:**
1. Use `waitForImages(page)` helper
2. Increase wait timeout
3. Check image URLs are correct
4. Verify backend serves images

### "Dark mode not working"

**Problem:** Dark mode toggle doesn't change UI.

**Solution:**
1. Verify TailwindCSS config has `darkMode: 'class'`
2. Check CSS uses `dark:` prefixes
3. Increase wait after toggle
4. View in headed mode to debug

### "Tests flaky/inconsistent"

**Problem:** Tests pass sometimes, fail others.

**Solution:**
1. Hide dynamic content with `hideTimestamps()`
2. Mask dynamic IDs with `maskDynamicIds()`
3. Increase wait times for animations
4. Use `waitForImages()` for image-heavy pages
5. Increase threshold in playwright.config.ts

## Environment Setup

### Required Services

Make sure these are running before tests:

```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Environment Variables

No special environment variables needed for visual tests. They use:
- `BASE_URL`: http://localhost:5173 (from playwright.config.ts)
- `API_URL`: http://localhost:8000 (from playwright.config.ts)

### Browser Configuration

Tests run on:
- ✓ Chromium (primary)
- ✓ Firefox
- ✓ WebKit (Safari)

To run on specific browser:
```bash
npx playwright test tests/visual --project=chromium
npx playwright test tests/visual --project=firefox
npx playwright test tests/visual --project=webkit
```

## Performance

### Test Duration

Full visual suite:
- **Development**: ~3-5 minutes (1 browser)
- **CI**: ~8-12 minutes (3 browsers)
- **Single test**: ~3-10 seconds

### Optimization Tips

Speed up test runs:
```bash
# Run only on Chromium
npx playwright test tests/visual --project=chromium

# Run specific suite
npx playwright test tests/visual -g "Dashboard"

# Run in parallel (faster on multi-core machines)
npx playwright test tests/visual --workers=4
```

## CI/CD Integration

### GitHub Actions

Tests run automatically on PRs:
- Triggered on push to main/develop
- Run on all 3 browsers
- Artifacts uploaded on failure

View results:
1. Go to PR → Actions tab
2. Click on workflow run
3. Download artifacts:
   - `playwright-report`
   - `test-results`

### Updating Baselines in CI

If tests fail in CI and changes are intentional:
```bash
# Checkout PR branch locally
git checkout pr-branch

# Update baselines
npm run test:e2e:visual:update

# Commit and push
git add e2e/tests/visual/__snapshots__/
git commit -m "Update visual baselines"
git push
```

## Resources

- [Full Documentation](./README.md) - Complete guide
- [Quick Reference](./QUICK_REFERENCE.md) - Command cheat sheet
- [Main E2E README](../README.md) - E2E testing overview
- [Playwright Docs](https://playwright.dev/docs/test-snapshots) - Official docs

## Getting Help

If you need help:
1. Check [Troubleshooting](#troubleshooting) section
2. Review [Quick Reference](./QUICK_REFERENCE.md)
3. Read [Full Documentation](./README.md)
4. Open issue in project repository

---

**Quick Commands Summary:**

```bash
# Run tests
npm run test:e2e:visual

# Update baselines
npm run test:e2e:visual:update

# Interactive UI
npm run test:e2e:visual:ui

# View report
npm run test:e2e:report

# Run specific suite
npm run test:e2e:visual -- -g "Dashboard"

# Debug mode
npx playwright test tests/visual --debug
```

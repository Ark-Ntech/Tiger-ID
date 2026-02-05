# Visual Regression Testing - Examples & Usage

Practical examples and usage patterns for visual regression testing in Tiger ID.

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Advanced Usage](#advanced-usage)
3. [Writing New Visual Tests](#writing-new-visual-tests)
4. [Debugging Failed Tests](#debugging-failed-tests)
5. [CI/CD Integration](#cicd-integration)
6. [Best Practices](#best-practices)

---

## Basic Usage

### Run All Visual Tests

```bash
# Using npm script
npm run test:e2e:visual

# Using test runner
node run-visual-tests.js run

# Using Playwright directly
npx playwright test tests/visual
```

**Expected Output:**
```
Running 103 tests using 4 workers

  ✓ Authentication Pages > login page - light mode - desktop (2s)
  ✓ Authentication Pages > login page - dark mode - desktop (2s)
  ✓ Dashboard > dashboard - full layout - light mode (3s)
  ...

103 passed (6m)
```

### Update Baseline Snapshots

When you make intentional UI changes, update the baselines:

```bash
# Using npm script
npm run test:e2e:visual:update

# Using test runner
node run-visual-tests.js update

# Using Playwright directly
npx playwright test tests/visual --update-snapshots
```

**Review changes before committing:**
```bash
git diff e2e/tests/visual/__snapshots__/
```

### Run Tests in Interactive UI Mode

Great for debugging and exploring tests:

```bash
# Using npm script
npm run test:e2e:visual:ui

# Using test runner
node run-visual-tests.js ui

# Using Playwright directly
npx playwright test tests/visual --ui
```

**Features:**
- Click to run individual tests
- View screenshots in real-time
- Step through test execution
- Inspect DOM at each step

### Run Tests in Headed Mode

See the browser during test execution:

```bash
# Using npm script
npm run test:e2e:visual:headed

# Using test runner
node run-visual-tests.js headed

# Using Playwright directly
npx playwright test tests/visual --headed
```

---

## Advanced Usage

### Run Specific Test Group

```bash
# Authentication tests only
node run-visual-tests.js group auth

# Dashboard tests only
node run-visual-tests.js group dashboard

# Tiger management tests only
node run-visual-tests.js group tigers

# Available groups: auth, dashboard, tigers, investigation,
#                   discovery, facilities, verification,
#                   templates, components, responsive
```

### Run Tests on Specific Browser

```bash
# Chromium (Chrome/Edge)
node run-visual-tests.js browser chromium

# Firefox
node run-visual-tests.js browser firefox

# WebKit (Safari)
node run-visual-tests.js browser webkit

# Or using Playwright directly
npx playwright test tests/visual --project=chromium
npx playwright test tests/visual --project=firefox
npx playwright test tests/visual --project=webkit
```

### Run Single Test

```bash
# Using grep pattern
npx playwright test tests/visual -g "login page - light mode"

# Run all tests matching pattern
npx playwright test tests/visual -g "dark mode"

# Run all dashboard tests
npx playwright test tests/visual -g "Dashboard"
```

### View Test Report

After running tests, view the HTML report:

```bash
# Using npm script
npm run test:e2e:report

# Using test runner
node run-visual-tests.js report

# Using Playwright directly
npx playwright show-report
```

**Report includes:**
- Test results (pass/fail)
- Execution time
- Screenshots (expected, actual, diff)
- Traces for failed tests

### Debug Specific Test

```bash
# Debug mode (opens browser, pauses at each step)
npx playwright test tests/visual -g "login page" --debug

# With browser console
npx playwright test tests/visual -g "login page" --headed --debug
```

**Debug Features:**
- Pause execution
- Step through test
- Inspect elements
- View console logs
- Take manual screenshots

---

## Writing New Visual Tests

### Basic Test Template

```typescript
test('page name - state - viewport', async ({ page }) => {
  // 1. Set viewport
  await page.setViewportSize({ width: 1920, height: 1080 })

  // 2. Navigate to page
  await page.goto('/page-url')

  // 3. Wait for content to load
  await waitForPageLoad(page)

  // 4. Take screenshot and compare
  const screenshot = await page.screenshot({
    path: 'screenshots/visual/category/page-name-state.png',
    fullPage: true
  })
  expect(screenshot).toMatchSnapshot('page-name-state.png')
})
```

### Test with Dark Mode

```typescript
test('dashboard - dark mode - desktop', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/dashboard')
  await waitForPageLoad(page)

  // Enable dark mode
  await toggleDarkMode(page, true)

  const screenshot = await page.screenshot({
    path: 'screenshots/visual/dashboard/dashboard-dark.png',
    fullPage: true
  })
  expect(screenshot).toMatchSnapshot('dashboard-dark.png')
})
```

### Test with Dynamic Content

```typescript
test('tigers list - with timestamps hidden', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/tigers')
  await waitForPageLoad(page)
  await waitForImages(page)

  // Hide dynamic content
  await hideTimestamps(page)
  await maskDynamicIds(page)

  const screenshot = await page.screenshot({
    path: 'screenshots/visual/tigers/tigers-list.png',
    fullPage: true
  })
  expect(screenshot).toMatchSnapshot('tigers-list.png')
})
```

### Component Screenshot

```typescript
test('tiger card - component only', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/tigers')
  await waitForPageLoad(page)
  await waitForImages(page)

  // Screenshot specific component
  const tigerCard = page.locator('[data-testid="tiger-card"]').first()

  if (await tigerCard.count() > 0) {
    const screenshot = await tigerCard.screenshot({
      path: 'screenshots/visual/components/tiger-card.png'
    })
    expect(screenshot).toMatchSnapshot('tiger-card.png')
  }
})
```

### Mobile Responsive Test

```typescript
test('login page - mobile', async ({ page }) => {
  // Set mobile viewport
  await page.setViewportSize({ width: 375, height: 667 })

  await page.goto('/login')
  await waitForPageLoad(page)

  const screenshot = await page.screenshot({
    path: 'screenshots/visual/auth/login-mobile.png',
    fullPage: true
  })
  expect(screenshot).toMatchSnapshot('login-mobile.png')
})
```

### Hover State Test

```typescript
test('card - hover state', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/tigers')
  await waitForPageLoad(page)

  const card = page.locator('[data-testid="tiger-card"]').first()

  if (await card.count() > 0) {
    // Hover over card
    await card.hover()
    await page.waitForTimeout(300)

    const screenshot = await card.screenshot({
      path: 'screenshots/visual/components/card-hover.png'
    })
    expect(screenshot).toMatchSnapshot('card-hover.png')
  }
})
```

### Test with Interaction

```typescript
test('modal - open state', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/tigers')
  await waitForPageLoad(page)

  // Click button to open modal
  const addButton = page.locator('button:has-text("Add")').first()
  if (await addButton.count() > 0) {
    await addButton.click()
    await page.waitForTimeout(500)

    // Screenshot modal
    const modal = page.locator('[data-testid="modal"]').first()
    if (await modal.count() > 0) {
      const screenshot = await modal.screenshot({
        path: 'screenshots/visual/components/modal.png'
      })
      expect(screenshot).toMatchSnapshot('modal.png')
    }
  }
})
```

---

## Debugging Failed Tests

### View Visual Diff

When a test fails, view the HTML report to see differences:

```bash
npm run test:e2e:report
```

**Report shows:**
1. **Expected** - Baseline snapshot
2. **Actual** - Current screenshot
3. **Diff** - Highlighted differences

### Example Failure Output

```
  1) visual.spec.ts:143:5 › Authentication Pages › login page - light mode - desktop

    Error: Screenshot comparison failed:

      26785 pixels (ratio 0.01 of all image pixels) are different.

    Expected: e2e/tests/visual/__snapshots__/login-light-desktop.png
    Actual: test-results/visual-Authentication-Pages-login-page-light-mode-desktop-chromium/login-light-desktop-actual.png
    Diff: test-results/visual-Authentication-Pages-login-page-light-mode-desktop-chromium/login-light-desktop-diff.png
```

### Analyze Differences

1. **Open the diff image** in `test-results/`
2. **Red pixels** = Changed areas
3. **Determine if intentional** or a bug

### Update Baseline if Intentional

If the change is intentional:

```bash
# Update this specific test
npx playwright test tests/visual -g "login page - light mode" --update-snapshots

# Or update all baselines
npm run test:e2e:visual:update
```

### Debug with Browser Console

```bash
# Run test in headed mode with console
npx playwright test tests/visual -g "login page" --headed

# Or in debug mode
npx playwright test tests/visual -g "login page" --debug
```

### Check Dynamic Content

If timestamps or IDs cause failures:

```typescript
// Add to test
await hideTimestamps(page)
await maskDynamicIds(page)
```

### Adjust Threshold for Specific Test

If small differences are acceptable:

```typescript
expect(screenshot).toMatchSnapshot('page.png', {
  threshold: 0.05,  // Allow 5% difference
  maxDiffPixelRatio: 0.05
})
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Visual Regression Tests

on:
  pull_request:
    branches: [main]

jobs:
  visual-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 18

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps chromium
        working-directory: ./frontend

      - name: Run visual regression tests
        run: npm run test:e2e:visual
        working-directory: ./frontend

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 30

      - name: Upload visual diffs
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: visual-diffs
          path: frontend/test-results/
          retention-days: 30

      - name: Comment PR with results
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '## Visual Regression Test Results\n\nView the [full report](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }})'
            })
```

### GitLab CI Example

```yaml
visual-regression-tests:
  stage: test
  image: mcr.microsoft.com/playwright:v1.40.0-focal
  script:
    - cd frontend
    - npm ci
    - npm run test:e2e:visual
  artifacts:
    when: always
    paths:
      - frontend/playwright-report/
      - frontend/test-results/
    reports:
      junit: frontend/test-results/junit.xml
  only:
    - merge_requests
    - main
```

---

## Best Practices

### 1. Stable Baselines

```typescript
// ✅ Good - Hide dynamic content
await hideTimestamps(page)
await maskDynamicIds(page)
await disableAnimations(page)

// ❌ Bad - Dynamic content causes flaky tests
await page.screenshot() // Timestamps and IDs will differ
```

### 2. Wait for Content

```typescript
// ✅ Good - Wait for all content
await waitForPageLoad(page)
await waitForImages(page)
await page.waitForTimeout(500) // Buffer for animations

// ❌ Bad - Screenshot too early
await page.goto('/page')
await page.screenshot() // Content may still be loading
```

### 3. Test Organization

```typescript
// ✅ Good - Descriptive test names
test('login page - dark mode - desktop', async ({ page }) => {
  // Test code
})

// ❌ Bad - Vague test names
test('login test', async ({ page }) => {
  // Test code
})
```

### 4. Component Screenshots

```typescript
// ✅ Good - Screenshot specific component
const component = page.locator('[data-testid="component"]').first()
if (await component.count() > 0) {
  await component.screenshot()
}

// ❌ Bad - No existence check
const component = page.locator('[data-testid="component"]')
await component.screenshot() // May fail if not found
```

### 5. Viewport Consistency

```typescript
// ✅ Good - Set viewport explicitly
await page.setViewportSize({ width: 1920, height: 1080 })

// ❌ Bad - Rely on default viewport
await page.goto('/page') // Viewport may vary
```

### 6. Theme Testing

```typescript
// ✅ Good - Test both themes
test('page - light mode', async ({ page }) => {
  // Test without dark mode
})

test('page - dark mode', async ({ page }) => {
  await toggleDarkMode(page, true)
  // Test with dark mode
})

// ❌ Bad - Only test one theme
test('page', async ({ page }) => {
  // Only tests default theme
})
```

### 7. Responsive Testing

```typescript
// ✅ Good - Test key breakpoints
test('page - desktop', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  // Test desktop
})

test('page - mobile', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 })
  // Test mobile
})

// ❌ Bad - Only test one viewport
test('page', async ({ page }) => {
  // Only tests default viewport
})
```

---

## Troubleshooting Cheat Sheet

| Issue | Solution |
|-------|----------|
| Tests fail on first run | Run `npm run test:e2e:visual:update` |
| Flaky tests | Add `hideTimestamps()` and `disableAnimations()` |
| Font differences | Wait for fonts with `await page.waitForLoadState('networkidle')` |
| Images not loaded | Use `await waitForImages(page)` |
| Animations differ | Use `await disableAnimations(page)` |
| Dark mode not applied | Use `await toggleDarkMode(page, true)` and wait |
| Tests pass locally, fail in CI | Use Docker or increase threshold |
| Need to see browser | Run with `--headed` flag |
| Need to debug | Run with `--debug` flag |

---

## Quick Reference

### Commands

```bash
# Run tests
npm run test:e2e:visual

# Update baselines
npm run test:e2e:visual:update

# UI mode
npm run test:e2e:visual:ui

# Headed mode
npm run test:e2e:visual:headed

# Show report
npm run test:e2e:report

# Run group
node run-visual-tests.js group [name]

# Run browser
node run-visual-tests.js browser [name]

# Debug test
npx playwright test tests/visual -g "test name" --debug
```

### Helper Functions

```typescript
// Dark mode
await toggleDarkMode(page, true)

// Wait for content
await waitForPageLoad(page)
await waitForImages(page)

// Hide dynamic content
await hideTimestamps(page)
await maskDynamicIds(page)
await disableAnimations(page)
```

### Viewports

```typescript
// Desktop
await page.setViewportSize({ width: 1920, height: 1080 })

// Tablet
await page.setViewportSize({ width: 768, height: 1024 })

// Mobile
await page.setViewportSize({ width: 375, height: 667 })
```

---

## Resources

- **Full Documentation**: `e2e/VISUAL_REGRESSION_TESTING.md`
- **Test Suite**: `e2e/tests/visual/visual.spec.ts`
- **Helper Tests**: `e2e/tests/visual/visual-helpers.test.ts`
- **Playwright Docs**: https://playwright.dev/docs/test-snapshots
- **Test Runner**: `run-visual-tests.js`

---

## Support

For issues or questions:
1. Check this guide
2. Review `VISUAL_REGRESSION_TESTING.md`
3. Check Playwright documentation
4. View test logs in CI artifacts
5. Contact team for help

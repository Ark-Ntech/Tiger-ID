# Visual Regression Testing Guide

Comprehensive visual regression testing for the Tiger ID application using Playwright screenshots and snapshot comparison.

## Overview

This test suite captures and compares screenshots across the entire application to detect unintended visual changes. Tests cover:

- **15 Test Suites** with 100+ visual tests
- **Light/Dark Mode** variations for all major pages
- **Responsive Layouts** (desktop 1920x1080, tablet 768x1024, mobile 375x667)
- **Component States** (empty, error, loading, hover)
- **Interactive Elements** (modals, toasts, badges, cards)

## Test Coverage

### 1. Authentication Pages
- Login page (light/dark/mobile)
- Login validation errors
- Password reset page (light/dark)

**Screenshots:** 6 snapshots

### 2. Dashboard & Analytics
- Full dashboard layout (light/dark/tablet/mobile)
- Quick stats section
- Analytics charts
- Sidebar navigation

**Screenshots:** 6 snapshots

### 3. Tiger Management
- Tigers list grid (light/dark/mobile)
- Individual tiger cards
- Tiger cards with badges
- Search and filter bar
- Pagination controls
- Empty states

**Screenshots:** 7 snapshots

### 4. Investigation Workflows
- Investigation 2.0 upload page (light/dark/mobile)
- Upload component with hover state
- Progress phase indicators
- Tab navigation
- Methodology panel
- Match cards with images
- Ensemble visualization charts
- Citations section

**Screenshots:** 10 snapshots

### 5. Discovery Pipeline
- Pipeline overview (light/dark/mobile)
- Crawl grid view
- Map visualization
- Status panel
- Crawl history timeline

**Screenshots:** 6 snapshots

### 6. Facility Management
- Facilities list (light/dark/mobile)
- Map view
- Facility cards
- Filter and search controls

**Screenshots:** 6 snapshots

### 7. Verification Queue
- Verification table (light/dark/mobile)
- Comparison view with images
- Filter controls
- Statistics panel

**Screenshots:** 6 snapshots

### 8. Templates Management
- Templates list (light/dark)
- Template cards

**Screenshots:** 3 snapshots

### 9. Empty State Components
- Empty state (light/dark)
- Empty state with action button

**Screenshots:** 3 snapshots

### 10. Error State Components
- Error state (light/dark)
- Error with details expanded
- Error with retry button

**Screenshots:** 4 snapshots

### 11. Modal Components
- Modal (light/dark)
- Modal with form fields
- Confirmation dialog

**Screenshots:** 4 snapshots

### 12. Loading States
- Loading spinner
- Skeleton card loaders
- Skeleton table row loaders
- Progress bars

**Screenshots:** 4 snapshots

### 13. Badge & Card Variations
- Status badges (success/warning/error)
- Tiger cards
- Facility cards
- Investigation cards
- Stat cards
- Card hover states

**Screenshots:** 10 snapshots

### 14. Responsive Layouts
- Tablet views (dashboard, investigation, tigers)
- Mobile views (dashboard, tigers, facilities, verification)
- Mobile navigation menu

**Screenshots:** 8 snapshots

### 15. Toast & Alert Components
- Success/error toasts
- Info/warning alert banners

**Screenshots:** 4 snapshots

**Total Coverage:** 87+ unique visual snapshots

## Running Visual Tests

### Run All Visual Tests
```bash
# From frontend directory
npx playwright test tests/visual

# Or with npm script
npm run test:e2e:visual
```

### Run Specific Test Suite
```bash
# Authentication pages only
npx playwright test tests/visual -g "Authentication"

# Dashboard only
npx playwright test tests/visual -g "Dashboard"

# Investigation workflows only
npx playwright test tests/visual -g "Investigation"

# Responsive layouts only
npx playwright test tests/visual -g "Responsive"
```

### Run Single Test
```bash
# Login page light mode
npx playwright test tests/visual -g "login page - light mode"

# Dashboard dark mode
npx playwright test tests/visual -g "dashboard - full layout - dark mode"
```

### Update Baseline Snapshots
```bash
# Update all snapshots
npx playwright test tests/visual --update-snapshots

# Update specific suite
npx playwright test tests/visual -g "Dashboard" --update-snapshots

# Update single test
npx playwright test tests/visual -g "login page - light mode" --update-snapshots
```

### Run in UI Mode (Interactive)
```bash
npx playwright test tests/visual --ui
```

### Run in Headed Mode (See Browser)
```bash
npx playwright test tests/visual --headed
```

### Run on Specific Browser
```bash
# Chromium only
npx playwright test tests/visual --project=chromium

# Firefox only
npx playwright test tests/visual --project=firefox

# WebKit only
npx playwright test tests/visual --project=webkit
```

## Screenshot Configuration

### Viewport Sizes
```typescript
const VIEWPORTS = {
  desktop: { width: 1920, height: 1080 },
  tablet: { width: 768, height: 1024 },
  mobile: { width: 375, height: 667 },
}
```

### Snapshot Comparison Settings
Configured in `playwright.config.ts`:
```typescript
expect: {
  toMatchSnapshot: {
    threshold: 0.01,        // 1% pixel difference threshold
    maxDiffPixelRatio: 0.01, // Maximum 1% pixels can differ
  }
}
```

### Screenshot Storage
- **Baseline snapshots:** `frontend/e2e/tests/visual/__snapshots__/`
- **Generated screenshots:** `frontend/screenshots/visual/`
- **Failure diffs:** `frontend/test-results/`

## Helper Functions

### `toggleDarkMode(page, enable)`
Toggles dark mode on the page by adding/removing the `dark` class from `<html>`.

```typescript
await toggleDarkMode(page, true)  // Enable dark mode
await toggleDarkMode(page, false) // Disable dark mode
```

### `waitForPageLoad(page)`
Waits for network idle and animations to complete.

```typescript
await waitForPageLoad(page)
```

### `waitForImages(page)`
Waits for all images on the page to finish loading.

```typescript
await waitForImages(page)
```

### `hideTimestamps(page)`
Hides dynamic timestamp elements to prevent false failures.

```typescript
await hideTimestamps(page)
```

### `maskDynamicIds(page)`
Replaces UUIDs and dynamic IDs with placeholders.

```typescript
await maskDynamicIds(page)
```

## Best Practices

### 1. **Hide Dynamic Content**
Always hide or mask content that changes between test runs:
- Timestamps
- UUIDs
- Live counters
- Random IDs

```typescript
await hideTimestamps(page)
await maskDynamicIds(page)
```

### 2. **Wait for Content to Load**
Ensure all content is loaded before taking screenshots:

```typescript
await waitForPageLoad(page)
await waitForImages(page) // For pages with many images
await page.waitForTimeout(1000) // For charts/animations
```

### 3. **Use Full Page Screenshots for Layouts**
For full page layouts, use `fullPage: true`:

```typescript
const screenshot = await page.screenshot({
  path: 'screenshots/visual/dashboard/dashboard-light.png',
  fullPage: true
})
```

### 4. **Use Element Screenshots for Components**
For individual components, screenshot the specific element:

```typescript
const card = page.locator('[data-testid="tiger-card"]').first()
const screenshot = await card.screenshot({
  path: 'screenshots/visual/components/card.png'
})
```

### 5. **Test Light and Dark Modes**
Always test both modes for UI consistency:

```typescript
// Light mode
await page.goto('/dashboard')
await page.screenshot({ path: 'dashboard-light.png' })

// Dark mode
await toggleDarkMode(page, true)
await page.screenshot({ path: 'dashboard-dark.png' })
```

### 6. **Test Responsive Layouts**
Test critical pages at different viewport sizes:

```typescript
// Desktop
await page.setViewportSize({ width: 1920, height: 1080 })
await page.screenshot({ path: 'desktop.png' })

// Tablet
await page.setViewportSize({ width: 768, height: 1024 })
await page.screenshot({ path: 'tablet.png' })

// Mobile
await page.setViewportSize({ width: 375, height: 667 })
await page.screenshot({ path: 'mobile.png' })
```

### 7. **Handle Conditional Elements**
Check if elements exist before screenshotting:

```typescript
const emptyState = page.locator('[data-testid="empty-state"]')
if (await emptyState.count() > 0) {
  await emptyState.screenshot({ path: 'empty-state.png' })
}
```

### 8. **Use Descriptive Snapshot Names**
Name snapshots clearly to identify what they test:

✅ Good:
- `login-light-desktop.png`
- `dashboard-dark-mobile.png`
- `modal-confirmation.png`

❌ Bad:
- `screenshot-1.png`
- `test.png`
- `page.png`

## Troubleshooting

### Test Failing with Visual Differences

**Cause:** Actual page rendering doesn't match baseline snapshot.

**Solutions:**
1. View the diff in `test-results/` to see what changed
2. If change is intentional, update baseline:
   ```bash
   npx playwright test tests/visual -g "test name" --update-snapshots
   ```
3. If change is unintentional, fix the CSS/component
4. Check for dynamic content not being hidden

### Screenshots Look Different Across Browsers

**Cause:** Different browsers render fonts/spacing slightly differently.

**Solutions:**
1. Accept browser-specific baselines (Playwright creates separate snapshots per browser)
2. Increase threshold in `playwright.config.ts`:
   ```typescript
   expect: {
     toMatchSnapshot: {
       threshold: 0.02, // Increase to 2%
     }
   }
   ```
3. Test only on Chromium if pixel-perfect consistency is required

### Dark Mode Not Working

**Cause:** `dark` class not being applied to `<html>` element.

**Solutions:**
1. Verify TailwindCSS dark mode is configured:
   ```javascript
   // tailwind.config.js
   module.exports = {
     darkMode: 'class', // or 'media'
   }
   ```
2. Check that `toggleDarkMode()` helper is being called correctly
3. Add debug wait after toggling:
   ```typescript
   await toggleDarkMode(page, true)
   await page.waitForTimeout(500) // Give time for transitions
   ```

### Images Not Loading in Screenshots

**Cause:** Images loading slowly or failing to load.

**Solutions:**
1. Use `waitForImages()` helper:
   ```typescript
   await waitForImages(page)
   ```
2. Increase timeout:
   ```typescript
   await page.waitForTimeout(2000)
   ```
3. Check network for failed image requests:
   ```bash
   npx playwright test tests/visual --headed
   ```

### Timestamps Causing Failures

**Cause:** Timestamps change on every test run.

**Solutions:**
1. Use `hideTimestamps()` helper
2. Mock the system time:
   ```typescript
   await page.clock.setFixedTime(new Date('2024-01-01T00:00:00Z'))
   ```
3. Replace timestamps with placeholders in DOM

### Modal/Dialog Not Visible

**Cause:** Modal animation not complete or modal closed too quickly.

**Solutions:**
1. Add wait after opening modal:
   ```typescript
   await button.click()
   await page.waitForTimeout(500)
   ```
2. Wait for modal to be visible:
   ```typescript
   await modal.waitFor({ state: 'visible' })
   ```
3. Check for animation duration in CSS

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Visual Regression Tests

on:
  pull_request:
    branches: [main, develop]

jobs:
  visual-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci
        working-directory: ./frontend

      - name: Install Playwright
        run: npx playwright install --with-deps
        working-directory: ./frontend

      - name: Run visual regression tests
        run: npx playwright test tests/visual
        working-directory: ./frontend

      - name: Upload screenshots on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: visual-test-failures
          path: frontend/test-results/
```

### Review Visual Changes in PRs
1. Visual tests run automatically on PRs
2. If tests fail, download `visual-test-failures` artifact
3. Review diff images in `test-results/`
4. If changes are intentional:
   ```bash
   git checkout pr-branch
   cd frontend
   npx playwright test tests/visual --update-snapshots
   git add e2e/tests/visual/__snapshots__/
   git commit -m "Update visual regression baselines"
   git push
   ```

## Maintenance

### When to Update Baselines

Update baseline snapshots when:
- ✅ Intentional UI changes (new design, layout changes)
- ✅ Component styling updates
- ✅ Upgrading UI libraries (TailwindCSS, etc.)
- ✅ Font or spacing changes

Do **NOT** update baselines for:
- ❌ Random test failures
- ❌ Unexplained visual differences
- ❌ Trying to make tests pass quickly

### Regular Review Schedule

1. **Weekly:** Review failed visual tests
2. **Before Major Releases:** Run full visual suite on all browsers
3. **After UI Library Updates:** Regenerate all baselines
4. **When Adding New Pages:** Add corresponding visual tests

### Adding New Visual Tests

1. Create test following existing patterns:
   ```typescript
   test('new page - light mode', async ({ page }) => {
     await page.setViewportSize(VIEWPORTS.desktop)
     await page.goto('/new-page')
     await waitForPageLoad(page)

     const screenshot = await page.screenshot({
       path: 'screenshots/visual/new-page/new-page-light.png',
       fullPage: true
     })
     expect(screenshot).toMatchSnapshot('new-page-light.png')
   })
   ```

2. Generate baseline:
   ```bash
   npx playwright test tests/visual -g "new page" --update-snapshots
   ```

3. Commit baseline snapshots:
   ```bash
   git add e2e/tests/visual/__snapshots__/
   git commit -m "Add visual regression test for new page"
   ```

## Resources

- [Playwright Visual Comparisons Docs](https://playwright.dev/docs/test-snapshots)
- [TailwindCSS Dark Mode](https://tailwindcss.com/docs/dark-mode)
- [Playwright Test Generator](https://playwright.dev/docs/codegen)
- [Tiger ID E2E Testing Guide](../README.md)

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review [Best Practices](#best-practices)
3. Consult main [E2E README](../README.md)
4. Open an issue in the project repository

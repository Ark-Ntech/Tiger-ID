# Visual Regression Testing Guide

Comprehensive guide for visual regression testing in Tiger ID using Playwright screenshots.

## Overview

Visual regression testing captures screenshots of the application and compares them against baseline snapshots to detect unintended visual changes. This helps catch UI bugs, CSS regressions, and layout issues automatically.

## Test Suite Structure

The visual regression test suite (`visual.spec.ts`) covers:

### 1. Authentication Pages
- Login page (light/dark mode, responsive)
- Password reset page

### 2. Dashboard Views
- Full dashboard layout (light/dark mode)
- Sidebar navigation
- Mobile/tablet responsive views

### 3. Tiger Management
- Tiger list grid view (light/dark mode)
- Individual tiger cards
- Empty states
- Mobile responsive views

### 4. Investigation Workflows
- Investigation 2.0 upload state (light/dark mode)
- Progress phase indicators
- Upload component details
- Mobile views

### 5. Discovery Pipeline
- Pipeline overview (light/dark mode)
- Crawl grid visualization
- Mobile responsive views

### 6. Facility Management
- Facility list view (light/dark mode)
- Map visualization
- Mobile responsive views

### 7. Verification Queue
- Queue table (light/dark mode)
- Comparison view
- Mobile responsive views

### 8. Templates
- Template list (light/dark mode)

### 9. Component States
- Empty state variations (small/medium/large)
- Error state variations (collapsed/expanded)
- Modal components (light/dark mode)
- Loading spinners and skeletons
- Badge variations
- Card variations

### 10. Responsive Layouts
- Desktop (1920x1080)
- Tablet (768x1024)
- Mobile (375x667)

## Running Visual Tests

### Run all visual tests
```bash
npx playwright test visual
```

### Run visual tests in specific browser
```bash
npx playwright test visual --project=chromium
npx playwright test visual --project=firefox
npx playwright test visual --project=webkit
```

### Run tests in headed mode (see browser)
```bash
npx playwright test visual --headed
```

### Run tests in UI mode (interactive)
```bash
npx playwright test visual --ui
```

### Update snapshots (baseline images)
```bash
npx playwright test visual --update-snapshots
```

### Run specific test
```bash
npx playwright test visual -g "login page - light mode"
```

## First-Time Setup

### 1. Generate Baseline Snapshots

On first run, you need to generate baseline snapshots:

```bash
# Make sure backend and frontend are running
cd backend && uvicorn main:app --reload --port 8000
cd frontend && npm run dev

# Generate baselines
npx playwright test visual --update-snapshots
```

This creates snapshot files in `e2e/__snapshots__/`.

### 2. Commit Snapshots to Git

```bash
git add e2e/__snapshots__
git commit -m "Add visual regression test baselines"
```

## Working with Visual Tests

### When Tests Pass

When visual tests pass, it means the current UI matches the baseline snapshots within the configured threshold (1% pixel difference).

### When Tests Fail

When visual tests fail, Playwright generates:

1. **Expected** - The baseline snapshot
2. **Actual** - The current screenshot
3. **Diff** - Visual diff highlighting changes

These are saved in `test-results/visual-diffs/`.

### Viewing Test Results

```bash
# Open HTML report with visual diffs
npx playwright show-report
```

The report shows:
- Side-by-side comparison of expected vs actual
- Highlighted differences
- Pixel difference percentage

### Updating Snapshots After Intentional Changes

If you've intentionally changed the UI:

```bash
# Update all snapshots
npx playwright test visual --update-snapshots

# Update specific test snapshots
npx playwright test visual -g "login page" --update-snapshots
```

## Visual Test Helpers

The `helpers/visual.ts` file provides utilities:

### Viewport Management
```typescript
import { setViewport, VIEWPORTS } from './helpers/visual'

await setViewport(page, 'mobile')
await setViewport(page, 'tablet')
await setViewport(page, 'desktop')
```

### Dark Mode Toggle
```typescript
import { toggleDarkMode } from './helpers/visual'

await toggleDarkMode(page, true)  // Enable dark mode
await toggleDarkMode(page, false) // Disable dark mode
```

### Wait for Page Load
```typescript
import { waitForPageLoad } from './helpers/visual'

await waitForPageLoad(page, { timeout: 30000, additionalDelay: 500 })
```

### Hide Dynamic Content
```typescript
import { hideDynamicContent } from './helpers/visual'

// Hides timestamps, animations, and spinners
await hideDynamicContent(page)
```

### Mask Elements
```typescript
import { maskElements } from './helpers/visual'

// Hide specific dynamic elements
await maskElements(page, ['[data-timestamp]', '.user-avatar'])
```

### Take Screenshots
```typescript
import { takeFullPageScreenshot, takeComponentScreenshot } from './helpers/visual'

// Full page screenshot
await takeFullPageScreenshot(page, 'screenshots/page.png', {
  mask: ['[data-timestamp]'],
  hideDynamic: true
})

// Component screenshot
await takeComponentScreenshot(page, '[data-testid="modal"]', 'screenshots/modal.png')
```

### Prepare for Visual Test
```typescript
import { prepareForVisualTest } from './helpers/visual'

// All-in-one setup
await prepareForVisualTest(page, {
  viewport: 'desktop',
  darkMode: false,
  disableAnimations: true,
  waitForImages: true,
  waitForFonts: true,
})
```

## Configuration

### Visual Config (`visual-config.ts`)

```typescript
export const visualConfig = {
  threshold: 0.01,              // 1% pixel difference allowed
  maxDiffPixelRatio: 0.01,      // Max 1% different pixels
  screenshotTimeout: 10000,     // 10 second timeout

  viewports: {
    desktop: { width: 1920, height: 1080 },
    tablet: { width: 768, height: 1024 },
    mobile: { width: 375, height: 667 },
  },

  maskSelectors: [              // Elements to mask
    '[data-timestamp]',
    '.timestamp',
  ],

  hideSelectors: [              // Elements to hide
    '.animate-spin',
    '.animate-pulse',
  ],
}
```

### Playwright Config (`playwright.config.ts`)

Visual regression settings in Playwright config:

```typescript
expect: {
  toMatchSnapshot: {
    threshold: 0.01,           // 1% threshold
    maxDiffPixelRatio: 0.01,
  },
}
```

## Best Practices

### 1. Stable Baselines
- Generate baselines on a stable environment
- Use consistent viewport sizes
- Disable animations and transitions
- Hide dynamic content (timestamps, random IDs)

### 2. Test Organization
- Group related tests in describe blocks
- Use descriptive test names
- Test light and dark modes separately
- Test responsive layouts explicitly

### 3. Handling Dynamic Content
```typescript
// Hide timestamps
await maskElements(page, ['[data-timestamp]', '.timestamp'])

// Disable animations
await disableAnimations(page)

// Wait for images and fonts
await waitForImages(page)
await waitForFonts(page)
```

### 4. Screenshot Best Practices
- Wait for content to load before taking screenshots
- Use `fullPage: true` for full page captures
- Use `animations: 'disabled'` to prevent animation flakiness
- Mask or hide dynamic elements that change between runs

### 5. Threshold Configuration
- Default threshold: 1% (0.01)
- Increase for pages with known variability
- Decrease for pixel-perfect components
- Consider anti-aliasing differences between browsers

### 6. Cross-Browser Testing
- Generate separate baselines per browser
- Chrome, Firefox, and Safari render slightly differently
- Use browser-specific snapshot directories

## Troubleshooting

### Tests Fail on First Run

**Problem**: Tests fail because no baselines exist

**Solution**: Generate baselines with `--update-snapshots`
```bash
npx playwright test visual --update-snapshots
```

### Flaky Tests (Random Failures)

**Problem**: Screenshots differ slightly on each run

**Solutions**:
1. Disable animations: `await disableAnimations(page)`
2. Wait for fonts: `await waitForFonts(page)`
3. Wait for images: `await waitForImages(page)`
4. Hide dynamic content: `await hideDynamicContent(page)`
5. Increase threshold in config

### Fonts Look Different

**Problem**: Font rendering differs between environments

**Solutions**:
1. Wait for fonts to load: `await waitForFonts(page)`
2. Use web-safe fonts in tests
3. Increase threshold slightly (0.02-0.03)

### Images Not Loaded

**Problem**: Screenshots show broken images or placeholders

**Solution**: Wait for images to load
```typescript
await waitForImages(page)
```

### Map/Chart Rendering Issues

**Problem**: Dynamic maps or charts differ on each run

**Solutions**:
1. Mask the map/chart element
2. Use static fixtures instead of live data
3. Mock API responses for consistent data

### Animations Cause Differences

**Problem**: Animated elements captured at different states

**Solution**: Disable animations globally
```typescript
await disableAnimations(page)
```

Or in Playwright screenshot options:
```typescript
await page.screenshot({ animations: 'disabled' })
```

### Dark Mode Not Applied

**Problem**: Dark mode screenshots look the same as light mode

**Solution**: Ensure dark mode is applied and wait for transitions
```typescript
await toggleDarkMode(page, true)
await page.waitForTimeout(300) // Wait for CSS transitions
```

### Snapshots Differ on CI vs Local

**Problem**: Tests pass locally but fail on CI

**Possible Causes**:
1. Different screen resolutions
2. Different font rendering (Linux vs Mac vs Windows)
3. Different browser versions
4. GPU rendering differences

**Solutions**:
1. Use Docker for consistent environment
2. Generate baselines on CI
3. Use browser-specific baselines
4. Increase threshold for CI runs

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
      - uses: actions/checkout@v3

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run visual tests
        run: npx playwright test visual

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30

      - name: Upload visual diffs
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: visual-diffs
          path: test-results/visual-diffs/
          retention-days: 30
```

### Updating Baselines on CI

When visual changes are intentional:

```bash
# Locally
npx playwright test visual --update-snapshots
git add e2e/__snapshots__
git commit -m "Update visual regression baselines"
git push
```

## Directory Structure

```
frontend/
├── e2e/
│   ├── visual.spec.ts                    # Main visual regression tests
│   ├── visual-config.ts                  # Configuration
│   ├── helpers/
│   │   └── visual.ts                     # Helper functions
│   ├── __snapshots__/                    # Baseline snapshots
│   │   └── visual.spec.ts-snapshots/     # Per-test snapshots
│   └── VISUAL_REGRESSION_TESTING.md      # This file
├── screenshots/                           # Screenshot outputs
│   ├── auth/
│   ├── dashboard/
│   ├── tigers/
│   ├── investigation/
│   ├── discovery/
│   ├── facilities/
│   ├── verification/
│   ├── templates/
│   ├── components/
│   └── responsive/
├── test-results/
│   └── visual-diffs/                     # Diff outputs on failures
└── playwright.config.ts                   # Playwright configuration
```

## Snapshot Naming Convention

Snapshots are named based on:
```
{page}-{state}-{viewport}-{theme}.png

Examples:
- login-light-desktop.png
- dashboard-dark-mobile.png
- tigers-list-light.png
- empty-state-tigers.png
- modal-dark.png
```

## Performance Considerations

- Full page screenshots are slower than viewport screenshots
- Disable animations to speed up tests
- Run visual tests in parallel (separate from functional tests)
- Use selective visual testing (not every test needs screenshots)
- Consider visual testing on key pages/components only

## Maintenance

### Regular Tasks

1. **Review visual test failures** - Verify changes are intentional
2. **Update baselines** - When UI changes are approved
3. **Clean old screenshots** - Remove outdated screenshot directories
4. **Update viewports** - As target devices change
5. **Tune thresholds** - Based on false positive rate

### When to Update Baselines

- After intentional design changes
- After library upgrades (React, TailwindCSS)
- After browser version updates
- When switching test environments

### When to Adjust Thresholds

- Too many false positives → Increase threshold
- Missing real regressions → Decrease threshold
- Specific components need different thresholds → Use per-test configuration

## Resources

- [Playwright Visual Comparisons](https://playwright.dev/docs/test-snapshots)
- [Percy (Commercial Alternative)](https://percy.io/)
- [Chromatic (Commercial Alternative)](https://www.chromatic.com/)
- [Visual Regression Testing Best Practices](https://martinfowler.com/articles/visual-testing.html)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review Playwright documentation
3. Check test logs in CI artifacts
4. Contact team for threshold adjustments

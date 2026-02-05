# Visual Regression Tests - Quick Reference

Quick commands and common workflows for visual regression testing.

## Quick Commands

```bash
# Run all visual tests
npm run test:e2e:visual

# Update all baseline snapshots
npm run test:e2e:visual:update

# Run in interactive UI mode
npm run test:e2e:visual:ui

# Run specific test
npx playwright test visual -g "login page"

# Run in headed mode (see browser)
npx playwright test visual --headed

# Run in specific browser
npx playwright test visual --project=chromium

# View test report
npx playwright show-report
```

## Common Workflows

### First Time Setup

```bash
# 1. Ensure backend and frontend are running
cd backend && uvicorn main:app --reload --port 8000 &
cd frontend && npm run dev &

# 2. Generate baseline snapshots
npm run test:e2e:visual:update

# 3. Commit baselines
git add e2e/__snapshots__
git commit -m "Add visual regression baselines"
```

### After UI Changes

```bash
# 1. Run visual tests to see what changed
npm run test:e2e:visual

# 2. View the differences
npx playwright show-report

# 3. If changes are intentional, update baselines
npm run test:e2e:visual:update

# 4. Commit updated baselines
git add e2e/__snapshots__
git commit -m "Update visual baselines after UI changes"
```

### Debugging Visual Failures

```bash
# 1. Run tests with UI mode
npm run test:e2e:visual:ui

# 2. In UI mode:
#    - Click on failed test
#    - View "Expected", "Actual", and "Diff" tabs
#    - Compare side-by-side

# 3. Or view HTML report
npx playwright show-report
```

### Update Specific Test Snapshots

```bash
# Update only login page snapshots
npx playwright test visual -g "login page" --update-snapshots

# Update only dark mode snapshots
npx playwright test visual -g "dark mode" --update-snapshots

# Update only mobile snapshots
npx playwright test visual -g "mobile" --update-snapshots
```

## Test Structure

### Test Organization

```
visual.spec.ts
├── Authentication Pages
│   ├── login page - light/dark/mobile
│   └── password reset page
├── Dashboard Views
│   ├── full layout - light/dark
│   ├── sidebar navigation
│   └── mobile/tablet views
├── Tiger Management
│   ├── grid view - light/dark
│   ├── tiger cards
│   └── empty states
├── Investigation Workflows
│   ├── upload state - light/dark
│   ├── progress indicators
│   └── mobile views
├── Discovery Pipeline
├── Facility Management
├── Verification Queue
├── Templates
├── Component States
│   ├── Empty states
│   ├── Error states
│   ├── Loading states
│   └── Modals
└── Responsive Layouts
    ├── Desktop (1920x1080)
    ├── Tablet (768x1024)
    └── Mobile (375x667)
```

## Helper Functions

### Visual Helpers (`helpers/visual.ts`)

```typescript
import {
  toggleDarkMode,
  waitForPageLoad,
  setViewport,
  prepareForVisualTest,
  takeFullPageScreenshot,
  takeComponentScreenshot,
  hideDynamicContent,
  maskElements,
  VIEWPORTS,
} from './helpers/visual'

// Toggle dark mode
await toggleDarkMode(page, true)

// Set viewport
await setViewport(page, 'mobile')
await setViewport(page, 'tablet')
await setViewport(page, 'desktop')

// All-in-one preparation
await prepareForVisualTest(page, {
  viewport: 'desktop',
  darkMode: false,
  disableAnimations: true,
  waitForImages: true,
  waitForFonts: true,
})

// Take screenshots
await takeFullPageScreenshot(page, 'screenshots/page.png')
await takeComponentScreenshot(page, '[data-testid="modal"]', 'screenshots/modal.png')

// Hide dynamic content
await hideDynamicContent(page)
await maskElements(page, ['[data-timestamp]', '.user-avatar'])
```

### Authentication Helpers (`helpers/auth.ts`)

```typescript
import { login, logout, isAuthenticated, clearAuth } from './helpers/auth'

// Login
await login(page)
await login(page, 'custom-user', 'custom-pass')

// Logout
await logout(page)

// Check auth
const authenticated = await isAuthenticated(page)

// Clear auth
await clearAuth(page)
```

## Configuration

### Visual Config (`visual-config.ts`)

```typescript
export const visualConfig = {
  threshold: 0.01, // 1% pixel difference
  maxDiffPixelRatio: 0.01,
  screenshotTimeout: 10000,
  viewports: {
    desktop: { width: 1920, height: 1080 },
    tablet: { width: 768, height: 1024 },
    mobile: { width: 375, height: 667 },
  },
}
```

### Playwright Config (`playwright.config.ts`)

```typescript
expect: {
  toMatchSnapshot: {
    threshold: 0.01,
    maxDiffPixelRatio: 0.01,
  },
}
```

## Troubleshooting

### Flaky Tests

```typescript
// Disable animations
await disableAnimations(page)

// Wait for fonts
await waitForFonts(page)

// Wait for images
await waitForImages(page)

// Hide dynamic content
await hideDynamicContent(page)
```

### Different Results on CI

```bash
# Use consistent viewport
await page.setViewportSize({ width: 1920, height: 1080 })

# Disable animations
await page.screenshot({ animations: 'disabled' })

# Increase threshold for CI
# In playwright.config.ts:
expect: {
  toMatchSnapshot: { threshold: 0.02 } // 2% for CI
}
```

### Fonts Look Different

```typescript
// Wait for fonts to load
await page.evaluate(async () => {
  await document.fonts.ready
})
```

## Screenshot Locations

```
frontend/
├── screenshots/              # Screenshot outputs
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
├── e2e/__snapshots__/       # Baseline snapshots
│   └── visual.spec.ts-snapshots/
└── test-results/            # Test artifacts
    └── visual-diffs/        # Diff images on failure
```

## CI/CD

### Update Baselines in CI

```yaml
# .github/workflows/update-visual-baselines.yml
name: Update Visual Baselines

on:
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Install Playwright
        run: npx playwright install --with-deps
      - name: Update snapshots
        run: cd frontend && npm run test:e2e:visual:update
      - name: Commit changes
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add e2e/__snapshots__
          git commit -m "Update visual regression baselines"
          git push
```

## Best Practices

1. **Always review diffs** - Don't blindly update snapshots
2. **Test in isolation** - Each test should be independent
3. **Hide dynamic content** - Timestamps, random IDs, animations
4. **Use consistent viewports** - Stick to defined sizes
5. **Test both themes** - Light and dark mode
6. **Test responsive** - Desktop, tablet, mobile
7. **Commit baselines** - Track in version control
8. **Document changes** - Explain why baselines were updated
9. **Run locally first** - Before pushing to CI
10. **Keep tests fast** - Avoid unnecessary full-page screenshots

## Viewport Sizes

```typescript
desktop: { width: 1920, height: 1080 }
desktopSmall: { width: 1366, height: 768 }
tablet: { width: 768, height: 1024 }
tabletLandscape: { width: 1024, height: 768 }
mobile: { width: 375, height: 667 }
mobileLarge: { width: 414, height: 896 }
```

## Useful Links

- [Full Documentation](./VISUAL_REGRESSION_TESTING.md)
- [E2E Tests README](./README.md)
- [Playwright Visual Comparisons](https://playwright.dev/docs/test-snapshots)

## Getting Help

```bash
# Validate setup
node validate-visual-tests.js

# Check Playwright version
npx playwright --version

# View test report
npx playwright show-report

# Debug specific test
npx playwright test visual -g "test name" --debug
```

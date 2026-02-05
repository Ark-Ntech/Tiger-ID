# Visual Regression Testing - Quick Reference

Fast command reference for visual regression testing with Playwright.

## Quick Start

```bash
# Run all visual tests
npx playwright test tests/visual

# Update all baselines
npx playwright test tests/visual --update-snapshots

# Run in UI mode (interactive)
npx playwright test tests/visual --ui
```

## Common Commands

### Running Tests

| Command | Description |
|---------|-------------|
| `npx playwright test tests/visual` | Run all visual tests |
| `npx playwright test tests/visual --headed` | Run with visible browser |
| `npx playwright test tests/visual --ui` | Interactive UI mode |
| `npx playwright test tests/visual --debug` | Debug mode with inspector |
| `npx playwright test tests/visual --project=chromium` | Run on Chromium only |

### Running Specific Tests

| Command | Description |
|---------|-------------|
| `npx playwright test tests/visual -g "Authentication"` | Authentication pages only |
| `npx playwright test tests/visual -g "Dashboard"` | Dashboard tests only |
| `npx playwright test tests/visual -g "Investigation"` | Investigation workflow tests |
| `npx playwright test tests/visual -g "Tigers"` | Tiger management tests |
| `npx playwright test tests/visual -g "dark mode"` | All dark mode tests |
| `npx playwright test tests/visual -g "mobile"` | All mobile viewport tests |
| `npx playwright test tests/visual -g "login page - light mode"` | Single test |

### Updating Snapshots

| Command | Description |
|---------|-------------|
| `npx playwright test tests/visual --update-snapshots` | Update all baselines |
| `npx playwright test tests/visual -g "Dashboard" --update-snapshots` | Update specific suite |
| `npx playwright test tests/visual -g "login page" --update-snapshots` | Update single test |
| `npx playwright test tests/visual -g "dark mode" --update-snapshots` | Update all dark mode |

### Viewing Results

| Command | Description |
|---------|-------------|
| `npx playwright show-report` | Open HTML report |
| `npx playwright show-trace trace.zip` | View trace file |

## Test Organization

```
tests/visual/
├── visual.spec.ts          # Main test file
├── README.md              # Full documentation
├── QUICK_REFERENCE.md     # This file
└── __snapshots__/         # Baseline snapshots (auto-generated)
```

## Test Suites

| Suite | Tests | Coverage |
|-------|-------|----------|
| Authentication Pages | 6 | Login, password reset, validation |
| Dashboard | 6 | Layout, stats, charts, sidebar |
| Tigers List | 7 | Grid, cards, badges, empty states |
| Investigation 2.0 | 10 | Upload, progress, results, ensemble |
| Discovery Pipeline | 6 | Overview, grid, map, timeline |
| Facilities | 6 | List, map, cards, filters |
| Verification Queue | 6 | Table, comparison, filters, stats |
| Templates | 3 | List, cards |
| Empty States | 3 | Light/dark, with actions |
| Error States | 4 | Light/dark, expanded, retry |
| Modals | 4 | Light/dark, forms, confirmation |
| Loading States | 4 | Spinners, skeletons, progress bars |
| Badges & Cards | 10 | Status badges, various card types |
| Responsive Layouts | 8 | Tablet/mobile views |
| Toasts & Alerts | 4 | Success/error/info/warning |

**Total:** 87+ visual snapshots

## Common Workflows

### 1. PR Review - Check Visual Changes
```bash
# Run tests to see if anything broke
npx playwright test tests/visual

# If failures exist, view the report
npx playwright show-report

# Review diffs in test-results/ folder
```

### 2. Intentional UI Change - Update Baselines
```bash
# Make your UI changes
# ...

# Update the affected snapshots
npx playwright test tests/visual -g "component name" --update-snapshots

# Or update all if many changes
npx playwright test tests/visual --update-snapshots

# Commit the new baselines
git add e2e/tests/visual/__snapshots__/
git commit -m "Update visual baselines for [component]"
```

### 3. New Feature - Add Visual Tests
```bash
# Add new test to visual.spec.ts
# ...

# Generate baseline
npx playwright test tests/visual -g "your new test" --update-snapshots

# Verify it works
npx playwright test tests/visual -g "your new test"

# Commit
git add e2e/tests/visual/
git commit -m "Add visual regression test for [feature]"
```

### 4. Debug Failing Test
```bash
# Run single test in debug mode
npx playwright test tests/visual -g "failing test name" --debug

# Or run in headed mode to see browser
npx playwright test tests/visual -g "failing test name" --headed

# Or use UI mode for interactive debugging
npx playwright test tests/visual -g "failing test name" --ui
```

### 5. Before Major Release - Full Suite
```bash
# Run on all browsers
npx playwright test tests/visual

# Generate comprehensive report
npx playwright show-report

# Check all screenshots in screenshots/visual/
```

## Viewport Sizes

| Device | Width | Height | Usage |
|--------|-------|--------|-------|
| Desktop | 1920 | 1080 | Primary desktop layout |
| Tablet | 768 | 1024 | iPad and tablet devices |
| Mobile | 375 | 667 | iPhone and mobile devices |

## Snapshot Thresholds

Configured in `playwright.config.ts`:
- **Pixel threshold:** 0.01 (1% difference allowed)
- **Max diff ratio:** 0.01 (max 1% pixels can differ)

## Typical Test Structure

```typescript
test('page name - light mode - desktop', async ({ page }) => {
  // 1. Set viewport
  await page.setViewportSize(VIEWPORTS.desktop)

  // 2. Navigate
  await page.goto('/page-path')

  // 3. Wait for content
  await waitForPageLoad(page)

  // 4. Optional: Hide dynamic content
  await hideTimestamps(page)

  // 5. Take screenshot
  const screenshot = await page.screenshot({
    path: 'screenshots/visual/category/page-name-light.png',
    fullPage: true
  })

  // 6. Compare with baseline
  expect(screenshot).toMatchSnapshot('page-name-light.png')
})
```

## Helper Functions

| Function | Purpose |
|----------|---------|
| `toggleDarkMode(page, true/false)` | Enable/disable dark mode |
| `waitForPageLoad(page)` | Wait for network idle + animations |
| `waitForImages(page)` | Wait for all images to load |
| `hideTimestamps(page)` | Hide dynamic timestamps |
| `maskDynamicIds(page)` | Replace UUIDs with placeholders |

## Tips & Tricks

### Hide Dynamic Content
```typescript
// Hide timestamps
await hideTimestamps(page)

// Or manually hide elements
await page.evaluate(() => {
  document.querySelectorAll('.timestamp').forEach(el => {
    (el as HTMLElement).style.visibility = 'hidden'
  })
})
```

### Wait for Animations
```typescript
// Wait for CSS transitions
await page.waitForTimeout(300)

// Wait for charts to render
await page.waitForTimeout(1000)
```

### Screenshot Element Only
```typescript
// Screenshot specific component
const card = page.locator('[data-testid="card"]').first()
await card.screenshot({ path: 'card.png' })
```

### Handle Conditional Elements
```typescript
// Only screenshot if element exists
const modal = page.locator('[data-testid="modal"]')
if (await modal.count() > 0) {
  await modal.screenshot({ path: 'modal.png' })
}
```

### Test Hover States
```typescript
const card = page.locator('[data-testid="card"]').first()
await card.hover()
await page.waitForTimeout(300)
await card.screenshot({ path: 'card-hover.png' })
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Test failing with visual diff | View `test-results/` for diff images |
| Timestamps causing failures | Use `hideTimestamps(page)` helper |
| Images not loading | Use `waitForImages(page)` helper |
| Dark mode not working | Check TailwindCSS config has `darkMode: 'class'` |
| Modal not visible | Add `await page.waitForTimeout(500)` after opening |
| Flaky tests | Increase wait times or hide dynamic content |
| Browser differences | Accept browser-specific baselines or increase threshold |

## File Locations

| Path | Contents |
|------|----------|
| `e2e/tests/visual/visual.spec.ts` | Test file |
| `e2e/tests/visual/__snapshots__/` | Baseline snapshots |
| `screenshots/visual/` | Generated screenshots |
| `test-results/` | Failure diffs and traces |
| `playwright-report/` | HTML test report |

## NPM Scripts

Add these to `package.json` for convenience:

```json
{
  "scripts": {
    "test:visual": "playwright test tests/visual",
    "test:visual:update": "playwright test tests/visual --update-snapshots",
    "test:visual:ui": "playwright test tests/visual --ui",
    "test:visual:headed": "playwright test tests/visual --headed",
    "test:visual:chromium": "playwright test tests/visual --project=chromium"
  }
}
```

Then run:
```bash
npm run test:visual
npm run test:visual:update
npm run test:visual:ui
```

## CI/CD

### GitHub Actions - Run on PR
```yaml
- name: Run visual tests
  run: npx playwright test tests/visual
  working-directory: ./frontend
```

### View Failures in CI
1. Check GitHub Actions logs
2. Download `playwright-report` artifact
3. Download `test-results` artifact
4. Open `playwright-report/index.html` locally
5. Review diff images in `test-results/`

## Best Practices Summary

✅ **Do:**
- Hide timestamps and dynamic IDs
- Wait for images and animations to load
- Test light and dark modes
- Test responsive layouts
- Update baselines intentionally
- Use descriptive snapshot names
- Screenshot individual components for focused tests

❌ **Don't:**
- Update baselines without reviewing changes
- Ignore failing tests
- Skip responsive testing
- Screenshot while content is loading
- Use generic snapshot names
- Test dynamic content without masking

## Quick Links

- [Full Documentation](./README.md)
- [Main E2E README](../README.md)
- [Playwright Docs](https://playwright.dev/docs/test-snapshots)

---

**Last Updated:** 2026-02-05

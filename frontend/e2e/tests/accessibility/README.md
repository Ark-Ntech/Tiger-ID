# Accessibility Testing with axe-core

Comprehensive accessibility tests for Tiger ID using `@axe-core/playwright` to detect WCAG 2.0/2.1 Level A and AA violations.

## Installation

Install the required package:

```bash
npm install --save-dev @axe-core/playwright
```

## Running Tests

### Run all accessibility tests
```bash
npx playwright test accessibility
```

### Run accessibility tests in UI mode
```bash
npx playwright test accessibility --ui
```

### Run accessibility tests with headed browser
```bash
npx playwright test accessibility --headed
```

### Run specific accessibility test
```bash
npx playwright test accessibility.spec.ts -g "Login page"
npx playwright test accessibility.spec.ts -g "Tigers list"
npx playwright test accessibility.spec.ts -g "Color Contrast"
```

### Generate detailed report
```bash
npx playwright test accessibility
npx playwright show-report
```

## Test Coverage

### Pages Tested

1. **Authentication Pages**
   - Login page
   - Password reset page

2. **Main Dashboard**
   - Dashboard page
   - Navigation header
   - Sidebar navigation

3. **Tiger Management**
   - Tigers list page
   - Tiger cards with images
   - Tiger detail pages

4. **Investigation Pages**
   - Investigation 2.0 page
   - File upload area
   - Investigation results

5. **Discovery Pipeline**
   - Discovery page
   - Discovery controls

6. **Facilities Management**
   - Facilities list page
   - Facility map (Leaflet)
   - Facility cards

7. **Verification Queue**
   - Verification queue page
   - Verification action buttons

### Component Tests

8. **Modal Components**
   - Focus trapping
   - ARIA labels
   - Close button accessibility

9. **Form Components**
   - Input labels
   - Validation error announcements
   - Required field indicators

### Cross-Cutting Concerns

10. **Color Contrast**
    - All pages tested for WCAG AA compliance

11. **Keyboard Navigation**
    - All interactive elements
    - Skip to main content
    - Logical tab order

12. **Screen Reader Compatibility**
    - Document structure
    - Live regions

## WCAG Standards Tested

The tests check for compliance with:

- **WCAG 2.0 Level A** (`wcag2a`)
- **WCAG 2.0 Level AA** (`wcag2aa`)
- **WCAG 2.1 Level A** (`wcag21a`)
- **WCAG 2.1 Level AA** (`wcag21aa`)

## Violation Impact Levels

axe-core classifies violations by impact:

- **Critical**: Must be fixed immediately - blocks users completely
- **Serious**: Should be fixed - creates significant barriers
- **Moderate**: Should be fixed - causes inconvenience
- **Minor**: Should be fixed eventually - causes annoyance

**Tests fail only on Critical and Serious violations** to avoid blocking development on minor issues.

## Common Violations and Fixes

### Image Alt Text
**Violation**: Images missing alt text
**Rule**: `image-alt`
**Fix**: Add `alt` attribute to all `<img>` tags
```tsx
<img src="tiger.jpg" alt="Bengal tiger named Raja" />
```

### Form Labels
**Violation**: Input fields without labels
**Rule**: `label`
**Fix**: Associate labels with inputs
```tsx
<label htmlFor="username">Username</label>
<input id="username" name="username" type="text" />
```

### Color Contrast
**Violation**: Text doesn't meet 4.5:1 contrast ratio
**Rule**: `color-contrast`
**Fix**: Use higher contrast colors or increase font weight
```css
/* Bad: #767676 on white (3.8:1) */
color: #767676;

/* Good: #595959 on white (7:1) */
color: #595959;
```

### Button Names
**Violation**: Buttons without accessible names
**Rule**: `button-name`
**Fix**: Add text content or aria-label
```tsx
<button aria-label="Close dialog">
  <XIcon />
</button>
```

### Heading Order
**Violation**: Skipped heading levels (h1 → h3)
**Rule**: `heading-order`
**Fix**: Use sequential heading hierarchy
```tsx
<h1>Page Title</h1>
<h2>Section Title</h2>
<h3>Subsection Title</h3>
```

### Landmark Regions
**Violation**: Missing main landmark
**Rule**: `region`
**Fix**: Use semantic HTML5 elements
```tsx
<main>
  {/* Page content */}
</main>
```

### Modal Accessibility
**Violation**: Dialog missing aria-modal
**Rule**: `aria-dialog-name`
**Fix**: Add proper ARIA attributes
```tsx
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
>
  <h2 id="dialog-title">Dialog Title</h2>
  {/* Dialog content */}
</div>
```

### Keyboard Accessibility
**Violation**: Interactive element not keyboard accessible
**Rule**: `keyboard-navigable`
**Fix**: Ensure interactive elements are focusable
```tsx
// Don't use div for buttons
<div onClick={handleClick}>Click me</div>

// Use actual button elements
<button onClick={handleClick}>Click me</button>
```

### Live Regions
**Violation**: Dynamic content updates not announced
**Rule**: `aria-live`
**Fix**: Add aria-live regions
```tsx
<div role="status" aria-live="polite">
  Investigation processing: {progress}%
</div>
```

## Test Structure

Each test follows this pattern:

```typescript
test('page should not have accessibility violations', async ({ page }) => {
  // 1. Navigate to page
  await page.goto('/path')
  await page.waitForLoadState('networkidle')

  // 2. Run accessibility scan
  const accessibilityScanResults = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze()

  // 3. Filter for critical/serious violations
  const criticalViolations = accessibilityScanResults.violations.filter(
    v => v.impact === 'critical' || v.impact === 'serious'
  )

  // 4. Assert no critical/serious violations
  expect(criticalViolations).toEqual([])
})
```

## Helper Functions

### `analyzeAccessibility(page, context)`
Runs axe scan and logs detailed violation information.

```typescript
const results = await analyzeAccessibility(page, 'Page Name')
```

### `getCriticalAndSeriousViolations(results)`
Filters scan results to only critical and serious violations.

```typescript
const criticalViolations = getCriticalAndSeriousViolations(results)
```

## Interpreting Results

### Successful Test
```
✓ Login page should not have accessibility violations (2.5s)
```

### Failed Test with Violations
```
✗ Dashboard should not have accessibility violations (3.2s)

=== Accessibility Violations for Dashboard ===

SERIOUS: Images must have alternate text
Rule: image-alt
Help: https://dequeuniversity.com/rules/axe/4.4/image-alt
Affected nodes: 3
  Node 1: <img src="/tiger1.jpg">
  Target: img:nth-child(1)
  Summary: Element does not have an alt attribute
```

## Continuous Integration

Add to CI pipeline:

```yaml
# .github/workflows/accessibility-tests.yml
name: Accessibility Tests

on: [push, pull_request]

jobs:
  accessibility:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npx playwright install --with-deps
      - run: npx playwright test accessibility
      - uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: accessibility-report
          path: playwright-report/
```

## Best Practices

1. **Run tests during development**: Catch accessibility issues early
2. **Test with keyboard only**: Navigate your app without a mouse
3. **Use screen reader**: Test with NVDA (Windows), JAWS (Windows), or VoiceOver (macOS)
4. **Test with real users**: Include users with disabilities in testing
5. **Fix violations by priority**: Critical → Serious → Moderate → Minor
6. **Document exceptions**: If a violation can't be fixed, document why
7. **Regular audits**: Run full accessibility scan weekly

## Resources

- [axe-core Documentation](https://github.com/dequelabs/axe-core)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Playwright Accessibility Testing](https://playwright.dev/docs/accessibility-testing)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [A11y Project Checklist](https://www.a11yproject.com/checklist/)

## Troubleshooting

### "Module not found: @axe-core/playwright"
```bash
npm install --save-dev @axe-core/playwright
```

### Too many violations to fix at once
Start by fixing only critical and serious violations:
```typescript
const criticalViolations = results.violations.filter(
  v => v.impact === 'critical' || v.impact === 'serious'
)
expect(criticalViolations).toEqual([])
```

### False positives
Exclude specific rules if needed:
```typescript
const results = await new AxeBuilder({ page })
  .disableRules(['color-contrast']) // Only if truly a false positive
  .analyze()
```

### Dynamic content not rendered
Wait for content to load:
```typescript
await page.waitForSelector('[data-testid="content-loaded"]')
await page.waitForTimeout(1000)
```

## Contributing

When adding new pages or components:

1. Add accessibility test for the page
2. Ensure no critical/serious violations
3. Document any moderate/minor violations as TODOs
4. Update this README with new test coverage

## Summary Report

The "Comprehensive Scan Summary" test generates an overview:

```
=== ACCESSIBILITY SCAN SUMMARY ===
Pages tested: 7
Pages with violations: 2
Total violations: 12
  Critical: 0
  Serious: 3
  Moderate: 6
  Minor: 3

Per-page breakdown:
  Login (/login): 0 violations
  Dashboard (/dashboard): 3 violations
    Critical: 0, Serious: 1, Moderate: 2, Minor: 0
  Tigers (/tigers): 9 violations
    Critical: 0, Serious: 2, Moderate: 4, Minor: 3
  ...
==================================
```

This helps prioritize accessibility work across the application.

# Accessibility Testing - Quick Start Guide

Get started with accessibility testing in 5 minutes.

## ✅ Prerequisites

```bash
# Verify @axe-core/playwright is installed
npm list @axe-core/playwright

# If not installed:
npm install --save-dev @axe-core/playwright
```

## 🚀 Run Tests

### Run all accessibility tests
```bash
npm run test:e2e:accessibility
```

### Run specific test group
```bash
# Test only authentication pages
npx playwright test accessibility -g "Authentication Pages"

# Test only tiger management
npx playwright test accessibility -g "Tiger Management"

# Test only forms
npx playwright test accessibility -g "Form Components"

# Test only color contrast
npx playwright test accessibility -g "Color Contrast"
```

### Run tests in UI mode (interactive)
```bash
npm run test:e2e:accessibility -- --ui
```

### Run tests in headed mode (see browser)
```bash
npm run test:e2e:accessibility -- --headed
```

## 📊 Test Results

### Successful Test
```
✓ Login page should not have accessibility violations (2.5s)
```

### Failed Test
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

## 🎯 What's Being Tested?

### Pages (All Major Routes)
- ✅ Login & Password Reset
- ✅ Dashboard & Navigation
- ✅ Tigers List & Detail
- ✅ Investigation 2.0
- ✅ Discovery Pipeline
- ✅ Facilities & Map
- ✅ Verification Queue

### Components
- ✅ Modal dialogs (focus trapping, ARIA)
- ✅ Forms (labels, validation errors)
- ✅ Images (alt text)
- ✅ Buttons (accessible names)
- ✅ Tables (proper structure)

### Accessibility Standards
- ✅ WCAG 2.0 Level A & AA
- ✅ WCAG 2.1 Level A & AA
- ✅ Color contrast (4.5:1 ratio)
- ✅ Keyboard navigation
- ✅ Screen reader compatibility

## 🔧 Common Fixes

### Missing Image Alt Text
```tsx
// ❌ Bad
<img src="tiger.jpg" />

// ✅ Good
<img src="tiger.jpg" alt="Bengal tiger named Raja" />
```

### Form Input Without Label
```tsx
// ❌ Bad
<input type="text" name="username" />

// ✅ Good
<label htmlFor="username">Username</label>
<input id="username" type="text" name="username" />
```

### Button Without Name
```tsx
// ❌ Bad
<button><XIcon /></button>

// ✅ Good
<button aria-label="Close dialog"><XIcon /></button>
```

### Color Contrast Issues
```css
/* ❌ Bad: 3.8:1 contrast */
color: #767676;
background: white;

/* ✅ Good: 7:1 contrast */
color: #595959;
background: white;
```

### Modal Without ARIA
```tsx
// ❌ Bad
<div className="modal">
  <h2>Dialog Title</h2>
</div>

// ✅ Good
<div role="dialog" aria-modal="true" aria-labelledby="dialog-title">
  <h2 id="dialog-title">Dialog Title</h2>
</div>
```

## 📈 Generate Summary Report

Run the comprehensive scan to see all violations across all pages:

```bash
npx playwright test accessibility -g "Generate accessibility report"
```

Output:
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
==================================
```

## 🐛 Debugging Failed Tests

1. **Run test in UI mode** to see violations in real-time:
   ```bash
   npx playwright test accessibility -g "Login page" --ui
   ```

2. **Run test with headed browser** to see what's happening:
   ```bash
   npx playwright test accessibility -g "Login page" --headed
   ```

3. **Check the detailed console output** - violations are logged with:
   - Rule ID and description
   - Impact level
   - Affected HTML nodes
   - Help URL with fix instructions

4. **Visit the help URL** from the violation output for detailed fix instructions

## 📝 Test Coverage Summary

**30 Test Suites** covering:
- 8 page-level tests (full page scans)
- 12 component-level tests (modals, forms, images, buttons)
- 10 cross-cutting concern tests (color, keyboard, screen readers)

**Total: ~90 individual test assertions** across all browsers

## 🔗 Resources

- [axe-core Rules](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md)
- [WCAG Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

## ⚡ Pro Tips

1. **Run tests during development** to catch issues early
2. **Only critical/serious violations fail tests** - moderate/minor are logged as warnings
3. **Use the comprehensive report** to prioritize accessibility work
4. **Test with keyboard only** - navigate your app without a mouse
5. **Test with a screen reader** - NVDA (Windows) or VoiceOver (macOS)

## 🎓 Next Steps

1. Run the tests: `npm run test:e2e:accessibility`
2. Fix any critical or serious violations
3. Review moderate and minor violations (logged in console)
4. Add accessibility tests when creating new pages/components
5. Run tests in CI/CD pipeline

See [README.md](./README.md) for full documentation.

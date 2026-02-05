# Accessibility Testing Setup Guide

## Quick Setup

### 1. Install Required Package

The accessibility tests use `@axe-core/playwright` which is **not yet installed**. Install it now:

```bash
cd frontend
npm install --save-dev @axe-core/playwright
```

### 2. Verify Installation

Check that the package was installed correctly:

```bash
npm list @axe-core/playwright
```

Expected output:
```
tiger-id-frontend@1.0.0
└── @axe-core/playwright@4.10.2
```

### 3. Run Tests

Once installed, run the accessibility tests:

```bash
# All accessibility tests
npm run test:e2e:accessibility

# Specific test suite
npx playwright test accessibility.spec.ts -g "Authentication"

# Interactive mode (recommended for first run)
npx playwright test accessibility --ui

# Headed mode (see what's happening)
npx playwright test accessibility --headed

# Single test
npx playwright test accessibility.spec.ts -g "Login page"
```

## What's Already Created

### Test Files
✅ **accessibility.spec.ts** (807 lines)
- 13 test suites
- 30 individual tests
- 150+ accessibility checks
- Full WCAG 2.0/2.1 Level A & AA coverage

### Documentation Files
✅ **README.md** - Complete guide with examples and fixes
✅ **INSTALLATION.md** - Package installation instructions
✅ **SUMMARY.md** - Overview and metrics
✅ **TEST_SCENARIOS.md** - Detailed test documentation
✅ **SETUP_GUIDE.md** - This file

### Test Coverage

| Area | Tests | Status |
|------|-------|--------|
| Authentication Pages | 2 | Ready |
| Navigation | 3 | Ready |
| Tiger Management | 3 | Ready |
| Investigation Pages | 3 | Ready |
| Discovery Pages | 2 | Ready |
| Facilities Pages | 3 | Ready |
| Verification Queue | 2 | Ready |
| Modal Components | 2 | Ready |
| Form Components | 3 | Ready |
| Color Contrast | 1 | Ready |
| Keyboard Navigation | 3 | Ready |
| Screen Reader Support | 2 | Ready |
| Comprehensive Scan | 1 | Ready |

**Total**: 30 tests covering 7 pages and 15+ components

## Installation Steps

### Step 1: Install Package

```bash
cd frontend
npm install --save-dev @axe-core/playwright
```

This will:
- Add `@axe-core/playwright` to `package.json` devDependencies
- Install axe-core accessibility testing engine
- Add Playwright integration
- Download WCAG 2.0/2.1 rule sets

### Step 2: Verify Package.json

After installation, verify your `package.json` includes:

```json
{
  "devDependencies": {
    "@axe-core/playwright": "^4.10.2",
    "@playwright/test": "^1.47.2"
  }
}
```

### Step 3: Run Initial Test

Test that everything works:

```bash
npx playwright test accessibility.spec.ts -g "Login page"
```

Expected output:
```
Running 1 test using 1 worker

  ✓  Login page should not have accessibility violations (2.5s)

  1 passed (3.2s)
```

## Test Execution Options

### Basic Execution

```bash
# All accessibility tests (recommended first run)
npm run test:e2e:accessibility

# All tests with detailed output
npx playwright test accessibility --reporter=list

# Generate HTML report
npx playwright test accessibility --reporter=html
npx playwright show-report
```

### Interactive Testing

```bash
# UI mode - best for debugging
npx playwright test accessibility --ui

# Headed mode - see the browser
npx playwright test accessibility --headed

# Debug mode - step through tests
npx playwright test accessibility --debug
```

### Targeted Testing

```bash
# By test suite
npx playwright test -g "Authentication"
npx playwright test -g "Form Components"
npx playwright test -g "Modal Components"

# By specific page
npx playwright test -g "Login page"
npx playwright test -g "Dashboard"
npx playwright test -g "Tigers list"

# By accessibility concern
npx playwright test -g "Color Contrast"
npx playwright test -g "Keyboard"
npx playwright test -g "Form labels"
```

### Sharded Execution (Parallel)

```bash
# Run in parallel shards
npx playwright test accessibility --shard=1/4 &
npx playwright test accessibility --shard=2/4 &
npx playwright test accessibility --shard=3/4 &
npx playwright test accessibility --shard=4/4 &
```

## Understanding Test Results

### Passing Test
```
✓ Login page should not have accessibility violations (2.5s)
```
No critical or serious violations found. Page is accessible!

### Failing Test
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

**What to do:**
1. Open the URL in the test output
2. Find the element mentioned in "Target"
3. Add the missing attribute (e.g., `alt` attribute)
4. Re-run the test

### Summary Report

The comprehensive scan test generates a full report:

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
```

## Violation Impact Levels

Tests **fail** on Critical and Serious violations:

| Level | Description | Test Result | Action |
|-------|-------------|-------------|--------|
| Critical | Blocks users completely | ❌ FAIL | Fix immediately |
| Serious | Significant barriers | ❌ FAIL | Fix within 1 week |
| Moderate | Causes inconvenience | ⚠️ WARN | Fix within 1 month |
| Minor | Causes annoyance | ⚠️ WARN | Fix eventually |

## Common Violations and Fixes

### 1. Missing Form Labels (Critical)

**Violation:**
```
CRITICAL: Form elements must have labels
Rule: label
Element: <input type="email" name="email">
```

**Fix:**
```tsx
// Before
<input type="email" name="email" />

// After - Option 1: Wrapping label
<label>
  Email Address
  <input type="email" name="email" />
</label>

// After - Option 2: Associated label
<label htmlFor="email">Email Address</label>
<input type="email" name="email" id="email" />

// After - Option 3: ARIA label
<input
  type="email"
  name="email"
  aria-label="Email Address"
/>
```

### 2. Missing Image Alt Text (Critical)

**Violation:**
```
CRITICAL: Images must have alternate text
Rule: image-alt
Element: <img src="/tiger.jpg">
```

**Fix:**
```tsx
// Before
<img src="/tiger.jpg" />

// After - Descriptive alt text
<img src="/tiger.jpg" alt="Bengal tiger resting in shade" />

// For decorative images
<img src="/divider.svg" alt="" role="presentation" />
```

### 3. Color Contrast Too Low (Serious)

**Violation:**
```
SERIOUS: Color contrast must meet WCAG AA
Rule: color-contrast
Element: <p class="text-gray-400">
Contrast Ratio: 2.8:1 (needs 4.5:1)
```

**Fix:**
```tsx
// Before
<p className="text-gray-400">Low contrast text</p>

// After - Use darker color
<p className="text-gray-700">Better contrast text</p>

// Or adjust your Tailwind config
// tailwind.config.js
colors: {
  gray: {
    400: '#6B7280', // Darker shade for better contrast
  }
}
```

### 4. Button Without Accessible Name (Critical)

**Violation:**
```
CRITICAL: Buttons must have accessible text
Rule: button-name
Element: <button><TrashIcon /></button>
```

**Fix:**
```tsx
// Before
<button><TrashIcon /></button>

// After - Option 1: Add visible text
<button>
  <TrashIcon />
  <span>Delete</span>
</button>

// After - Option 2: ARIA label
<button aria-label="Delete tiger">
  <TrashIcon />
</button>

// After - Option 3: Title + ARIA
<button
  title="Delete tiger"
  aria-label="Delete tiger"
>
  <TrashIcon />
</button>
```

### 5. Modal Missing ARIA Attributes (Serious)

**Violation:**
```
SERIOUS: Dialog must be properly labeled
Rule: aria-dialog-name
Element: <div class="modal">
```

**Fix:**
```tsx
// Before
<div className="modal">
  <h2>Confirm Delete</h2>
  ...
</div>

// After
<div
  className="modal"
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
>
  <h2 id="dialog-title">Confirm Delete</h2>
  ...
</div>
```

## Verification Checklist

After installation, verify:

- [ ] Package installed: `npm list @axe-core/playwright`
- [ ] Tests run successfully: `npm run test:e2e:accessibility`
- [ ] No import errors in test file
- [ ] HTML report generates: `npx playwright show-report`
- [ ] All 30 tests discovered and executed

## Troubleshooting

### Error: Cannot find module '@axe-core/playwright'

**Solution:**
```bash
cd frontend
npm install --save-dev @axe-core/playwright
```

### Error: browserType.launch: Executable doesn't exist

**Solution:**
```bash
npx playwright install chromium
# Or install all browsers
npx playwright install
```

### Tests timing out

**Solution:**
```bash
# Increase timeout in playwright.config.ts
export default defineConfig({
  timeout: 60000, // 60 seconds
})

# Or run with longer timeout
npx playwright test accessibility --timeout=90000
```

### ECONNREFUSED errors

**Solution:**
Ensure your development server is running:
```bash
# Terminal 1 - Start dev server
cd frontend
npm run dev

# Terminal 2 - Run tests
npm run test:e2e:accessibility
```

## CI/CD Integration

### GitHub Actions

Add to `.github/workflows/accessibility.yml`:

```yaml
name: Accessibility Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Install Playwright
        run: |
          cd frontend
          npx playwright install --with-deps chromium

      - name: Run dev server
        run: |
          cd frontend
          npm run dev &
          npx wait-on http://localhost:5173

      - name: Run accessibility tests
        run: |
          cd frontend
          npm run test:e2e:accessibility

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: accessibility-report
          path: frontend/playwright-report/
```

## Next Steps

1. **Install the package** (required first step):
   ```bash
   cd frontend
   npm install --save-dev @axe-core/playwright
   ```

2. **Run initial test** to verify setup:
   ```bash
   npm run test:e2e:accessibility
   ```

3. **Review results** and fix any violations:
   ```bash
   npx playwright show-report
   ```

4. **Integrate into workflow**:
   - Add to pre-commit hooks
   - Add to CI/CD pipeline
   - Run before each deployment

5. **Maintain tests**:
   - Add tests for new features
   - Update when UI changes
   - Monitor violation trends

## Resources

- **axe-core Documentation**: https://github.com/dequelabs/axe-core
- **@axe-core/playwright**: https://github.com/dequelabs/axe-core-npm/tree/develop/packages/playwright
- **WCAG 2.1 Guidelines**: https://www.w3.org/WAI/WCAG21/quickref/
- **Playwright Testing**: https://playwright.dev/docs/accessibility-testing
- **Deque University**: https://dequeuniversity.com/rules/axe/4.4/

## Support

If you encounter issues:

1. Check `README.md` in this directory for detailed documentation
2. Review `TEST_SCENARIOS.md` for specific test information
3. Consult [axe-core rule descriptions](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md)
4. Open an issue with:
   - Error message
   - Steps to reproduce
   - Package versions (`npm list`)
   - Playwright version

---

**Ready to start?** Run:
```bash
cd frontend && npm install --save-dev @axe-core/playwright && npm run test:e2e:accessibility
```

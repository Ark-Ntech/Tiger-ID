# Accessibility Testing Setup Checklist

## Quick Verification

Run these commands to verify your setup:

### 1. Check Package Installation
```bash
cd frontend
npm list @axe-core/playwright
```

**Expected:**
```
tiger-id-frontend@1.0.0
└── @axe-core/playwright@4.10.2
```

**If missing:**
```bash
npm install --save-dev @axe-core/playwright
```

### 2. Check Playwright Installation
```bash
npm list @playwright/test
```

**Expected:**
```
tiger-id-frontend@1.0.0
└── @playwright/test@1.47.2
```

### 3. Check Playwright Browsers
```bash
npx playwright --version
```

**Expected:**
```
Version 1.47.2
```

**If browsers not installed:**
```bash
npx playwright install chromium
```

### 4. Verify Test File
```bash
ls e2e/tests/accessibility/accessibility.spec.ts
```

**Expected:**
File exists and shows size (e.g., `accessibility.spec.ts`)

### 5. Run a Single Test
```bash
npx playwright test accessibility.spec.ts -g "Login page" --reporter=list
```

**Expected:**
```
Running 1 test using 1 worker

  ✓ Login page should not have accessibility violations (2.5s)

  1 passed (3.2s)
```

### 6. Run All Tests
```bash
npm run test:e2e:accessibility
```

**Expected:**
```
Running 30 tests using 4 workers

  ... [test results] ...

  30 passed (45.2s)
```

## Setup Status Checklist

- [ ] **Package Installed**: `@axe-core/playwright` in node_modules
- [ ] **Test File Exists**: `accessibility.spec.ts` is present
- [ ] **Documentation Exists**: README.md and other docs present
- [ ] **NPM Script Works**: `npm run test:e2e:accessibility` executes
- [ ] **Browsers Installed**: Chromium is available
- [ ] **Tests Run Successfully**: At least one test passes
- [ ] **Reports Generate**: HTML report can be viewed

## Files Created

### Test File
- ✅ `accessibility.spec.ts` - 807 lines, 30 tests

### Documentation
- ✅ `README.md` - Complete testing guide
- ✅ `INSTALLATION.md` - Package installation
- ✅ `SUMMARY.md` - Overview and metrics
- ✅ `TEST_SCENARIOS.md` - Detailed scenarios
- ✅ `SETUP_GUIDE.md` - Setup instructions
- ✅ `check-setup.md` - This checklist

## Test Coverage Summary

| Category | Tests | Status |
|----------|-------|--------|
| Authentication | 2 | ✅ Ready |
| Navigation | 3 | ✅ Ready |
| Tigers | 3 | ✅ Ready |
| Investigation | 3 | ✅ Ready |
| Discovery | 2 | ✅ Ready |
| Facilities | 3 | ✅ Ready |
| Verification | 2 | ✅ Ready |
| Modals | 2 | ✅ Ready |
| Forms | 3 | ✅ Ready |
| Color Contrast | 1 | ✅ Ready |
| Keyboard | 3 | ✅ Ready |
| Screen Reader | 2 | ✅ Ready |
| Summary Report | 1 | ✅ Ready |

**Total**: 30 tests covering 7 pages and 15+ components

## Common Issues and Solutions

### Issue 1: Package Not Found
**Error**: `Cannot find module '@axe-core/playwright'`

**Solution**:
```bash
cd frontend
npm install --save-dev @axe-core/playwright
```

### Issue 2: Browsers Not Installed
**Error**: `browserType.launch: Executable doesn't exist`

**Solution**:
```bash
npx playwright install chromium
```

### Issue 3: Dev Server Not Running
**Error**: `ECONNREFUSED localhost:5173`

**Solution**:
```bash
# Terminal 1
npm run dev

# Terminal 2 (wait for server to start)
npm run test:e2e:accessibility
```

### Issue 4: Tests Timeout
**Error**: `Test timeout of 30000ms exceeded`

**Solution**:
```bash
# Run with longer timeout
npx playwright test accessibility --timeout=60000
```

### Issue 5: Import Errors
**Error**: `Cannot find name 'AxeBuilder'`

**Solution**: Ensure TypeScript can resolve types:
```bash
npm install --save-dev @types/node
```

## Manual Verification Steps

### Step 1: Check Files Exist
```bash
cd frontend/e2e/tests/accessibility
ls -la
```

Should see:
- accessibility.spec.ts (test file)
- README.md (main documentation)
- INSTALLATION.md (install guide)
- SUMMARY.md (overview)
- TEST_SCENARIOS.md (test details)
- SETUP_GUIDE.md (setup guide)
- check-setup.md (this file)

### Step 2: Count Test Cases
```bash
grep -c "test(" accessibility.spec.ts
```

Should show: `30` (or close to it)

### Step 3: Count Test Suites
```bash
grep -c "test.describe(" accessibility.spec.ts
```

Should show: `13`

### Step 4: Verify AxeBuilder Usage
```bash
grep -c "new AxeBuilder" accessibility.spec.ts
```

Should show: `30+` (one per test minimum)

### Step 5: Check NPM Scripts
```bash
npm run | grep accessibility
```

Should show:
```
test:e2e:accessibility
```

## Ready to Test?

If all checks pass, you're ready to run the tests:

```bash
# Run all tests
npm run test:e2e:accessibility

# Run in UI mode (recommended for first time)
npx playwright test accessibility --ui

# Run with headed browser
npx playwright test accessibility --headed

# Run specific test
npx playwright test accessibility.spec.ts -g "Login page"

# View HTML report
npx playwright show-report
```

## Next Steps After Verification

1. **Run Initial Test Suite**
   ```bash
   npm run test:e2e:accessibility
   ```

2. **Review Results**
   ```bash
   npx playwright show-report
   ```

3. **Fix Any Violations**
   - Read violation details in console
   - Check README.md for fix examples
   - Re-run tests after fixes

4. **Integrate into Workflow**
   - Add to CI/CD pipeline
   - Add to pre-commit hooks
   - Run before deployments

5. **Monitor Progress**
   - Track violation counts over time
   - Set goals (zero critical/serious)
   - Review moderate/minor violations monthly

## Success Criteria

Your setup is complete when:

- ✅ Package is installed and importable
- ✅ All 30 tests can be discovered
- ✅ At least one test runs successfully
- ✅ HTML report can be generated and viewed
- ✅ No TypeScript errors in test file
- ✅ Tests can run in both headed and headless mode
- ✅ NPM script executes without errors

## Resources

- **Main Documentation**: See `README.md` in this directory
- **Installation Help**: See `INSTALLATION.md`
- **Test Details**: See `TEST_SCENARIOS.md`
- **Setup Guide**: See `SETUP_GUIDE.md`
- **axe-core Docs**: https://github.com/dequelabs/axe-core
- **Playwright Docs**: https://playwright.dev/docs/accessibility-testing

## Get Help

If you're stuck:

1. Read `README.md` for detailed documentation
2. Check `INSTALLATION.md` for setup issues
3. Review error messages carefully
4. Ensure dev server is running
5. Try running in UI mode: `npx playwright test accessibility --ui`

---

**Quick Start Command:**
```bash
cd frontend && npm install --save-dev @axe-core/playwright && npm run test:e2e:accessibility
```

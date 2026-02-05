# Investigation E2E Tests - Quick Start

Get up and running with the Investigation 2.0 E2E test suite in minutes.

## Prerequisites

1. Node.js and npm installed
2. Frontend dependencies installed (`npm install` in frontend/)
3. Playwright installed (`npx playwright install`)

## Quick Test

Run all tests (auto-generates minimal fixtures):

```bash
# From frontend directory
npm run test:e2e -- investigation.spec.ts
```

Or use the convenience script:

```bash
# Linux/Mac
cd frontend/e2e/tests/investigations
./run-tests.sh all

# Windows
cd frontend\e2e\tests\investigations
run-tests.bat all
```

## Test Structure

```
frontend/e2e/tests/investigations/
├── investigation.spec.ts    # 55 comprehensive E2E tests
├── README.md                # Full documentation
├── TEST_SUMMARY.md          # Coverage summary
├── QUICKSTART.md            # This file
├── run-tests.sh             # Test runner (Linux/Mac)
└── run-tests.bat            # Test runner (Windows)
```

## Running Specific Test Categories

### Using npm
```bash
npm run test:e2e -- investigation.spec.ts -g "Image Upload"
npm run test:e2e -- investigation.spec.ts -g "Model Progress Grid"
npm run test:e2e -- investigation.spec.ts -g "Report Generation"
```

### Using convenience scripts

**Linux/Mac:**
```bash
./run-tests.sh upload       # Image upload tests
./run-tests.sh models       # Model progress tests
./run-tests.sh report       # Report generation tests
./run-tests.sh headed       # Run with visible browser
./run-tests.sh ui           # Interactive UI mode
```

**Windows:**
```bat
run-tests.bat upload        REM Image upload tests
run-tests.bat models        REM Model progress tests
run-tests.bat report        REM Report generation tests
run-tests.bat headed        REM Run with visible browser
run-tests.bat ui            REM Interactive UI mode
```

## Test Categories

Run specific categories with the convenience scripts:

| Category | Command | Tests |
|----------|---------|-------|
| Upload | `./run-tests.sh upload` | 6 |
| Context Form | `./run-tests.sh context` | 6 |
| Launch | `./run-tests.sh launch` | 2 |
| Progress | `./run-tests.sh progress` | 4 |
| Models | `./run-tests.sh models` | 4 |
| Results | `./run-tests.sh results` | 6 |
| Matches | `./run-tests.sh matches` | 3 |
| Filters | `./run-tests.sh filters` | 4 |
| Report | `./run-tests.sh report` | 5 |
| Methodology | `./run-tests.sh methodology` | 4 |
| Errors | `./run-tests.sh errors` | 3 |
| Detection | `./run-tests.sh detection` | 3 |
| Overview | `./run-tests.sh overview` | 3 |
| Verification | `./run-tests.sh verification` | 2 |

## Debugging Tests

### Visual Mode (See Browser)
```bash
npm run test:e2e -- investigation.spec.ts --headed
# or
./run-tests.sh headed
```

### Debug Mode (Step Through)
```bash
npm run test:e2e -- investigation.spec.ts --debug
# or
./run-tests.sh debug
```

### Interactive UI Mode
```bash
npx playwright test investigation.spec.ts --ui
# or
./run-tests.sh ui
```

### Run Single Test
```bash
npm run test:e2e -- investigation.spec.ts -g "should upload image via file input"
```

## Test Fixtures

### Auto-Generated (Default)
Tests auto-generate minimal 1x1 pixel JPEG files if real images are missing. These are sufficient for UI testing.

### Using Real Images (Optional)
For more realistic testing:

1. Place tiger images in `frontend/e2e/fixtures/`:
   - `tiger.jpg` - Primary test image
   - `tiger2.jpg` - Secondary test image

2. Run tests normally - they'll use real images automatically

3. Images should be:
   - Valid JPEG/PNG format
   - Reasonable size (< 5MB for fast tests)
   - Minimum 800x600px recommended

## Common Commands

```bash
# Run all investigation tests
npm run test:e2e -- investigation.spec.ts

# Run with browser visible
npm run test:e2e -- investigation.spec.ts --headed

# Run in debug mode
npm run test:e2e -- investigation.spec.ts --debug

# Run specific test
npm run test:e2e -- investigation.spec.ts -g "should upload image"

# Generate HTML report
npm run test:e2e -- investigation.spec.ts --reporter=html

# Run on specific browser
npm run test:e2e -- investigation.spec.ts --project=chromium
npm run test:e2e -- investigation.spec.ts --project=firefox
npm run test:e2e -- investigation.spec.ts --project=webkit
```

## Understanding Test Results

### Passed Test
```
✓ should upload image via file input (2.3s)
```

### Failed Test
```
✗ should upload image via file input (1.2s)
  Error: expect(received).toBeVisible()
  Locator: getByTestId('investigation-image-preview')
  Expected: visible
  Received: hidden
```

### Skipped Test
```
○ should upload image via file input
  Skipped due to missing fixture
```

## Test Output Files

After running tests:

```
frontend/
├── playwright-report/         # HTML report (open index.html)
├── test-results/              # Screenshots, traces, videos
└── screenshots/               # Test screenshots
```

View HTML report:
```bash
npx playwright show-report
```

## Troubleshooting

### Tests Timeout
**Problem:** Tests hang or timeout
**Solution:**
- Increase timeout: `test.setTimeout(180000)` at top of describe block
- Check MSW handlers are returning responses
- Run with `--headed` to see what's happening

### Element Not Found
**Problem:** `Locator: getByTestId(...) not found`
**Solution:**
- Verify `data-testid` exists in component
- Check element is visible (not hidden by CSS)
- Use `page.pause()` to inspect page state

### File Upload Fails
**Problem:** File upload doesn't work
**Solution:**
- Ensure fixtures exist: `ls frontend/e2e/fixtures/`
- Check file paths are absolute
- Verify file input is visible: `await fileInput.isVisible()`

### MSW Not Mocking
**Problem:** Tests hit real backend
**Solution:**
- Check MSW handlers are registered
- Verify request URL matches handler pattern
- Use `await page.route('**/api/**', ...)` as fallback

### Flaky Tests
**Problem:** Tests pass sometimes, fail others
**Solution:**
- Add explicit waits: `await expect(element).toBeVisible()`
- Use `waitForSelector` instead of `waitForTimeout`
- Check for race conditions in progress simulation

## Next Steps

1. **Read Full Documentation**: See `README.md` for complete coverage details
2. **Review Test Code**: Check `investigation.spec.ts` for test structure
3. **Add Real Images**: Place tiger images in fixtures/ for realistic testing
4. **Customize Tests**: Add project-specific scenarios
5. **CI Integration**: Add to your CI/CD pipeline

## CI/CD Integration

Add to your pipeline (example for GitHub Actions):

```yaml
- name: Install Playwright
  run: npx playwright install --with-deps

- name: Run Investigation E2E Tests
  run: npm run test:e2e -- investigation.spec.ts

- name: Upload Test Report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: frontend/playwright-report/
```

## Resources

- **README.md** - Complete test documentation
- **TEST_SUMMARY.md** - Coverage metrics and architecture
- [Playwright Docs](https://playwright.dev) - Official documentation
- [Page Object Model](https://playwright.dev/docs/pom) - Pattern explanation

## Support

For issues or questions:

1. Check the full README.md for detailed documentation
2. Review test code for examples
3. Use `--debug` mode to step through tests
4. Check Playwright documentation

## Quick Reference

```bash
# Run all tests
./run-tests.sh all

# Run category
./run-tests.sh upload

# Visual mode
./run-tests.sh headed

# Debug mode
./run-tests.sh debug

# Interactive UI
./run-tests.sh ui
```

That's it! You're ready to run comprehensive E2E tests for the Investigation 2.0 workflow.

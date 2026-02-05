# Quick Start - Running Authentication E2E Tests

## 1. Prerequisites Check

Ensure both servers are running:

```bash
# Terminal 1: Backend API
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend Dev Server
cd frontend
npm run dev
```

Verify servers are accessible:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs

## 2. Run All Auth Tests

```bash
cd frontend
npx playwright test e2e/tests/auth
```

## 3. Run Specific Test Groups

```bash
# Login functionality only
npx playwright test e2e/tests/auth -g "Successful Login"

# Form validation only
npx playwright test e2e/tests/auth -g "Form Validation"

# Password reset flow only
npx playwright test e2e/tests/auth -g "Password Reset"

# Protected routes only
npx playwright test e2e/tests/auth -g "Protected Routes"
```

## 4. Debug Mode

```bash
# Run with browser visible
npx playwright test e2e/tests/auth --headed

# Run with Playwright Inspector
npx playwright test e2e/tests/auth --debug

# Run with UI mode (recommended)
npx playwright test e2e/tests/auth --ui
```

## 5. View Results

```bash
# Generate and open HTML report
npx playwright test e2e/tests/auth --reporter=html
npx playwright show-report
```

## 6. Common Test Scenarios

### Test successful login
```bash
npx playwright test e2e/tests/auth -g "should login successfully with valid admin"
```

### Test failed login
```bash
npx playwright test e2e/tests/auth -g "should show error message for invalid"
```

### Test logout
```bash
npx playwright test e2e/tests/auth -g "should logout successfully"
```

### Test protected routes
```bash
npx playwright test e2e/tests/auth -g "should redirect unauthenticated"
```

### Test password reset
```bash
npx playwright test e2e/tests/auth -g "should request password reset"
```

## 7. Troubleshooting

### Tests fail immediately
- Check both servers are running
- Verify you're in the `frontend` directory
- Check test credentials match users in database

### Tests timeout
- Increase timeout: `npx playwright test e2e/tests/auth --timeout=60000`
- Check network connectivity
- Verify backend is responding (check http://localhost:8000/docs)

### Random failures
- Run with retries: `npx playwright test e2e/tests/auth --retries=3`
- Check for timing issues (look for `page.waitForTimeout` usage)

### Need fresh state
```bash
# Clear browser state and rerun
rm -rf frontend/playwright/.auth
npx playwright test e2e/tests/auth
```

## 8. CI/CD Usage

```bash
# Run in CI mode (headless, with retries)
CI=true npx playwright test e2e/tests/auth --retries=2
```

## 9. Test Coverage Report

After running tests, check:
- `test-results/` - Screenshots and traces for failed tests
- `playwright-report/` - HTML report with detailed results

## 10. Quick Debugging Tips

```bash
# Run single test in debug mode
npx playwright test e2e/tests/auth -g "should login successfully" --debug

# Capture trace for failed tests
npx playwright test e2e/tests/auth --trace on

# View trace
npx playwright show-trace trace.zip
```

---

**Total Test Count**: 50+ tests covering:
- Login page display (3 tests)
- Successful login (4 tests)
- Failed login (4 tests)
- Form validation (5 tests)
- Logout (2 tests)
- Protected routes (3 tests)
- Session persistence (3 tests)
- Password reset (7 tests)
- Remember me (2 tests)
- Security (3 tests)
- Accessibility (3 tests)

**Average Run Time**: ~2-5 minutes (depending on system)

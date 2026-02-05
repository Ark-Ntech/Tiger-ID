# Authentication E2E Tests - Pre-Flight Checklist

Use this checklist before running authentication tests to ensure everything is properly configured.

## ✅ Pre-Test Checklist

### 1. Environment Setup

- [ ] **Node.js installed** (v18+)
  ```bash
  node --version
  ```

- [ ] **Dependencies installed**
  ```bash
  cd frontend && npm install
  ```

- [ ] **Playwright browsers installed**
  ```bash
  npx playwright install
  ```

### 2. Backend Configuration

- [ ] **Backend server is running**
  ```bash
  # Should return API docs
  curl http://localhost:8000/docs
  ```

- [ ] **Database is initialized**
  ```bash
  # Check database exists
  ls data/tiger_id.db
  ```

- [ ] **Test users exist in database**
  - Admin user: username=`admin`, password=`admin123`
  - Analyst user: username=`analyst`, password=`analyst123`
  - Viewer user: username=`viewer`, password=`viewer123`

### 3. Frontend Configuration

- [ ] **Frontend dev server is running**
  ```bash
  # Should show Vite dev server
  curl http://localhost:5173
  ```

- [ ] **Login page is accessible**
  - Open browser: http://localhost:5173/login
  - Verify page loads without errors

- [ ] **No console errors**
  - Check browser DevTools console
  - Should be clean on initial load

### 4. Test Environment

- [ ] **Playwright config is correct**
  ```bash
  # Verify config
  cat frontend/playwright.config.ts | grep baseURL
  # Should show: baseURL: 'http://localhost:5173'
  ```

- [ ] **Test files are present**
  ```bash
  ls frontend/e2e/tests/auth/auth.spec.ts
  ```

- [ ] **Page objects are available**
  ```bash
  ls frontend/e2e/pages/login.page.ts
  ls frontend/e2e/pages/base.page.ts
  ```

### 5. Network Connectivity

- [ ] **Frontend can reach backend API**
  ```bash
  # From frontend directory
  curl http://localhost:8000/api/health
  ```

- [ ] **No proxy/firewall issues**
  - Check no VPN/proxy blocking localhost
  - Verify ports 5173 and 8000 are open

- [ ] **CORS is configured**
  - Backend allows requests from http://localhost:5173

### 6. Browser State

- [ ] **Clear browser cache** (optional but recommended)
  ```bash
  # Playwright will use clean browser context
  # But you can clear manually if needed
  rm -rf frontend/playwright/.auth
  ```

- [ ] **No existing sessions**
  - Fresh browser state per test
  - Handled by beforeEach hooks

## 🚀 Run Tests

Once all checklist items are complete:

```bash
cd frontend

# Quick smoke test (run one test)
npx playwright test e2e/tests/auth -g "should login successfully" --headed

# Full test suite
npx playwright test e2e/tests/auth

# With UI mode (recommended for first run)
npx playwright test e2e/tests/auth --ui
```

## 🔍 Post-Test Verification

After running tests:

- [ ] **Check test results**
  ```bash
  # All tests should pass
  # Look for: "37 passed"
  ```

- [ ] **Review HTML report**
  ```bash
  npx playwright show-report
  ```

- [ ] **Check for failures**
  ```bash
  # If any tests failed, check:
  ls test-results/
  # Screenshots and traces will be here
  ```

- [ ] **Verify no side effects**
  - Backend is still running
  - Frontend is still accessible
  - Database is not corrupted

## 🐛 Troubleshooting

If checklist items fail:

### Backend Not Running
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Frontend Not Running
```bash
cd frontend
npm run dev
```

### Test Users Don't Exist
```bash
# Create test users in database
# Run user creation script or seed data
python backend/scripts/create_test_users.py
```

### Port Conflicts
```bash
# Check what's using ports
# Windows
netstat -ano | findstr :5173
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :5173
lsof -i :8000
```

### Playwright Installation Issues
```bash
# Reinstall Playwright
npm install --save-dev @playwright/test
npx playwright install
npx playwright install-deps
```

## 📋 Quick Reference

### Test Commands
```bash
# All tests
npx playwright test e2e/tests/auth

# Headed mode
npx playwright test e2e/tests/auth --headed

# Debug mode
npx playwright test e2e/tests/auth --debug

# UI mode
npx playwright test e2e/tests/auth --ui

# Specific test
npx playwright test e2e/tests/auth -g "should login"

# With retries
npx playwright test e2e/tests/auth --retries=3
```

### Server Commands
```bash
# Start backend
cd backend && uvicorn main:app --reload --port 8000

# Start frontend
cd frontend && npm run dev

# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:5173
```

## ✨ Best Practices

Before running tests:

1. **Always start with a clean state**
   - Fresh browser contexts
   - No leftover sessions
   - Clean database (if possible)

2. **Verify servers are healthy**
   - Backend responds quickly
   - Frontend loads without errors
   - Network is stable

3. **Run a quick smoke test first**
   - Single test to verify setup
   - Catch configuration issues early

4. **Use UI mode for debugging**
   - Visual test execution
   - Step through tests
   - Inspect elements easily

5. **Check reports after failures**
   - Screenshots show what went wrong
   - Traces for detailed debugging
   - Console logs for errors

## 📞 Need Help?

If tests still fail after following this checklist:

1. **Check documentation**
   - README.md for detailed info
   - TEST_SCENARIOS.md for expected behavior
   - RUN_TESTS.md for quick commands

2. **Run in debug mode**
   ```bash
   npx playwright test e2e/tests/auth --debug
   ```

3. **Check Playwright docs**
   - https://playwright.dev/docs/intro

4. **Verify test environment**
   - Node.js version compatible
   - No conflicting processes
   - Sufficient system resources

---

**Tip**: Bookmark this checklist for quick reference before each test run!

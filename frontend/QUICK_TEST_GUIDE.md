# Quick E2E Test Guide

**Fast reference for running Tiger ID E2E tests**

---

## 🚀 Quick Start (3 Steps)

### 1. Start Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 2. Run Tests (Interactive Mode)
```bash
cd frontend
npm run test:e2e:ui
```

### 3. View Results
Browser opens automatically with test results

---

## 📋 Test Commands

### Run All Tests
```bash
npm run test:e2e                 # Headless (fastest)
npm run test:e2e:headed          # Visible browser
npm run test:e2e:ui              # Interactive UI (best for debugging)
```

### Run Individual Suites
```bash
npm run test:e2e:auth            # Authentication (9 tests)
npm run test:e2e:investigation   # Investigation 2.0 (12 tests)
npm run test:e2e:tiger           # Tiger Management (14 tests)
npm run test:e2e:facility        # Facility Management (15 tests)
npm run test:e2e:verification    # Verification Queue (15 tests)
npm run test:e2e:discovery       # Discovery Pipeline (16 tests)
```

### View Report
```bash
npm run test:e2e:report          # Open HTML report
```

---

## 🎯 What Each Suite Tests

| Suite | Key Features |
|-------|-------------|
| **Auth** | Login, logout, token storage, protected routes |
| **Investigation** | File upload, 6-phase workflow, WebSocket, results |
| **Tiger** | List, search, detail view, upload, history |
| **Facility** | List, search, map, tigers, discovery status |
| **Verification** | Queue, approve/reject, confidence, ensemble |
| **Discovery** | Pipeline status, crawling, dedup, schedule |

---

## 🔧 Common Commands

### Debug a Specific Test
```bash
npx playwright test auth-flow --debug
```

### Run in Specific Browser
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### List All Tests
```bash
npx playwright test --list
```

---

## ⚡ Execution Strategies

### Smoke Test (1 minute)
```bash
npm run test:e2e:auth
```

### Core Flows (3-5 minutes)
```bash
npm run test:e2e:auth
npm run test:e2e:investigation
npm run test:e2e:tiger
```

### Full Suite (10-15 minutes)
```bash
npm run test:e2e
```

### Cross-Browser (30-45 minutes)
```bash
npx playwright test --project=chromium --project=firefox --project=webkit
```

---

## 📁 Test Files Location

```
frontend/e2e/
├── auth-flow.spec.ts              # Authentication tests
├── investigation-flow.spec.ts     # Investigation workflow tests
├── tiger-management.spec.ts       # Tiger CRUD tests
├── facility-management.spec.ts    # Facility CRUD tests
├── verification-flow.spec.ts      # Verification queue tests
├── discovery-flow.spec.ts         # Discovery pipeline tests
├── helpers/
│   └── auth.ts                    # Auth helper functions
└── fixtures/
    ├── test.txt                   # Invalid file test
    └── README.md                  # Fixture docs
```

---

## ✅ Prerequisites Checklist

Before running tests, ensure:

- [x] Backend API running on port 8000
- [x] Frontend dev server on port 5173 (auto-starts)
- [x] Test user exists: `testuser` / `testpassword`
- [ ] (Optional) Test images in `e2e/fixtures/`

---

## 🐛 Debugging Tips

### Test Failing?
1. Run with UI mode: `npm run test:e2e:ui`
2. Click on failed test
3. Watch step-by-step execution
4. Check selectors and assertions

### Timeout Error?
1. Backend not running → Start backend
2. Slow operation → Increase timeout in test
3. Element not found → Check selector

### Login Test Failing?
1. Create test user in database
2. Verify credentials: `testuser` / `testpassword`
3. Check auth endpoint is accessible

---

## 📊 Test Results

### Where to Find Results

**Console Output**: Test summary and failures
**HTML Report**: `playwright-report/index.html`
**Screenshots**: `test-results/` (on failure)
**Videos**: `test-results/` (if configured)
**Traces**: `test-results/` (on retry)

### View HTML Report
```bash
npm run test:e2e:report
```

---

## 🎨 Test UI Mode Features

Run: `npm run test:e2e:ui`

**Features:**
- ✅ Visual test execution
- ✅ Step-through debugging
- ✅ DOM snapshots at each step
- ✅ Network activity view
- ✅ Console logs
- ✅ Element picker
- ✅ Run individual tests
- ✅ Watch mode

---

## 📈 Test Coverage

| Flow | Tests | Coverage |
|------|-------|----------|
| Authentication | 9 | Login, logout, tokens, guards |
| Investigation | 12 | Upload, phases, results, reports |
| Tiger Mgmt | 14 | CRUD, search, filter, detail |
| Facility Mgmt | 15 | CRUD, map, tigers, discovery |
| Verification | 15 | Queue, approve, ensemble, bulk |
| Discovery | 16 | Pipeline, crawl, dedup, schedule |
| **Total** | **81** | **All critical flows** |

---

## 🔄 Typical Workflow

1. **Develop feature** in Tiger ID
2. **Run smoke test**: `npm run test:e2e:auth`
3. **Run related suite**: e.g., `npm run test:e2e:tiger`
4. **Fix any failures**
5. **Run full suite**: `npm run test:e2e`
6. **Commit with confidence** ✅

---

## 📝 Adding New Tests

### Quick Template

```typescript
test('should [describe behavior]', async ({ page }) => {
  // Arrange - setup
  await page.goto('/your-page')

  // Act - perform action
  await page.click('button')

  // Assert - verify result
  await expect(page.locator('.result')).toBeVisible()
})
```

### Where to Add

- Authentication → `auth-flow.spec.ts`
- Investigation → `investigation-flow.spec.ts`
- Tigers → `tiger-management.spec.ts`
- Facilities → `facility-management.spec.ts`
- Verification → `verification-flow.spec.ts`
- Discovery → `discovery-flow.spec.ts`

---

## 🎓 Resources

- **Detailed Docs**: `frontend/e2e/README.md`
- **Test Report**: `frontend/E2E_TEST_REPORT.md`
- **Execution Summary**: `TEST_EXECUTION_SUMMARY.md`
- **Playwright Docs**: https://playwright.dev/

---

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| Backend not found | Start: `cd backend && uvicorn main:app --reload --port 8000` |
| Test user missing | Create user with credentials: `testuser` / `testpassword` |
| Slow tests | Run headless: `npm run test:e2e` (not `headed`) |
| Flaky tests | Use UI mode to identify issue: `npm run test:e2e:ui` |
| Browser not installed | Run: `npx playwright install` |

---

## ✨ Pro Tips

1. **Use UI Mode First**: Best for understanding tests
2. **Run Specific Suites**: Faster feedback during development
3. **Check Screenshots**: Auto-captured on failures
4. **Use Traces**: Great for debugging flaky tests
5. **Watch Mode**: UI mode auto-reruns on changes

---

**Quick Command Reference:**

```bash
npm run test:e2e           # Run all (headless)
npm run test:e2e:ui        # Interactive UI
npm run test:e2e:headed    # Visible browser
npm run test:e2e:auth      # Auth tests only
npm run test:e2e:report    # View HTML report
```

**Ready to test!** 🎉

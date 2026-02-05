# Authentication E2E Tests

Comprehensive end-to-end tests for the Tiger ID authentication flow using Playwright and the Page Object Model pattern.

## Test File

- `auth.spec.ts` - Complete authentication flow tests

## Test Coverage

### 1. Login Page Display
- ✅ All required elements are visible
- ✅ Proper input attributes (name, type, autocomplete)
- ✅ Branding and navigation elements

### 2. Successful Login
- ✅ Login with admin credentials
- ✅ Login with analyst credentials
- ✅ Login with viewer credentials
- ✅ Token storage in localStorage
- ✅ Redirect to dashboard after login

### 3. Failed Login
- ✅ Invalid username/password error message
- ✅ Wrong password error
- ✅ Non-existent user error
- ✅ Error clearing on retry

### 4. Form Validation
- ✅ Empty username validation
- ✅ Empty password validation
- ✅ Empty form submission prevention
- ✅ Submit button loading state

### 5. Logout
- ✅ Successful logout flow
- ✅ Redirect to login after logout
- ✅ Clear authentication data
- ✅ Clear token from localStorage

### 6. Protected Routes
- ✅ Redirect unauthenticated users to login
- ✅ Allow authenticated users access
- ✅ Redirect on invalid token

### 7. Session Persistence
- ✅ Authentication persists across page refreshes
- ✅ Authentication persists across navigation
- ✅ Token restoration in new session

### 8. Password Reset Flow
- ✅ Navigate to password reset page
- ✅ Request password reset with valid email
- ✅ Validation error for invalid email
- ✅ Reset password with valid token
- ✅ Password mismatch validation
- ✅ Minimum password length validation
- ✅ Navigate back to login

### 9. Remember Me Functionality
- ✅ Remember me checkbox visibility
- ✅ Check/uncheck functionality

### 10. Security
- ✅ Password input masking
- ✅ No credentials in URL
- ✅ No token exposure in console

### 11. Accessibility
- ✅ Accessible form labels
- ✅ Keyboard navigation support
- ✅ Screen reader error announcements

## Test Credentials

The tests use predefined credentials from `e2e/data/factories/user.factory.ts`:

```typescript
{
  admin: { username: 'admin', password: 'admin123' },
  analyst: { username: 'analyst', password: 'analyst123' },
  viewer: { username: 'viewer', password: 'viewer123' }
}
```

## Page Objects Used

- **LoginPage** (`e2e/pages/login.page.ts`) - Login page interactions
- **BasePage** (`e2e/pages/base.page.ts`) - Common page functionality (abstract base class)

## API Integration

These E2E tests run against the real backend API. Ensure the backend server is running before executing tests.

Key API endpoints tested:
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user
- `POST /api/auth/refresh` - Refresh auth token
- `POST /api/auth/password-reset/request` - Request password reset
- `POST /api/auth/password-reset/confirm` - Confirm password reset

## Prerequisites

Before running tests:

1. **Start the backend API**:
   ```bash
   cd backend && uvicorn main:app --reload --port 8000
   ```

2. **Start the frontend dev server**:
   ```bash
   cd frontend && npm run dev
   ```

3. **Ensure test user accounts exist** in the database with the credentials specified in `testCredentials`.

## Running Tests

```bash
# Run all auth tests
npx playwright test e2e/tests/auth

# Run specific test file
npx playwright test e2e/tests/auth/auth.spec.ts

# Run in headed mode
npx playwright test e2e/tests/auth --headed

# Run with UI mode
npx playwright test e2e/tests/auth --ui

# Run specific test by name
npx playwright test e2e/tests/auth -g "should login successfully"

# Generate HTML report
npx playwright test e2e/tests/auth --reporter=html
```

## Test Structure

Each test follows this pattern:

1. **Setup** (beforeEach) - Clear auth state, reset mocks
2. **Arrange** - Navigate to page, set up page objects
3. **Act** - Perform user actions (fill forms, click buttons)
4. **Assert** - Verify expected outcomes (redirects, messages, state)

## Data-TestId Selectors

The tests use data-testid attributes from components:

| Component | Selector | Source |
|-----------|----------|--------|
| Input | `data-testid="input"` | `src/components/common/Input.tsx` |
| Input Label | `data-testid="input-label"` | `src/components/common/Input.tsx` |
| Input Error | `data-testid="input-error"` | `src/components/common/Input.tsx` |
| Button | `data-testid="button"` | `src/components/common/Button.tsx` |
| Alert | `data-testid="alert"` | `src/components/common/Alert.tsx` |
| Alert Message | `data-testid="alert-message"` | `src/components/common/Alert.tsx` |

## Debugging Tips

### View test execution
```bash
npx playwright test e2e/tests/auth --headed --debug
```

### Generate trace
```bash
npx playwright test e2e/tests/auth --trace on
```

### View trace
```bash
npx playwright show-trace trace.zip
```

### Screenshots on failure
Tests automatically capture screenshots on failure. Find them in `test-results/`.

## Common Issues

### Tests fail with "locator not found"
- Ensure the frontend dev server is running on `http://localhost:5173`
- Ensure the backend API server is running on `http://localhost:8000`
- Check that components have proper data-testid attributes
- Verify test user accounts exist in the database

### Authentication state not clearing
- Check beforeEach hooks are clearing localStorage/cookies
- Verify no authentication tokens persist between tests
- Check backend session management

### Tests timeout
- Increase timeout in test or globally in playwright.config.ts
- Check for network issues or slow API responses
- Verify no infinite loading states

## Best Practices

1. **Use Page Objects** - Never use raw selectors in tests
2. **Clear State** - Always reset auth state in beforeEach
3. **Wait Properly** - Use Playwright's auto-waiting, avoid arbitrary timeouts
4. **Descriptive Names** - Test names should explain what they test
5. **Independent Tests** - Each test should run independently
6. **Assertions First** - Use expect() for all verifications

## Future Enhancements

- [ ] Add tests for 2FA/MFA flows
- [ ] Add tests for session timeout
- [ ] Add tests for concurrent login detection
- [ ] Add tests for rate limiting
- [ ] Add performance benchmarks
- [ ] Add visual regression tests

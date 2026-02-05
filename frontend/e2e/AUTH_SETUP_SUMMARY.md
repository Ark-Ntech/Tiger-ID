# Authentication Setup Summary

This document summarizes the authentication state management system created for Playwright E2E tests.

## Files Created

### 1. Global Setup (`e2e/global.setup.ts`)
- **Purpose**: Runs once before all tests
- **Actions**:
  - Authenticates three test users (admin, analyst, viewer)
  - Saves storage states to `.auth/` directory
  - Verifies backend API availability
  - Sets up test data if needed
- **Output**: Creates `.auth/admin.json`, `.auth/analyst.json`, `.auth/viewer.json`

### 2. Global Teardown (`e2e/global.teardown.ts`)
- **Purpose**: Runs once after all tests
- **Actions**:
  - Deletes authentication storage state files
  - Cleans up test data from database
  - Removes temporary test artifacts
- **Output**: Clean state after test runs

### 3. Auth Fixtures (`e2e/fixtures/auth.fixture.ts`)
- **Purpose**: Provides pre-authenticated page contexts
- **Fixtures**:
  - `adminPage` - Admin user (full permissions)
  - `analystPage` - Analyst user (standard permissions)
  - `viewerPage` - Viewer user (read-only)
  - `authenticatedPage` - Default authenticated context (analyst)
- **Helpers**:
  - `isAuthenticated(page)` - Check if page has auth token
  - `getCurrentUserRole(page)` - Get current user's role
  - `waitForAuthToken(page, timeout)` - Wait for auth token to appear

### 4. Example Tests (`e2e/examples/auth-fixture-usage.spec.ts`)
- **Purpose**: Demonstrates fixture usage patterns
- **Content**: Examples of using each fixture type

### 5. Documentation (`e2e/fixtures/README.md`)
- **Purpose**: Comprehensive guide to authentication fixtures
- **Content**:
  - Architecture overview
  - Usage examples
  - Troubleshooting guide
  - Best practices

## Configuration Changes

### `playwright.config.ts`

Added global setup and teardown:

```typescript
export default defineConfig({
  globalSetup: './e2e/global.setup.ts',
  globalTeardown: './e2e/global.teardown.ts',
  // ... rest of config
})
```

## Test Credentials

Defined in `e2e/data/factories/user.factory.ts`:

```typescript
export const testCredentials = {
  admin: { username: 'admin', password: 'admin123' },
  analyst: { username: 'analyst', password: 'analyst123' },
  viewer: { username: 'viewer', password: 'viewer123' },
}
```

## Usage Quick Start

### 1. Basic Authenticated Test

```typescript
import { test, expect } from './fixtures/auth.fixture'

test('user can view dashboard', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/dashboard')
  await expect(authenticatedPage).toHaveTitle(/Dashboard/)
})
```

### 2. Role-Specific Test

```typescript
test('admin can manage users', async ({ adminPage }) => {
  await adminPage.goto('/admin/users')
  await expect(adminPage.locator('[data-testid="user-list"]')).toBeVisible()
})
```

### 3. Multiple Roles

```typescript
test('permissions differ by role', async ({ adminPage, viewerPage }) => {
  await adminPage.goto('/admin')
  await expect(adminPage.locator('[data-testid="admin-panel"]')).toBeVisible()
  
  await viewerPage.goto('/admin')
  await expect(viewerPage).toHaveURL(/access-denied/)
})
```

## Benefits

1. **Performance**: Authentication happens once, not per test
2. **Reliability**: Consistent auth state across test runs
3. **Maintainability**: Centralized auth management
4. **Flexibility**: Easy to test different role permissions
5. **Isolation**: Each test gets fresh authenticated context

## Setup Requirements

Before running tests, ensure:

1. **Test users exist** in database with credentials from `user.factory.ts`
2. **Backend is running** at `http://localhost:8000`
3. **Frontend is running** at `http://localhost:5173`
4. **.auth directory** is in `.gitignore` (already configured)

## Running Tests

```bash
# Run all E2E tests (triggers global setup automatically)
npm run test:e2e

# Run specific test file
npm run test:e2e auth-flow.spec.ts

# Run with UI mode
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed
```

## Troubleshooting

### Setup Fails

If global setup fails:
1. Check error screenshots in `.auth/` directory
2. Verify test user credentials
3. Ensure backend is accessible
4. Check console logs for specific errors

### Tests Still Require Login

If tests redirect to login:
1. Verify importing from `./fixtures/auth.fixture`
2. Check storage state files exist in `.auth/`
3. Verify token storage keys match app
4. Check token hasn't expired

### Slow Test Execution

If tests are slow:
1. Ensure using fixtures (not logging in per test)
2. Check parallel execution is enabled
3. Verify global setup is running once only
4. Consider reducing test timeout values

## Next Steps

To integrate into existing tests:

1. **Update imports**: Change from `@playwright/test` to `./fixtures/auth.fixture`
2. **Remove login code**: Delete manual login steps
3. **Use fixtures**: Replace `page` with `authenticatedPage`, `adminPage`, etc.
4. **Add role tests**: Test different permissions with different fixtures
5. **Update test data**: Ensure test users exist in database

## File Structure

```
frontend/e2e/
├── global.setup.ts              # Global authentication setup
├── global.teardown.ts           # Global cleanup
├── fixtures/
│   ├── auth.fixture.ts          # Authentication fixtures
│   └── README.md                # Fixture documentation
├── examples/
│   └── auth-fixture-usage.spec.ts  # Usage examples
├── data/
│   └── factories/
│       └── user.factory.ts      # Test credentials
└── .auth/                       # Generated auth states (gitignored)
    ├── admin.json
    ├── analyst.json
    └── viewer.json
```

## Related Documentation

- `e2e/fixtures/README.md` - Detailed fixture documentation
- `e2e/examples/auth-fixture-usage.spec.ts` - Usage examples
- `playwright.config.ts` - Playwright configuration
- `e2e/README.md` - General E2E testing guide

## Support

For issues or questions:
1. Check the troubleshooting section in `e2e/fixtures/README.md`
2. Review example tests in `e2e/examples/`
3. Check Playwright documentation: https://playwright.dev
4. Review authentication setup logs during test runs

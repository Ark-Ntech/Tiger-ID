# Authentication Fixtures

This directory contains authentication fixtures for Playwright E2E tests, providing pre-authenticated page contexts for different user roles.

## Overview

The authentication fixtures allow you to write tests with pre-authenticated users without repeatedly logging in for each test. This significantly speeds up test execution and reduces test flakiness.

## Architecture

### Global Setup (`global.setup.ts`)

Runs once before all tests to:
1. Authenticate three test users (admin, analyst, viewer)
2. Save their authentication states to `.auth/` directory
3. Verify backend API availability
4. Setup test data if needed

The authenticated states are saved as JSON files:
- `.auth/admin.json` - Admin user storage state
- `.auth/analyst.json` - Analyst user storage state
- `.auth/viewer.json` - Viewer user storage state

### Global Teardown (`global.teardown.ts`)

Runs once after all tests to:
1. Clean up authentication storage state files
2. Remove test data created during tests
3. Delete temporary test artifacts

### Auth Fixtures (`auth.fixture.ts`)

Extends the base Playwright test with four fixtures:
- `adminPage` - Admin user context (full permissions)
- `analystPage` - Analyst user context (create/edit capabilities)
- `viewerPage` - Viewer user context (read-only)
- `authenticatedPage` - Default authenticated context (uses analyst role)

## Usage

### Basic Usage

Import the `test` and `expect` from the auth fixture:

```typescript
import { test, expect } from './fixtures/auth.fixture'

test('user can view dashboard', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/dashboard')
  await expect(authenticatedPage).toHaveTitle(/Dashboard/)
})
```

### Role-Specific Tests

Use different fixtures for different roles:

```typescript
import { test, expect } from './fixtures/auth.fixture'

// Admin-only test
test('admin can manage users', async ({ adminPage }) => {
  await adminPage.goto('/admin/users')
  await expect(adminPage.locator('[data-testid="user-list"]')).toBeVisible()
})

// Analyst test
test('analyst can create investigation', async ({ analystPage }) => {
  await analystPage.goto('/investigations/new')
  await analystPage.fill('[name="title"]', 'Test Investigation')
  await analystPage.click('button[type="submit"]')
})

// Viewer test (read-only)
test('viewer cannot edit tigers', async ({ viewerPage }) => {
  await viewerPage.goto('/tigers/123')
  await expect(viewerPage.locator('[data-testid="edit-button"]')).not.toBeVisible()
})
```

### Multiple Roles in One Test

You can use multiple fixtures in a single test:

```typescript
test('permissions differ by role', async ({ adminPage, viewerPage }) => {
  // Admin can access admin panel
  await adminPage.goto('/admin')
  await expect(adminPage.locator('[data-testid="admin-panel"]')).toBeVisible()
  
  // Viewer gets redirected or sees access denied
  await viewerPage.goto('/admin')
  await expect(viewerPage).toHaveURL(/access-denied|dashboard/)
})
```

### Helper Functions

The fixture also exports helper functions:

```typescript
import { test, expect, isAuthenticated, getCurrentUserRole, waitForAuthToken } from './fixtures/auth.fixture'

test('verify user role', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/profile')
  
  // Check authentication status
  const authenticated = await isAuthenticated(authenticatedPage)
  expect(authenticated).toBe(true)
  
  // Get current user role
  const role = await getCurrentUserRole(authenticatedPage)
  expect(role).toBe('analyst')
  
  // Wait for auth token if needed
  await waitForAuthToken(authenticatedPage, 5000)
})
```

## Test Credentials

Test credentials are defined in `e2e/data/factories/user.factory.ts`:

```typescript
export const testCredentials = {
  admin: { username: 'admin', password: 'admin123' },
  analyst: { username: 'analyst', password: 'analyst123' },
  viewer: { username: 'viewer', password: 'viewer123' },
}
```

Make sure these users exist in your test database before running tests.

## Configuration

The authentication setup is configured in `playwright.config.ts`:

```typescript
export default defineConfig({
  globalSetup: './e2e/global.setup.ts',
  globalTeardown: './e2e/global.teardown.ts',
  
  projects: [
    {
      name: 'chromium',
      use: {
        storageState: '.auth/analyst.json', // Default for all tests
      },
    },
  ],
})
```

## Troubleshooting

### Authentication Failures

If global setup fails with authentication errors:

1. Verify test users exist in the database
2. Check credentials in `user.factory.ts`
3. Ensure backend is running at `http://localhost:8000`
4. Check `.auth/` directory for error screenshots

### Storage State Not Found

If tests fail with "storage state not found":

1. Run `npm run test:e2e` to trigger global setup
2. Check that `.auth/` directory exists with JSON files
3. Verify `playwright.config.ts` has correct paths

### Tests Still Require Login

If tests redirect to login page despite auth fixture:

1. Check that test is importing from `./fixtures/auth.fixture`
2. Verify storage state path in fixture matches actual file
3. Check token is being saved to correct localStorage key
4. Ensure backend session hasn't expired

## Best Practices

1. **Use `authenticatedPage` by default** - Only use role-specific fixtures when testing role-specific behavior
2. **Don't login in tests** - Let the fixture handle authentication
3. **Keep setup fast** - Only create essential test data in global setup
4. **Clean up properly** - Use teardown to remove test data
5. **Mock external services** - Don't rely on external APIs in E2E tests
6. **Use data-testid** - Add test IDs to make tests more reliable

## Examples

See `examples/auth-fixture-usage.spec.ts` for comprehensive examples of using authentication fixtures.

## Related Files

- `e2e/global.setup.ts` - Global setup script
- `e2e/global.teardown.ts` - Global teardown script
- `e2e/fixtures/auth.fixture.ts` - Authentication fixtures
- `e2e/data/factories/user.factory.ts` - Test user credentials
- `playwright.config.ts` - Playwright configuration

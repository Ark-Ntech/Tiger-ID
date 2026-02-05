import { test as setup, expect } from '@playwright/test';
import * as path from 'path';

/**
 * Authentication setup test
 *
 * This runs as part of the 'setup' project before other tests.
 * It logs in once and saves the authenticated state to .auth/user.json
 * which is then reused by all test projects.
 *
 * This approach is faster than logging in before each test and
 * reduces API load on the authentication endpoints.
 */

const authFile = path.join(process.cwd(), '.auth', 'user.json');

setup('authenticate', async ({ page }) => {
  console.log('🔐 Authenticating user...');

  // Get credentials from environment or use test defaults
  const testEmail = process.env.TEST_USER_EMAIL || 'test@example.com';
  const testPassword = process.env.TEST_USER_PASSWORD || 'password123';

  // Navigate to login page
  await page.goto('/login');

  // Wait for login form to be visible
  await expect(page.locator('input[type="email"]')).toBeVisible();

  // Fill in login credentials
  await page.fill('input[type="email"]', testEmail);
  await page.fill('input[type="password"]', testPassword);

  // Submit login form
  await page.click('button[type="submit"]');

  // Wait for successful navigation
  // Adjust the URL pattern based on your app's post-login redirect
  await page.waitForURL('**/dashboard', { timeout: 10000 }).catch(async () => {
    // Alternative: check for any authenticated page indicators
    const isAuthenticated = await page.locator('[data-testid="user-menu"]').isVisible({ timeout: 5000 })
      || await page.locator('[data-testid="logout-button"]').isVisible({ timeout: 5000 })
      || !page.url().includes('/login');

    if (!isAuthenticated) {
      throw new Error('Authentication failed - could not verify successful login');
    }
  });

  // Verify we're authenticated by checking for user-specific elements
  // Adjust these selectors based on your app's layout
  const authIndicators = [
    page.locator('[data-testid="user-menu"]'),
    page.locator('button:has-text("Logout")'),
    page.locator('[role="navigation"]'),
  ];

  let foundIndicator = false;
  for (const indicator of authIndicators) {
    if (await indicator.isVisible({ timeout: 2000 }).catch(() => false)) {
      foundIndicator = true;
      break;
    }
  }

  if (!foundIndicator && page.url().includes('/login')) {
    throw new Error('Authentication verification failed - still on login page');
  }

  console.log('✅ Authentication successful');

  // Save authenticated state
  await page.context().storageState({ path: authFile });
  console.log(`💾 Saved auth state to ${authFile}`);
});

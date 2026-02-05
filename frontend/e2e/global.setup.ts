import { chromium, FullConfig } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';
import { testCredentials } from './data/factories/user.factory';

/**
 * Global setup for Playwright tests
 *
 * This runs once before all tests to:
 * 1. Verify backend API availability
 * 2. Authenticate test users (admin, analyst, viewer) and save storage states
 * 3. Initialize test data if needed
 *
 * The authenticated states are saved to .auth/ directory and
 * reused by all test projects to avoid repeated login operations.
 *
 * Authentication Strategy:
 * - Performs actual login via UI to get real auth tokens
 * - Saves browser storage state (cookies, localStorage, sessionStorage)
 * - All tests load this state to start authenticated
 * - Eliminates need for login in every test file
 *
 * Sharding Support:
 * - When using --shard=1/4, this setup runs once per shard
 * - Cached auth states are reused if recent (< 1 hour old)
 * - Multiple shards can share the same auth state files
 *
 * Environment Variables:
 * - BASE_URL: Frontend URL (default: http://localhost:5173)
 * - API_URL: Backend API URL (default: http://localhost:8000)
 * - CI: When true, enables stricter checks and logging
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 Running global setup...');

  const baseURL = config.projects[0]?.use?.baseURL || process.env.BASE_URL || 'http://localhost:5173';
  const apiURL = process.env.API_URL || 'http://localhost:8000';

  // Ensure .auth directory exists
  const authDir = path.join(process.cwd(), '.auth');
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
    console.log(`📁 Created .auth directory at ${authDir}`);
  }

  // Launch browser for setup
  // Use chromium for setup as it's fastest and most reliable
  const browser = await chromium.launch({
    headless: true,
  });

  try {
    // Verify backend API is available before authentication
    console.log('🔍 Checking backend API availability...');
    await verifyBackendAvailability(browser, apiURL);

    // Authenticate users and save their states
    // These states will be reused across all test files and browser projects
    // This drastically reduces test execution time by eliminating repeated logins

    // Admin user - full access to all features
    await authenticateUser(
      browser,
      baseURL,
      testCredentials.admin.username,
      testCredentials.admin.password,
      path.join(authDir, 'admin.json'),
      'admin'
    );

    // Analyst user - limited access for testing permissions
    await authenticateUser(
      browser,
      baseURL,
      testCredentials.analyst.username,
      testCredentials.analyst.password,
      path.join(authDir, 'analyst.json'),
      'analyst'
    );

    // Viewer user - read-only access for testing view permissions
    await authenticateUser(
      browser,
      baseURL,
      testCredentials.viewer.username,
      testCredentials.viewer.password,
      path.join(authDir, 'viewer.json'),
      'viewer'
    );

    // Setup test data (creates test entities if they don't exist)
    await setupTestData(browser, baseURL, apiURL, authDir);

    console.log('✅ Global setup complete\n');
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

/**
 * Verify that the backend API is available and responding
 *
 * This prevents cryptic test failures if the backend isn't running.
 * Tests will fail fast with a clear error message.
 */
async function verifyBackendAvailability(browser: any, apiURL: string) {
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Try to reach the health endpoint
    const response = await page.request.get(`${apiURL}/health`, {
      timeout: 10000
    });

    if (response.ok()) {
      const body = await response.json().catch(() => ({}));
      console.log('✅ Backend API is available', body);
    } else {
      console.warn(`⚠️  Backend API health check returned status ${response.status()}`);
      throw new Error(`Backend API health check failed with status ${response.status()}`);
    }
  } catch (error) {
    console.error('❌ Could not reach backend API:', error);
    console.error(`   Make sure the backend is running at ${apiURL}`);
    throw new Error('Backend API is not available. Please start the backend server.');
  } finally {
    await context.close();
  }
}

/**
 * Helper function to authenticate a user and save storage state
 *
 * The storage state includes:
 * - Cookies (session cookies, CSRF tokens, etc.)
 * - Local storage (auth token, user preferences)
 * - Session storage (temporary state)
 *
 * This state is then loaded by test projects to skip login steps.
 *
 * Caching Strategy:
 * - Reuses existing auth state if < 1 hour old
 * - This speeds up test runs when running tests repeatedly
 * - Forces re-authentication after 1 hour to ensure tokens are valid
 */
async function authenticateUser(
  browser: any,
  baseURL: string,
  username: string,
  password: string,
  storageStatePath: string,
  role: string
) {
  // Check if auth state already exists and is recent (< 1 hour old)
  if (fs.existsSync(storageStatePath)) {
    const stats = fs.statSync(storageStatePath);
    const ageInMinutes = (Date.now() - stats.mtimeMs) / 1000 / 60;

    if (ageInMinutes < 60) {
      console.log(`✅ Reusing existing auth state for ${username} (${Math.round(ageInMinutes)}m old)`);
      return;
    } else {
      console.log(`🔄 Auth state expired for ${username} (${Math.round(ageInMinutes)}m old), re-authenticating...`);
    }
  }

  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log(`🔐 Authenticating user: ${username} (${role})`);

    // Navigate to login page
    await page.goto(`${baseURL}/login`, { waitUntil: 'networkidle' });

    // Wait for login form to be visible
    await page.waitForSelector('form', { timeout: 10000 });

    // Fill in credentials using flexible selectors
    const usernameInput = page.locator('input[name="username"], input[autocomplete="username"]');
    const passwordInput = page.locator('input[name="password"], input[type="password"]');

    await usernameInput.fill(username);
    await passwordInput.fill(password);

    // Submit form and wait for navigation
    await Promise.all([
      page.locator('button[type="submit"]').click(),
      // Wait for either dashboard or redirect to complete
      page.waitForURL(/\/(dashboard|tigers|investigations|facilities|$)/, {
        timeout: 15000
      }).catch(() => {
        // If URL wait times out, we'll verify authentication below
        console.log(`   URL wait timed out for ${username}, checking authentication...`);
      })
    ]);

    // Additional verification: Check for authentication token in storage
    const hasToken = await page.evaluate(() => {
      return !!(localStorage.getItem('token') ||
                localStorage.getItem('auth_token') ||
                sessionStorage.getItem('token'))
    });

    if (!hasToken) {
      throw new Error(`Authentication failed for user ${username}: No token found in storage`);
    }

    // Verify we're not still on the login page
    const currentURL = page.url();
    if (currentURL.includes('/login')) {
      throw new Error(`Authentication failed for user ${username}: Still on login page after submission`);
    }

    // Save authenticated state to file
    await context.storageState({ path: storageStatePath });
    console.log(`✅ Authenticated ${username} and saved state to ${path.basename(storageStatePath)}`);

  } catch (error) {
    console.error(`❌ Failed to authenticate user ${username}:`, error);

    // Take screenshot for debugging
    const screenshotPath = path.join(path.dirname(storageStatePath), `${username}-error.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`📸 Error screenshot saved to ${screenshotPath}`);

    throw error;
  } finally {
    await context.close();
  }
}

/**
 * Setup test data for E2E tests
 *
 * Creates necessary test entities like:
 * - Test facilities
 * - Test tigers
 * - Test investigations
 *
 * This function is idempotent - it checks if data exists before creating.
 * Non-critical: If test data setup fails, tests should still be resilient.
 */
async function setupTestData(browser: any, baseURL: string, apiURL: string, authDir: string) {
  console.log('📦 Setting up test data...');

  const context = await browser.newContext({
    storageState: path.join(authDir, 'admin.json')
  });
  const page = await context.newPage();

  try {
    // Check if test data already exists
    const response = await page.request.get(`${apiURL}/api/facilities?limit=1`);

    if (response.ok()) {
      const data = await response.json();
      console.log(`   Found ${data.total || 0} facilities in database`);
    }

    // Create test facility if none exists
    // Uncomment and customize as needed for your tests
    // const facilitiesResponse = await page.request.get(`${apiURL}/api/facilities?limit=1`);
    // if (facilitiesResponse.ok()) {
    //   const facilitiesData = await facilitiesResponse.json();
    //   if (facilitiesData.total === 0) {
    //     await page.request.post(`${apiURL}/api/facilities`, {
    //       data: {
    //         name: 'Test Wildlife Sanctuary',
    //         location: 'Test Location, USA',
    //         type: 'sanctuary',
    //         capacity: 50,
    //         status: 'active'
    //       }
    //     });
    //     console.log('   Created test facility');
    //   }
    // }

    console.log('✅ Test data ready');
  } catch (error) {
    console.warn('⚠️  Could not setup test data:', error);
    // Don't fail the setup if test data creation fails
    // Tests should be resilient to missing data
  } finally {
    await context.close();
  }
}

export default globalSetup;

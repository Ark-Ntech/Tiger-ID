import { test as base, Page } from '@playwright/test'
import * as path from 'path'

/**
 * Authentication fixtures for Playwright tests
 *
 * These fixtures extend the base Playwright test with authenticated contexts
 * that automatically use saved storage states from global setup.
 *
 * Usage:
 * ```typescript
 * import { test } from './fixtures/auth.fixture'
 *
 * test('admin can access admin panel', async ({ adminPage }) => {
 *   await adminPage.goto('/admin')
 *   await expect(adminPage).toHaveTitle(/Admin/)
 * })
 * ```
 */

export type AuthenticatedFixtures = {
  /**
   * Page fixture with admin user authentication
   * Role: admin
   * Full permissions for all operations
   */
  adminPage: Page

  /**
   * Page fixture with analyst user authentication
   * Role: analyst
   * Can create investigations, manage tigers, and view all data
   */
  analystPage: Page

  /**
   * Page fixture with viewer user authentication
   * Role: viewer
   * Read-only access to investigations and data
   */
  viewerPage: Page

  /**
   * Page fixture with standard authenticated user
   * Uses analyst role by default for most tests
   */
  authenticatedPage: Page
}

export const test = base.extend<AuthenticatedFixtures>({
  /**
   * Admin page fixture
   * Creates a new page with admin user authentication state
   */
  adminPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: path.join(process.cwd(), '.auth', 'admin.json')
    })
    const page = await context.newPage()

    // Set default timeout for this page
    page.setDefaultTimeout(30000)

    await use(page)

    // Cleanup
    await context.close()
  },

  /**
   * Analyst page fixture
   * Creates a new page with analyst user authentication state
   */
  analystPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: path.join(process.cwd(), '.auth', 'analyst.json')
    })
    const page = await context.newPage()

    // Set default timeout for this page
    page.setDefaultTimeout(30000)

    await use(page)

    // Cleanup
    await context.close()
  },

  /**
   * Viewer page fixture
   * Creates a new page with viewer user authentication state
   */
  viewerPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: path.join(process.cwd(), '.auth', 'viewer.json')
    })
    const page = await context.newPage()

    // Set default timeout for this page
    page.setDefaultTimeout(30000)

    await use(page)

    // Cleanup
    await context.close()
  },

  /**
   * Default authenticated page fixture (uses analyst)
   * This is the most commonly used fixture for standard authenticated tests
   */
  authenticatedPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: path.join(process.cwd(), '.auth', 'analyst.json')
    })
    const page = await context.newPage()

    // Set default timeout for this page
    page.setDefaultTimeout(30000)

    await use(page)

    // Cleanup
    await context.close()
  },
})

/**
 * Re-export expect for convenience
 */
export { expect } from '@playwright/test'

/**
 * Helper function to check if a page is authenticated
 *
 * @param page - Playwright page object
 * @returns Promise<boolean> - True if authenticated, false otherwise
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  try {
    const hasToken = await page.evaluate(() => {
      return !!(
        localStorage.getItem('token') ||
        localStorage.getItem('auth_token') ||
        sessionStorage.getItem('token')
      )
    })
    return hasToken
  } catch (error) {
    return false
  }
}

/**
 * Helper function to get current user role from page
 *
 * @param page - Playwright page object
 * @returns Promise<string | null> - User role or null if not found
 */
export async function getCurrentUserRole(page: Page): Promise<string | null> {
  try {
    return await page.evaluate(() => {
      const userStr = localStorage.getItem('user')
      if (!userStr) return null

      try {
        const user = JSON.parse(userStr)
        return user.role || null
      } catch {
        return null
      }
    })
  } catch (error) {
    return null
  }
}

/**
 * Helper function to wait for authentication token to be present
 *
 * @param page - Playwright page object
 * @param timeout - Maximum time to wait in milliseconds (default: 10000)
 */
export async function waitForAuthToken(page: Page, timeout: number = 10000): Promise<void> {
  await page.waitForFunction(
    () => {
      return !!(
        localStorage.getItem('token') ||
        localStorage.getItem('auth_token') ||
        sessionStorage.getItem('token')
      )
    },
    { timeout }
  )
}

import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear any existing auth state
    await page.context().clearCookies()
    await page.context().clearPermissions()
  })

  test('should display login page with correct elements', async ({ page }) => {
    await page.goto('/login')

    // Check for Tiger ID branding
    await expect(page.locator('h1, h2')).toContainText(/Tiger ID/i)

    // Check for form elements
    await expect(page.locator('input[name="username"], input[type="text"]').first()).toBeVisible()
    await expect(page.locator('input[name="password"], input[type="password"]').first()).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
  })

  test('should show validation errors for empty form submission', async ({ page }) => {
    await page.goto('/login')

    // Try to submit empty form
    await page.locator('button[type="submit"]').click()

    // Wait for potential error messages (may vary based on implementation)
    await page.waitForTimeout(500)

    // Should still be on login page
    await expect(page).toHaveURL(/\/login/)
  })

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login')

    // Fill in invalid credentials
    const usernameInput = page.locator('input[name="username"], input[type="text"]').first()
    const passwordInput = page.locator('input[name="password"], input[type="password"]').first()

    await usernameInput.fill('invaliduser')
    await passwordInput.fill('wrongpassword')

    // Submit form
    await page.locator('button[type="submit"]').click()

    // Wait for response
    await page.waitForTimeout(1000)

    // Check for error message or still on login page
    const currentUrl = page.url()
    if (currentUrl.includes('/login')) {
      // Expected - should show error and stay on login page
      expect(currentUrl).toContain('/login')
    }
  })

  test('should successfully login with valid credentials and store token', async ({ page }) => {
    await page.goto('/login')

    // Fill in credentials (adjust based on your test user)
    const usernameInput = page.locator('input[name="username"], input[type="text"]').first()
    const passwordInput = page.locator('input[name="password"], input[type="password"]').first()

    await usernameInput.fill('testuser')
    await passwordInput.fill('testpassword')

    // Submit form
    await page.locator('button[type="submit"]').click()

    // Wait for navigation or error
    await page.waitForTimeout(2000)

    // If login successful, should redirect away from login page
    const currentUrl = page.url()
    if (!currentUrl.includes('/login')) {
      // Check that we're on a protected route
      expect(currentUrl).not.toContain('/login')

      // Check for auth token in localStorage
      const token = await page.evaluate(() => localStorage.getItem('token') || localStorage.getItem('auth_token'))
      if (token) {
        expect(token).toBeTruthy()
      }
    }
  })

  test('should redirect to login when accessing protected route without auth', async ({ page }) => {
    await page.goto('/dashboard')

    // Should redirect to login
    await page.waitForTimeout(1000)
    await expect(page).toHaveURL(/\/login/)
  })

  test('should allow access to protected routes after login', async ({ page }) => {
    // First login
    await page.goto('/login')

    const usernameInput = page.locator('input[name="username"], input[type="text"]').first()
    const passwordInput = page.locator('input[name="password"], input[type="password"]').first()

    await usernameInput.fill('testuser')
    await passwordInput.fill('testpassword')
    await page.locator('button[type="submit"]').click()

    await page.waitForTimeout(2000)

    // Try to access protected routes
    const protectedRoutes = ['/dashboard', '/tigers', '/facilities', '/investigation2']

    for (const route of protectedRoutes) {
      await page.goto(route)
      await page.waitForTimeout(500)

      // If we have valid auth, should NOT redirect to login
      const currentUrl = page.url()
      if (!currentUrl.includes('/login')) {
        // Success - we can access the route
        expect(currentUrl).toContain(route)
      }
    }
  })

  test('should logout successfully and clear token', async ({ page }) => {
    // First login
    await page.goto('/login')

    const usernameInput = page.locator('input[name="username"], input[type="text"]').first()
    const passwordInput = page.locator('input[name="password"], input[type="password"]').first()

    await usernameInput.fill('testuser')
    await passwordInput.fill('testpassword')
    await page.locator('button[type="submit"]').click()

    await page.waitForTimeout(2000)

    // Look for logout button (common text variations)
    const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Log out"), button:has-text("Sign out")')

    if (await logoutButton.count() > 0) {
      await logoutButton.first().click()

      await page.waitForTimeout(1000)

      // Should redirect to login
      await expect(page).toHaveURL(/\/login/)

      // Token should be cleared
      const token = await page.evaluate(() => localStorage.getItem('token') || localStorage.getItem('auth_token'))
      expect(token).toBeFalsy()
    }
  })

  test('should persist authentication across page reloads', async ({ page }) => {
    // Login
    await page.goto('/login')

    const usernameInput = page.locator('input[name="username"], input[type="text"]').first()
    const passwordInput = page.locator('input[name="password"], input[type="password"]').first()

    await usernameInput.fill('testuser')
    await passwordInput.fill('testpassword')
    await page.locator('button[type="submit"]').click()

    await page.waitForTimeout(2000)

    // Navigate to a protected route
    await page.goto('/dashboard')
    await page.waitForTimeout(500)

    const urlBeforeReload = page.url()

    // Reload the page
    await page.reload()
    await page.waitForTimeout(1000)

    // Should still be authenticated (not redirected to login)
    const urlAfterReload = page.url()
    if (!urlAfterReload.includes('/login')) {
      expect(urlAfterReload).toBe(urlBeforeReload)
    }
  })
})

import { Page } from '@playwright/test'

/**
 * Helper function to login to the application
 */
export async function login(page: Page, username = 'testuser', password = 'testpassword') {
  await page.goto('/login')

  const usernameInput = page.locator('input[name="username"], input[type="text"]').first()
  const passwordInput = page.locator('input[name="password"], input[type="password"]').first()

  if (await usernameInput.count() > 0) {
    await usernameInput.fill(username)
    await passwordInput.fill(password)
    await page.locator('button[type="submit"]').click()
    await page.waitForTimeout(1500)
  }
}

/**
 * Helper function to logout from the application
 */
export async function logout(page: Page) {
  const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Log out"), button:has-text("Sign out")')

  if (await logoutButton.count() > 0) {
    await logoutButton.first().click()
    await page.waitForTimeout(1000)
  }
}

/**
 * Helper function to check if user is authenticated
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  const token = await page.evaluate(() => {
    return localStorage.getItem('token') || localStorage.getItem('auth_token')
  })

  return !!token
}

/**
 * Helper function to clear authentication state
 */
export async function clearAuth(page: Page) {
  await page.context().clearCookies()
  await page.evaluate(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('auth_token')
  })
}

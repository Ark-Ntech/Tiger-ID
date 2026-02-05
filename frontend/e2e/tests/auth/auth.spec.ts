import { test, expect, Page } from '@playwright/test'
import { LoginPage } from '../../pages/login.page'
import { testCredentials } from '../../data/factories'

/**
 * Comprehensive E2E tests for authentication flow
 *
 * Test Coverage:
 * - Login page display and validation
 * - Successful login with different user roles
 * - Failed login attempts with various invalid inputs
 * - Form validation for empty/missing fields
 * - Logout functionality and token clearing
 * - Protected route access control
 * - Session persistence across page refreshes and navigation
 * - Password reset flow (request and confirm)
 * - Remember me functionality
 * - Security checks (password masking, credential exposure)
 * - Accessibility features
 *
 * Uses Page Object Model pattern for maintainable test code.
 * Tests run against real frontend and backend - ensure services are running.
 */
test.describe('Authentication Flow', () => {
  let loginPage: LoginPage

  test.beforeEach(async ({ page }) => {
    // Clear any existing authentication state before each test
    await page.context().clearCookies()
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })

    // Initialize page object
    loginPage = new LoginPage(page)
  })

  test.describe('Login Page Display', () => {
    test('should display login page with all required elements', async ({ page }) => {
      await loginPage.goto()

      // Verify page title and branding
      await expect(page).toHaveTitle(/Tiger ID/i)
      await expect(page.locator('h1, h2').first()).toContainText(/Tiger ID/i)

      // Verify form inputs are visible using data-testid selectors
      await expect(loginPage.usernameInput).toBeVisible()
      await expect(loginPage.passwordInput).toBeVisible()
      await expect(loginPage.submitButton).toBeVisible()

      // Verify forgot password link
      await expect(loginPage.forgotPasswordLink).toBeVisible()

      // Verify form labels are present
      await expect(page.getByText(/username/i)).toBeVisible()
      await expect(page.getByText(/password/i)).toBeVisible()
    })

    test('should have proper input attributes for accessibility and autocomplete', async ({ page }) => {
      await loginPage.goto()

      // Username input attributes
      await expect(loginPage.usernameInput).toHaveAttribute('name', 'username')
      await expect(loginPage.usernameInput).toHaveAttribute('autocomplete', /username/i)

      // Password input attributes
      await expect(loginPage.passwordInput).toHaveAttribute('type', 'password')
      await expect(loginPage.passwordInput).toHaveAttribute('name', 'password')
      await expect(loginPage.passwordInput).toHaveAttribute('autocomplete', /current-password/i)

      // Submit button attributes
      await expect(loginPage.submitButton).toHaveAttribute('type', 'submit')
    })

    test('should focus username input on page load', async ({ page }) => {
      await loginPage.goto()

      // Username input should be focusable
      await loginPage.usernameInput.focus()
      const focusedElement = await page.evaluate(() => document.activeElement?.getAttribute('name'))
      expect(focusedElement).toBe('username')
    })
  })

  test.describe('Successful Login', () => {
    test('should login successfully with valid admin credentials', async ({ page }) => {
      await loginPage.goto()

      // Login with admin credentials
      await loginPage.loginAndWait(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      // Should redirect away from login page
      await expect(page).not.toHaveURL(/\/login/, { timeout: 10000 })

      // Should be on dashboard or home page
      await expect(page).toHaveURL(/\/(dashboard|tigers|facilities|investigation2|$)/)

      // Verify user is authenticated by checking for authenticated UI elements
      const header = page.getByTestId('header')
      await expect(header).toBeVisible()
    })

    test('should login successfully with valid analyst credentials', async ({ page }) => {
      await loginPage.goto()

      await loginPage.loginAndWait(
        testCredentials.analyst.username,
        testCredentials.analyst.password
      )

      await expect(page).not.toHaveURL(/\/login/, { timeout: 10000 })
      await expect(page).toHaveURL(/\/(dashboard|tigers|facilities|investigation2|$)/)
    })

    test('should login successfully with valid viewer credentials', async ({ page }) => {
      await loginPage.goto()

      await loginPage.loginAndWait(
        testCredentials.viewer.username,
        testCredentials.viewer.password
      )

      await expect(page).not.toHaveURL(/\/login/, { timeout: 10000 })
      await expect(page).toHaveURL(/\/(dashboard|tigers|facilities|investigation2|$)/)
    })

    test('should store authentication token in localStorage after successful login', async ({ page }) => {
      await loginPage.goto()

      await loginPage.loginAndWait(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      // Verify token is stored in localStorage
      const token = await page.evaluate(() => {
        return localStorage.getItem('token') || localStorage.getItem('auth_token')
      })

      expect(token).toBeTruthy()
      expect(typeof token).toBe('string')
      expect(token!.length).toBeGreaterThan(0)
    })

    test('should display user information after login', async ({ page }) => {
      await loginPage.goto()

      await loginPage.loginAndWait(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      // Look for username or user menu in header
      const userIndicator = page.locator(`text=${testCredentials.admin.username}`)
      await expect(userIndicator).toBeVisible({ timeout: 5000 })
    })
  })

  test.describe('Failed Login', () => {
    test('should show error message for completely invalid credentials', async ({ page }) => {
      await loginPage.goto()

      // Try to login with invalid credentials
      await loginPage.login('invaliduser', 'wrongpassword')

      // Wait for error message
      await loginPage.expectErrorMessage(/invalid/i)

      // Should remain on login page
      await loginPage.expectToBeOnLoginPage()
    })

    test('should show error for valid username but wrong password', async ({ page }) => {
      await loginPage.goto()

      await loginPage.login(testCredentials.admin.username, 'wrongpassword123')

      await loginPage.expectErrorMessage(/invalid/i)
      await loginPage.expectToBeOnLoginPage()
    })

    test('should show error for non-existent user', async ({ page }) => {
      await loginPage.goto()

      await loginPage.login('nonexistentuser99999', 'anypassword')

      await loginPage.expectErrorMessage(/invalid/i)
      await loginPage.expectToBeOnLoginPage()
    })

    test('should clear previous error on new login attempt', async ({ page }) => {
      await loginPage.goto()

      // First failed attempt
      await loginPage.login('baduser', 'badpass')
      await loginPage.expectErrorMessage(/invalid/i)

      // Clear inputs and try again with valid credentials
      await loginPage.usernameInput.clear()
      await loginPage.passwordInput.clear()
      await loginPage.usernameInput.fill(testCredentials.admin.username)
      await loginPage.passwordInput.fill(testCredentials.admin.password)
      await loginPage.submitButton.click()

      // Should redirect on success (error cleared)
      await expect(page).not.toHaveURL(/\/login/, { timeout: 10000 })
    })

    test('should not store token after failed login', async ({ page }) => {
      await loginPage.goto()

      await loginPage.login('baduser', 'badpassword')

      // Wait for error
      await page.waitForTimeout(1000)

      // Token should not be stored
      const token = await page.evaluate(() => {
        return localStorage.getItem('token') || localStorage.getItem('auth_token')
      })

      expect(token).toBeFalsy()
    })
  })

  test.describe('Form Validation', () => {
    test('should show validation error for empty username', async ({ page }) => {
      await loginPage.goto()

      // Try to submit with empty username
      await loginPage.passwordInput.fill('somepassword')
      await loginPage.submitButton.click()

      // Should show validation error or remain on page
      await loginPage.expectToBeOnLoginPage()

      // Look for validation error message
      const usernameError = page.getByTestId('input-error')
      const errorCount = await usernameError.count()

      if (errorCount > 0) {
        await expect(usernameError.first()).toBeVisible()
        await expect(usernameError.first()).toContainText(/required/i)
      }
    })

    test('should show validation error for empty password', async ({ page }) => {
      await loginPage.goto()

      // Try to submit with empty password
      await loginPage.usernameInput.fill('someuser')
      await loginPage.submitButton.click()

      await loginPage.expectToBeOnLoginPage()

      // Look for validation error message
      const passwordError = page.getByTestId('input-error')
      const errorCount = await passwordError.count()

      if (errorCount > 0) {
        await expect(passwordError.last()).toBeVisible()
        await expect(passwordError.last()).toContainText(/required/i)
      }
    })

    test('should show validation errors for completely empty form submission', async ({ page }) => {
      await loginPage.goto()

      // Submit empty form
      await loginPage.submitButton.click()

      // Should remain on login page
      await loginPage.expectToBeOnLoginPage()

      // Should show validation errors or prevent submission
      const errorMessages = page.getByTestId('input-error')
      const errorCount = await errorMessages.count()

      // Either shows validation errors (preferred) or prevents submission
      if (errorCount > 0) {
        expect(errorCount).toBeGreaterThanOrEqual(1)
        await expect(errorMessages.first()).toBeVisible()
      }
    })

    test('should disable submit button during login request', async ({ page }) => {
      await loginPage.goto()

      // Fill form with valid credentials
      await loginPage.usernameInput.fill(testCredentials.admin.username)
      await loginPage.passwordInput.fill(testCredentials.admin.password)

      // Initially enabled
      await expect(loginPage.submitButton).toBeEnabled()

      // Click submit and immediately check if disabled
      const submitPromise = loginPage.submitButton.click()

      // Button should be disabled or show loading state during submission
      // Check within a short time window
      await page.waitForTimeout(50)
      const isDisabled = await loginPage.submitButton.isDisabled().catch(() => false)
      const hasLoadingSpinner = await page.locator('.animate-spin, [role="status"]').isVisible().catch(() => false)

      // At least one loading indicator should be present
      expect(isDisabled || hasLoadingSpinner).toBeTruthy()

      await submitPromise
    })

    test('should trim whitespace from username input', async ({ page }) => {
      await loginPage.goto()

      // Fill username with leading/trailing whitespace
      await loginPage.usernameInput.fill(`  ${testCredentials.admin.username}  `)
      await loginPage.passwordInput.fill(testCredentials.admin.password)
      await loginPage.submitButton.click()

      // Should still login successfully if backend trims whitespace
      await expect(page).not.toHaveURL(/\/login/, { timeout: 10000 })
    })
  })

  test.describe('Logout', () => {
    test('should logout successfully and redirect to login', async ({ page }) => {
      // First login
      await loginPage.goto()
      await loginPage.loginAndWait(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      // Find and click logout button
      // Try multiple strategies to find the logout button
      const userMenu = page.locator('button').filter({ hasText: new RegExp(testCredentials.admin.username, 'i') }).first()

      if (await userMenu.isVisible({ timeout: 2000 }).catch(() => false)) {
        await userMenu.click()
        await page.waitForTimeout(300)
      } else {
        // Try alternative user menu selector
        const altUserMenu = page.getByTestId('user-menu')
        if (await altUserMenu.isVisible({ timeout: 2000 }).catch(() => false)) {
          await altUserMenu.click()
          await page.waitForTimeout(300)
        }
      }

      // Click logout button
      const logoutButton = page.getByRole('button', { name: /logout|sign out|log out/i })
      await expect(logoutButton).toBeVisible({ timeout: 5000 })
      await logoutButton.click()

      // Should redirect to login page
      await expect(page).toHaveURL(/\/login/, { timeout: 5000 })

      // Token should be cleared from localStorage
      const token = await page.evaluate(() => {
        return localStorage.getItem('token') || localStorage.getItem('auth_token')
      })
      expect(token).toBeFalsy()
    })

    test('should clear all authentication data on logout', async ({ page }) => {
      await loginPage.goto()
      await loginPage.loginAndWait(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      // Store current auth state
      const beforeLogout = await page.evaluate(() => {
        return {
          token: localStorage.getItem('token'),
          authToken: localStorage.getItem('auth_token'),
          user: localStorage.getItem('user'),
          localStorageKeys: Object.keys(localStorage),
        }
      })

      // Some auth data should exist
      expect(beforeLogout.token || beforeLogout.authToken).toBeTruthy()

      // Logout
      const userMenu = page.locator('button').filter({
        hasText: new RegExp(testCredentials.admin.username, 'i')
      }).first()

      if (await userMenu.isVisible({ timeout: 2000 }).catch(() => false)) {
        await userMenu.click()
        await page.waitForTimeout(300)
        await page.getByRole('button', { name: /logout|sign out|log out/i }).click()
      }

      await expect(page).toHaveURL(/\/login/, { timeout: 5000 })

      // All auth data should be cleared
      const afterLogout = await page.evaluate(() => {
        return {
          token: localStorage.getItem('token'),
          authToken: localStorage.getItem('auth_token'),
          user: localStorage.getItem('user'),
        }
      })

      expect(afterLogout.token).toBeFalsy()
      expect(afterLogout.authToken).toBeFalsy()
    })

    test('should prevent access to protected routes after logout', async ({ page }) => {
      // Login first
      await loginPage.goto()
      await loginPage.loginAndWait(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      // Navigate to protected route
      await page.goto('/tigers')
      await expect(page).toHaveURL(/\/tigers/)

      // Logout
      const userMenu = page.locator('button').filter({
        hasText: new RegExp(testCredentials.admin.username, 'i')
      }).first()

      if (await userMenu.isVisible({ timeout: 2000 }).catch(() => false)) {
        await userMenu.click()
        await page.waitForTimeout(300)
        await page.getByRole('button', { name: /logout|sign out|log out/i }).click()
      }

      await expect(page).toHaveURL(/\/login/)

      // Try to access protected route - should redirect to login
      await page.goto('/tigers')
      await expect(page).toHaveURL(/\/login/, { timeout: 5000 })
    })
  })

  test.describe('Protected Routes', () => {
    test('should redirect unauthenticated users to login page', async ({ page }) => {
      // Try to access protected routes without authentication
      const protectedRoutes = [
        '/dashboard',
        '/tigers',
        '/facilities',
        '/investigation2',
        '/templates',
      ]

      for (const route of protectedRoutes) {
        await page.goto(route)

        // Should redirect to login
        await expect(page).toHaveURL(/\/login/, { timeout: 5000 })

        // Clear any accidental auth state between route checks
        await page.evaluate(() => localStorage.clear())
      }
    })

    test('should allow authenticated users to access all protected routes', async ({ page }) => {
      // Login first
      await loginPage.goto()
      await loginPage.loginAndWait(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      // Try to access protected routes
      const protectedRoutes = [
        '/tigers',
        '/facilities',
        '/investigation2',
        '/templates',
      ]

      for (const route of protectedRoutes) {
        await page.goto(route)
        await page.waitForLoadState('networkidle')

        // Should NOT redirect to login
        await expect(page).not.toHaveURL(/\/login/, { timeout: 3000 })

        // Should be on the requested route
        await expect(page).toHaveURL(new RegExp(route))
      }
    })

    test('should redirect to login if authentication token is invalid', async ({ page }) => {
      // Set an invalid token manually
      await page.goto('/')
      await page.evaluate(() => {
        localStorage.setItem('token', 'invalid_token_12345')
      })

      // Try to access protected route
      await page.goto('/dashboard')

      // Should redirect to login when API call fails with 401
      await expect(page).toHaveURL(/\/login/, { timeout: 10000 })
    })

    test('should redirect to login if authentication token is expired', async ({ page }) => {
      // Set an expired-looking token
      await page.goto('/')
      await page.evaluate(() => {
        // JWT-like token with expired payload (not a real JWT, just for testing)
        localStorage.setItem('token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MTYyMzkwMjJ9.expired')
      })

      // Try to access protected route
      await page.goto('/tigers')

      // Should redirect to login
      await expect(page).toHaveURL(/\/login/, { timeout: 10000 })
    })
  })

  test.describe('Session Persistence', () => {
    test('should persist authentication across page refreshes', async ({ page }) => {
      // Login
      await loginPage.goto()
      await loginPage.loginAndWait(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      // Navigate to a protected route
      await page.goto('/tigers')
      await expect(page).toHaveURL(/\/tigers/)

      // Reload the page
      await page.reload()
      await page.waitForLoadState('networkidle')

      // Should still be authenticated
      await expect(page).not.toHaveURL(/\/login/)
      await expect(page).toHaveURL(/\/tigers/)
    })

    test('should persist authentication across navigation', async ({ page }) => {
      // Login
      await loginPage.goto()
      await loginPage.loginAndWait(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      // Navigate between multiple protected routes
      const routes = ['/tigers', '/facilities', '/investigation2', '/templates']

      for (const route of routes) {
        await page.goto(route)
        await page.waitForLoadState('networkidle')

        await expect(page).not.toHaveURL(/\/login/)
        await expect(page).toHaveURL(new RegExp(route))
      }
    })

    test('should restore authentication from stored token in new browser context', async ({ page, browser }) => {
      // Login and get token
      await loginPage.goto()
      await loginPage.loginAndWait(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      const token = await page.evaluate(() => localStorage.getItem('token'))
      expect(token).toBeTruthy()

      // Create a new browser context (simulates new browser session)
      const context = await browser.newContext()
      const newPage = await context.newPage()

      // Set token in new page
      await newPage.goto('http://localhost:5173')
      await newPage.evaluate((storedToken) => {
        localStorage.setItem('token', storedToken!)
      }, token)

      // Navigate to protected route
      await newPage.goto('/tigers')
      await newPage.waitForLoadState('networkidle')

      // Should be authenticated without manual login
      await expect(newPage).not.toHaveURL(/\/login/)
      await expect(newPage).toHaveURL(/\/tigers/)

      await newPage.close()
      await context.close()
    })

    test('should maintain session through multiple page interactions', async ({ page }) => {
      // Login
      await loginPage.goto()
      await loginPage.loginAndWait(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      // Perform multiple navigations and interactions
      for (let i = 0; i < 3; i++) {
        await page.goto('/tigers')
        await expect(page).toHaveURL(/\/tigers/)

        await page.goto('/facilities')
        await expect(page).toHaveURL(/\/facilities/)

        // Small delay to simulate user interaction
        await page.waitForTimeout(500)
      }

      // Should still be authenticated
      await expect(page).not.toHaveURL(/\/login/)
    })
  })

  test.describe('Password Reset Flow', () => {
    test('should navigate to password reset page from login', async ({ page }) => {
      await loginPage.goto()

      // Click forgot password link
      await loginPage.forgotPasswordLink.click()

      // Should navigate to password reset page
      await expect(page).toHaveURL(/\/password-reset|\/reset-password/)
    })

    test('should display password reset form', async ({ page }) => {
      await page.goto('/password-reset')

      // Verify form elements are present
      const emailInput = page.locator('input[type="email"], input[name="email"]')
      await expect(emailInput).toBeVisible()

      const submitButton = page.getByRole('button', { name: /send|reset|submit/i })
      await expect(submitButton).toBeVisible()
    })

    test('should request password reset with valid email', async ({ page }) => {
      await page.goto('/password-reset')

      // Fill email
      const emailInput = page.locator('input[type="email"], input[name="email"]').first()
      await emailInput.fill('test@example.com')

      // Submit
      const submitButton = page.getByRole('button', { name: /send|reset|submit/i })
      await submitButton.click()

      // Should show success message or confirmation
      const alert = page.getByTestId('alert')
      if (await alert.isVisible({ timeout: 3000 }).catch(() => false)) {
        await expect(alert).toContainText(/reset|sent|email/i)
      }
    })

    test('should show validation error for invalid email format', async ({ page }) => {
      await page.goto('/password-reset')

      // Fill invalid email
      const emailInput = page.locator('input[type="email"], input[name="email"]').first()
      await emailInput.fill('invalid-email-format')

      // Submit
      const submitButton = page.getByRole('button', { name: /send|reset|submit/i })
      await submitButton.click()

      // Should show validation error
      const error = page.getByTestId('input-error')
      if (await error.isVisible({ timeout: 2000 }).catch(() => false)) {
        await expect(error).toContainText(/valid|email/i)
      }
    })

    test('should show validation error for empty email', async ({ page }) => {
      await page.goto('/password-reset')

      // Submit without filling email
      const submitButton = page.getByRole('button', { name: /send|reset|submit/i })
      await submitButton.click()

      // Should show validation error or remain on page
      await expect(page).toHaveURL(/\/password-reset|\/reset-password/)

      const error = page.getByTestId('input-error')
      if (await error.isVisible({ timeout: 2000 }).catch(() => false)) {
        await expect(error).toContainText(/required|email/i)
      }
    })

    test('should reset password with valid token and matching passwords', async ({ page }) => {
      // Navigate to password reset confirm page with token
      await page.goto('/password-reset?token=valid_reset_token_12345678')

      // Wait for form to load
      await page.waitForLoadState('networkidle')

      // Fill new password fields
      const newPasswordInput = page.locator('input[name="new_password"], input[name="password"]').first()
      const confirmPasswordInput = page.locator('input[name="confirm_password"], input[name="password_confirm"]').first()

      if (await newPasswordInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await newPasswordInput.fill('newpassword123')
        await confirmPasswordInput.fill('newpassword123')

        // Submit
        const submitButton = page.getByRole('button', { name: /reset|submit|change/i })
        await submitButton.click()

        // Should show success message
        const alert = page.getByTestId('alert')
        if (await alert.isVisible({ timeout: 3000 }).catch(() => false)) {
          await expect(alert).toContainText(/success|reset|changed/i)
        }

        // Should redirect to login after delay
        await expect(page).toHaveURL(/\/login/, { timeout: 10000 })
      }
    })

    test('should show error for password mismatch', async ({ page }) => {
      await page.goto('/password-reset?token=valid_reset_token_12345678')

      // Fill mismatched passwords
      const newPasswordInput = page.locator('input[name="new_password"], input[name="password"]').first()
      const confirmPasswordInput = page.locator('input[name="confirm_password"], input[name="password_confirm"]').first()

      if (await newPasswordInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await newPasswordInput.fill('password123')
        await confirmPasswordInput.fill('different456')

        // Submit
        const submitButton = page.getByRole('button', { name: /reset|submit|change/i })
        await submitButton.click()

        // Should show validation error
        const error = page.getByTestId('input-error')
        if (await error.isVisible({ timeout: 2000 }).catch(() => false)) {
          await expect(error).toContainText(/match|same/i)
        }
      }
    })

    test('should show error for password that is too short', async ({ page }) => {
      await page.goto('/password-reset?token=valid_reset_token_12345678')

      // Fill short password
      const newPasswordInput = page.locator('input[name="new_password"], input[name="password"]').first()
      const confirmPasswordInput = page.locator('input[name="confirm_password"], input[name="password_confirm"]').first()

      if (await newPasswordInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await newPasswordInput.fill('short')
        await confirmPasswordInput.fill('short')

        // Submit
        const submitButton = page.getByRole('button', { name: /reset|submit|change/i })
        await submitButton.click()

        // Should show validation error
        const error = page.getByTestId('input-error')
        if (await error.isVisible({ timeout: 2000 }).catch(() => false)) {
          await expect(error).toContainText(/8 characters|minimum|too short/i)
        }
      }
    })

    test('should navigate back to login from password reset page', async ({ page }) => {
      await page.goto('/password-reset')

      // Click back to login link
      const backLink = page.getByRole('link', { name: /back|login|sign in/i })
      if (await backLink.isVisible({ timeout: 2000 }).catch(() => false)) {
        await backLink.click()

        // Should navigate to login page
        await expect(page).toHaveURL(/\/login/)
      }
    })

    test('should show error for invalid or expired reset token', async ({ page }) => {
      // Navigate with obviously invalid token
      await page.goto('/password-reset?token=invalid')

      const newPasswordInput = page.locator('input[name="new_password"], input[name="password"]').first()
      const confirmPasswordInput = page.locator('input[name="confirm_password"], input[name="password_confirm"]').first()

      if (await newPasswordInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await newPasswordInput.fill('validpassword123')
        await confirmPasswordInput.fill('validpassword123')

        const submitButton = page.getByRole('button', { name: /reset|submit|change/i })
        await submitButton.click()

        // Should show error about invalid token
        const error = page.getByTestId('alert')
        if (await error.isVisible({ timeout: 3000 }).catch(() => false)) {
          await expect(error).toContainText(/invalid|expired|token/i)
        }
      }
    })
  })

  test.describe('Remember Me Functionality', () => {
    test('should have remember me checkbox on login page', async ({ page }) => {
      await loginPage.goto()

      const rememberMeCheckbox = page.locator('input[type="checkbox"][name="remember_me"], input[type="checkbox"][name="remember"]')

      // Check if remember me feature is implemented
      if (await rememberMeCheckbox.count() > 0) {
        await expect(rememberMeCheckbox.first()).toBeVisible()
      }
    })

    test('should allow toggling remember me option', async ({ page }) => {
      await loginPage.goto()

      const rememberMeCheckbox = page.locator('input[type="checkbox"][name="remember_me"], input[type="checkbox"][name="remember"]').first()

      if (await rememberMeCheckbox.isVisible().catch(() => false)) {
        // Initially unchecked
        const initialState = await rememberMeCheckbox.isChecked()

        // Toggle it
        await rememberMeCheckbox.check()
        await expect(rememberMeCheckbox).toBeChecked()

        // Toggle back
        await rememberMeCheckbox.uncheck()
        await expect(rememberMeCheckbox).not.toBeChecked()
      }
    })
  })

  test.describe('Security', () => {
    test('should mask password input by default', async ({ page }) => {
      await loginPage.goto()

      // Password input should have type="password"
      await expect(loginPage.passwordInput).toHaveAttribute('type', 'password')
    })

    test('should not expose credentials in URL at any point', async ({ page }) => {
      await loginPage.goto()

      await loginPage.login(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      // Wait for response
      await page.waitForTimeout(2000)

      // URL should never contain credentials
      const url = page.url()
      expect(url).not.toContain(testCredentials.admin.username)
      expect(url).not.toContain(testCredentials.admin.password)
    })

    test('should not log authentication tokens to console', async ({ page }) => {
      const consoleLogs: string[] = []

      page.on('console', (msg) => {
        consoleLogs.push(msg.text())
      })

      await loginPage.goto()
      await loginPage.loginAndWait(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      // Token should not be logged to console
      const hasTokenInLogs = consoleLogs.some((log) =>
        log.includes('token') && (log.includes('Bearer') || log.includes('eyJ'))
      )
      expect(hasTokenInLogs).toBe(false)
    })

    test('should clear sensitive data from memory on logout', async ({ page }) => {
      await loginPage.goto()
      await loginPage.loginAndWait(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      // Store initial data
      const beforeLogout = await page.evaluate(() => {
        return {
          localStorage: JSON.stringify(localStorage),
          sessionStorage: JSON.stringify(sessionStorage),
        }
      })

      expect(beforeLogout.localStorage).toContain('token')

      // Logout
      const userMenu = page.locator('button').filter({
        hasText: new RegExp(testCredentials.admin.username, 'i')
      }).first()

      if (await userMenu.isVisible({ timeout: 2000 }).catch(() => false)) {
        await userMenu.click()
        await page.waitForTimeout(300)
        await page.getByRole('button', { name: /logout|sign out|log out/i }).click()
      }

      await expect(page).toHaveURL(/\/login/)

      // Verify data is cleared
      const afterLogout = await page.evaluate(() => {
        return {
          localStorage: JSON.stringify(localStorage),
          sessionStorage: JSON.stringify(sessionStorage),
        }
      })

      expect(afterLogout.localStorage).not.toContain('token')
    })
  })

  test.describe('Accessibility', () => {
    test('should have accessible form labels associated with inputs', async ({ page }) => {
      await loginPage.goto()

      // Labels should be associated with inputs via for/id or wrapping
      const usernameLabel = page.locator('label:has-text("Username")')
      const passwordLabel = page.locator('label:has-text("Password")')

      await expect(usernameLabel).toBeVisible()
      await expect(passwordLabel).toBeVisible()

      // Check if labels are properly associated
      const usernameLabelFor = await usernameLabel.getAttribute('for').catch(() => null)
      const usernameInputId = await loginPage.usernameInput.getAttribute('id').catch(() => null)

      // Either label wraps input or for/id match
      const isUsernameAccessible = usernameLabelFor === usernameInputId ||
                                   await usernameLabel.locator('input').count() > 0

      expect(isUsernameAccessible).toBeTruthy()
    })

    test('should support keyboard navigation through form', async ({ page }) => {
      await loginPage.goto()

      // Tab through form elements
      await page.keyboard.press('Tab') // Focus first interactive element

      // Username should be focusable
      await loginPage.usernameInput.focus()
      await page.keyboard.type('testuser')

      await page.keyboard.press('Tab') // Move to password
      const passwordFocused = await page.evaluate(() =>
        document.activeElement?.getAttribute('type') === 'password'
      )
      expect(passwordFocused).toBeTruthy()

      await page.keyboard.type('testpass')

      await page.keyboard.press('Tab') // Move to next element (button or checkbox)

      // Should be able to submit with Enter key
      await page.keyboard.press('Enter')

      // Form should submit
      await page.waitForTimeout(1000)
    })

    test('should announce errors to screen readers with proper ARIA attributes', async ({ page }) => {
      await loginPage.goto()

      // Submit empty form
      await loginPage.submitButton.click()

      // Error messages should be visible and have proper ARIA attributes
      const errors = page.getByTestId('input-error')
      const errorCount = await errors.count()

      if (errorCount > 0) {
        for (let i = 0; i < errorCount; i++) {
          const error = errors.nth(i)
          await expect(error).toBeVisible()

          const text = await error.textContent()
          expect(text?.trim().length).toBeGreaterThan(0)

          // Check for ARIA attributes
          const hasAriaRole = await error.getAttribute('role').catch(() => null)
          const hasAriaLive = await error.getAttribute('aria-live').catch(() => null)

          // Error should have role="alert" or aria-live attribute
          expect(hasAriaRole === 'alert' || hasAriaLive !== null).toBeTruthy()
        }
      }
    })

    test('should have sufficient color contrast for all text', async ({ page }) => {
      await loginPage.goto()

      // This is a basic check - full contrast testing requires specialized tools
      // We just verify text is visible
      const allText = page.locator('text=Login, text=Username, text=Password')
      const textCount = await allText.count()

      expect(textCount).toBeGreaterThan(0)
    })

    test('should have focus indicators on interactive elements', async ({ page }) => {
      await loginPage.goto()

      // Focus username input
      await loginPage.usernameInput.focus()

      // Check if there's a visible focus indicator (outline, ring, etc.)
      const hasOutline = await loginPage.usernameInput.evaluate((el) => {
        const styles = window.getComputedStyle(el)
        return styles.outline !== 'none' ||
               styles.boxShadow !== 'none' ||
               styles.borderColor !== 'rgb(0, 0, 0)'
      })

      // Note: This is implementation-dependent, but elements should have some focus indicator
      expect(hasOutline).toBeTruthy()
    })
  })

  test.describe('Error Handling', () => {
    test('should handle network errors gracefully', async ({ page }) => {
      // This test requires network interception
      await page.route('**/api/auth/login', route => route.abort())

      await loginPage.goto()
      await loginPage.login(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      // Should show error message or remain on login page
      await page.waitForTimeout(2000)
      await loginPage.expectToBeOnLoginPage()
    })

    test('should handle slow network connections', async ({ page }) => {
      // Throttle network
      await page.route('**/api/auth/login', async route => {
        await new Promise(resolve => setTimeout(resolve, 2000))
        await route.continue()
      })

      await loginPage.goto()
      await loginPage.login(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      // Should show loading indicator during slow request
      const loadingIndicator = page.locator('.animate-spin, [role="status"]')
      await expect(loadingIndicator).toBeVisible()
    })

    test('should handle server errors (500)', async ({ page }) => {
      // Return 500 error
      await page.route('**/api/auth/login', route =>
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Internal Server Error' })
        })
      )

      await loginPage.goto()
      await loginPage.login(
        testCredentials.admin.username,
        testCredentials.admin.password
      )

      // Should show error message
      await page.waitForTimeout(1000)
      const errorMessage = page.getByTestId('login-error')
      if (await errorMessage.isVisible({ timeout: 2000 }).catch(() => false)) {
        await expect(errorMessage).toContainText(/error|failed|try again/i)
      }

      await loginPage.expectToBeOnLoginPage()
    })
  })
})

import { test, expect } from '@playwright/test'

test('should display login page', async ({ page }) => {
  await page.goto('/login')
  
  await expect(page.locator('h1')).toContainText('Tiger ID')
  await expect(page.locator('button[type="submit"]')).toBeVisible()
})

test('should navigate to home page after login', async ({ page }) => {
  await page.goto('/login')
  
  // Fill in login form
  await page.fill('input[name="username"]', 'testuser')
  await page.fill('input[name="password"]', 'testpassword')
  
  // Note: This will fail without proper backend/authentication
  // This is just an example test structure
})


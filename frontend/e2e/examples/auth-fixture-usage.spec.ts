/**
 * Example test file demonstrating authentication fixture usage
 *
 * This file shows how to use the auth.fixture.ts fixtures in your tests.
 * DO NOT run this file - it is just examples!
 */
import { test, expect } from '../fixtures/auth.fixture'

// Example 1: Using authenticatedPage (default analyst role)
test.skip('authenticated user can access dashboard', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/')
  
  // Should be redirected to dashboard or already authenticated
  await expect(authenticatedPage).toHaveURL(/\/(dashboard|tigers|investigations)/)
  
  // Verify user is authenticated
  const hasToken = await authenticatedPage.evaluate(() => {
    return !!localStorage.getItem('token')
  })
  expect(hasToken).toBe(true)
})

// Example 2: Using adminPage for admin-only tests
test.skip('admin can access user management', async ({ adminPage }) => {
  await adminPage.goto('/admin/users')
  
  // Admin-specific functionality
  await expect(adminPage.locator('h1')).toContainText('User Management')
  
  // Should see admin controls
  await expect(adminPage.locator('[data-testid="create-user-button"]')).toBeVisible()
})

// Example 3: Using analystPage explicitly
test.skip('analyst can create investigation', async ({ analystPage }) => {
  await analystPage.goto('/investigations')
  
  // Click create investigation
  await analystPage.click('[data-testid="create-investigation-button"]')
  
  // Fill investigation form
  await analystPage.fill('[name="title"]', 'Test Investigation')
  await analystPage.click('[data-testid="submit-investigation"]')
  
  // Verify investigation created
  await expect(analystPage.locator('[data-testid="investigation-success"]')).toBeVisible()
})

// Example 4: Using viewerPage for read-only tests
test.skip('viewer cannot create investigations', async ({ viewerPage }) => {
  await viewerPage.goto('/investigations')
  
  // Create button should not be visible for viewer role
  await expect(viewerPage.locator('[data-testid="create-investigation-button"]')).not.toBeVisible()
  
  // But can view existing investigations
  await expect(viewerPage.locator('[data-testid="investigations-list"]')).toBeVisible()
})

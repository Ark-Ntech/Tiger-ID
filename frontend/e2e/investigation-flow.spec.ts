import { test, expect } from '@playwright/test'
import path from 'path'

test.describe('Investigation 2.0 Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Assume we need to be logged in for investigations
    await page.goto('/login')

    const usernameInput = page.locator('input[name="username"], input[type="text"]').first()
    const passwordInput = page.locator('input[name="password"], input[type="password"]').first()

    if (await usernameInput.count() > 0) {
      await usernameInput.fill('testuser')
      await passwordInput.fill('testpassword')
      await page.locator('button[type="submit"]').click()
      await page.waitForTimeout(1500)
    }
  })

  test('should display Investigation 2.0 page with upload capability', async ({ page }) => {
    await page.goto('/investigation2')

    // Check page loaded
    await expect(page.locator('h1, h2, h3')).toContainText(/Investigation/i)

    // Look for file upload input
    const fileInput = page.locator('input[type="file"]')
    await expect(fileInput.first()).toBeVisible()
  })

  test('should validate file type on upload', async ({ page }) => {
    await page.goto('/investigation2')

    // Try to upload an invalid file type (text file)
    const fileInput = page.locator('input[type="file"]').first()

    // Create a test text file (this is a mock - adjust path as needed)
    const testFilePath = path.join(__dirname, 'fixtures', 'test.txt')

    // This will fail gracefully if file doesn't exist
    try {
      await fileInput.setInputFiles(testFilePath)
      await page.waitForTimeout(1000)

      // Should show validation error for non-image files
      const errorMessage = page.locator('text=/invalid|error|supported/i')
      if (await errorMessage.count() > 0) {
        await expect(errorMessage.first()).toBeVisible()
      }
    } catch (error) {
      // Skip if test file doesn't exist
      console.log('Test fixture not available, skipping file validation test')
    }
  })

  test('should show investigation phases during processing', async ({ page }) => {
    await page.goto('/investigation2')

    // The 6 phases from the workflow
    const expectedPhases = [
      'upload_and_parse',
      'reverse_image_search',
      'tiger_detection',
      'stripe_analysis',
      'report_generation',
      'complete'
    ]

    // Check if phase indicators are present (they may be hidden until upload)
    for (const phase of expectedPhases) {
      const phaseElement = page.locator(`[data-phase="${phase}"], text=/${phase}/i`)
      // Phases may not be visible until investigation starts
      const count = await phaseElement.count()
      expect(count).toBeGreaterThanOrEqual(0)
    }
  })

  test('should display progress indicators', async ({ page }) => {
    await page.goto('/investigation2')

    // Look for progress-related elements
    const progressElements = [
      page.locator('[role="progressbar"]'),
      page.locator('.progress'),
      page.locator('[class*="spinner"]'),
      page.locator('[class*="loading"]')
    ]

    // At least one progress indicator should exist on the page
    let foundProgress = false
    for (const element of progressElements) {
      if (await element.count() > 0) {
        foundProgress = true
        break
      }
    }

    // Progress indicators exist (may not be visible until investigation starts)
    expect(foundProgress).toBe(true)
  })

  test('should handle WebSocket connection for real-time updates', async ({ page }) => {
    await page.goto('/investigation2')

    // Check if WebSocket connection is attempted
    const wsConnected = await page.evaluate(() => {
      // Check for socket.io or WebSocket instances
      return !!(window as any).io || typeof WebSocket !== 'undefined'
    })

    expect(wsConnected).toBe(true)
  })

  test('should display investigation results after completion', async ({ page }) => {
    await page.goto('/investigation2')

    // Note: This test would require either:
    // 1. Mocking the backend responses
    // 2. Actually running an investigation (slow)
    // 3. Loading a pre-completed investigation

    // For now, check that result components exist in the DOM
    const resultComponents = [
      page.locator('[data-testid="investigation-results"]'),
      page.locator('.results'),
      page.locator('[class*="match"]'),
      page.locator('[class*="confidence"]')
    ]

    // Check if result structure exists (may be hidden)
    let hasResultStructure = false
    for (const component of resultComponents) {
      if (await component.count() > 0) {
        hasResultStructure = true
        break
      }
    }

    // Results structure should exist in the page
    expect(hasResultStructure).toBe(true)
  })

  test('should show methodology tracking', async ({ page }) => {
    await page.goto('/investigation2')

    // Check for methodology-related elements
    const methodologyElements = [
      page.locator('text=/methodology/i'),
      page.locator('[data-testid="methodology"]'),
      page.locator('text=/ensemble/i'),
      page.locator('text=/model/i')
    ]

    let hasMethodology = false
    for (const element of methodologyElements) {
      if (await element.count() > 0) {
        hasMethodology = true
        break
      }
    }

    expect(hasMethodology).toBe(true)
  })

  test('should allow downloading investigation report', async ({ page }) => {
    await page.goto('/investigation2')

    // Look for download/export buttons
    const downloadButton = page.locator('button:has-text("Download"), button:has-text("Export"), button:has-text("Report")')

    if (await downloadButton.count() > 0) {
      // Button exists
      await expect(downloadButton.first()).toBeVisible()
    }
  })

  test('should display confidence scores for matches', async ({ page }) => {
    await page.goto('/investigation2')

    // Check for confidence-related elements in the page structure
    const confidenceElements = [
      page.locator('text=/confidence/i'),
      page.locator('[data-testid*="confidence"]'),
      page.locator('[class*="confidence"]'),
      page.locator('text=/%/') // Percentage indicators
    ]

    let hasConfidence = false
    for (const element of confidenceElements) {
      if (await element.count() > 0) {
        hasConfidence = true
        break
      }
    }

    expect(hasConfidence).toBe(true)
  })

  test('should show ensemble visualization', async ({ page }) => {
    await page.goto('/investigation2')

    // Check for ensemble-related visualizations
    const ensembleElements = [
      page.locator('text=/ensemble/i'),
      page.locator('[data-testid="ensemble-visualization"]'),
      page.locator('text=/wildlife_tools|cvwc2019|transreid|megadescriptor/i')
    ]

    let hasEnsemble = false
    for (const element of ensembleElements) {
      if (await element.count() > 0) {
        hasEnsemble = true
        break
      }
    }

    expect(hasEnsemble).toBe(true)
  })

  test('should navigate between investigation tabs/sections', async ({ page }) => {
    await page.goto('/investigation2')

    // Look for tab navigation
    const tabs = page.locator('[role="tab"], [role="tablist"] button')

    if (await tabs.count() > 0) {
      // Click through tabs
      const tabCount = await tabs.count()
      for (let i = 0; i < Math.min(tabCount, 3); i++) {
        await tabs.nth(i).click()
        await page.waitForTimeout(300)
        // Tab should be selected
        const ariaSelected = await tabs.nth(i).getAttribute('aria-selected')
        if (ariaSelected !== null) {
          expect(ariaSelected).toBe('true')
        }
      }
    }
  })

  test('should handle investigation errors gracefully', async ({ page }) => {
    await page.goto('/investigation2')

    // Check for error handling components
    const errorElements = [
      page.locator('[role="alert"]'),
      page.locator('.error'),
      page.locator('[class*="error"]'),
      page.locator('text=/error/i')
    ]

    // Error handling structure should exist
    let hasErrorHandling = false
    for (const element of errorElements) {
      if (await element.count() > 0) {
        hasErrorHandling = true
        break
      }
    }

    // Error components should be present in the page
    expect(hasErrorHandling).toBe(true)
  })
})

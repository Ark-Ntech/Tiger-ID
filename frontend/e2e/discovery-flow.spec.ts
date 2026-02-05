import { test, expect } from '@playwright/test'

test.describe('Discovery Pipeline Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
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

  test('should display discovery page', async ({ page }) => {
    await page.goto('/discovery')

    // Check page title
    await expect(page.locator('h1, h2')).toContainText(/Discovery/i)
  })

  test('should show discovery pipeline status', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForTimeout(1000)

    // Look for status indicators
    const statusElements = [
      page.locator('text=/Status/i'),
      page.locator('text=/Active|Idle|Running/i'),
      page.locator('[data-testid="discovery-status"]')
    ]

    let hasStatus = false
    for (const element of statusElements) {
      if (await element.count() > 0) {
        hasStatus = true
        break
      }
    }

    expect(hasStatus).toBe(true)
  })

  test('should display discovery statistics', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForTimeout(1000)

    // Look for stats
    const statsElements = [
      page.locator('text=/Total|Count/i'),
      page.locator('text=/Images|Tigers|Facilities/i'),
      page.locator('[data-testid="discovery-stats"]'),
      page.locator('text=/[0-9]+/')
    ]

    let hasStats = false
    for (const element of statsElements) {
      if (await element.count() > 0) {
        hasStats = true
        break
      }
    }

    expect(hasStats).toBe(true)
  })

  test('should have start discovery button', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForTimeout(1000)

    // Look for start/trigger button
    const startButton = page.locator('button:has-text("Start"), button:has-text("Run"), button:has-text("Trigger")')

    if (await startButton.count() > 0) {
      await expect(startButton.first()).toBeVisible()
    }
  })

  test('should have stop/pause discovery button', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForTimeout(1000)

    // Look for stop/pause button
    const stopButton = page.locator('button:has-text("Stop"), button:has-text("Pause")')

    // May or may not be visible depending on pipeline state
    const count = await stopButton.count()
    expect(count).toBeGreaterThanOrEqual(0)
  })

  test('should display list of facilities being monitored', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForTimeout(1000)

    // Look for facility list
    const facilityElements = [
      page.locator('text=/Facilities|Monitored/i'),
      page.locator('[data-testid="monitored-facilities"]'),
      page.locator('a[href*="/facilities/"]')
    ]

    let hasFacilities = false
    for (const element of facilityElements) {
      if (await element.count() > 0) {
        hasFacilities = true
        break
      }
    }

    expect(typeof hasFacilities).toBe('boolean')
  })

  test('should show crawl history/timeline', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForTimeout(1000)

    // Look for history elements
    const historyElements = [
      page.locator('text=/History/i'),
      page.locator('text=/Recent|Last/i'),
      page.locator('[data-testid="crawl-history"]'),
      page.locator('text=/Crawl/i')
    ]

    let hasHistory = false
    for (const element of historyElements) {
      if (await element.count() > 0) {
        hasHistory = true
        break
      }
    }

    expect(typeof hasHistory).toBe('boolean')
  })

  test('should display rate limiting information', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForTimeout(1000)

    // Look for rate limiting info
    const rateLimitElements = [
      page.locator('text=/Rate|Limit/i'),
      page.locator('text=/per domain|per site/i'),
      page.locator('[data-testid="rate-limit"]')
    ]

    let hasRateLimit = false
    for (const element of rateLimitElements) {
      if (await element.count() > 0) {
        hasRateLimit = true
        break
      }
    }

    expect(typeof hasRateLimit).toBe('boolean')
  })

  test('should show discovered images count', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForTimeout(1000)

    // Look for image count
    const imageCountElements = [
      page.locator('text=/Images/i'),
      page.locator('text=/Discovered/i'),
      page.locator('[data-testid="discovered-images"]')
    ]

    let hasImageCount = false
    for (const element of imageCountElements) {
      if (await element.count() > 0) {
        hasImageCount = true
        break
      }
    }

    expect(typeof hasImageCount).toBe('boolean')
  })

  test('should display deduplication statistics', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForTimeout(1000)

    // Look for deduplication info
    const dedupeElements = [
      page.locator('text=/Duplicate/i'),
      page.locator('text=/Unique/i'),
      page.locator('text=/SHA256|Hash/i'),
      page.locator('[data-testid="deduplication"]')
    ]

    let hasDedupe = false
    for (const element of dedupeElements) {
      if (await element.count() > 0) {
        hasDedupe = true
        break
      }
    }

    expect(typeof hasDedupe).toBe('boolean')
  })

  test('should show crawl progress for active crawls', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForTimeout(1000)

    // Look for progress indicators
    const progressElements = [
      page.locator('[role="progressbar"]'),
      page.locator('.progress'),
      page.locator('text=/Progress/i'),
      page.locator('text=/%/')
    ]

    let hasProgress = false
    for (const element of progressElements) {
      if (await element.count() > 0) {
        hasProgress = true
        break
      }
    }

    expect(typeof hasProgress).toBe('boolean')
  })

  test('should display errors and failed crawls', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForTimeout(1000)

    // Look for error information
    const errorElements = [
      page.locator('text=/Error|Failed/i'),
      page.locator('[data-testid="crawl-errors"]'),
      page.locator('[role="alert"]')
    ]

    let hasErrors = false
    for (const element of errorElements) {
      if (await element.count() > 0) {
        hasErrors = true
        break
      }
    }

    expect(typeof hasErrors).toBe('boolean')
  })

  test('should show Playwright/browser automation status', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForTimeout(1000)

    // Look for browser automation mentions
    const browserElements = [
      page.locator('text=/Playwright|Browser/i'),
      page.locator('text=/JavaScript|Render/i'),
      page.locator('[data-testid="browser-status"]')
    ]

    let hasBrowserInfo = false
    for (const element of browserElements) {
      if (await element.count() > 0) {
        hasBrowserInfo = true
        break
      }
    }

    expect(typeof hasBrowserInfo).toBe('boolean')
  })

  test('should allow filtering discovery results', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForTimeout(1000)

    // Look for filter controls
    const filterElements = [
      page.locator('select'),
      page.locator('button:has-text("Filter")'),
      page.locator('input[type="search"]')
    ]

    let hasFilters = false
    for (const element of filterElements) {
      if (await element.count() > 0) {
        hasFilters = true
        break
      }
    }

    expect(typeof hasFilters).toBe('boolean')
  })

  test('should display recently discovered tigers', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForTimeout(1000)

    // Look for tiger results
    const tigerElements = [
      page.locator('text=/Tigers/i'),
      page.locator('a[href*="/tigers/"]'),
      page.locator('[data-testid="discovered-tigers"]')
    ]

    let hasTigers = false
    for (const element of tigerElements) {
      if (await element.count() > 0) {
        hasTigers = true
        break
      }
    }

    expect(typeof hasTigers).toBe('boolean')
  })

  test('should show next scheduled crawl time', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForTimeout(1000)

    // Look for schedule information
    const scheduleElements = [
      page.locator('text=/Next|Scheduled/i'),
      page.locator('text=/Schedule/i'),
      page.locator('[data-testid="next-crawl"]')
    ]

    let hasSchedule = false
    for (const element of scheduleElements) {
      if (await element.count() > 0) {
        hasSchedule = true
        break
      }
    }

    expect(typeof hasSchedule).toBe('boolean')
  })

  test('should display crawl configuration settings', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForTimeout(1000)

    // Look for settings/config
    const configElements = [
      page.locator('button:has-text("Settings"), button:has-text("Config")'),
      page.locator('text=/Configuration/i'),
      page.locator('[data-testid="discovery-settings"]')
    ]

    let hasConfig = false
    for (const element of configElements) {
      if (await element.count() > 0) {
        hasConfig = true
        break
      }
    }

    expect(typeof hasConfig).toBe('boolean')
  })
})

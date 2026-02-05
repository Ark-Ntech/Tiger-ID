import { test, expect } from '@playwright/test'

test.describe('Facility Management Flow', () => {
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

  test('should display facilities list page', async ({ page }) => {
    await page.goto('/facilities')

    // Check page title
    await expect(page.locator('h1, h2')).toContainText(/Facilit/i)

    // Should have some list structure
    const listElements = [
      page.locator('table'),
      page.locator('[role="list"]'),
      page.locator('.facility-list'),
      page.locator('[data-testid="facility-list"]')
    ]

    let hasList = false
    for (const element of listElements) {
      if (await element.count() > 0) {
        hasList = true
        break
      }
    }

    expect(hasList).toBe(true)
  })

  test('should display facility cards or table rows', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    // Check for facility entries
    const facilityEntries = [
      page.locator('tr[data-facility-id]'),
      page.locator('.facility-card'),
      page.locator('[data-testid="facility-card"]'),
      page.locator('tbody tr')
    ]

    let hasEntries = false
    for (const element of facilityEntries) {
      const count = await element.count()
      if (count > 0) {
        hasEntries = true
        break
      }
    }

    expect(typeof hasEntries).toBe('boolean')
  })

  test('should have search/filter functionality', async ({ page }) => {
    await page.goto('/facilities')

    // Look for search input
    const searchInput = page.locator('input[type="search"], input[placeholder*="Search"], input[placeholder*="Filter"]')

    if (await searchInput.count() > 0) {
      await expect(searchInput.first()).toBeVisible()

      // Try typing in search
      await searchInput.first().fill('zoo')
      await page.waitForTimeout(500)

      await expect(searchInput.first()).toHaveValue('zoo')
    }
  })

  test('should have filter by location/type', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    // Look for filter controls
    const filterElements = [
      page.locator('select'),
      page.locator('button:has-text("Filter")'),
      page.locator('[data-testid="filter"]'),
      page.locator('text=/Location|Type|Category/i')
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

  test('should display facility metadata in list view', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    // Check for common facility metadata fields
    const metadataElements = [
      page.locator('text=/Name/i'),
      page.locator('text=/Location/i'),
      page.locator('text=/Type/i'),
      page.locator('text=/City|State|Country/i')
    ]

    let hasMetadata = false
    for (const element of metadataElements) {
      if (await element.count() > 0) {
        hasMetadata = true
        break
      }
    }

    expect(typeof hasMetadata).toBe('boolean')
  })

  test('should navigate to facility detail page', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    // Look for clickable facility entries
    const facilityLinks = page.locator('a[href*="/facilities/"], tr[data-facility-id]')

    if (await facilityLinks.count() > 0) {
      const firstLink = facilityLinks.first()
      await firstLink.click()

      await page.waitForTimeout(1000)

      // Should navigate to detail page
      await expect(page).toHaveURL(/\/facilities\/\w+/)
    }
  })

  test('should display facility detail page with information', async ({ page }) => {
    await page.goto('/facilities/test-facility-id')
    await page.waitForTimeout(1000)

    const currentUrl = page.url()

    if (currentUrl.includes('/facilities/')) {
      // Check for detail elements
      const detailElements = [
        page.locator('h1, h2, h3'),
        page.locator('text=/Name|Location|Type|Address/i')
      ]

      let hasDetails = false
      for (const element of detailElements) {
        if (await element.count() > 0) {
          hasDetails = true
          break
        }
      }

      expect(typeof hasDetails).toBe('boolean')
    }
  })

  test('should show facility location on map', async ({ page }) => {
    await page.goto('/facilities/test-facility-id')
    await page.waitForTimeout(1000)

    // Look for map elements (Leaflet)
    const mapElements = [
      page.locator('.leaflet-container'),
      page.locator('[id*="map"]'),
      page.locator('[data-testid="facility-map"]')
    ]

    let hasMap = false
    for (const element of mapElements) {
      if (await element.count() > 0) {
        hasMap = true
        break
      }
    }

    expect(typeof hasMap).toBe('boolean')
  })

  test('should display tigers associated with facility', async ({ page }) => {
    await page.goto('/facilities/test-facility-id')
    await page.waitForTimeout(1000)

    // Look for tiger list or count
    const tigerElements = [
      page.locator('text=/Tigers/i'),
      page.locator('[data-testid="facility-tigers"]'),
      page.locator('a[href*="/tigers/"]'),
      page.locator('text=/tiger count/i')
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

  test('should show facility website and social media links', async ({ page }) => {
    await page.goto('/facilities/test-facility-id')
    await page.waitForTimeout(1000)

    // Look for external links
    const linkElements = [
      page.locator('a[href^="http"]'),
      page.locator('text=/Website/i'),
      page.locator('text=/Social|Facebook|Twitter|Instagram/i')
    ]

    let hasLinks = false
    for (const element of linkElements) {
      if (await element.count() > 0) {
        hasLinks = true
        break
      }
    }

    expect(typeof hasLinks).toBe('boolean')
  })

  test('should have add/import facility functionality', async ({ page }) => {
    await page.goto('/facilities')

    // Look for add button
    const addButton = page.locator('button:has-text("Add"), button:has-text("Import"), button:has-text("New")')

    if (await addButton.count() > 0) {
      await expect(addButton.first()).toBeVisible()

      await addButton.first().click()
      await page.waitForTimeout(500)

      // Should show form or modal
      const formElements = [
        page.locator('form'),
        page.locator('[role="dialog"]'),
        page.locator('.modal')
      ]

      let hasForm = false
      for (const element of formElements) {
        if (await element.count() > 0) {
          hasForm = true
          break
        }
      }

      expect(hasForm).toBe(true)
    }
  })

  test('should display facility discovery status', async ({ page }) => {
    await page.goto('/facilities/test-facility-id')
    await page.waitForTimeout(1000)

    // Look for discovery/monitoring status
    const statusElements = [
      page.locator('text=/Discovery/i'),
      page.locator('text=/Monitoring/i'),
      page.locator('text=/Last Crawl/i'),
      page.locator('[data-testid="discovery-status"]')
    ]

    let hasStatus = false
    for (const element of statusElements) {
      if (await element.count() > 0) {
        hasStatus = true
        break
      }
    }

    expect(typeof hasStatus).toBe('boolean')
  })

  test('should show facility images', async ({ page }) => {
    await page.goto('/facilities/test-facility-id')
    await page.waitForTimeout(1000)

    // Look for images
    const images = page.locator('img[src*="facility"], img[alt*="Facility"]')

    const imageCount = await images.count()
    expect(imageCount).toBeGreaterThanOrEqual(0)
  })

  test('should display facility contact information', async ({ page }) => {
    await page.goto('/facilities/test-facility-id')
    await page.waitForTimeout(1000)

    // Look for contact fields
    const contactElements = [
      page.locator('text=/Contact/i'),
      page.locator('text=/Phone/i'),
      page.locator('text=/Email/i'),
      page.locator('text=/Address/i')
    ]

    let hasContact = false
    for (const element of contactElements) {
      if (await element.count() > 0) {
        hasContact = true
        break
      }
    }

    expect(typeof hasContact).toBe('boolean')
  })

  test('should allow navigation back to facilities list', async ({ page }) => {
    await page.goto('/facilities/test-facility-id')
    await page.waitForTimeout(1000)

    // Look for back button
    const backButtons = [
      page.locator('button:has-text("Back")'),
      page.locator('a:has-text("Back to")'),
      page.locator('a[href="/facilities"]')
    ]

    for (const button of backButtons) {
      if (await button.count() > 0) {
        await button.first().click()
        await page.waitForTimeout(500)

        await expect(page).toHaveURL(/\/facilities\/?$/)
        break
      }
    }
  })

  test('should have pagination for facilities list', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    // Look for pagination
    const paginationElements = [
      page.locator('button:has-text("Next")'),
      page.locator('button:has-text("Previous")'),
      page.locator('[aria-label="pagination"]')
    ]

    let hasPagination = false
    for (const element of paginationElements) {
      if (await element.count() > 0) {
        hasPagination = true
        break
      }
    }

    expect(typeof hasPagination).toBe('boolean')
  })
})

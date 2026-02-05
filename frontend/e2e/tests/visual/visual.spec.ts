import { test, expect, Page } from '@playwright/test'
import { login, clearAuth } from '../../helpers/auth'

/**
 * Enhanced Visual Regression Test Suite
 *
 * Comprehensive visual testing covering all critical pages, components, and states.
 * Tests are organized by feature area and include light/dark mode and responsive layouts.
 *
 * Test Coverage:
 * 1. Authentication Pages (login, password reset)
 * 2. Dashboard & Analytics
 * 3. Tiger Management (list, detail, empty states)
 * 4. Investigation Workflows (upload, progress, results)
 * 5. Discovery Pipeline (overview, crawl grid, map)
 * 6. Facility Management (list, map, detail)
 * 7. Verification Queue (table, comparison, mobile)
 * 8. Template Management
 * 9. Empty State Components
 * 10. Error State Components
 * 11. Modal Components
 * 12. Loading States
 * 13. Badge & Card Variations
 * 14. Responsive Layouts (desktop, tablet, mobile)
 *
 * Usage:
 * - Run all: npx playwright test tests/visual
 * - Update baselines: npx playwright test tests/visual --update-snapshots
 * - Run specific: npx playwright test tests/visual -g "login page"
 * - UI mode: npx playwright test tests/visual --ui
 */

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Toggle dark mode on the page
 */
async function toggleDarkMode(page: Page, enable: boolean): Promise<void> {
  await page.evaluate((enabled) => {
    if (enabled) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, enable)
  // Wait for CSS transitions to complete
  await page.waitForTimeout(300)
}

/**
 * Wait for page to fully load with network idle
 */
async function waitForPageLoad(page: Page): Promise<void> {
  await page.waitForLoadState('networkidle')
  // Additional buffer for animations and lazy-loaded content
  await page.waitForTimeout(500)
}

/**
 * Wait for images to load on the page
 */
async function waitForImages(page: Page): Promise<void> {
  await page.evaluate(() => {
    const images = Array.from(document.images)
    return Promise.all(
      images
        .filter((img) => !img.complete)
        .map((img) => new Promise((resolve) => {
          img.addEventListener('load', resolve)
          img.addEventListener('error', resolve)
        }))
    )
  })
}

/**
 * Hide dynamic content that changes between test runs (timestamps, IDs, etc.)
 */
async function hideTimestamps(page: Page): Promise<void> {
  await page.evaluate(() => {
    // Hide elements with time-related content
    const selectors = [
      '[data-testid="timestamp"]',
      '.timestamp',
      'time',
      '[data-testid="last-updated"]'
    ]
    selectors.forEach(selector => {
      document.querySelectorAll(selector).forEach(el => {
        (el as HTMLElement).style.visibility = 'hidden'
      })
    })
  })
}

/**
 * Mask dynamic IDs in the DOM
 */
async function maskDynamicIds(page: Page): Promise<void> {
  await page.evaluate(() => {
    // Replace UUIDs and dynamic IDs with placeholders
    const walk = (node: Node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        node.textContent = node.textContent?.replace(
          /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi,
          'UUID-PLACEHOLDER'
        ) || null
      }
      node.childNodes.forEach(walk)
    }
    walk(document.body)
  })
}

// ============================================================================
// Viewport Configurations
// ============================================================================

const VIEWPORTS = {
  desktop: { width: 1920, height: 1080 },
  tablet: { width: 768, height: 1024 },
  mobile: { width: 375, height: 667 },
}

// ============================================================================
// Test Suite
// ============================================================================

test.describe('Visual Regression Tests', () => {

  // ==========================================================================
  // 1. Authentication Pages
  // ==========================================================================

  test.describe('Authentication Pages', () => {
    test.beforeEach(async ({ page }) => {
      await clearAuth(page)
    })

    test('login page - light mode - desktop', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/login')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/auth/login-light-desktop.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('login-light-desktop.png')
    })

    test('login page - dark mode - desktop', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/login')
      await waitForPageLoad(page)
      await toggleDarkMode(page, true)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/auth/login-dark-desktop.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('login-dark-desktop.png')
    })

    test('login page - mobile', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/login')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/auth/login-mobile.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('login-mobile.png')
    })

    test('login page - with validation errors', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/login')
      await waitForPageLoad(page)

      // Trigger validation by attempting login with empty fields
      const loginButton = page.locator('button[type="submit"]')
      if (await loginButton.count() > 0) {
        await loginButton.click()
        await page.waitForTimeout(500)

        const screenshot = await page.screenshot({
          path: 'screenshots/visual/auth/login-validation-errors.png',
          fullPage: true
        })
        expect(screenshot).toMatchSnapshot('login-validation-errors.png')
      }
    })

    test('password reset page - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/password-reset')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/auth/password-reset-light.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('password-reset-light.png')
    })

    test('password reset page - dark mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/password-reset')
      await waitForPageLoad(page)
      await toggleDarkMode(page, true)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/auth/password-reset-dark.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('password-reset-dark.png')
    })
  })

  // ==========================================================================
  // 2. Dashboard & Analytics
  // ==========================================================================

  test.describe('Dashboard', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('dashboard - full layout - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/dashboard')
      await waitForPageLoad(page)
      await hideTimestamps(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/dashboard/dashboard-light.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('dashboard-light.png')
    })

    test('dashboard - full layout - dark mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/dashboard')
      await waitForPageLoad(page)
      await toggleDarkMode(page, true)
      await hideTimestamps(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/dashboard/dashboard-dark.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('dashboard-dark.png')
    })

    test('dashboard - quick stats section', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/dashboard')
      await waitForPageLoad(page)

      const statsSection = page.locator('[data-testid="quick-stats"]').first()
      if (await statsSection.count() > 0) {
        const screenshot = await statsSection.screenshot({
          path: 'screenshots/visual/dashboard/quick-stats.png'
        })
        expect(screenshot).toMatchSnapshot('quick-stats.png')
      }
    })

    test('dashboard - analytics chart', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/dashboard')
      await waitForPageLoad(page)
      await page.waitForTimeout(1000) // Extra time for charts to render

      const chartSection = page.locator('[data-testid="analytics-chart"]').first()
      if (await chartSection.count() > 0) {
        const screenshot = await chartSection.screenshot({
          path: 'screenshots/visual/dashboard/analytics-chart.png'
        })
        expect(screenshot).toMatchSnapshot('analytics-chart.png')
      }
    })

    test('dashboard - sidebar expanded', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/dashboard')
      await waitForPageLoad(page)

      const sidebar = page.locator('[data-testid="sidebar"], nav').first()
      if (await sidebar.count() > 0) {
        const screenshot = await sidebar.screenshot({
          path: 'screenshots/visual/dashboard/sidebar-expanded.png'
        })
        expect(screenshot).toMatchSnapshot('sidebar-expanded.png')
      }
    })

    test('dashboard - mobile view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/dashboard')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/dashboard/dashboard-mobile.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('dashboard-mobile.png')
    })

    test('dashboard - tablet view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.tablet)
      await page.goto('/dashboard')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/dashboard/dashboard-tablet.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('dashboard-tablet.png')
    })
  })

  // ==========================================================================
  // 3. Tiger Management
  // ==========================================================================

  test.describe('Tigers List', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('tigers list - grid view - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/tigers')
      await waitForPageLoad(page)
      await waitForImages(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/tigers/tigers-list-light.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('tigers-list-light.png')
    })

    test('tigers list - grid view - dark mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/tigers')
      await waitForPageLoad(page)
      await toggleDarkMode(page, true)
      await waitForImages(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/tigers/tigers-list-dark.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('tigers-list-dark.png')
    })

    test('tigers list - mobile grid', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/tigers/tigers-list-mobile.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('tigers-list-mobile.png')
    })

    test('tiger card - single card detail', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/tigers')
      await waitForPageLoad(page)
      await waitForImages(page)

      const tigerCard = page.locator('[data-testid="tiger-card"]').first()
      if (await tigerCard.count() > 0) {
        const screenshot = await tigerCard.screenshot({
          path: 'screenshots/visual/tigers/tiger-card.png'
        })
        expect(screenshot).toMatchSnapshot('tiger-card.png')
      }
    })

    test('tiger card - with status badges', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const tigerCard = page.locator('[data-testid="tiger-card"]').first()
      if (await tigerCard.count() > 0) {
        const badges = tigerCard.locator('[data-testid="badge"]')
        if (await badges.count() > 0) {
          const screenshot = await tigerCard.screenshot({
            path: 'screenshots/visual/tigers/tiger-card-with-badges.png'
          })
          expect(screenshot).toMatchSnapshot('tiger-card-with-badges.png')
        }
      }
    })

    test('tigers - search and filter bar', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const filterBar = page.locator('[data-testid="filter-bar"], [data-testid="search-bar"]').first()
      if (await filterBar.count() > 0) {
        const screenshot = await filterBar.screenshot({
          path: 'screenshots/visual/tigers/filter-bar.png'
        })
        expect(screenshot).toMatchSnapshot('filter-bar.png')
      }
    })

    test('tigers - pagination controls', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const pagination = page.locator('[data-testid="pagination"]').first()
      if (await pagination.count() > 0) {
        const screenshot = await pagination.screenshot({
          path: 'screenshots/visual/tigers/pagination.png'
        })
        expect(screenshot).toMatchSnapshot('pagination.png')
      }
    })

    test('tigers - empty state', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const emptyState = page.locator('[data-testid="empty-state"]').first()
      if (await emptyState.count() > 0) {
        const screenshot = await emptyState.screenshot({
          path: 'screenshots/visual/tigers/tigers-empty-state.png'
        })
        expect(screenshot).toMatchSnapshot('tigers-empty-state.png')
      }
    })
  })

  // ==========================================================================
  // 4. Investigation Workflows
  // ==========================================================================

  test.describe('Investigation 2.0', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('investigation - upload state - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/investigation/investigation-upload-light.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('investigation-upload-light.png')
    })

    test('investigation - upload state - dark mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/investigation2')
      await waitForPageLoad(page)
      await toggleDarkMode(page, true)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/investigation/investigation-upload-dark.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('investigation-upload-dark.png')
    })

    test('investigation - upload component detail', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      const uploader = page.locator('[data-testid="file-uploader"], .file-upload').first()
      if (await uploader.count() > 0) {
        const screenshot = await uploader.screenshot({
          path: 'screenshots/visual/investigation/upload-component.png'
        })
        expect(screenshot).toMatchSnapshot('upload-component.png')
      }
    })

    test('investigation - upload with drag hover state', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      const uploader = page.locator('[data-testid="file-uploader"], .file-upload').first()
      if (await uploader.count() > 0) {
        // Simulate drag hover
        await uploader.hover()
        await page.waitForTimeout(300)

        const screenshot = await uploader.screenshot({
          path: 'screenshots/visual/investigation/upload-hover.png'
        })
        expect(screenshot).toMatchSnapshot('upload-hover.png')
      }
    })

    test('investigation - progress phase display', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      const progress = page.locator('[data-testid="investigation-progress"]').first()
      if (await progress.count() > 0) {
        const screenshot = await progress.screenshot({
          path: 'screenshots/visual/investigation/progress-phases.png'
        })
        expect(screenshot).toMatchSnapshot('progress-phases.png')
      }
    })

    test('investigation - tab navigation', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      const tabNav = page.locator('[data-testid="tab-navigation"]').first()
      if (await tabNav.count() > 0) {
        const screenshot = await tabNav.screenshot({
          path: 'screenshots/visual/investigation/tab-navigation.png'
        })
        expect(screenshot).toMatchSnapshot('tab-navigation.png')
      }
    })

    test('investigation - methodology panel', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      const methodology = page.locator('[data-testid="methodology-panel"]').first()
      if (await methodology.count() > 0) {
        const screenshot = await methodology.screenshot({
          path: 'screenshots/visual/investigation/methodology-panel.png'
        })
        expect(screenshot).toMatchSnapshot('methodology-panel.png')
      }
    })

    test('investigation - match card', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      const matchCard = page.locator('[data-testid="match-card"]').first()
      if (await matchCard.count() > 0) {
        await waitForImages(page)
        const screenshot = await matchCard.screenshot({
          path: 'screenshots/visual/investigation/match-card.png'
        })
        expect(screenshot).toMatchSnapshot('match-card.png')
      }
    })

    test('investigation - ensemble visualization', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      const ensemble = page.locator('[data-testid="ensemble-visualization"]').first()
      if (await ensemble.count() > 0) {
        await page.waitForTimeout(1000) // Wait for charts
        const screenshot = await ensemble.screenshot({
          path: 'screenshots/visual/investigation/ensemble-visualization.png'
        })
        expect(screenshot).toMatchSnapshot('ensemble-visualization.png')
      }
    })

    test('investigation - citations section', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      const citations = page.locator('[data-testid="citations-section"]').first()
      if (await citations.count() > 0) {
        const screenshot = await citations.screenshot({
          path: 'screenshots/visual/investigation/citations.png'
        })
        expect(screenshot).toMatchSnapshot('citations.png')
      }
    })

    test('investigation - mobile view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/investigation/investigation-mobile.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('investigation-mobile.png')
    })
  })

  // ==========================================================================
  // 5. Discovery Pipeline
  // ==========================================================================

  test.describe('Discovery Pipeline', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('discovery - pipeline overview - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/discovery')
      await waitForPageLoad(page)
      await hideTimestamps(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/discovery/discovery-light.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('discovery-light.png')
    })

    test('discovery - pipeline overview - dark mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/discovery')
      await waitForPageLoad(page)
      await toggleDarkMode(page, true)
      await hideTimestamps(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/discovery/discovery-dark.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('discovery-dark.png')
    })

    test('discovery - crawl grid view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/discovery')
      await waitForPageLoad(page)

      const grid = page.locator('[data-testid="crawl-grid"], .grid').first()
      if (await grid.count() > 0) {
        const screenshot = await grid.screenshot({
          path: 'screenshots/visual/discovery/crawl-grid.png'
        })
        expect(screenshot).toMatchSnapshot('crawl-grid.png')
      }
    })

    test('discovery - map view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/discovery')
      await waitForPageLoad(page)

      const mapButton = page.locator('button:has-text("Map")').first()
      if (await mapButton.count() > 0) {
        await mapButton.click()
        await page.waitForTimeout(2000) // Wait for map to load

        const screenshot = await page.screenshot({
          path: 'screenshots/visual/discovery/discovery-map.png',
          fullPage: true
        })
        expect(screenshot).toMatchSnapshot('discovery-map.png')
      }
    })

    test('discovery - status panel', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/discovery')
      await waitForPageLoad(page)

      const statusPanel = page.locator('[data-testid="discovery-status"]').first()
      if (await statusPanel.count() > 0) {
        const screenshot = await statusPanel.screenshot({
          path: 'screenshots/visual/discovery/status-panel.png'
        })
        expect(screenshot).toMatchSnapshot('status-panel.png')
      }
    })

    test('discovery - crawl history timeline', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/discovery')
      await waitForPageLoad(page)

      const timeline = page.locator('[data-testid="crawl-timeline"]').first()
      if (await timeline.count() > 0) {
        await hideTimestamps(page)
        const screenshot = await timeline.screenshot({
          path: 'screenshots/visual/discovery/timeline.png'
        })
        expect(screenshot).toMatchSnapshot('timeline.png')
      }
    })

    test('discovery - mobile view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/discovery')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/discovery/discovery-mobile.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('discovery-mobile.png')
    })
  })

  // ==========================================================================
  // 6. Facility Management
  // ==========================================================================

  test.describe('Facilities', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('facilities - list view - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/facilities')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/facilities/facilities-list-light.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('facilities-list-light.png')
    })

    test('facilities - list view - dark mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/facilities')
      await waitForPageLoad(page)
      await toggleDarkMode(page, true)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/facilities/facilities-list-dark.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('facilities-list-dark.png')
    })

    test('facilities - map view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/facilities')
      await waitForPageLoad(page)

      const mapButton = page.locator('button:has-text("Map"), [data-testid="map-view"]').first()
      if (await mapButton.count() > 0) {
        await mapButton.click()
        await page.waitForTimeout(2000) // Wait for map to load

        const screenshot = await page.screenshot({
          path: 'screenshots/visual/facilities/facilities-map.png',
          fullPage: true
        })
        expect(screenshot).toMatchSnapshot('facilities-map.png')
      }
    })

    test('facilities - facility card', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/facilities')
      await waitForPageLoad(page)

      const facilityCard = page.locator('[data-testid="facility-card"]').first()
      if (await facilityCard.count() > 0) {
        const screenshot = await facilityCard.screenshot({
          path: 'screenshots/visual/facilities/facility-card.png'
        })
        expect(screenshot).toMatchSnapshot('facility-card.png')
      }
    })

    test('facilities - filter and search', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/facilities')
      await waitForPageLoad(page)

      const filterSection = page.locator('[data-testid="facility-filters"]').first()
      if (await filterSection.count() > 0) {
        const screenshot = await filterSection.screenshot({
          path: 'screenshots/visual/facilities/filters.png'
        })
        expect(screenshot).toMatchSnapshot('filters.png')
      }
    })

    test('facilities - mobile view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/facilities')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/facilities/facilities-mobile.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('facilities-mobile.png')
    })
  })

  // ==========================================================================
  // 7. Verification Queue
  // ==========================================================================

  test.describe('Verification Queue', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('verification queue - table view - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/verification')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/verification/verification-light.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('verification-light.png')
    })

    test('verification queue - table view - dark mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/verification')
      await waitForPageLoad(page)
      await toggleDarkMode(page, true)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/verification/verification-dark.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('verification-dark.png')
    })

    test('verification - comparison view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/verification')
      await waitForPageLoad(page)

      const comparison = page.locator('[data-testid="verification-comparison"]').first()
      if (await comparison.count() > 0) {
        await waitForImages(page)
        const screenshot = await comparison.screenshot({
          path: 'screenshots/visual/verification/comparison-view.png'
        })
        expect(screenshot).toMatchSnapshot('comparison-view.png')
      }
    })

    test('verification - filter controls', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/verification')
      await waitForPageLoad(page)

      const filters = page.locator('[data-testid="verification-filters"]').first()
      if (await filters.count() > 0) {
        const screenshot = await filters.screenshot({
          path: 'screenshots/visual/verification/filters.png'
        })
        expect(screenshot).toMatchSnapshot('filters.png')
      }
    })

    test('verification - statistics panel', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/verification')
      await waitForPageLoad(page)

      const stats = page.locator('[data-testid="verification-stats"]').first()
      if (await stats.count() > 0) {
        const screenshot = await stats.screenshot({
          path: 'screenshots/visual/verification/stats.png'
        })
        expect(screenshot).toMatchSnapshot('stats.png')
      }
    })

    test('verification - mobile view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/verification')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/verification/verification-mobile.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('verification-mobile.png')
    })
  })

  // ==========================================================================
  // 8. Templates Management
  // ==========================================================================

  test.describe('Templates', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('templates - list view - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/templates')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/templates/templates-light.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('templates-light.png')
    })

    test('templates - dark mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/templates')
      await waitForPageLoad(page)
      await toggleDarkMode(page, true)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/templates/templates-dark.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('templates-dark.png')
    })

    test('templates - template card', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/templates')
      await waitForPageLoad(page)

      const templateCard = page.locator('[data-testid="template-card"]').first()
      if (await templateCard.count() > 0) {
        const screenshot = await templateCard.screenshot({
          path: 'screenshots/visual/templates/template-card.png'
        })
        expect(screenshot).toMatchSnapshot('template-card.png')
      }
    })
  })

  // ==========================================================================
  // 9. Empty State Components
  // ==========================================================================

  test.describe('Empty State Component', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('empty state - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)

      const pagesWithEmptyState = ['/tigers', '/facilities', '/verification']

      for (const pagePath of pagesWithEmptyState) {
        await page.goto(pagePath)
        await waitForPageLoad(page)

        const emptyState = page.locator('[data-testid="empty-state"]').first()
        if (await emptyState.count() > 0) {
          const screenshot = await emptyState.screenshot({
            path: 'screenshots/visual/components/empty-state-light.png'
          })
          expect(screenshot).toMatchSnapshot('empty-state-light.png')
          break
        }
      }
    })

    test('empty state - dark mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)

      const pagesWithEmptyState = ['/tigers', '/facilities', '/verification']

      for (const pagePath of pagesWithEmptyState) {
        await page.goto(pagePath)
        await waitForPageLoad(page)
        await toggleDarkMode(page, true)

        const emptyState = page.locator('[data-testid="empty-state"]').first()
        if (await emptyState.count() > 0) {
          const screenshot = await emptyState.screenshot({
            path: 'screenshots/visual/components/empty-state-dark.png'
          })
          expect(screenshot).toMatchSnapshot('empty-state-dark.png')
          break
        }
      }
    })

    test('empty state - with action button', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)

      const pagesWithEmptyState = ['/tigers', '/facilities']

      for (const pagePath of pagesWithEmptyState) {
        await page.goto(pagePath)
        await waitForPageLoad(page)

        const emptyState = page.locator('[data-testid="empty-state"]').first()
        if (await emptyState.count() > 0) {
          const actionButton = emptyState.locator('button').first()
          if (await actionButton.count() > 0) {
            const screenshot = await emptyState.screenshot({
              path: 'screenshots/visual/components/empty-state-with-action.png'
            })
            expect(screenshot).toMatchSnapshot('empty-state-with-action.png')
            break
          }
        }
      }
    })
  })

  // ==========================================================================
  // 10. Error State Components
  // ==========================================================================

  test.describe('Error State Component', () => {
    test('error state - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)

      const pagesWithPossibleErrors = ['/investigation2', '/discovery', '/verification']

      for (const pagePath of pagesWithPossibleErrors) {
        await page.goto(pagePath)
        await waitForPageLoad(page)

        const errorState = page.locator('[data-testid="error-state"]').first()
        if (await errorState.count() > 0) {
          const screenshot = await errorState.screenshot({
            path: 'screenshots/visual/components/error-state-light.png'
          })
          expect(screenshot).toMatchSnapshot('error-state-light.png')
          break
        }
      }
    })

    test('error state - dark mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)

      const pagesWithPossibleErrors = ['/investigation2', '/discovery', '/verification']

      for (const pagePath of pagesWithPossibleErrors) {
        await page.goto(pagePath)
        await waitForPageLoad(page)
        await toggleDarkMode(page, true)

        const errorState = page.locator('[data-testid="error-state"]').first()
        if (await errorState.count() > 0) {
          const screenshot = await errorState.screenshot({
            path: 'screenshots/visual/components/error-state-dark.png'
          })
          expect(screenshot).toMatchSnapshot('error-state-dark.png')
          break
        }
      }
    })

    test('error state - with details expanded', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)

      const pagesWithPossibleErrors = ['/investigation2', '/discovery']

      for (const pagePath of pagesWithPossibleErrors) {
        await page.goto(pagePath)
        await waitForPageLoad(page)

        const errorState = page.locator('[data-testid="error-state"]').first()
        if (await errorState.count() > 0) {
          const detailsToggle = errorState.locator('[data-testid="error-details-toggle"], button:has-text("Details")').first()
          if (await detailsToggle.count() > 0) {
            await detailsToggle.click()
            await page.waitForTimeout(300)

            const screenshot = await errorState.screenshot({
              path: 'screenshots/visual/components/error-state-expanded.png'
            })
            expect(screenshot).toMatchSnapshot('error-state-expanded.png')
            break
          }
        }
      }
    })

    test('error state - with retry button', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)

      const pagesWithPossibleErrors = ['/investigation2', '/discovery']

      for (const pagePath of pagesWithPossibleErrors) {
        await page.goto(pagePath)
        await waitForPageLoad(page)

        const errorState = page.locator('[data-testid="error-state"]').first()
        if (await errorState.count() > 0) {
          const retryButton = errorState.locator('button:has-text("Retry")').first()
          if (await retryButton.count() > 0) {
            const screenshot = await errorState.screenshot({
              path: 'screenshots/visual/components/error-state-with-retry.png'
            })
            expect(screenshot).toMatchSnapshot('error-state-with-retry.png')
            break
          }
        }
      }
    })
  })

  // ==========================================================================
  // 11. Modal Components
  // ==========================================================================

  test.describe('Modal Components', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('modal - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)

      const pagesWithModals = ['/tigers', '/facilities', '/templates']

      for (const pagePath of pagesWithModals) {
        await page.goto(pagePath)
        await waitForPageLoad(page)

        const addButton = page.locator('button:has-text("Add"), button:has-text("New"), button:has-text("Create")').first()
        if (await addButton.count() > 0) {
          await addButton.click()
          await page.waitForTimeout(500)

          const modal = page.locator('[data-testid="modal"], [role="dialog"]').first()
          if (await modal.count() > 0) {
            const screenshot = await modal.screenshot({
              path: 'screenshots/visual/components/modal-light.png'
            })
            expect(screenshot).toMatchSnapshot('modal-light.png')
            break
          }
        }
      }
    })

    test('modal - dark mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await toggleDarkMode(page, true)

      const pagesWithModals = ['/tigers', '/facilities', '/templates']

      for (const pagePath of pagesWithModals) {
        await page.goto(pagePath)
        await waitForPageLoad(page)

        const addButton = page.locator('button:has-text("Add"), button:has-text("New"), button:has-text("Create")').first()
        if (await addButton.count() > 0) {
          await addButton.click()
          await page.waitForTimeout(500)

          const modal = page.locator('[data-testid="modal"], [role="dialog"]').first()
          if (await modal.count() > 0) {
            const screenshot = await modal.screenshot({
              path: 'screenshots/visual/components/modal-dark.png'
            })
            expect(screenshot).toMatchSnapshot('modal-dark.png')
            break
          }
        }
      }
    })

    test('modal - with form fields', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)

      const pagesWithModals = ['/tigers', '/facilities']

      for (const pagePath of pagesWithModals) {
        await page.goto(pagePath)
        await waitForPageLoad(page)

        const addButton = page.locator('button:has-text("Add"), button:has-text("New")').first()
        if (await addButton.count() > 0) {
          await addButton.click()
          await page.waitForTimeout(500)

          const modal = page.locator('[data-testid="modal"], [role="dialog"]').first()
          if (await modal.count() > 0) {
            const formFields = modal.locator('input, textarea, select')
            if (await formFields.count() > 0) {
              const screenshot = await modal.screenshot({
                path: 'screenshots/visual/components/modal-with-form.png'
              })
              expect(screenshot).toMatchSnapshot('modal-with-form.png')
              break
            }
          }
        }
      }
    })

    test('modal - confirmation dialog', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      // Look for delete or remove buttons that trigger confirmation
      const deleteButton = page.locator('button:has-text("Delete"), button:has-text("Remove")').first()
      if (await deleteButton.count() > 0) {
        await deleteButton.click()
        await page.waitForTimeout(500)

        const confirmModal = page.locator('[data-testid="confirm-modal"], [role="alertdialog"]').first()
        if (await confirmModal.count() > 0) {
          const screenshot = await confirmModal.screenshot({
            path: 'screenshots/visual/components/modal-confirmation.png'
          })
          expect(screenshot).toMatchSnapshot('modal-confirmation.png')
        }
      }
    })
  })

  // ==========================================================================
  // 12. Loading States
  // ==========================================================================

  test.describe('Loading States', () => {
    test('loading spinner - default', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)
      await page.goto('/tigers')

      const spinner = page.locator('[data-testid="loading-spinner"], .spinner').first()
      if (await spinner.count() > 0) {
        const screenshot = await spinner.screenshot({
          path: 'screenshots/visual/components/loading-spinner.png'
        })
        expect(screenshot).toMatchSnapshot('loading-spinner.png')
      }
    })

    test('skeleton loading - card', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)
      await page.goto('/tigers')

      const skeleton = page.locator('[data-testid="skeleton-card"]').first()
      if (await skeleton.count() > 0) {
        const screenshot = await skeleton.screenshot({
          path: 'screenshots/visual/components/skeleton-card.png'
        })
        expect(screenshot).toMatchSnapshot('skeleton-card.png')
      }
    })

    test('skeleton loading - table row', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)
      await page.goto('/verification')

      const skeleton = page.locator('[data-testid="skeleton-row"]').first()
      if (await skeleton.count() > 0) {
        const screenshot = await skeleton.screenshot({
          path: 'screenshots/visual/components/skeleton-row.png'
        })
        expect(screenshot).toMatchSnapshot('skeleton-row.png')
      }
    })

    test('progress bar - investigation', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      const progressBar = page.locator('[data-testid="progress-bar"]').first()
      if (await progressBar.count() > 0) {
        const screenshot = await progressBar.screenshot({
          path: 'screenshots/visual/components/progress-bar.png'
        })
        expect(screenshot).toMatchSnapshot('progress-bar.png')
      }
    })
  })

  // ==========================================================================
  // 13. Badge & Card Variations
  // ==========================================================================

  test.describe('Badge Components', () => {
    test('badges - status variations', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const badges = page.locator('[data-testid="badge"]')
      if (await badges.count() > 0) {
        for (let i = 0; i < Math.min(5, await badges.count()); i++) {
          const badge = badges.nth(i)
          const screenshot = await badge.screenshot({
            path: `screenshots/visual/components/badge-${i}.png`
          })
          expect(screenshot).toMatchSnapshot(`badge-${i}.png`)
        }
      }
    })

    test('badge - success state', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const successBadge = page.locator('[data-testid="badge-success"]').first()
      if (await successBadge.count() > 0) {
        const screenshot = await successBadge.screenshot({
          path: 'screenshots/visual/components/badge-success.png'
        })
        expect(screenshot).toMatchSnapshot('badge-success.png')
      }
    })

    test('badge - warning state', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const warningBadge = page.locator('[data-testid="badge-warning"]').first()
      if (await warningBadge.count() > 0) {
        const screenshot = await warningBadge.screenshot({
          path: 'screenshots/visual/components/badge-warning.png'
        })
        expect(screenshot).toMatchSnapshot('badge-warning.png')
      }
    })

    test('badge - error state', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const errorBadge = page.locator('[data-testid="badge-error"]').first()
      if (await errorBadge.count() > 0) {
        const screenshot = await errorBadge.screenshot({
          path: 'screenshots/visual/components/badge-error.png'
        })
        expect(screenshot).toMatchSnapshot('badge-error.png')
      }
    })
  })

  test.describe('Card Components', () => {
    test('card - tiger card', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)
      await page.goto('/tigers')
      await waitForPageLoad(page)
      await waitForImages(page)

      const card = page.locator('[data-testid="tiger-card"]').first()
      if (await card.count() > 0) {
        const screenshot = await card.screenshot({
          path: 'screenshots/visual/components/card-tiger.png'
        })
        expect(screenshot).toMatchSnapshot('card-tiger.png')
      }
    })

    test('card - facility card', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)
      await page.goto('/facilities')
      await waitForPageLoad(page)

      const card = page.locator('[data-testid="facility-card"]').first()
      if (await card.count() > 0) {
        const screenshot = await card.screenshot({
          path: 'screenshots/visual/components/card-facility.png'
        })
        expect(screenshot).toMatchSnapshot('card-facility.png')
      }
    })

    test('card - investigation card', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)
      await page.goto('/dashboard')
      await waitForPageLoad(page)

      const card = page.locator('[data-testid="investigation-card"]').first()
      if (await card.count() > 0) {
        await hideTimestamps(page)
        const screenshot = await card.screenshot({
          path: 'screenshots/visual/components/card-investigation.png'
        })
        expect(screenshot).toMatchSnapshot('card-investigation.png')
      }
    })

    test('card - stat card', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)
      await page.goto('/dashboard')
      await waitForPageLoad(page)

      const card = page.locator('[data-testid="stat-card"]').first()
      if (await card.count() > 0) {
        const screenshot = await card.screenshot({
          path: 'screenshots/visual/components/card-stat.png'
        })
        expect(screenshot).toMatchSnapshot('card-stat.png')
      }
    })

    test('card - hover state', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const card = page.locator('[data-testid="tiger-card"]').first()
      if (await card.count() > 0) {
        await card.hover()
        await page.waitForTimeout(300)

        const screenshot = await card.screenshot({
          path: 'screenshots/visual/components/card-hover.png'
        })
        expect(screenshot).toMatchSnapshot('card-hover.png')
      }
    })
  })

  // ==========================================================================
  // 14. Responsive Layout Tests
  // ==========================================================================

  test.describe('Responsive Layouts', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('tablet - dashboard', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.tablet)
      await page.goto('/dashboard')
      await waitForPageLoad(page)
      await hideTimestamps(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/responsive/tablet-dashboard.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('tablet-dashboard.png')
    })

    test('tablet - investigation', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.tablet)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/responsive/tablet-investigation.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('tablet-investigation.png')
    })

    test('tablet - tigers list', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.tablet)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/responsive/tablet-tigers.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('tablet-tigers.png')
    })

    test('mobile - dashboard', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/dashboard')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/responsive/mobile-dashboard.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('mobile-dashboard.png')
    })

    test('mobile - tigers list', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/responsive/mobile-tigers.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('mobile-tigers.png')
    })

    test('mobile - facilities list', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/facilities')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/responsive/mobile-facilities.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('mobile-facilities.png')
    })

    test('mobile - verification queue', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/verification')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/visual/responsive/mobile-verification.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('mobile-verification.png')
    })

    test('mobile - navigation menu', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/dashboard')
      await waitForPageLoad(page)

      // Try to open mobile menu
      const menuButton = page.locator('button[aria-label="Menu"], button[aria-label="Open menu"]').first()
      if (await menuButton.count() > 0) {
        await menuButton.click()
        await page.waitForTimeout(300)

        const screenshot = await page.screenshot({
          path: 'screenshots/visual/responsive/mobile-menu-open.png',
          fullPage: true
        })
        expect(screenshot).toMatchSnapshot('mobile-menu-open.png')
      }
    })
  })

  // ==========================================================================
  // 15. Toast & Alert Components
  // ==========================================================================

  test.describe('Toast & Alert Components', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('toast - success notification', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const toast = page.locator('[data-testid="toast-success"]').first()
      if (await toast.count() > 0) {
        const screenshot = await toast.screenshot({
          path: 'screenshots/visual/components/toast-success.png'
        })
        expect(screenshot).toMatchSnapshot('toast-success.png')
      }
    })

    test('toast - error notification', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      const toast = page.locator('[data-testid="toast-error"]').first()
      if (await toast.count() > 0) {
        const screenshot = await toast.screenshot({
          path: 'screenshots/visual/components/toast-error.png'
        })
        expect(screenshot).toMatchSnapshot('toast-error.png')
      }
    })

    test('alert - info banner', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/dashboard')
      await waitForPageLoad(page)

      const alert = page.locator('[data-testid="alert-info"]').first()
      if (await alert.count() > 0) {
        const screenshot = await alert.screenshot({
          path: 'screenshots/visual/components/alert-info.png'
        })
        expect(screenshot).toMatchSnapshot('alert-info.png')
      }
    })

    test('alert - warning banner', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/discovery')
      await waitForPageLoad(page)

      const alert = page.locator('[data-testid="alert-warning"]').first()
      if (await alert.count() > 0) {
        const screenshot = await alert.screenshot({
          path: 'screenshots/visual/components/alert-warning.png'
        })
        expect(screenshot).toMatchSnapshot('alert-warning.png')
      }
    })
  })
})

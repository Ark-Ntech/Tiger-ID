import { test, expect, Page } from '@playwright/test'
import { login, clearAuth } from './helpers/auth'

/**
 * Visual Regression Test Suite
 *
 * Tests visual consistency across the application using Playwright screenshots.
 * Covers light/dark mode, responsive layouts, and various UI states.
 *
 * Test Organization:
 * 1. Authentication Pages
 * 2. Dashboard Views
 * 3. Tiger Management
 * 4. Investigation Workflows
 * 5. Discovery Pipeline
 * 6. Facility Management
 * 7. Verification Queue
 * 8. Component States (Empty, Error, Modal)
 */

// Helper function to toggle dark mode
async function toggleDarkMode(page: Page, enable: boolean) {
  await page.evaluate((enabled) => {
    if (enabled) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, enable)
  await page.waitForTimeout(300) // Wait for transitions
}

// Helper function to wait for page load
async function waitForPageLoad(page: Page) {
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(500) // Additional buffer for animations
}

// Configure viewports
const VIEWPORTS = {
  desktop: { width: 1920, height: 1080 },
  tablet: { width: 768, height: 1024 },
  mobile: { width: 375, height: 667 },
}

test.describe('Visual Regression Tests', () => {

  // ============================================================================
  // 1. Authentication Pages
  // ============================================================================

  test.describe('Authentication Pages', () => {
    test.beforeEach(async ({ page }) => {
      await clearAuth(page)
    })

    test('login page - light mode - desktop', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/login')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/auth/login-light-desktop.png',
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
        path: 'screenshots/auth/login-dark-desktop.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('login-dark-desktop.png')
    })

    test('login page - mobile', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/login')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/auth/login-mobile.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('login-mobile.png')
    })

    test('password reset page - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/password-reset')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/auth/password-reset-light.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('password-reset-light.png')
    })
  })

  // ============================================================================
  // 2. Dashboard Views
  // ============================================================================

  test.describe('Dashboard', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('dashboard - full layout - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/dashboard')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/dashboard/dashboard-light.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('dashboard-light.png')
    })

    test('dashboard - full layout - dark mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/dashboard')
      await waitForPageLoad(page)
      await toggleDarkMode(page, true)

      const screenshot = await page.screenshot({
        path: 'screenshots/dashboard/dashboard-dark.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('dashboard-dark.png')
    })

    test('dashboard - mobile view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/dashboard')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/dashboard/dashboard-mobile.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('dashboard-mobile.png')
    })

    test('sidebar navigation - expanded', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/dashboard')
      await waitForPageLoad(page)

      // Screenshot just the sidebar
      const sidebar = page.locator('[data-testid="sidebar"], nav').first()
      if (await sidebar.count() > 0) {
        const screenshot = await sidebar.screenshot({
          path: 'screenshots/dashboard/sidebar-expanded.png'
        })
        expect(screenshot).toMatchSnapshot('sidebar-expanded.png')
      }
    })
  })

  // ============================================================================
  // 3. Tiger Management
  // ============================================================================

  test.describe('Tigers List', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('tigers list - grid view - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/tigers/tigers-list-light.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('tigers-list-light.png')
    })

    test('tigers list - grid view - dark mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/tigers')
      await waitForPageLoad(page)
      await toggleDarkMode(page, true)

      const screenshot = await page.screenshot({
        path: 'screenshots/tigers/tigers-list-dark.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('tigers-list-dark.png')
    })

    test('tigers list - mobile grid', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/tigers/tigers-list-mobile.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('tigers-list-mobile.png')
    })

    test('tiger card - single card detail', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      // Screenshot first tiger card if available
      const tigerCard = page.locator('[data-testid="tiger-card"]').first()
      if (await tigerCard.count() > 0) {
        const screenshot = await tigerCard.screenshot({
          path: 'screenshots/tigers/tiger-card.png'
        })
        expect(screenshot).toMatchSnapshot('tiger-card.png')
      }
    })

    test('tigers - empty state', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      // Look for empty state
      const emptyState = page.locator('[data-testid="empty-state"]')
      if (await emptyState.count() > 0) {
        const screenshot = await emptyState.screenshot({
          path: 'screenshots/tigers/tigers-empty-state.png'
        })
        expect(screenshot).toMatchSnapshot('tigers-empty-state.png')
      }
    })
  })

  // ============================================================================
  // 4. Investigation Workflows
  // ============================================================================

  test.describe('Investigation 2.0', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('investigation - upload state - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/investigation/investigation-upload-light.png',
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
        path: 'screenshots/investigation/investigation-upload-dark.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('investigation-upload-dark.png')
    })

    test('investigation - upload component detail', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      // Screenshot upload component specifically
      const uploader = page.locator('[data-testid="file-uploader"], .file-upload').first()
      if (await uploader.count() > 0) {
        const screenshot = await uploader.screenshot({
          path: 'screenshots/investigation/upload-component.png'
        })
        expect(screenshot).toMatchSnapshot('upload-component.png')
      }
    })

    test('investigation - progress phase display', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      // Look for progress component
      const progress = page.locator('[data-testid="investigation-progress"]')
      if (await progress.count() > 0) {
        const screenshot = await progress.screenshot({
          path: 'screenshots/investigation/progress-phases.png'
        })
        expect(screenshot).toMatchSnapshot('progress-phases.png')
      }
    })

    test('investigation - mobile view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/investigation/investigation-mobile.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('investigation-mobile.png')
    })
  })

  // ============================================================================
  // 5. Discovery Pipeline
  // ============================================================================

  test.describe('Discovery Pipeline', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('discovery - pipeline overview - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/discovery')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/discovery/discovery-light.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('discovery-light.png')
    })

    test('discovery - pipeline overview - dark mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/discovery')
      await waitForPageLoad(page)
      await toggleDarkMode(page, true)

      const screenshot = await page.screenshot({
        path: 'screenshots/discovery/discovery-dark.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('discovery-dark.png')
    })

    test('discovery - crawl grid view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/discovery')
      await waitForPageLoad(page)

      // Look for grid view of crawls
      const grid = page.locator('[data-testid="crawl-grid"], .grid').first()
      if (await grid.count() > 0) {
        const screenshot = await grid.screenshot({
          path: 'screenshots/discovery/crawl-grid.png'
        })
        expect(screenshot).toMatchSnapshot('crawl-grid.png')
      }
    })

    test('discovery - mobile view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/discovery')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/discovery/discovery-mobile.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('discovery-mobile.png')
    })
  })

  // ============================================================================
  // 6. Facility Management
  // ============================================================================

  test.describe('Facilities', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('facilities - list view - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/facilities')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/facilities/facilities-list-light.png',
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
        path: 'screenshots/facilities/facilities-list-dark.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('facilities-list-dark.png')
    })

    test('facilities - map view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/facilities')
      await waitForPageLoad(page)

      // Click map view button if available
      const mapButton = page.locator('button:has-text("Map"), [data-testid="map-view"]')
      if (await mapButton.count() > 0) {
        await mapButton.first().click()
        await page.waitForTimeout(2000) // Wait for map to load

        const screenshot = await page.screenshot({
          path: 'screenshots/facilities/facilities-map.png',
          fullPage: true
        })
        expect(screenshot).toMatchSnapshot('facilities-map.png')
      }
    })

    test('facilities - mobile view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/facilities')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/facilities/facilities-mobile.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('facilities-mobile.png')
    })
  })

  // ============================================================================
  // 7. Verification Queue
  // ============================================================================

  test.describe('Verification Queue', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('verification queue - table view - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/verification')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/verification/verification-light.png',
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
        path: 'screenshots/verification/verification-dark.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('verification-dark.png')
    })

    test('verification - comparison view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/verification')
      await waitForPageLoad(page)

      // Look for comparison component
      const comparison = page.locator('[data-testid="verification-comparison"]')
      if (await comparison.count() > 0) {
        const screenshot = await comparison.screenshot({
          path: 'screenshots/verification/comparison-view.png'
        })
        expect(screenshot).toMatchSnapshot('comparison-view.png')
      }
    })

    test('verification - mobile view', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/verification')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/verification/verification-mobile.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('verification-mobile.png')
    })
  })

  // ============================================================================
  // 8. Templates Management
  // ============================================================================

  test.describe('Templates', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('templates - list view - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await page.goto('/templates')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/templates/templates-light.png',
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
        path: 'screenshots/templates/templates-dark.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('templates-dark.png')
    })
  })

  // ============================================================================
  // 9. Component States - Empty State
  // ============================================================================

  test.describe('Empty State Component', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('empty state - small size', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)

      // Navigate to pages that might show empty states
      const pagesWithEmptyState = ['/tigers', '/facilities', '/verification']

      for (const pagePath of pagesWithEmptyState) {
        await page.goto(pagePath)
        await waitForPageLoad(page)

        const emptyState = page.locator('[data-testid="empty-state"]').first()
        if (await emptyState.count() > 0) {
          const screenshot = await emptyState.screenshot({
            path: `screenshots/components/empty-state-${pagePath.replace('/', '')}.png`
          })
          expect(screenshot).toMatchSnapshot(`empty-state-${pagePath.replace('/', '')}.png`)
          break // Found one, that's enough
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
            path: `screenshots/components/empty-state-dark.png`
          })
          expect(screenshot).toMatchSnapshot('empty-state-dark.png')
          break
        }
      }
    })
  })

  // ============================================================================
  // 10. Component States - Error State
  // ============================================================================

  test.describe('Error State Component', () => {
    test('error state - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)

      // Look for error states on various pages
      const pagesWithPossibleErrors = ['/investigation2', '/discovery', '/verification']

      for (const pagePath of pagesWithPossibleErrors) {
        await page.goto(pagePath)
        await waitForPageLoad(page)

        const errorState = page.locator('[data-testid="error-state"]').first()
        if (await errorState.count() > 0) {
          const screenshot = await errorState.screenshot({
            path: 'screenshots/components/error-state-light.png'
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
            path: 'screenshots/components/error-state-dark.png'
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
          // Try to expand details
          const detailsToggle = errorState.locator('[data-testid="error-state-details-toggle"]')
          if (await detailsToggle.count() > 0) {
            await detailsToggle.click()
            await page.waitForTimeout(300)

            const screenshot = await errorState.screenshot({
              path: 'screenshots/components/error-state-expanded.png'
            })
            expect(screenshot).toMatchSnapshot('error-state-expanded.png')
          }
          break
        }
      }
    })
  })

  // ============================================================================
  // 11. Modal Components
  // ============================================================================

  test.describe('Modal Components', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('modal - light mode', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)

      // Try to trigger modals on various pages
      const pagesWithModals = ['/tigers', '/facilities', '/templates']

      for (const pagePath of pagesWithModals) {
        await page.goto(pagePath)
        await waitForPageLoad(page)

        // Look for buttons that might open modals
        const addButton = page.locator('button:has-text("Add"), button:has-text("New"), button:has-text("Create")').first()
        if (await addButton.count() > 0) {
          await addButton.click()
          await page.waitForTimeout(500)

          const modal = page.locator('[data-testid="modal-content"], [role="dialog"]')
          if (await modal.count() > 0) {
            const screenshot = await modal.screenshot({
              path: 'screenshots/components/modal-light.png'
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

          const modal = page.locator('[data-testid="modal-content"], [role="dialog"]')
          if (await modal.count() > 0) {
            const screenshot = await modal.screenshot({
              path: 'screenshots/components/modal-dark.png'
            })
            expect(screenshot).toMatchSnapshot('modal-dark.png')
            break
          }
        }
      }
    })
  })

  // ============================================================================
  // 12. Loading States
  // ============================================================================

  test.describe('Loading States', () => {
    test('loading spinner', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)

      // Navigate and try to catch loading state
      await page.goto('/tigers')

      const spinner = page.locator('[data-testid="loading-spinner"], .animate-spin').first()
      if (await spinner.count() > 0) {
        const screenshot = await spinner.screenshot({
          path: 'screenshots/components/loading-spinner.png'
        })
        expect(screenshot).toMatchSnapshot('loading-spinner.png')
      }
    })

    test('skeleton loading', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)

      // Navigate and look for skeleton loaders
      await page.goto('/tigers')

      const skeleton = page.locator('[data-testid="skeleton"], .animate-pulse').first()
      if (await skeleton.count() > 0) {
        const screenshot = await skeleton.screenshot({
          path: 'screenshots/components/skeleton.png'
        })
        expect(screenshot).toMatchSnapshot('skeleton.png')
      }
    })
  })

  // ============================================================================
  // 13. Badge Component Variations
  // ============================================================================

  test.describe('Badge Components', () => {
    test('badges - various states', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)

      // Tigers page likely has status badges
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const badges = page.locator('[data-testid="badge"]')
      if (await badges.count() > 0) {
        // Screenshot first few badges
        for (let i = 0; i < Math.min(3, await badges.count()); i++) {
          const badge = badges.nth(i)
          const screenshot = await badge.screenshot({
            path: `screenshots/components/badge-${i}.png`
          })
          expect(screenshot).toMatchSnapshot(`badge-${i}.png`)
        }
      }
    })
  })

  // ============================================================================
  // 14. Card Component Variations
  // ============================================================================

  test.describe('Card Components', () => {
    test('card - tiger card', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const card = page.locator('[data-testid="card"], .card').first()
      if (await card.count() > 0) {
        const screenshot = await card.screenshot({
          path: 'screenshots/components/card-tiger.png'
        })
        expect(screenshot).toMatchSnapshot('card-tiger.png')
      }
    })

    test('card - facility card', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)
      await login(page)
      await page.goto('/facilities')
      await waitForPageLoad(page)

      const card = page.locator('[data-testid="card"], .card').first()
      if (await card.count() > 0) {
        const screenshot = await card.screenshot({
          path: 'screenshots/components/card-facility.png'
        })
        expect(screenshot).toMatchSnapshot('card-facility.png')
      }
    })
  })

  // ============================================================================
  // 15. Responsive Layout Tests
  // ============================================================================

  test.describe('Responsive Layouts', () => {
    test.beforeEach(async ({ page }) => {
      await login(page)
    })

    test('tablet - dashboard', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.tablet)
      await page.goto('/dashboard')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/responsive/tablet-dashboard.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('tablet-dashboard.png')
    })

    test('tablet - investigation', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.tablet)
      await page.goto('/investigation2')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/responsive/tablet-investigation.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('tablet-investigation.png')
    })

    test('mobile - tigers list', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/tigers')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/responsive/mobile-tigers.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('mobile-tigers.png')
    })

    test('mobile - facilities list', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)
      await page.goto('/facilities')
      await waitForPageLoad(page)

      const screenshot = await page.screenshot({
        path: 'screenshots/responsive/mobile-facilities.png',
        fullPage: true
      })
      expect(screenshot).toMatchSnapshot('mobile-facilities.png')
    })
  })
})

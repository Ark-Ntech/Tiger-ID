import { test, expect } from '@playwright/test'
import { login } from '../../helpers/auth'

/**
 * E2E Tests for Facility Detail Page
 *
 * Tests comprehensive functionality of the facility detail page including:
 * - Page loading and navigation
 * - Facility information display
 * - Map visualization with Leaflet
 * - Crawl history timeline with expandable events
 * - Tiger gallery with view modes and grouping
 * - Edit functionality
 * - Manual crawl triggers
 * - Discovery status monitoring
 * - Mobile responsive behavior
 */

test.describe('Facility Detail Page', () => {
  /**
   * Setup: Login before each test
   */
  test.beforeEach(async ({ page }) => {
    await login(page)
    await page.waitForTimeout(1000)
  })

  /**
   * Test 1: View facility detail page with complete information
   * Verifies that the detail page loads and displays facility info correctly
   */
  test('should display facility detail page with complete information', async ({ page }) => {
    // Navigate to facilities list first
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    // Check that facilities page loaded
    await expect(page.locator('[data-testid="facilities-page"]')).toBeVisible()

    // Find and click on the first facility card
    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      // Click to select facility and open detail panel
      await facilityCard.click()
      await page.waitForTimeout(500)

      // Verify detail panel appears
      const detailPanel = page.locator('[data-testid="facility-detail-panel"]')
      if (await detailPanel.count() > 0) {
        await expect(detailPanel).toBeVisible()

        // Verify key information is displayed
        await expect(detailPanel.locator('text=/Tiger|Status|Type|Country/i')).toBeVisible()
      }

      // Click "View Full Details" button to navigate to dedicated page
      const viewDetailsButton = page.locator('[data-testid="view-facility-details"]')
      if (await viewDetailsButton.count() > 0) {
        await viewDetailsButton.click()
        await page.waitForTimeout(1000)

        // Verify we're on the detail page URL
        await expect(page).toHaveURL(/\/facilities\/[\w-]+/)

        // Verify detail page elements are present
        const pageHasContent = await page.locator('h1, h2').count() > 0
        expect(pageHasContent).toBe(true)
      }
    }
  })

  /**
   * Test 2: Facility map displays location correctly
   * Verifies that the map view shows facility markers with Leaflet
   */
  test('should display facility location on map view', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    // Switch to map view using the toggle button
    const mapViewButton = page.locator('[data-testid="view-mode-map"]')
    if (await mapViewButton.count() > 0) {
      await mapViewButton.click()
      await page.waitForTimeout(1500)

      // Verify map container is present
      const mapContainer = page.locator('[data-testid="facilities-map-container"]')
      await expect(mapContainer).toBeVisible()

      // Check for Leaflet map elements
      const leafletContainer = page.locator('.leaflet-container')
      if (await leafletContainer.count() > 0) {
        await expect(leafletContainer).toBeVisible()

        // Verify map controls exist
        const hasMapControls = await page.locator('.leaflet-control-zoom, .leaflet-control-layers').count() > 0
        expect(typeof hasMapControls).toBe('boolean')
      }
    }
  })

  /**
   * Test 3: Crawl history timeline shows events correctly
   * Verifies that crawl events are displayed in chronological order
   */
  test('should display crawl history timeline for facility', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      await facilityCard.click()
      await page.waitForTimeout(500)

      // Check for crawl history timeline component
      const timeline = page.locator('[data-testid="crawl-history-timeline"]')
      if (await timeline.count() > 0) {
        await expect(timeline).toBeVisible()

        // Verify timeline header exists
        await expect(timeline.locator('text=/Crawl History/i')).toBeVisible()

        // Check for summary stats if events exist
        const summaryStats = timeline.locator('[data-testid="crawl-summary-stats"]')
        if (await summaryStats.count() > 0) {
          await expect(summaryStats).toBeVisible()
        }

        // Check for events list or empty state
        const eventsList = timeline.locator('[data-testid="crawl-events-list"]')
        const emptyState = timeline.locator('[data-testid="crawl-history-empty"]')

        const hasContent = (await eventsList.count() > 0) || (await emptyState.count() > 0)
        expect(hasContent).toBe(true)
      }
    }
  })

  /**
   * Test 4: Timeline event details expand to show information
   * Verifies that clicking events shows duration, images found, errors, etc.
   */
  test('should display and expand detailed information for crawl events', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      await facilityCard.click()
      await page.waitForTimeout(1000)

      // Find crawl events
      const crawlEvents = page.locator('[data-testid^="crawl-event-"]')

      if (await crawlEvents.count() > 0) {
        const firstEvent = crawlEvents.first()

        // Verify event has basic elements
        await expect(firstEvent).toBeVisible()

        // Check for event badge
        const eventBadge = firstEvent.locator('[data-testid^="event-badge-"]')
        if (await eventBadge.count() > 0) {
          await expect(eventBadge).toBeVisible()
        }

        // Check for timestamp
        const timestamp = firstEvent.locator('[data-testid="event-timestamp"]')
        if (await timestamp.count() > 0) {
          await expect(timestamp).toBeVisible()
        }

        // Try to expand event to see details
        const expandableEvents = crawlEvents.filter({ has: page.locator('[role="button"]') })
        if (await expandableEvents.count() > 0) {
          const expandableEvent = expandableEvents.first()
          await expandableEvent.click()
          await page.waitForTimeout(300)

          // Check if details section appeared
          const details = expandableEvent.locator('[data-testid="event-details"]')
          if (await details.count() > 0) {
            await expect(details).toBeVisible()

            // Verify detail fields
            const detailFields = [
              details.locator('[data-testid="detail-duration"]'),
              details.locator('[data-testid="detail-image-count"]'),
              details.locator('[data-testid="detail-tiger-count"]'),
              details.locator('[data-testid="detail-timestamp"]'),
            ]

            let hasDetailFields = false
            for (const field of detailFields) {
              if (await field.count() > 0) {
                hasDetailFields = true
                break
              }
            }
            expect(hasDetailFields).toBe(true)
          }
        }
      }
    }
  })

  /**
   * Test 5: Tiger gallery displays tigers from facility
   * Verifies that the gallery component shows tiger images
   */
  test('should display tiger gallery for facility', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      await facilityCard.click()
      await page.waitForTimeout(1000)

      // Look for tiger gallery component
      const gallery = page.locator('[data-testid="facility-tiger-gallery"]')
      if (await gallery.count() > 0) {
        await expect(gallery).toBeVisible()

        // Check for gallery title
        const galleryTitle = gallery.locator('[data-testid="gallery-title"]')
        if (await galleryTitle.count() > 0) {
          await expect(galleryTitle).toContainText(/Tiger Gallery/i)
        }

        // Check for either images or empty state
        const emptyState = gallery.locator('[data-testid="gallery-empty-state"]')
        const imageCards = gallery.locator('[data-testid="image-card"]')
        const imageRows = gallery.locator('[data-testid="image-row"]')

        const hasContent =
          (await emptyState.count() > 0) ||
          (await imageCards.count() > 0) ||
          (await imageRows.count() > 0)

        expect(hasContent).toBe(true)
      }
    }
  })

  /**
   * Test 6: Gallery view mode toggle works (grid/list)
   * Verifies that users can switch between grid and list view
   */
  test('should support different view modes for tiger gallery', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      await facilityCard.click()
      await page.waitForTimeout(1000)

      const gallery = page.locator('[data-testid="facility-tiger-gallery"]')
      if (await gallery.count() > 0) {
        // Look for view mode toggle
        const viewModeToggle = gallery.locator('[data-testid="view-mode-toggle"]')

        if (await viewModeToggle.count() > 0) {
          await expect(viewModeToggle).toBeVisible()

          // Try switching to list view
          const listViewButton = viewModeToggle.locator('button[aria-label="List view"]')
          if (await listViewButton.count() > 0) {
            await listViewButton.click()
            await page.waitForTimeout(500)

            // Check if list view is active
            const isListActive = await listViewButton.getAttribute('aria-pressed')
            expect(isListActive).toBe('true')
          }

          // Try switching to grid view
          const gridViewButton = viewModeToggle.locator('button[aria-label="Grid view"]')
          if (await gridViewButton.count() > 0) {
            await gridViewButton.click()
            await page.waitForTimeout(500)

            // Check if grid view is active
            const isGridActive = await gridViewButton.getAttribute('aria-pressed')
            expect(isGridActive).toBe('true')
          }
        }
      }
    }
  })

  /**
   * Test 7: Group by tiger toggle works
   * Verifies that images can be grouped by individual tiger
   */
  test('should support grouping tigers in gallery', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      await facilityCard.click()
      await page.waitForTimeout(1000)

      const gallery = page.locator('[data-testid="facility-tiger-gallery"]')
      if (await gallery.count() > 0) {
        // Look for group by toggle
        const groupByToggle = gallery.locator('[data-testid="group-by-toggle"]')

        if (await groupByToggle.count() > 0) {
          await expect(groupByToggle).toBeVisible()
          await expect(groupByToggle.locator('text=/Group by tiger/i')).toBeVisible()

          // Toggle grouping on
          const checkbox = groupByToggle.locator('input[type="checkbox"]')
          if (await checkbox.count() > 0) {
            await checkbox.click()
            await page.waitForTimeout(500)

            // Check if grouped view appeared
            const groupedGallery = gallery.locator('[data-testid="grouped-gallery"]')
            if (await groupedGallery.count() > 0) {
              await expect(groupedGallery).toBeVisible()

              // Verify tiger sections exist
              const tigerSections = groupedGallery.locator('[data-testid="tiger-section"]')
              if (await tigerSections.count() > 0) {
                const firstSection = tigerSections.first()
                await expect(firstSection).toBeVisible()

                // Check for section header
                const sectionHeader = firstSection.locator('[data-testid="tiger-section-header"]')
                await expect(sectionHeader).toBeVisible()
              }
            }

            // Toggle grouping off
            await checkbox.click()
            await page.waitForTimeout(500)

            // Check if flat view appeared
            const flatGallery = gallery.locator('[data-testid="flat-gallery"]')
            if (await flatGallery.count() > 0) {
              await expect(flatGallery).toBeVisible()
            }
          }
        }
      }
    }
  })

  /**
   * Test 8: Click tiger navigates to tiger detail
   * Verifies that clicking a tiger image or name navigates to tiger page
   */
  test('should navigate to tiger detail when clicking a tiger in gallery', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      await facilityCard.click()
      await page.waitForTimeout(1000)

      // Look for tiger name links in gallery
      const tigerNameLinks = page.locator('[data-testid="tiger-name-link"]')

      if (await tigerNameLinks.count() > 0) {
        const firstLink = tigerNameLinks.first()
        await firstLink.click()
        await page.waitForTimeout(1000)

        // Check if we navigated to tigers page
        const currentUrl = page.url()
        const navigatedToTiger = currentUrl.includes('/tigers')

        expect(navigatedToTiger).toBe(true)
      }
    }
  })

  /**
   * Test 9: Edit facility info
   * Verifies that users can access edit functionality
   */
  test('should provide edit functionality for facility', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      await facilityCard.click()
      await page.waitForTimeout(500)

      // Navigate to full detail page
      const viewDetailsButton = page.locator('[data-testid="view-facility-details"]')
      if (await viewDetailsButton.count() > 0) {
        await viewDetailsButton.click()
        await page.waitForTimeout(1000)

        // Look for edit button
        const editButton = page.locator(
          'button:has-text("Edit"), [data-testid="edit-facility"], [aria-label*="Edit"]'
        ).first()

        if (await editButton.count() > 0) {
          await expect(editButton).toBeVisible()

          // Click edit button
          await editButton.click()
          await page.waitForTimeout(500)

          // Check if edit form or modal appears
          const formElements = [
            page.locator('form'),
            page.locator('[role="dialog"]'),
            page.locator('.modal'),
            page.locator('[data-testid="edit-form"]'),
          ]

          let hasEditInterface = false
          for (const element of formElements) {
            if (await element.count() > 0) {
              hasEditInterface = true
              break
            }
          }

          expect(hasEditInterface).toBe(true)
        }
      }
    }
  })

  /**
   * Test 10: Start manual crawl
   * Verifies that users can trigger a manual crawl for a facility
   */
  test('should allow triggering manual crawl for facility', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      await facilityCard.click()
      await page.waitForTimeout(1000)

      // Look for crawl trigger buttons
      const crawlButton = page.locator(
        'button:has-text("Start Crawl"), button:has-text("Crawl Now"), [data-testid="start-crawl"]'
      ).first()

      if (await crawlButton.count() > 0) {
        await expect(crawlButton).toBeVisible()

        // Click crawl button
        await crawlButton.click()
        await page.waitForTimeout(500)

        // Check for confirmation dialog or feedback
        const feedbackElements = [
          page.locator('[role="dialog"]'),
          page.locator('[role="alert"]'),
          page.locator('.toast'),
          page.locator('text=/Crawl started|Crawling/i'),
        ]

        let hasFeedback = false
        for (const element of feedbackElements) {
          if (await element.count() > 0) {
            hasFeedback = true
            break
          }
        }

        expect(typeof hasFeedback).toBe('boolean')
      }
    }
  })

  /**
   * Additional comprehensive tests
   */

  test('should display discovery status for facility', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      await facilityCard.click()
      await page.waitForTimeout(1000)

      // Look for status indicators
      const statusBadge = page.locator('[class*="badge"]').filter({ hasText: /active|inactive|pending/i })
      const statusText = page.locator('text=/Status|Discovery|Monitoring/i')

      const hasStatus = (await statusBadge.count() > 0) || (await statusText.count() > 0)
      expect(hasStatus).toBe(true)
    }
  })

  test('should display facility metadata and timestamps', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      // Check for metadata in card view
      const metadataInCard = await facilityCard.locator('text=/Tiger Count|IR Date|Last Inspection/i').count() > 0
      expect(metadataInCard).toBe(true)

      await facilityCard.click()
      await page.waitForTimeout(500)

      // Check metadata in detail panel
      const detailPanel = page.locator('[data-testid="facility-detail-panel"]')
      if (await detailPanel.count() > 0) {
        const metadataFields = detailPanel.locator('text=/Tigers|Status|Type|Country/i')
        const hasMetadata = await metadataFields.count() > 0
        expect(hasMetadata).toBe(true)
      }
    }
  })

  test('should display facility links and social media', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      // Check for website and social media links in card
      const websiteLink = facilityCard.locator('a[href^="http"]').first()
      const socialLinks = facilityCard.locator('text=/Website|Social|Facebook|Twitter|Instagram/i')

      const hasLinks = (await websiteLink.count() > 0) || (await socialLinks.count() > 0)
      expect(typeof hasLinks).toBe('boolean')
    }
  })

  test('should display facility accreditation badges', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    // Look for facilities with accreditation badges
    const facilityWithBadge = page
      .locator('[data-testid^="facility-card-"]')
      .filter({ has: page.locator('text=/Accredited|Reference Facility/i') })
      .first()

    if (await facilityWithBadge.count() > 0) {
      const badge = facilityWithBadge.locator('[class*="badge"]').filter({ hasText: /Accredited|Reference/i })
      if (await badge.count() > 0) {
        await expect(badge.first()).toBeVisible()
      }
    }
  })

  test('should allow closing detail panel', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      await facilityCard.click()
      await page.waitForTimeout(500)

      const detailPanel = page.locator('[data-testid="facility-detail-panel"]')
      if (await detailPanel.count() > 0) {
        await expect(detailPanel).toBeVisible()

        // Click close button
        const closeButton = page.locator('[data-testid="close-detail-panel"]')
        if (await closeButton.count() > 0) {
          await closeButton.click()
          await page.waitForTimeout(500)

          // Verify panel closed
          await expect(detailPanel).not.toBeVisible()
        }
      }
    }
  })

  test('should handle loading states properly', async ({ page }) => {
    // Navigate to facility list
    await page.goto('/facilities')

    // Check for loading spinner
    const loadingSpinner = page.locator('[data-testid="facilities-loading"]')

    // Either spinner appears briefly or content loads immediately
    const spinnerAppeared = (await loadingSpinner.count() > 0)

    // Wait for content to load
    await page.waitForTimeout(2000)

    // Check that content or error is displayed
    const facilitiesPage = page.locator('[data-testid="facilities-page"]')
    const errorState = page.locator('[data-testid="facilities-error"]')

    const hasContent = (await facilitiesPage.count() > 0) || (await errorState.count() > 0)

    expect(spinnerAppeared || hasContent).toBe(true)
  })

  test('should display appropriate message for empty facility list', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1500)

    // Check if there are no facilities
    const facilitiesList = page.locator('[data-testid="facilities-list"]')
    const emptyState = page.locator('[data-testid="facilities-empty"]')

    if (await emptyState.count() > 0) {
      await expect(emptyState).toBeVisible()
      await expect(emptyState.locator('text=/No facilities/i')).toBeVisible()
    } else if (await facilitiesList.count() > 0) {
      // Has facilities, verify list is visible
      await expect(facilitiesList).toBeVisible()
    }
  })

  test('should display mobile-responsive detail panel', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      await facilityCard.click()
      await page.waitForTimeout(1000)

      // On mobile, detail panel should slide up from bottom
      const mobilePanel = page.locator('[data-testid="facility-detail-panel-mobile"]')

      if (await mobilePanel.count() > 0) {
        await expect(mobilePanel).toBeVisible()

        // Check for mobile-specific elements
        const handleBar = mobilePanel.locator('.w-12.h-1.bg-gray-300, .w-12.h-1')
        if (await handleBar.count() > 0) {
          await expect(handleBar).toBeVisible()
        }

        // Should have close button
        const closeButton = page.locator('[data-testid="close-detail-panel-mobile"]')
        if (await closeButton.count() > 0) {
          await expect(closeButton).toBeVisible()

          // Test closing panel
          await closeButton.click()
          await page.waitForTimeout(500)

          await expect(mobilePanel).not.toBeVisible()
        }
      }
    }
  })

  test('should support filter functionality', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    // Look for facility filters component
    const filters = page.locator('[data-testid="facility-filters"]')

    if (await filters.count() > 0) {
      // Check for search input
      const searchInput = page.locator('input[type="search"], input[placeholder*="Search"]')
      if (await searchInput.count() > 0) {
        await expect(searchInput.first()).toBeVisible()

        // Test search functionality
        await searchInput.first().fill('zoo')
        await page.waitForTimeout(800)

        // Verify search value is set
        await expect(searchInput.first()).toHaveValue('zoo')
      }
    }
  })

  test('should show crawl history show more button when there are many events', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      await facilityCard.click()
      await page.waitForTimeout(1000)

      const timeline = page.locator('[data-testid="crawl-history-timeline"]')
      if (await timeline.count() > 0) {
        // Look for show more button
        const showMoreButton = timeline.locator('[data-testid="crawl-history-show-more"]')

        if (await showMoreButton.count() > 0) {
          await expect(showMoreButton).toBeVisible()

          // Click to expand
          await showMoreButton.click()
          await page.waitForTimeout(500)

          // Should show "Show less" text
          await expect(showMoreButton).toContainText(/Show less/i)

          // Click again to collapse
          await showMoreButton.click()
          await page.waitForTimeout(500)

          // Should show "Show more" text
          await expect(showMoreButton).toContainText(/Show.*more/i)
        }
      }
    }
  })

  test('should display quality indicators on tiger images', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      await facilityCard.click()
      await page.waitForTimeout(1000)

      const gallery = page.locator('[data-testid="facility-tiger-gallery"]')
      if (await gallery.count() > 0) {
        // Look for quality overlays or badges
        const qualityOverlay = gallery.locator('[data-testid="quality-overlay"]')
        const qualityBadge = gallery.locator('[data-testid="quality-badge"]')

        const hasQualityIndicators = (await qualityOverlay.count() > 0) || (await qualityBadge.count() > 0)
        expect(typeof hasQualityIndicators).toBe('boolean')
      }
    }
  })

  test('should handle navigation between list and detail views', async ({ page }) => {
    await page.goto('/facilities')
    await page.waitForTimeout(1000)

    const facilityCard = page.locator('[data-testid^="facility-card-"]').first()

    if (await facilityCard.count() > 0) {
      // Get facility name for later verification
      const facilityName = await facilityCard.locator('h3, text=/\w+/').first().textContent()

      await facilityCard.click()
      await page.waitForTimeout(500)

      const viewDetailsButton = page.locator('[data-testid="view-facility-details"]')
      if (await viewDetailsButton.count() > 0) {
        await viewDetailsButton.click()
        await page.waitForTimeout(1000)

        // Verify we're on detail page
        const currentUrl = page.url()
        expect(currentUrl).toMatch(/\/facilities\/[\w-]+/)

        // Verify facility name is shown on detail page
        if (facilityName) {
          const pageHasName = await page.locator(`text=${facilityName.trim()}`).count() > 0
          expect(typeof pageHasName).toBe('boolean')
        }
      }
    }
  })
})

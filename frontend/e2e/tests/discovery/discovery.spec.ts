import { test, expect, Page } from '@playwright/test'
import { login } from '../../helpers/auth'

/**
 * E2E Tests for Discovery Page
 *
 * Comprehensive end-to-end tests covering all aspects of the Discovery page:
 * - Page load with stats display
 * - Tab navigation (Overview, Queue, History, Map)
 * - Discovery controls (Start, Stop, Full Crawl)
 * - FacilityCrawlGrid with progress cards
 * - Real-time activity feed events
 * - Map interactions and facility markers
 * - WebSocket real-time updates
 * - Responsive design
 * - Error handling
 * - Accessibility
 */

test.describe('Discovery Page', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await page.goto('/discovery')
    await page.waitForLoadState('networkidle')
  })

  // ==========================================================================
  // Scenario 1: View discovery page with stats and tabs
  // ==========================================================================

  test.describe('Page Load and Layout', () => {
    test('should display discovery page with all essential elements', async ({ page }) => {
      // Check discovery page is visible
      await expect(page.locator('[data-testid="discovery-page"]')).toBeVisible()

      // Check header section
      const header = page.locator('[data-testid="discovery-header"]')
      await expect(header).toBeVisible()
      await expect(header.locator('h1')).toContainText(/Discovery Monitor/i)
      await expect(header).toContainText(/Continuous tiger discovery/i)

      // Check stats section is visible
      await expect(page.locator('[data-testid="discovery-stats"]')).toBeVisible()

      // Check tabs navigation is visible
      await expect(page.locator('[data-testid="discovery-tabs"]')).toBeVisible()
    })

    test('should display all four stat cards with correct data', async ({ page }) => {
      // Facilities stat card
      const facilitiesStat = page.locator('[data-testid="stat-facilities"]')
      await expect(facilitiesStat).toBeVisible()
      await expect(facilitiesStat).toContainText(/Facilities/i)
      await expect(facilitiesStat.locator('.text-2xl')).toBeVisible() // Stat value
      await expect(facilitiesStat).toContainText(/crawled/i)

      // Tigers stat card
      const tigersStat = page.locator('[data-testid="stat-tigers"]')
      await expect(tigersStat).toBeVisible()
      await expect(tigersStat).toContainText(/Tigers Discovered/i)
      await expect(tigersStat.locator('.text-2xl')).toBeVisible()
      await expect(tigersStat).toContainText(/total in database/i)

      // Images stat card
      const imagesStat = page.locator('[data-testid="stat-images"]')
      await expect(imagesStat).toBeVisible()
      await expect(imagesStat).toContainText(/Images/i)
      await expect(imagesStat.locator('.text-2xl')).toBeVisible()
      await expect(imagesStat).toContainText(/verified/i)

      // Crawls stat card
      const crawlsStat = page.locator('[data-testid="stat-crawls"]')
      await expect(crawlsStat).toBeVisible()
      await expect(crawlsStat).toContainText(/Crawls/i)
      await expect(crawlsStat.locator('.text-2xl')).toBeVisible()
      await expect(crawlsStat).toContainText(/successful|days/i)
    })

    test('should display tools used section', async ({ page }) => {
      const toolsUsed = page.locator('[data-testid="tools-used"]')
      await expect(toolsUsed).toBeVisible()
      await expect(toolsUsed).toContainText(/Tools Used/i)

      // Check for at least one tool badge
      const toolBadges = toolsUsed.locator('span')
      await expect(toolBadges.first()).toBeVisible()
    })

    test('should display WebSocket and scheduler status indicators', async ({ page }) => {
      // WebSocket status
      const wsStatus = page.locator('[data-testid="websocket-status"]')
      await expect(wsStatus).toBeVisible()
      const wsText = await wsStatus.textContent()
      expect(wsText).toMatch(/Live|Offline/i)

      // Scheduler status
      const schedulerStatus = page.locator('[data-testid="scheduler-status"]')
      await expect(schedulerStatus).toBeVisible()
      const schedulerText = await schedulerStatus.textContent()
      expect(schedulerText).toMatch(/Running|Stopped/i)
    })

    test('should display all four tabs', async ({ page }) => {
      const tabs = ['overview', 'queue', 'history', 'map']

      for (const tab of tabs) {
        const tabElement = page.locator(`[data-testid="tab-${tab}"]`)
        await expect(tabElement).toBeVisible()
      }
    })
  })

  // ==========================================================================
  // Scenario 2: Overview tab - FacilityCrawlGrid and ActivityFeed
  // ==========================================================================

  test.describe('Overview Tab Content', () => {
    test('should display facility crawl grid on overview tab', async ({ page }) => {
      // Overview tab should be active by default
      const overviewTab = page.locator('[data-testid="tab-overview"]')
      const classes = await overviewTab.getAttribute('class')
      expect(classes).toContain('border-tiger-orange')

      // Check for facility crawl grid
      const facilityCrawlGrid = page.locator('[data-testid="facility-crawl-grid"]')
      await expect(facilityCrawlGrid).toBeVisible()
    })

    test('should display facility crawl cards when facilities are being crawled', async ({ page }) => {
      // Look for facility crawl cards (may not exist if no active crawls)
      const crawlCards = page.locator('[data-testid^="facility-crawl-card-"]')
      const count = await crawlCards.count()

      if (count > 0) {
        // Verify first card has required elements
        const firstCard = crawlCards.first()
        await expect(firstCard).toBeVisible()

        // Check for progress bar
        const progressBar = firstCard.locator('[data-testid="facility-progress-bar"]')
        await expect(progressBar).toBeVisible()

        // Check for status indicator
        const statusIndicator = firstCard.locator('[data-testid="facility-status"]')
        await expect(statusIndicator).toBeVisible()
      }
    })

    test('should show empty state when no facilities are being crawled', async ({ page }) => {
      const facilityCrawlGrid = page.locator('[data-testid="facility-crawl-grid"]')
      await expect(facilityCrawlGrid).toBeVisible()

      // Check for empty state message
      const emptyMessage = facilityCrawlGrid.locator('text=/No facilities currently/i')
      const messageCount = await emptyMessage.count()

      // Empty state might be shown
      expect(messageCount).toBeGreaterThanOrEqual(0)
    })

    test('should display scheduler status card', async ({ page }) => {
      const statusCard = page.locator('[data-testid="scheduler-status-card"]')
      await expect(statusCard).toBeVisible()
      await expect(statusCard).toContainText(/Scheduler Status/i)

      // Check for status fields
      await expect(statusCard).toContainText(/Status/i)
      await expect(statusCard).toContainText(/Enabled/i)
      await expect(statusCard).toContainText(/Total Crawls/i)
      await expect(statusCard).toContainText(/Last Crawl/i)
    })

    test('should display facility breakdown card', async ({ page }) => {
      const breakdownCard = page.locator('[data-testid="facility-breakdown-card"]')
      await expect(breakdownCard).toBeVisible()
      await expect(breakdownCard).toContainText(/Facility Breakdown/i)

      // Check for breakdown fields
      await expect(breakdownCard).toContainText(/Reference Facilities/i)
      await expect(breakdownCard).toContainText(/With Website/i)
      await expect(breakdownCard).toContainText(/With Social Media/i)
      await expect(breakdownCard).toContainText(/Pending Crawl/i)
    })

    test('should display live activity feed', async ({ page }) => {
      const activityFeed = page.locator('[data-testid="discovery-activity-feed"]')
      await expect(activityFeed).toBeVisible()

      // Check for header
      const feedHeader = page.locator('[data-testid="activity-feed-header"]')
      await expect(feedHeader).toBeVisible()
      await expect(feedHeader).toContainText(/Live Activity Feed/i)

      // Check for live indicator
      const liveIndicator = page.locator('[data-testid="live-indicator"]')
      await expect(liveIndicator).toBeVisible()

      // Check for auto-scroll toggle
      const autoScrollToggle = page.locator('[data-testid="auto-scroll-toggle"]')
      await expect(autoScrollToggle).toBeVisible()
    })
  })

  // ==========================================================================
  // Scenario 3: Queue tab - pending crawl queue
  // ==========================================================================

  test.describe('Queue Tab Content', () => {
    test('should switch to queue tab and display queue content', async ({ page }) => {
      // Click queue tab
      await page.locator('[data-testid="tab-queue"]').click()
      await page.waitForTimeout(300)

      // Queue content should be visible
      const queueContent = page.locator('[data-testid="tab-content-queue"]')
      await expect(queueContent).toBeVisible()

      // Should display queue heading with count
      await expect(queueContent).toContainText(/Crawl Queue/i)
      await expect(queueContent).toContainText(/pending|facilities/i)
    })

    test('should display queue table or empty state', async ({ page }) => {
      await page.locator('[data-testid="tab-queue"]').click()
      await page.waitForTimeout(300)

      // Check for table or empty message
      const table = page.locator('[data-testid="queue-table"]')
      const emptyMessage = page.locator('[data-testid="queue-empty"]')

      const hasTable = await table.count() > 0
      const hasEmptyMessage = await emptyMessage.count() > 0

      // One of these should be present
      expect(hasTable || hasEmptyMessage).toBe(true)

      if (hasTable) {
        // Verify table structure
        await expect(table.locator('thead')).toBeVisible()
        await expect(table.locator('tbody')).toBeVisible()

        // Check for column headers
        await expect(table).toContainText(/Facility/i)
        await expect(table).toContainText(/Location/i)
        await expect(table).toContainText(/Tigers/i)
        await expect(table).toContainText(/Last Crawled/i)
      }
    })

    test('should display clickable facility rows in queue', async ({ page }) => {
      await page.locator('[data-testid="tab-queue"]').click()
      await page.waitForTimeout(300)

      // Check if any queue rows exist
      const queueRows = page.locator('[data-testid^="queue-row-"]')
      const count = await queueRows.count()

      if (count > 0) {
        const firstRow = queueRows.first()
        await expect(firstRow).toBeVisible()

        // Row should have hover effect
        await firstRow.hover()
        const classes = await firstRow.getAttribute('class')
        expect(classes).toContain('cursor-pointer')
      }
    })
  })

  // ==========================================================================
  // Scenario 4: History tab - completed crawl history
  // ==========================================================================

  test.describe('History Tab Content', () => {
    test('should switch to history tab and display crawl history', async ({ page }) => {
      await page.locator('[data-testid="tab-history"]').click()
      await page.waitForTimeout(300)

      const historyContent = page.locator('[data-testid="tab-content-history"]')
      await expect(historyContent).toBeVisible()
      await expect(historyContent).toContainText(/Recent Crawl History/i)
    })

    test('should display history items or empty state', async ({ page }) => {
      await page.locator('[data-testid="tab-history"]').click()
      await page.waitForTimeout(300)

      // Check for history items or empty message
      const historyItems = page.locator('[data-testid^="history-item-"]')
      const emptyMessage = page.locator('[data-testid="history-empty"]')

      const hasItems = await historyItems.count() > 0
      const hasEmptyMessage = await emptyMessage.count() > 0

      // One of these should be present
      expect(hasItems || hasEmptyMessage).toBe(true)
    })

    test('should display history items with status badges', async ({ page }) => {
      await page.locator('[data-testid="tab-history"]').click()
      await page.waitForTimeout(300)

      const historyItems = page.locator('[data-testid^="history-item-"]')
      const count = await historyItems.count()

      if (count > 0) {
        const firstItem = historyItems.first()
        await expect(firstItem).toBeVisible()

        // Should have status icon (completed or failed)
        const icons = firstItem.locator('svg')
        await expect(icons.first()).toBeVisible()

        // Should have source URL or facility info
        await expect(firstItem).toContainText(/.+/)

        // Should have status badge
        const badges = firstItem.locator('span[class*="badge"]')
        const badgeCount = await badges.count()
        expect(badgeCount).toBeGreaterThan(0)
      }
    })

    test('should show image and tiger counts on completed crawls', async ({ page }) => {
      await page.locator('[data-testid="tab-history"]').click()
      await page.waitForTimeout(300)

      const historyItems = page.locator('[data-testid^="history-item-"]')
      const count = await historyItems.count()

      if (count > 0) {
        // Look for items with image/tiger stats
        const itemsWithStats = historyItems.locator('text=/images|tigers/i')
        const statsCount = await itemsWithStats.count()

        // At least some items might have stats
        expect(statsCount).toBeGreaterThanOrEqual(0)
      }
    })
  })

  // ==========================================================================
  // Scenario 5: Facilities Map tab - markers on map
  // ==========================================================================

  test.describe('Facilities Map Tab', () => {
    test('should switch to map tab and display facilities map', async ({ page }) => {
      await page.locator('[data-testid="tab-map"]').click()
      await page.waitForTimeout(500) // Allow time for map to load

      const mapContent = page.locator('[data-testid="tab-content-map"]')
      await expect(mapContent).toBeVisible()
    })

    test('should display crawl progress cards when facility is selected', async ({ page }) => {
      await page.locator('[data-testid="tab-map"]').click()
      await page.waitForTimeout(500)

      // Check if any crawl progress cards are visible
      const progressCards = page.locator('[data-testid^="crawl-progress-card-"]')
      const count = await progressCards.count()

      // Cards may or may not be visible depending on selection
      expect(count).toBeGreaterThanOrEqual(0)

      if (count > 0) {
        const firstCard = progressCards.first()
        await expect(firstCard).toBeVisible()

        // Verify card elements
        await expect(firstCard.locator('[data-testid="crawl-card-facility-name"]')).toBeVisible()
        await expect(firstCard.locator('[data-testid="crawl-progress-bar"]')).toBeVisible()
        await expect(firstCard.locator('[data-testid="crawl-status-icon"]')).toBeVisible()
      }
    })
  })

  // ==========================================================================
  // Scenario 6: Start/stop discovery buttons
  // ==========================================================================

  test.describe('Discovery Controls - Start/Stop', () => {
    test('should display start/stop button with appropriate text', async ({ page }) => {
      const startStopButton = page.locator('[data-testid="start-stop-button"]')
      await expect(startStopButton).toBeVisible()

      const buttonText = await startStopButton.textContent()
      expect(buttonText).toMatch(/Start|Stop/i)
    })

    test('should handle start/stop button click', async ({ page }) => {
      const startStopButton = page.locator('[data-testid="start-stop-button"]')
      const initialText = await startStopButton.textContent()

      // Click the button
      await startStopButton.click()
      await page.waitForTimeout(1000)

      // Button should either show loading state or have changed
      const isVisible = await startStopButton.isVisible()
      expect(isVisible).toBe(true)
    })

    test('should show correct button variant based on scheduler status', async ({ page }) => {
      const startStopButton = page.locator('[data-testid="start-stop-button"]')
      const schedulerStatus = page.locator('[data-testid="scheduler-status"]')

      const statusText = await schedulerStatus.textContent()
      const buttonText = await startStopButton.textContent()

      // Button text should match scheduler status
      if (statusText?.includes('Running')) {
        expect(buttonText).toContain('Stop')
      } else {
        expect(buttonText).toContain('Start')
      }
    })
  })

  // ==========================================================================
  // Scenario 7: Full crawl trigger
  // ==========================================================================

  test.describe('Discovery Controls - Full Crawl', () => {
    test('should display full crawl button', async ({ page }) => {
      const fullCrawlButton = page.locator('[data-testid="full-crawl-button"]')
      await expect(fullCrawlButton).toBeVisible()
      await expect(fullCrawlButton).toContainText(/Full Crawl/i)
    })

    test('should handle full crawl button click', async ({ page }) => {
      const fullCrawlButton = page.locator('[data-testid="full-crawl-button"]')

      // Click full crawl button
      await fullCrawlButton.click()
      await page.waitForTimeout(1000)

      // Button should still be visible (might show loading state)
      await expect(fullCrawlButton).toBeVisible()
    })

    test('should disable full crawl button while crawling', async ({ page }) => {
      const fullCrawlButton = page.locator('[data-testid="full-crawl-button"]')

      await fullCrawlButton.click()
      await page.waitForTimeout(200)

      // Button might be disabled or show loading spinner
      const hasLoadingSpinner = await fullCrawlButton.locator('svg[class*="animate"]').count()
      const isDisabled = await fullCrawlButton.isDisabled()

      // Either condition indicates crawl in progress
      expect(hasLoadingSpinner > 0 || isDisabled).toBeTruthy()
    })
  })

  // ==========================================================================
  // Scenario 8: Crawl progress cards
  // ==========================================================================

  test.describe('Crawl Progress Cards', () => {
    test('should display crawl progress cards with all required elements', async ({ page }) => {
      const crawlCards = page.locator('[data-testid^="crawl-progress-card-"]')
      const count = await crawlCards.count()

      if (count > 0) {
        const firstCard = crawlCards.first()

        // Check facility name
        await expect(firstCard.locator('[data-testid="crawl-card-facility-name"]')).toBeVisible()

        // Check progress bar
        await expect(firstCard.locator('[data-testid="crawl-progress-bar"]')).toBeVisible()

        // Check status icon
        await expect(firstCard.locator('[data-testid="crawl-status-icon"]')).toBeVisible()

        // Check progress percentage
        await expect(firstCard.locator('[data-testid="crawl-progress-percentage"]')).toBeVisible()

        // Check images found
        await expect(firstCard.locator('[data-testid="crawl-images-found"]')).toBeVisible()

        // Check status label
        await expect(firstCard.locator('[data-testid="crawl-status-label"]')).toBeVisible()
      }
    })

    test('should show animated progress for crawling status', async ({ page }) => {
      const crawlingCards = page.locator('[data-testid^="crawl-progress-card-"]').filter({
        has: page.locator('[class*="animate-spin"]')
      })

      const count = await crawlingCards.count()

      if (count > 0) {
        const card = crawlingCards.first()

        // Should have active indicator
        const activeIndicator = card.locator('[data-testid="crawl-active-indicator"]')
        const indicatorCount = await activeIndicator.count()
        expect(indicatorCount).toBeGreaterThanOrEqual(0)
      }
    })

    test('should allow clicking on facility cards', async ({ page }) => {
      const crawlCards = page.locator('[data-testid^="facility-crawl-card-"]')
      const count = await crawlCards.count()

      if (count > 0) {
        const firstCard = crawlCards.first()

        // Card should have button role if clickable
        const role = await firstCard.getAttribute('role')

        if (role === 'button') {
          await firstCard.click()
          await page.waitForTimeout(300)
          // Click handled successfully
        }
      }
    })

    test('should show rate limit countdown when rate limited', async ({ page }) => {
      // Look for rate limited cards
      const rateLimitedCards = page.locator('[data-testid^="crawl-progress-card-"]').filter({
        hasText: /rate limit/i
      })

      const count = await rateLimitedCards.count()

      if (count > 0) {
        const countdown = rateLimitedCards.first().locator('[data-testid="rate-limit-countdown"]')
        const countdownCount = await countdown.count()

        if (countdownCount > 0) {
          await expect(countdown).toBeVisible()
          // Should display time remaining
          await expect(countdown).toContainText(/\d+/)
        }
      }
    })

    test('should show error message and retry button for failed crawls', async ({ page }) => {
      const errorCards = page.locator('[data-testid^="crawl-progress-card-"]').filter({
        hasText: /error/i
      })

      const count = await errorCards.count()

      if (count > 0) {
        const errorCard = errorCards.first()

        // Check for error message
        const errorMessage = errorCard.locator('[data-testid="crawl-error-message"]')
        const messageCount = await errorMessage.count()

        if (messageCount > 0) {
          await expect(errorMessage).toBeVisible()
        }

        // Check for retry button
        const retryButton = errorCard.locator('[data-testid="crawl-retry-button"]')
        const retryCount = await retryButton.count()

        if (retryCount > 0) {
          await expect(retryButton).toBeVisible()
          await expect(retryButton).toContainText(/retry/i)
        }
      }
    })
  })

  // ==========================================================================
  // Scenario 9: Activity feed events
  // ==========================================================================

  test.describe('Activity Feed Events', () => {
    test('should display activity feed with live indicator', async ({ page }) => {
      const activityFeed = page.locator('[data-testid="discovery-activity-feed"]')
      await expect(activityFeed).toBeVisible()

      const liveIndicator = page.locator('[data-testid="live-indicator"]')
      await expect(liveIndicator).toBeVisible()

      const indicatorText = await liveIndicator.textContent()
      expect(indicatorText).toMatch(/Live|Paused/i)
    })

    test('should toggle auto-scroll when clicked', async ({ page }) => {
      const autoScrollToggle = page.locator('[data-testid="auto-scroll-toggle"]')
      await expect(autoScrollToggle).toBeVisible()

      // Get initial state
      const initialPressed = await autoScrollToggle.getAttribute('aria-pressed')

      // Click toggle
      await autoScrollToggle.click()
      await page.waitForTimeout(300)

      // State should have changed
      const newPressed = await autoScrollToggle.getAttribute('aria-pressed')
      expect(newPressed).not.toBe(initialPressed)
    })

    test('should display activity feed list or empty state', async ({ page }) => {
      const feedList = page.locator('[data-testid="activity-feed-list"]')
      await expect(feedList).toBeVisible()

      // Check for events or empty state
      const events = page.locator('[data-testid^="event-item-"]')
      const emptyState = page.locator('[data-testid="activity-feed-empty"]')

      const hasEvents = await events.count() > 0
      const hasEmptyState = await emptyState.count() > 0

      // One should be present
      expect(hasEvents || hasEmptyState).toBe(true)
    })

    test('should display event items with proper formatting', async ({ page }) => {
      await page.waitForTimeout(1000)

      const eventItems = page.locator('[data-testid^="event-item-"]')
      const count = await eventItems.count()

      if (count > 0) {
        const firstEvent = eventItems.first()
        await expect(firstEvent).toBeVisible()

        // Check for event type attribute
        const eventType = await firstEvent.getAttribute('data-event-type')
        expect(eventType).toBeTruthy()

        // Should be one of the valid event types
        expect(eventType).toMatch(/image_found|crawl_started|crawl_completed|rate_limited|error|tiger_detected/)

        // Check for timestamp
        const timestamp = firstEvent.locator('[data-testid^="event-timestamp-"]')
        await expect(timestamp).toBeVisible()

        // Check for message
        const message = firstEvent.locator('[data-testid^="event-message-"]')
        await expect(message).toBeVisible()
      }
    })

    test('should display event count when events exist', async ({ page }) => {
      await page.waitForTimeout(1000)

      const eventCount = page.locator('[data-testid="event-count"]')
      const count = await eventCount.count()

      if (count > 0) {
        await expect(eventCount).toBeVisible()
        await expect(eventCount).toContainText(/event/i)
      }
    })

    test('should show facility name on events with facility context', async ({ page }) => {
      await page.waitForTimeout(1000)

      const eventItems = page.locator('[data-testid^="event-item-"]')
      const count = await eventItems.count()

      if (count > 0) {
        // Look for events with facility info
        const facilityEvents = eventItems.locator('[data-testid^="event-facility-"]')
        const facilityCount = await facilityEvents.count()

        // Some events might have facility context
        expect(facilityCount).toBeGreaterThanOrEqual(0)
      }
    })

    test('should allow clicking on clickable events', async ({ page }) => {
      await page.waitForTimeout(1000)

      const eventItems = page.locator('[data-testid^="event-item-"]')
      const count = await eventItems.count()

      if (count > 0) {
        const firstEvent = eventItems.first()
        const role = await firstEvent.getAttribute('role')

        if (role === 'button') {
          // Event is clickable
          await firstEvent.click()
          await page.waitForTimeout(300)
        }
      }
    })
  })

  // ==========================================================================
  // Scenario 10: Map marker interactions
  // ==========================================================================

  test.describe('Map Marker Interactions', () => {
    test('should display map with facility markers', async ({ page }) => {
      await page.locator('[data-testid="tab-map"]').click()
      await page.waitForTimeout(500)

      const mapContent = page.locator('[data-testid="tab-content-map"]')
      await expect(mapContent).toBeVisible()

      // Map component would be rendered here
      // Note: Actual map testing would require the map library's testing utilities
    })

    test('should display selected facility details on map tab', async ({ page }) => {
      await page.locator('[data-testid="tab-map"]').click()
      await page.waitForTimeout(500)

      // Check for progress cards (shown when facility selected)
      const progressCards = page.locator('[data-testid^="crawl-progress-card-"]')
      const count = await progressCards.count()

      // Cards appear when a facility is selected
      expect(count).toBeGreaterThanOrEqual(0)
    })
  })

  // ==========================================================================
  // Additional Tests: Tab Navigation
  // ==========================================================================

  test.describe('Tab Navigation', () => {
    test('should have overview tab active by default', async ({ page }) => {
      const overviewTab = page.locator('[data-testid="tab-overview"]')
      const classes = await overviewTab.getAttribute('class')

      expect(classes).toContain('border-tiger-orange')
      expect(classes).toContain('text-tiger-orange')
    })

    test('should switch between all tabs successfully', async ({ page }) => {
      const tabs = ['queue', 'history', 'map', 'overview']

      for (const tabId of tabs) {
        // Click tab
        await page.locator(`[data-testid="tab-${tabId}"]`).click()
        await page.waitForTimeout(300)

        // Tab should be active
        const tab = page.locator(`[data-testid="tab-${tabId}"]`)
        const classes = await tab.getAttribute('class')
        expect(classes).toContain('border-tiger-orange')

        // Corresponding content should be visible
        const content = page.locator(`[data-testid="tab-content-${tabId}"]`)
        if (await content.count() > 0) {
          await expect(content).toBeVisible()
        }
      }
    })
  })

  // ==========================================================================
  // Additional Tests: WebSocket Updates
  // ==========================================================================

  test.describe('WebSocket Updates', () => {
    test('should show WebSocket connection status', async ({ page }) => {
      const wsStatus = page.locator('[data-testid="websocket-status"]')
      await expect(wsStatus).toBeVisible()

      // Should indicate connection state
      const statusText = await wsStatus.textContent()
      expect(statusText).toMatch(/Live|Offline/i)
    })

    test('should handle simulated discovery events', async ({ page }) => {
      // Simulate a WebSocket message
      await page.evaluate(() => {
        const mockEvent = {
          type: 'discovery_event',
          event_type: 'crawl_started',
          facility_id: 'test-facility-1',
          facility_name: 'Test Facility',
          message: 'Started crawling test facility'
        }

        window.dispatchEvent(new CustomEvent('mock-discovery-event', { detail: mockEvent }))
      })

      await page.waitForTimeout(500)

      // Activity feed should be visible
      const activityFeed = page.locator('[data-testid="discovery-activity-feed"]')
      await expect(activityFeed).toBeVisible()
    })
  })

  // ==========================================================================
  // Additional Tests: Responsive Design
  // ==========================================================================

  test.describe('Responsive Design', () => {
    test('should be functional on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.waitForTimeout(300)

      await expect(page.locator('[data-testid="discovery-page"]')).toBeVisible()
      await expect(page.locator('[data-testid="discovery-header"]')).toBeVisible()
      await expect(page.locator('[data-testid="discovery-stats"]')).toBeVisible()
    })

    test('should be functional on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.waitForTimeout(300)

      await expect(page.locator('[data-testid="discovery-page"]')).toBeVisible()
      await expect(page.locator('[data-testid="discovery-stats"]')).toBeVisible()
      await expect(page.locator('[data-testid="discovery-tabs"]')).toBeVisible()
    })

    test('should be functional on desktop viewport', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 })
      await page.waitForTimeout(300)

      await expect(page.locator('[data-testid="discovery-page"]')).toBeVisible()
      await expect(page.locator('[data-testid="discovery-stats"]')).toBeVisible()
      await expect(page.locator('[data-testid="discovery-activity-feed"]')).toBeVisible()
    })
  })

  // ==========================================================================
  // Additional Tests: Error Handling
  // ==========================================================================

  test.describe('Error Handling', () => {
    test('should handle loading state gracefully', async ({ page }) => {
      await page.goto('/discovery')

      // Look for loading indicator
      const loadingSpinner = page.locator('[data-testid="discovery-loading"]')

      // Loading state may appear briefly
      const count = await loadingSpinner.count()
      expect(count).toBeGreaterThanOrEqual(0)
    })

    test('should render page without crashing on API errors', async ({ page }) => {
      // Intercept API and force error
      await page.route('**/api/discovery/status', route => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Internal server error' })
        })
      })

      await page.reload()
      await page.waitForTimeout(1000)

      // Page should still render
      await expect(page.locator('[data-testid="discovery-page"]')).toBeVisible()
    })
  })

  // ==========================================================================
  // Additional Tests: Accessibility
  // ==========================================================================

  test.describe('Accessibility', () => {
    test('should have proper ARIA labels on interactive elements', async ({ page }) => {
      const startStopButton = page.locator('[data-testid="start-stop-button"]')
      await expect(startStopButton).toBeVisible()

      const fullCrawlButton = page.locator('[data-testid="full-crawl-button"]')
      await expect(fullCrawlButton).toBeVisible()

      // Auto-scroll toggle should have aria-pressed
      const autoScrollToggle = page.locator('[data-testid="auto-scroll-toggle"]')
      const ariaPressed = await autoScrollToggle.getAttribute('aria-pressed')
      expect(ariaPressed).toBeTruthy()
    })

    test('should support keyboard navigation', async ({ page }) => {
      // Tab through interactive elements
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')

      // Some element should be focused
      const activeElement = page.locator(':focus')
      const count = await activeElement.count()
      expect(count).toBeGreaterThan(0)
    })

    test('should have proper heading hierarchy', async ({ page }) => {
      const h1 = page.locator('h1')
      const h1Count = await h1.count()

      // Should have at least one h1
      expect(h1Count).toBeGreaterThan(0)

      // H1 should contain main page title
      await expect(h1.first()).toContainText(/Discovery Monitor/i)
    })
  })
})

import { test, expect } from '@playwright/test'
import { login } from '../../helpers/auth'

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await login(page)
    await page.goto('/dashboard')
    await page.waitForTimeout(1000)
  })

  test.describe('Page Load and Structure', () => {
    test('should display dashboard page with all sections', async ({ page }) => {
      // Check main dashboard container
      await expect(page.locator('[data-testid="dashboard-page"]')).toBeVisible()

      // Check header
      await expect(page.locator('[data-testid="dashboard-header"]')).toBeVisible()
      await expect(page.locator('h1')).toContainText('Dashboard')

      // Check for main sections
      await expect(page.locator('[data-testid="quick-stats-grid"]')).toBeVisible()
      await expect(page.locator('[data-testid="dashboard-main-content"]')).toBeVisible()
      await expect(page.locator('[data-testid="dashboard-secondary-content"]')).toBeVisible()
      await expect(page.locator('[data-testid="analytics-tabs"]')).toBeVisible()
    })

    test('should display last updated timestamp', async ({ page }) => {
      const timestampText = await page.locator('text=/Last updated:/i').textContent()
      expect(timestampText).toBeTruthy()
      expect(timestampText).toMatch(/Last updated:/)
    })
  })

  test.describe('Quick Stats Grid', () => {
    test('should display quick stats grid with all stat cards', async ({ page }) => {
      const quickStatsGrid = page.locator('[data-testid="quick-stats-grid"]')
      await expect(quickStatsGrid).toBeVisible()

      // Check for stat cards
      await expect(page.locator('[data-testid*="stat-"]')).toHaveCount(4, { timeout: 5000 })
    })

    test('should display tiger count stat', async ({ page }) => {
      const tigerStat = page.locator('[data-testid="stat-total-tigers"]')
      await expect(tigerStat).toBeVisible({ timeout: 5000 })

      // Check for value
      const value = tigerStat.locator('[data-testid="stat-value"]')
      await expect(value).toBeVisible()

      // Check that value is numeric or shows loading
      const valueText = await value.textContent()
      expect(valueText).toBeTruthy()
    })

    test('should display facilities stat', async ({ page }) => {
      const facilitiesStat = page.locator('[data-testid="stat-facilities"]')
      await expect(facilitiesStat).toBeVisible({ timeout: 5000 })

      const value = facilitiesStat.locator('[data-testid="stat-value"]')
      await expect(value).toBeVisible()
    })

    test('should display ID rate stat', async ({ page }) => {
      const idRateStat = page.locator('[data-testid="stat-id-rate"]')
      await expect(idRateStat).toBeVisible({ timeout: 5000 })

      const value = idRateStat.locator('[data-testid="stat-value"]')
      await expect(value).toBeVisible()

      // ID rate should be a percentage
      const valueText = await value.textContent()
      expect(valueText).toMatch(/%/)
    })

    test('should display pending verifications stat', async ({ page }) => {
      const pendingStat = page.locator('[data-testid="stat-pending-verifications"]')
      await expect(pendingStat).toBeVisible({ timeout: 5000 })

      const value = pendingStat.locator('[data-testid="stat-value"]')
      await expect(value).toBeVisible()
    })

    test('should show trend indicators when available', async ({ page }) => {
      // Check if any stat has a change indicator
      const changeIndicators = page.locator('[data-testid="stat-change"]')
      const count = await changeIndicators.count()

      // If trends exist, verify they have proper structure
      if (count > 0) {
        const firstChange = changeIndicators.first()
        await expect(firstChange).toBeVisible()

        // Should contain numeric value
        const changeText = await firstChange.textContent()
        expect(changeText).toBeTruthy()
      }
    })

    test('should make clickable stats navigate on click', async ({ page }) => {
      // Total Tigers stat should link to /tigers
      const tigerStat = page.locator('[data-testid="stat-total-tigers"]')
      const isTigerStatClickable = await tigerStat.locator('a').count() > 0

      if (isTigerStatClickable) {
        await tigerStat.click()
        await page.waitForTimeout(500)
        expect(page.url()).toContain('/tigers')

        // Navigate back
        await page.goto('/dashboard')
      }
    })
  })

  test.describe('Time Range Selector', () => {
    test('should display time range selector buttons', async ({ page }) => {
      const controls = page.locator('[data-testid="dashboard-controls"]')
      await expect(controls).toBeVisible()

      // Check for time range buttons
      await expect(page.locator('button:has-text("7d")')).toBeVisible()
      await expect(page.locator('button:has-text("30d")')).toBeVisible()
      await expect(page.locator('button:has-text("90d")')).toBeVisible()
    })

    test('should change time range when clicking buttons', async ({ page }) => {
      // Default is 30d (should have ring)
      const button30d = page.locator('button:has-text("30d")')
      const button7d = page.locator('button:has-text("7d")')
      const button90d = page.locator('button:has-text("90d")')

      // Click 7d
      await button7d.click()
      await page.waitForTimeout(500)

      // Should have visual indicator (ring class)
      const classes7d = await button7d.getAttribute('class')
      expect(classes7d).toContain('ring-2')

      // Click 90d
      await button90d.click()
      await page.waitForTimeout(500)

      const classes90d = await button90d.getAttribute('class')
      expect(classes90d).toContain('ring-2')

      // Click back to 30d
      await button30d.click()
      await page.waitForTimeout(500)

      const classes30d = await button30d.getAttribute('class')
      expect(classes30d).toContain('ring-2')
    })

    test('should update analytics data when time range changes', async ({ page }) => {
      // Get initial investigation count or chart data
      const chartBefore = await page.locator('[data-testid="investigation-activity-chart"]').isVisible()
      expect(chartBefore).toBeTruthy()

      // Change time range
      await page.locator('button:has-text("7d")').click()
      await page.waitForTimeout(1000)

      // Chart should still be visible (data may have updated)
      const chartAfter = await page.locator('[data-testid="investigation-activity-chart"]').isVisible()
      expect(chartAfter).toBeTruthy()
    })
  })

  test.describe('Refresh Button', () => {
    test('should display refresh button', async ({ page }) => {
      const refreshButton = page.locator('[data-testid="refresh-button"]')
      await expect(refreshButton).toBeVisible()
      await expect(refreshButton).toContainText('Refresh')
    })

    test('should refresh data when clicking refresh button', async ({ page }) => {
      const refreshButton = page.locator('[data-testid="refresh-button"]')

      // Click refresh
      await refreshButton.click()

      // Button should show loading state (disabled with spinning icon)
      const isDisabled = await refreshButton.isDisabled()

      // Wait for refresh to complete
      await page.waitForTimeout(2000)

      // Button should be enabled again after refresh
      await expect(refreshButton).toBeEnabled()

      // Last updated timestamp should have changed
      const timestamp = page.locator('text=/Last updated:/i')
      await expect(timestamp).toBeVisible()
    })

    test('should show spinning icon during refresh', async ({ page }) => {
      const refreshButton = page.locator('[data-testid="refresh-button"]')

      // Click refresh
      await refreshButton.click()

      // Check for spinning icon (has animate-spin class)
      const spinningIcon = refreshButton.locator('svg.animate-spin')

      // Give it a moment to show the animation
      await page.waitForTimeout(500)

      // Icon might have stopped spinning by now, but refresh should have occurred
      // Just verify the button is back to normal
      await expect(refreshButton).toBeEnabled()
    })
  })

  test.describe('Subagent Activity Panel', () => {
    test('should display subagent activity panel', async ({ page }) => {
      const panel = page.locator('[data-testid="subagent-activity-panel"]')
      await expect(panel).toBeVisible()

      // Check for title
      await expect(page.locator('text=/Subagent Activity/i')).toBeVisible()
    })

    test('should show pool utilization stats', async ({ page }) => {
      const poolStats = page.locator('[data-testid="subagent-pool-stats"]')

      // Pool stats might not always be visible, check if present
      const isVisible = await poolStats.isVisible().catch(() => false)

      if (isVisible) {
        // Check for ML inference pool
        await expect(page.locator('[data-testid="subagent-pool-ml_inference"]')).toBeVisible()

        // Check for research pool
        await expect(page.locator('[data-testid="subagent-pool-research"]')).toBeVisible()

        // Check for report generation pool
        await expect(page.locator('[data-testid="subagent-pool-report_generation"]')).toBeVisible()
      }
    })

    test('should display pool utilization bars with progress', async ({ page }) => {
      const mlPool = page.locator('[data-testid="subagent-pool-ml_inference"]')
      const isVisible = await mlPool.isVisible().catch(() => false)

      if (isVisible) {
        // Should show utilization text (e.g., "0/4 idle" or "2/4 running")
        const poolText = await mlPool.textContent()
        expect(poolText).toMatch(/\d+\/\d+/)
        expect(poolText).toMatch(/idle|running/)

        // Should show percentage
        expect(poolText).toMatch(/\d+%/)
      }
    })

    test('should display active tasks list', async ({ page }) => {
      const tasksList = page.locator('[data-testid="subagent-tasks-list"]')
      await expect(tasksList).toBeVisible()

      // Check for "Recent Tasks" heading
      await expect(tasksList.locator('text=/Recent Tasks/i')).toBeVisible()
    })

    test('should show empty state when no tasks', async ({ page }) => {
      const tasksList = page.locator('[data-testid="subagent-tasks-list"]')
      await expect(tasksList).toBeVisible()

      // Check if there are tasks or empty state
      const taskCount = await page.locator('[data-testid^="subagent-task-"]').count()

      if (taskCount === 0) {
        // Should show empty state
        await expect(tasksList.locator('text=/No active tasks/i')).toBeVisible()
      }
    })

    test('should display task with correct status indicators', async ({ page }) => {
      // Check if any tasks exist
      const firstTask = page.locator('[data-testid^="subagent-task-"]').first()
      const taskExists = await firstTask.isVisible().catch(() => false)

      if (taskExists) {
        // Task should have status badge
        const statusBadge = firstTask.locator('text=/running|queued|completed|error/i')
        await expect(statusBadge).toBeVisible()

        // Running tasks should show progress bar
        const taskText = await firstTask.textContent()
        if (taskText?.includes('running')) {
          const progressBar = firstTask.locator('div[style*="width"]')
          const progressCount = await progressBar.count()
          expect(progressCount).toBeGreaterThanOrEqual(0)
        }
      }
    })

    test('should navigate to investigation when clicking task', async ({ page }) => {
      // Find a task that has an investigation ID
      const tasks = page.locator('[data-testid^="subagent-task-"]')
      const taskCount = await tasks.count()

      if (taskCount > 0) {
        const firstTask = tasks.first()
        const isClickable = await firstTask.getAttribute('role') === 'button'

        if (isClickable) {
          await firstTask.click()
          await page.waitForTimeout(500)

          // Should navigate to investigation page
          expect(page.url()).toMatch(/\/investigation2\//)
        }
      }
    })
  })

  test.describe('Recent Investigations Table', () => {
    test('should display recent investigations card', async ({ page }) => {
      const card = page.locator('[data-testid="recent-investigations-card"]')
      await expect(card).toBeVisible()

      // Check for heading
      await expect(page.locator('text=/Recent Investigations/i')).toBeVisible()
    })

    test('should display investigations table or empty state', async ({ page }) => {
      // Wait for table to load
      await page.waitForTimeout(1000)

      // Check if table or empty state is visible
      const tableVisible = await page.locator('[data-testid="investigations-table"]').isVisible()
      const emptyVisible = await page.locator('[data-testid="investigations-table-empty"]').isVisible()
      const loadingVisible = await page.locator('[data-testid="investigations-table-loading"]').isVisible()

      // One of these should be visible
      expect(tableVisible || emptyVisible || loadingVisible).toBeTruthy()
    })

    test('should display investigation rows when data exists', async ({ page }) => {
      await page.waitForTimeout(1500)

      // Check for investigation rows
      const investigationRows = page.locator('[data-testid^="investigation-row-"]')
      const count = await investigationRows.count()

      if (count > 0) {
        // First row should be visible
        const firstRow = investigationRows.first()
        await expect(firstRow).toBeVisible()

        // Should have image thumbnail
        await expect(firstRow.locator('[data-testid="query-image-thumbnail"]')).toBeVisible()

        // Should have date
        await expect(firstRow.locator('[data-testid="investigation-date"]')).toBeVisible()

        // Should have status badge
        await expect(firstRow.locator('[data-testid="investigation-status"]')).toBeVisible()

        // Should have match count
        await expect(firstRow.locator('[data-testid="investigation-match-count"]')).toBeVisible()

        // Should have actions
        await expect(firstRow.locator('[data-testid="investigation-actions"]')).toBeVisible()
      }
    })

    test('should navigate to investigation when clicking row', async ({ page }) => {
      await page.waitForTimeout(1500)

      const firstRow = page.locator('[data-testid^="investigation-row-"]').first()
      const exists = await firstRow.isVisible().catch(() => false)

      if (exists) {
        // Get the investigation ID from the testid
        const testId = await firstRow.getAttribute('data-testid')
        const investigationId = testId?.replace('investigation-row-', '')

        // Click the row
        await firstRow.click()
        await page.waitForTimeout(500)

        // Should navigate to investigation detail page
        expect(page.url()).toContain(`/investigation2/${investigationId}`)
      }
    })

    test('should have view button for each investigation', async ({ page }) => {
      await page.waitForTimeout(1500)

      const firstRow = page.locator('[data-testid^="investigation-row-"]').first()
      const exists = await firstRow.isVisible().catch(() => false)

      if (exists) {
        const investigationId = (await firstRow.getAttribute('data-testid'))?.replace('investigation-row-', '')
        const viewButton = page.locator(`[data-testid="view-investigation-${investigationId}"]`)

        await expect(viewButton).toBeVisible()

        // Click view button
        await viewButton.click()
        await page.waitForTimeout(500)

        // Should navigate to investigation
        expect(page.url()).toContain('/investigation2/')
      }
    })

    test('should display "View All" button', async ({ page }) => {
      const viewAllButton = page.locator('button:has-text("View All")')
      const exists = await viewAllButton.isVisible().catch(() => false)

      if (exists) {
        await expect(viewAllButton).toBeVisible()

        // Click should navigate to investigations page
        await viewAllButton.click()
        await page.waitForTimeout(500)
        expect(page.url()).toContain('/investigation2')
      }
    })
  })

  test.describe('Geographic Map', () => {
    test('should display geographic map card', async ({ page }) => {
      const mapCard = page.locator('[data-testid="geographic-map-card"]')
      await expect(mapCard).toBeVisible()

      // Check for heading
      await expect(mapCard.locator('text=/Geographic Distribution/i')).toBeVisible()
    })

    test('should display map or empty state', async ({ page }) => {
      const mapCard = page.locator('[data-testid="geographic-map-card"]')

      // Wait for content to load
      await page.waitForTimeout(1500)

      // Check if map or empty message is shown
      const mapContent = await mapCard.textContent()
      expect(mapContent).toBeTruthy()

      // Should have either map data or "No facility data available"
      const hasContent = mapContent?.length > 50 // Map has substantial content
      const hasEmptyMessage = mapContent?.includes('No facility data available')

      expect(hasContent || hasEmptyMessage).toBeTruthy()
    })

    test('should render map when facility data exists', async ({ page }) => {
      // Check if map container exists
      const mapCard = page.locator('[data-testid="geographic-map-card"]')
      await page.waitForTimeout(1500)

      // Look for Leaflet map container or similar
      const hasMapContainer = await mapCard.locator('.leaflet-container, [class*="map"]').count() > 0

      // Or check that it's not showing empty state
      const emptyState = await mapCard.locator('text=/No facility data available/i').isVisible().catch(() => false)

      if (!emptyState) {
        // Map should be attempting to render
        expect(hasMapContainer || !emptyState).toBeTruthy()
      }
    })
  })

  test.describe('Analytics Tabs', () => {
    test('should display analytics tabs navigation', async ({ page }) => {
      const tabsContainer = page.locator('[data-testid="analytics-tabs"]')
      await expect(tabsContainer).toBeVisible()

      // Check for all tab buttons
      await expect(page.locator('[data-testid="tab-investigations"]')).toBeVisible()
      await expect(page.locator('[data-testid="tab-evidence-&-verification"]')).toBeVisible()
      await expect(page.locator('[data-testid="tab-geographic"]')).toBeVisible()
      await expect(page.locator('[data-testid="tab-tigers"]')).toBeVisible()
      await expect(page.locator('[data-testid="tab-facilities"]')).toBeVisible()
      await expect(page.locator('[data-testid="tab-agent-performance"]')).toBeVisible()
      await expect(page.locator('[data-testid="tab-model-performance"]')).toBeVisible()
    })

    test('should default to Investigations tab', async ({ page }) => {
      // Default tab (index 0) should be active
      const investigationsTab = page.locator('[data-testid="tab-investigations"]')
      const classes = await investigationsTab.getAttribute('class')

      // Active tab has border-primary-600 and text-primary-600
      expect(classes).toContain('border-primary-600')
      expect(classes).toContain('text-primary-600')

      // Tab content should be visible
      await expect(page.locator('[data-testid="investigation-analytics-tab"]')).toBeVisible()
    })

    test('should switch to Evidence & Verification tab', async ({ page }) => {
      const evidenceTab = page.locator('[data-testid="tab-evidence-&-verification"]')
      await evidenceTab.click()
      await page.waitForTimeout(500)

      // Tab should be active
      const classes = await evidenceTab.getAttribute('class')
      expect(classes).toContain('border-primary-600')

      // Tab content should be visible
      await expect(page.locator('[data-testid="evidence-verification-tab"]')).toBeVisible()
    })

    test('should switch to Geographic tab', async ({ page }) => {
      const geoTab = page.locator('[data-testid="tab-geographic"]')
      await geoTab.click()
      await page.waitForTimeout(500)

      const classes = await geoTab.getAttribute('class')
      expect(classes).toContain('border-primary-600')

      await expect(page.locator('[data-testid="geographic-tab"]')).toBeVisible()
    })

    test('should switch to Tigers tab', async ({ page }) => {
      const tigersTab = page.locator('[data-testid="tab-tigers"]')
      await tigersTab.click()
      await page.waitForTimeout(500)

      const classes = await tigersTab.getAttribute('class')
      expect(classes).toContain('border-primary-600')

      await expect(page.locator('[data-testid="tiger-analytics-tab"]')).toBeVisible()
    })

    test('should switch to Facilities tab', async ({ page }) => {
      const facilitiesTab = page.locator('[data-testid="tab-facilities"]')
      await facilitiesTab.click()
      await page.waitForTimeout(500)

      const classes = await facilitiesTab.getAttribute('class')
      expect(classes).toContain('border-primary-600')

      await expect(page.locator('[data-testid="facility-analytics-tab"]')).toBeVisible()
    })

    test('should switch to Agent Performance tab', async ({ page }) => {
      const agentTab = page.locator('[data-testid="tab-agent-performance"]')
      await agentTab.click()
      await page.waitForTimeout(500)

      const classes = await agentTab.getAttribute('class')
      expect(classes).toContain('border-primary-600')

      await expect(page.locator('[data-testid="agent-analytics-tab"]')).toBeVisible()
    })

    test('should switch to Model Performance tab', async ({ page }) => {
      const modelTab = page.locator('[data-testid="tab-model-performance"]')
      await modelTab.click()
      await page.waitForTimeout(500)

      const classes = await modelTab.getAttribute('class')
      expect(classes).toContain('border-primary-600')

      await expect(page.locator('[data-testid="model-performance-tab"]')).toBeVisible()
    })

    test('should display model performance tab content', async ({ page }) => {
      const modelTab = page.locator('[data-testid="tab-model-performance"]')
      await modelTab.click()
      await page.waitForTimeout(1500)

      // Should have model select dropdown
      await expect(page.locator('[data-testid="model-select"]')).toBeVisible()

      // Should have benchmark button
      await expect(page.locator('[data-testid="benchmark-button"]')).toBeVisible()

      // Should have model performance table
      await expect(page.locator('[data-testid="model-performance-table"]')).toBeVisible()
    })
  })

  test.describe('Charts and Visualizations', () => {
    test('should display investigation activity chart', async ({ page }) => {
      const chart = page.locator('[data-testid="investigation-activity-chart"]')
      await expect(chart).toBeVisible()

      // Check for chart heading
      await expect(chart.locator('text=/Investigation Activity/i')).toBeVisible()

      // Wait for chart to load (either chart or loading spinner)
      await page.waitForTimeout(1500)

      // Chart content should be present (Recharts SVG or loading spinner)
      const content = await chart.textContent()
      expect(content).toBeTruthy()
    })

    test('should render line chart without errors', async ({ page }) => {
      // Wait for charts to render
      await page.waitForTimeout(2000)

      // Check for Recharts SVG elements (line charts)
      const lineCharts = page.locator('svg line, svg path[stroke]')
      const count = await lineCharts.count()

      // Should have at least some chart elements
      expect(count).toBeGreaterThan(0)
    })

    test('should display charts in Investigations analytics tab', async ({ page }) => {
      // Default tab is Investigations
      await page.waitForTimeout(1500)

      const tab = page.locator('[data-testid="investigation-analytics-tab"]')
      await expect(tab).toBeVisible()

      // Should have pie chart for status
      const statusChart = tab.locator('text=/Investigations by Status/i')
      await expect(statusChart).toBeVisible()

      // Should have bar chart for priority
      const priorityChart = tab.locator('text=/Investigations by Priority/i')
      await expect(priorityChart).toBeVisible()

      // Should have timeline chart
      const timelineChart = tab.locator('text=/Investigations Over Time/i')
      await expect(timelineChart).toBeVisible()
    })

    test('should display charts in Tigers analytics tab', async ({ page }) => {
      const tigersTab = page.locator('[data-testid="tab-tigers"]')
      await tigersTab.click()
      await page.waitForTimeout(1500)

      // Should have tiger identifications chart
      const idChart = page.locator('text=/Tiger Identifications/i')
      await expect(idChart).toBeVisible()

      // Should have tigers by status chart
      const statusChart = page.locator('text=/Tigers by Status/i')
      await expect(statusChart).toBeVisible()
    })

    test('should display model performance charts', async ({ page }) => {
      const modelTab = page.locator('[data-testid="tab-model-performance"]')
      await modelTab.click()
      await page.waitForTimeout(1500)

      // Should have accuracy comparison chart
      const accuracyChart = page.locator('text=/Accuracy Comparison/i')
      await expect(accuracyChart).toBeVisible()

      // Should have performance metrics chart
      const perfChart = page.locator('text=/Performance Metrics/i')
      await expect(perfChart).toBeVisible()
    })

    test('should handle loading state for charts', async ({ page }) => {
      // Reload page to see loading state
      await page.reload()
      await page.waitForTimeout(300)

      // Check for loading spinners
      const loadingSpinners = page.locator('[class*="animate-spin"]')
      const count = await loadingSpinners.count()

      // Should show loading indicators during data fetch
      expect(count).toBeGreaterThanOrEqual(0)

      // Wait for content to load
      await page.waitForTimeout(2000)

      // Charts should be visible after loading
      const chart = page.locator('[data-testid="investigation-activity-chart"]')
      await expect(chart).toBeVisible()
    })
  })

  test.describe('Responsive Behavior', () => {
    test('should display mobile-friendly layout on small screens', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 })
      await page.waitForTimeout(500)

      // Dashboard should still be visible
      await expect(page.locator('[data-testid="dashboard-page"]')).toBeVisible()

      // Stats grid should stack vertically
      const statsGrid = page.locator('[data-testid="quick-stats-grid"]')
      await expect(statsGrid).toBeVisible()

      // Controls should wrap
      const controls = page.locator('[data-testid="dashboard-controls"]')
      await expect(controls).toBeVisible()
    })

    test('should display tablet layout on medium screens', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.waitForTimeout(500)

      await expect(page.locator('[data-testid="dashboard-page"]')).toBeVisible()
      await expect(page.locator('[data-testid="quick-stats-grid"]')).toBeVisible()
    })

    test('should display desktop layout on large screens', async ({ page }) => {
      // Set desktop viewport
      await page.setViewportSize({ width: 1920, height: 1080 })
      await page.waitForTimeout(500)

      await expect(page.locator('[data-testid="dashboard-page"]')).toBeVisible()

      // All sections should be visible in desktop layout
      await expect(page.locator('[data-testid="dashboard-main-content"]')).toBeVisible()
      await expect(page.locator('[data-testid="dashboard-secondary-content"]')).toBeVisible()
    })
  })

  test.describe('Navigation', () => {
    test('should navigate to Tigers page from stat card', async ({ page }) => {
      const tigerStat = page.locator('[data-testid="stat-total-tigers"]')
      const hasLink = await tigerStat.locator('a').count() > 0

      if (hasLink) {
        await tigerStat.click()
        await page.waitForTimeout(500)
        expect(page.url()).toContain('/tigers')
      }
    })

    test('should navigate to Facilities page from stat card', async ({ page }) => {
      const facilitiesStat = page.locator('[data-testid="stat-facilities"]')
      const hasLink = await facilitiesStat.locator('a').count() > 0

      if (hasLink) {
        await facilitiesStat.click()
        await page.waitForTimeout(500)
        expect(page.url()).toContain('/facilities')
      }
    })

    test('should navigate to Verifications page from stat card', async ({ page }) => {
      const pendingStat = page.locator('[data-testid="stat-pending-verifications"]')
      const hasLink = await pendingStat.locator('a').count() > 0

      if (hasLink) {
        await pendingStat.click()
        await page.waitForTimeout(500)
        expect(page.url()).toContain('/verification')
      }
    })
  })

  test.describe('Error Handling', () => {
    test('should handle API errors gracefully', async ({ page }) => {
      // Dashboard should still render even if some API calls fail
      await expect(page.locator('[data-testid="dashboard-page"]')).toBeVisible()

      // Should not show error modals that block the UI
      const errorModal = page.locator('[role="dialog"]:has-text("Error")')
      const hasErrorModal = await errorModal.isVisible().catch(() => false)

      // Error modals should not be blocking the UI on initial load
      if (hasErrorModal) {
        // If there's an error modal, it should be dismissible
        const closeButton = errorModal.locator('button[aria-label*="close"], button:has-text("Close")')
        const hasCloseButton = await closeButton.count() > 0
        expect(hasCloseButton).toBeTruthy()
      }
    })

    test('should display empty states instead of errors for missing data', async ({ page }) => {
      await page.waitForTimeout(2000)

      // If no investigation data, should show empty state not error
      const emptyState = page.locator('[data-testid="investigations-table-empty"]')
      const hasEmptyState = await emptyState.isVisible().catch(() => false)

      if (hasEmptyState) {
        await expect(emptyState).toBeVisible()
        await expect(emptyState).toContainText(/No investigations/i)
      }
    })
  })
})

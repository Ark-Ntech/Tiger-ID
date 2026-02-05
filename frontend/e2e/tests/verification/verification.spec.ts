import { test, expect, Page } from '@playwright/test'
import { VerificationQueuePage } from '../../pages/verification/verification-queue.page'
import { login } from '../../helpers/auth'
import {
  createVerificationQueue,
  createHighConfidenceItem,
  createLowConfidenceItem,
  createFacilityVerificationItem,
} from '../../data/factories'

/**
 * Comprehensive E2E tests for the Verification Queue
 * Tests all major verification workflows including filtering, bulk actions, and individual operations
 */

test.describe('Verification Queue', () => {
  let verificationPage: VerificationQueuePage

  test.beforeEach(async ({ page }) => {
    // Authenticate user before each test
    await login(page)

    // Initialize page object
    verificationPage = new VerificationQueuePage(page)

    // Navigate to verification queue
    await verificationPage.goto()
  })

  test.describe('Page Load and Initial State', () => {
    test('should load verification queue page', async () => {
      // Verify page title is displayed
      await expect(verificationPage.pageTitle).toBeVisible()
      await expect(verificationPage.pageTitle).toContainText(/verification/i)
    })

    test('should display pending count badge', async () => {
      // Pending count should be visible
      await expect(verificationPage.pendingCount).toBeVisible()

      // Should contain a number
      const countText = await verificationPage.pendingCount.textContent()
      expect(countText).toMatch(/\d+/)
    })

    test('should show empty state when no items', async ({ page }) => {
      // Mock empty response
      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [],
            total: 0,
            page: 1,
            per_page: 20,
          }),
        })
      })

      // Reload page
      await verificationPage.goto()

      // Should show empty state
      await verificationPage.expectEmptyState()
    })

    test('should display verification queue with items', async ({ page }) => {
      // Mock queue with items
      const mockItems = createVerificationQueue(5)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems.filter((item) => item.status === 'pending'),
            total: mockItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      // Reload page
      await verificationPage.goto()

      // Should have queue rows
      const pendingItems = mockItems.filter((item) => item.status === 'pending')
      await verificationPage.expectQueueCount(pendingItems.length)
    })
  })

  test.describe('Filtering', () => {
    test('should filter by status', async ({ page }) => {
      // Mock API response for different statuses
      await page.route('**/api/verification/queue*', async (route) => {
        const url = new URL(route.request().url())
        const status = url.searchParams.get('status')

        const allItems = createVerificationQueue(10)
        const filteredItems = status
          ? allItems.filter((item) => item.status === status)
          : allItems

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: filteredItems,
            total: filteredItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      // Initial load
      await verificationPage.goto()
      const initialCount = await verificationPage.queueRows.count()

      // Filter by status
      await verificationPage.statusFilter.selectOption('approved')
      await verificationPage.waitForSpinnerToDisappear()

      // Should update results
      const filteredCount = await verificationPage.queueRows.count()
      expect(filteredCount).toBeLessThanOrEqual(initialCount)
    })

    test('should filter by confidence level', async ({ page }) => {
      // Mock high confidence items
      const highConfItems = [
        createHighConfidenceItem(),
        createHighConfidenceItem(),
        createHighConfidenceItem(),
      ]

      await page.route('**/api/verification/queue*', async (route) => {
        const url = new URL(route.request().url())
        const confidence = url.searchParams.get('min_confidence')

        let items = createVerificationQueue(10)

        if (confidence && parseFloat(confidence) >= 0.9) {
          items = highConfItems
        }

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items,
            total: items.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      // Initial load
      await verificationPage.goto()

      // Filter by high confidence
      await verificationPage.filterByConfidence('high')

      // Should show fewer items (only high confidence)
      await verificationPage.expectQueueCount(highConfItems.length)
    })

    test('should filter by entity type (tiger/facility)', async ({ page }) => {
      const tigerItems = createVerificationQueue(5)
      const facilityItems = [
        createFacilityVerificationItem(),
        createFacilityVerificationItem(),
      ]

      await page.route('**/api/verification/queue*', async (route) => {
        const url = new URL(route.request().url())
        const entityType = url.searchParams.get('entity_type')

        let items = [...tigerItems, ...facilityItems]

        if (entityType === 'tiger') {
          items = tigerItems
        } else if (entityType === 'facility') {
          items = facilityItems
        }

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items,
            total: items.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      // Initial load
      await verificationPage.goto()

      // Filter by tiger
      const tigerFilter = verificationPage.getPage().getByTestId(
        'verification-filter-entity-type'
      )
      await tigerFilter.selectOption('tiger')
      await verificationPage.waitForSpinnerToDisappear()

      // Should show only tiger items
      await verificationPage.expectQueueCount(tigerItems.length)

      // Filter by facility
      await tigerFilter.selectOption('facility')
      await verificationPage.waitForSpinnerToDisappear()

      // Should show only facility items
      await verificationPage.expectQueueCount(facilityItems.length)
    })
  })

  test.describe('Item Selection', () => {
    test('should select individual items with checkboxes', async ({ page }) => {
      const mockItems = createVerificationQueue(5)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      await verificationPage.goto()

      // Select first item
      await verificationPage.selectRow(0)

      // Checkbox should be checked
      const checkbox = verificationPage.getRowCheckbox(0)
      await expect(checkbox).toBeChecked()

      // Bulk actions should become enabled
      await expect(verificationPage.bulkActionsDropdown).toBeEnabled()
    })

    test('should select all items with select-all checkbox', async ({ page }) => {
      const mockItems = createVerificationQueue(5)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      await verificationPage.goto()

      // Select all
      await verificationPage.selectAllRows()

      // All checkboxes should be checked
      const rowCount = await verificationPage.queueRows.count()
      for (let i = 0; i < rowCount; i++) {
        const checkbox = verificationPage.getRowCheckbox(i)
        await expect(checkbox).toBeChecked()
      }
    })

    test('should deselect all when clicking select-all again', async ({ page }) => {
      const mockItems = createVerificationQueue(5)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      await verificationPage.goto()

      // Select all
      await verificationPage.selectAllRows()

      // Deselect all
      await verificationPage.selectAllRows()

      // All checkboxes should be unchecked
      const rowCount = await verificationPage.queueRows.count()
      for (let i = 0; i < rowCount; i++) {
        const checkbox = verificationPage.getRowCheckbox(i)
        await expect(checkbox).not.toBeChecked()
      }
    })
  })

  test.describe('Bulk Actions', () => {
    test('should bulk approve selected items with confirmation', async ({ page }) => {
      const mockItems = createVerificationQueue(3)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      // Mock bulk approve endpoint
      let approveRequestMade = false
      await page.route('**/api/verification/bulk-approve', async (route) => {
        approveRequestMade = true
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            approved_count: 2,
          }),
        })
      })

      await verificationPage.goto()

      // Select first two items
      await verificationPage.selectRow(0)
      await verificationPage.selectRow(1)

      // Mock confirmation dialog
      page.on('dialog', async (dialog) => {
        expect(dialog.message()).toContain('approve')
        await dialog.accept()
      })

      // Bulk approve
      await verificationPage.bulkApprove()

      // Should make API call
      expect(approveRequestMade).toBe(true)

      // Should show success message
      await verificationPage.expectToastWithText(/approved/i)
    })

    test('should bulk reject selected items with confirmation', async ({ page }) => {
      const mockItems = createVerificationQueue(3)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      // Mock bulk reject endpoint
      let rejectRequestMade = false
      await page.route('**/api/verification/bulk-reject', async (route) => {
        rejectRequestMade = true
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            rejected_count: 2,
          }),
        })
      })

      await verificationPage.goto()

      // Select first two items
      await verificationPage.selectRow(0)
      await verificationPage.selectRow(1)

      // Mock confirmation dialog
      page.on('dialog', async (dialog) => {
        expect(dialog.message()).toContain('reject')
        await dialog.accept()
      })

      // Bulk reject
      await verificationPage.bulkReject()

      // Should make API call
      expect(rejectRequestMade).toBe(true)

      // Should show success message
      await verificationPage.expectToastWithText(/rejected/i)
    })

    test('should cancel bulk actions when dialog is dismissed', async ({ page }) => {
      const mockItems = createVerificationQueue(3)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      // Mock bulk approve endpoint (should NOT be called)
      let approveRequestMade = false
      await page.route('**/api/verification/bulk-approve', async (route) => {
        approveRequestMade = true
        await route.fulfill({ status: 200 })
      })

      await verificationPage.goto()

      // Select items
      await verificationPage.selectRow(0)
      await verificationPage.selectRow(1)

      // Dismiss confirmation dialog
      page.on('dialog', async (dialog) => {
        await dialog.dismiss()
      })

      // Try bulk approve
      await verificationPage.bulkApprove()

      // Should NOT make API call
      expect(approveRequestMade).toBe(false)
    })
  })

  test.describe('Individual Item Actions', () => {
    test('should approve individual item', async ({ page }) => {
      const mockItems = createVerificationQueue(3)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      // Mock approve endpoint
      let approvedItemId: string | null = null
      await page.route('**/api/verification/*/approve', async (route) => {
        approvedItemId = route.request().url().split('/').slice(-2)[0]
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true }),
        })
      })

      await verificationPage.goto()

      // Approve first item
      await verificationPage.approveItem(0)

      // Should make API call
      expect(approvedItemId).toBe(mockItems[0].id)

      // Should show success message
      await verificationPage.expectToastWithText(/approved/i)
    })

    test('should reject individual item', async ({ page }) => {
      const mockItems = createVerificationQueue(3)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      // Mock reject endpoint
      let rejectedItemId: string | null = null
      await page.route('**/api/verification/*/reject', async (route) => {
        rejectedItemId = route.request().url().split('/').slice(-2)[0]
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true }),
        })
      })

      await verificationPage.goto()

      // Reject first item
      await verificationPage.rejectItem(0)

      // Should make API call
      expect(rejectedItemId).toBe(mockItems[0].id)

      // Should show success message
      await verificationPage.expectToastWithText(/rejected/i)
    })

    test('should handle approve errors gracefully', async ({ page }) => {
      const mockItems = createVerificationQueue(3)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      // Mock error response
      await page.route('**/api/verification/*/approve', async (route) => {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Failed to approve verification',
          }),
        })
      })

      await verificationPage.goto()

      // Try to approve
      await verificationPage.approveItem(0)

      // Should show error message
      await verificationPage.expectToastWithText(/error|failed/i)
    })
  })

  test.describe('Comparison Overlay', () => {
    test('should open comparison overlay when clicking view button', async ({ page }) => {
      const mockItems = createVerificationQueue(3)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      await verificationPage.goto()

      // Open comparison for first item
      await verificationPage.viewComparison(0)

      // Overlay should be visible
      await verificationPage.expectComparisonVisible()
    })

    test('should display query and match images in overlay', async ({ page }) => {
      const mockItems = createVerificationQueue(3)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      await verificationPage.goto()

      // Open comparison
      await verificationPage.viewComparison(0)

      // Both images should be visible
      await expect(verificationPage.queryImage).toBeVisible()
      await expect(verificationPage.matchImage).toBeVisible()
    })

    test('should close comparison overlay when clicking close button', async ({ page }) => {
      const mockItems = createVerificationQueue(3)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      await verificationPage.goto()

      // Open comparison
      await verificationPage.viewComparison(0)

      // Close overlay
      await verificationPage.closeComparison()

      // Overlay should not be visible
      await expect(verificationPage.comparisonOverlay).not.toBeVisible()
    })

    test('should close overlay when pressing Escape key', async ({ page }) => {
      const mockItems = createVerificationQueue(3)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      await verificationPage.goto()

      // Open comparison
      await verificationPage.viewComparison(0)

      // Press Escape
      await page.keyboard.press('Escape')

      // Overlay should close
      await expect(verificationPage.comparisonOverlay).not.toBeVisible()
    })
  })

  test.describe('Model Agreement Badge', () => {
    test('should display model agreement badge with correct text', async ({ page }) => {
      const highAgreementItem = createHighConfidenceItem({
        model_agreement: 0.95,
      })

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [highAgreementItem],
            total: 1,
            page: 1,
            per_page: 20,
          }),
        })
      })

      await verificationPage.goto()

      // Badge should show high agreement
      await verificationPage.expectModelAgreement(0, '95%')
    })

    test('should show different badge styles for different agreement levels', async ({
      page,
    }) => {
      const items = [
        createHighConfidenceItem({ model_agreement: 0.95 }), // High agreement
        createVerificationQueue(1)[0], // Medium agreement
        createLowConfidenceItem({ model_agreement: 0.55 }), // Low agreement
      ]

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items,
            total: items.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      await verificationPage.goto()

      // Each badge should have different class/color based on agreement level
      const badge0 = verificationPage.getModelAgreementBadge(0)
      const badge1 = verificationPage.getModelAgreementBadge(1)
      const badge2 = verificationPage.getModelAgreementBadge(2)

      await expect(badge0).toBeVisible()
      await expect(badge1).toBeVisible()
      await expect(badge2).toBeVisible()

      // Badges should have different visual indicators
      // This could be checked via classes or computed styles
      const badge0Class = await badge0.getAttribute('class')
      const badge2Class = await badge2.getAttribute('class')

      expect(badge0Class).not.toBe(badge2Class)
    })

    test('should show consensus indicator when all models agree', async ({ page }) => {
      const perfectAgreementItem = createHighConfidenceItem({
        model_agreement: 1.0,
        model_scores: {
          wildlife_tools: 0.98,
          cvwc2019_reid: 0.98,
          transreid: 0.98,
          megadescriptor_b: 0.98,
          tiger_reid: 0.98,
          rapid_reid: 0.98,
        },
      })

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [perfectAgreementItem],
            total: 1,
            page: 1,
            per_page: 20,
          }),
        })
      })

      await verificationPage.goto()

      // Should show consensus indicator
      const badge = verificationPage.getModelAgreementBadge(0)
      const badgeText = await badge.textContent()
      expect(badgeText).toMatch(/100%|perfect|consensus/i)
    })
  })

  test.describe('Pagination', () => {
    test('should navigate to next page', async ({ page }) => {
      // Create enough items to require pagination
      const allItems = createVerificationQueue(30)
      const itemsPerPage = 10

      await page.route('**/api/verification/queue*', async (route) => {
        const url = new URL(route.request().url())
        const pageNum = parseInt(url.searchParams.get('page') || '1')

        const startIdx = (pageNum - 1) * itemsPerPage
        const endIdx = startIdx + itemsPerPage
        const pageItems = allItems.slice(startIdx, endIdx)

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: pageItems,
            total: allItems.length,
            page: pageNum,
            per_page: itemsPerPage,
            total_pages: Math.ceil(allItems.length / itemsPerPage),
          }),
        })
      })

      await verificationPage.goto()

      // Should show first page
      await verificationPage.expectQueueCount(itemsPerPage)

      // Click next page button
      const nextButton = verificationPage.getPage().getByTestId('pagination-next')
      await nextButton.click()
      await verificationPage.waitForSpinnerToDisappear()

      // Should show second page
      await verificationPage.expectQueueCount(itemsPerPage)
    })

    test('should navigate to previous page', async ({ page }) => {
      const allItems = createVerificationQueue(30)
      const itemsPerPage = 10

      await page.route('**/api/verification/queue*', async (route) => {
        const url = new URL(route.request().url())
        const pageNum = parseInt(url.searchParams.get('page') || '1')

        const startIdx = (pageNum - 1) * itemsPerPage
        const endIdx = startIdx + itemsPerPage
        const pageItems = allItems.slice(startIdx, endIdx)

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: pageItems,
            total: allItems.length,
            page: pageNum,
            per_page: itemsPerPage,
            total_pages: Math.ceil(allItems.length / itemsPerPage),
          }),
        })
      })

      // Navigate to page 2 first
      await verificationPage.getPage().goto('/verification?page=2')
      await verificationPage.waitForPageLoad()

      // Click previous page button
      const prevButton = verificationPage.getPage().getByTestId('pagination-prev')
      await prevButton.click()
      await verificationPage.waitForSpinnerToDisappear()

      // Should show first page
      const url = new URL(verificationPage.getPage().url())
      expect(url.searchParams.get('page')).toBe('1')
    })

    test('should disable previous button on first page', async ({ page }) => {
      const mockItems = createVerificationQueue(5)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
            total_pages: 1,
          }),
        })
      })

      await verificationPage.goto()

      // Previous button should be disabled
      const prevButton = verificationPage.getPage().getByTestId('pagination-prev')
      await expect(prevButton).toBeDisabled()
    })

    test('should disable next button on last page', async ({ page }) => {
      const mockItems = createVerificationQueue(5)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
            total_pages: 1,
          }),
        })
      })

      await verificationPage.goto()

      // Next button should be disabled (only 1 page)
      const nextButton = verificationPage.getPage().getByTestId('pagination-next')
      await expect(nextButton).toBeDisabled()
    })

    test('should display current page and total pages', async ({ page }) => {
      const allItems = createVerificationQueue(30)
      const itemsPerPage = 10

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: allItems.slice(0, itemsPerPage),
            total: allItems.length,
            page: 1,
            per_page: itemsPerPage,
            total_pages: 3,
          }),
        })
      })

      await verificationPage.goto()

      // Should show page indicator
      const pageInfo = verificationPage.getPage().getByTestId('pagination-info')
      await expect(pageInfo).toBeVisible()
      await expect(pageInfo).toContainText(/1.*3|page 1/i)
    })
  })

  test.describe('Real-time Updates', () => {
    test('should handle queue updates when items are reviewed', async ({ page }) => {
      const mockItems = createVerificationQueue(3)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      await verificationPage.goto()
      const initialCount = await verificationPage.queueRows.count()

      // Approve an item
      await page.route('**/api/verification/*/approve', async (route) => {
        await route.fulfill({ status: 200 })
      })

      await verificationPage.approveItem(0)

      // Queue should update (item removed or status changed)
      await verificationPage.getPage().waitForTimeout(1000)

      const newCount = await verificationPage.queueRows.count()
      expect(newCount).toBeLessThanOrEqual(initialCount)
    })
  })

  test.describe('Accessibility', () => {
    test('should have proper ARIA labels', async () => {
      await verificationPage.goto()

      // Check for ARIA labels on buttons
      const approveButton = verificationPage.getRowApproveButton(0)
      const rejectButton = verificationPage.getRowRejectButton(0)

      if ((await approveButton.count()) > 0) {
        const ariaLabel = await approveButton.getAttribute('aria-label')
        expect(ariaLabel).toContain('approve')
      }

      if ((await rejectButton.count()) > 0) {
        const ariaLabel = await rejectButton.getAttribute('aria-label')
        expect(ariaLabel).toContain('reject')
      }
    })

    test('should be keyboard navigable', async ({ page }) => {
      const mockItems = createVerificationQueue(3)

      await page.route('**/api/verification/queue*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: mockItems,
            total: mockItems.length,
            page: 1,
            per_page: 20,
          }),
        })
      })

      await verificationPage.goto()

      // Tab through interactive elements
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')

      // Should be able to focus on buttons
      const focusedElement = await page.evaluate(() => {
        return document.activeElement?.tagName
      })

      expect(['BUTTON', 'INPUT', 'SELECT', 'A']).toContain(focusedElement)
    })
  })
})

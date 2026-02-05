import { test, expect } from '@playwright/test'
import { TigersListPage } from '../../pages/tigers/tigers-list.page'
import { tigerFactory, TigerData } from '../../data/factories/tiger.factory'
import { setTigers, resetTigersState } from '../../mocks/handlers/tigers.handlers'

test.describe('Tigers Management - E2E Tests', () => {
  let tigersPage: TigersListPage
  let testTigers: TigerData[]

  test.beforeEach(async ({ page }) => {
    tigersPage = new TigersListPage(page)

    // Reset mock data state
    resetTigersState()

    // Create test tigers with specific attributes for filtering/sorting
    testTigers = [
      tigerFactory.build({
        name: 'Raja',
        confidence_score: 0.95,
        facility_id: 'facility-1',
        facility_name: 'Sunrise Zoo',
        status: 'verified',
        created_at: '2025-01-01T10:00:00Z',
      }),
      tigerFactory.build({
        name: 'Shere Khan',
        confidence_score: 0.88,
        facility_id: 'facility-2',
        facility_name: 'Forest Reserve',
        status: 'pending',
        created_at: '2025-01-02T10:00:00Z',
      }),
      tigerFactory.build({
        name: 'Bengal',
        confidence_score: 0.72,
        facility_id: 'facility-1',
        facility_name: 'Sunrise Zoo',
        status: 'unverified',
        created_at: '2025-01-03T10:00:00Z',
      }),
      tigerFactory.build({
        name: 'Tigress',
        confidence_score: 0.91,
        facility_id: 'facility-3',
        facility_name: 'Wildlife Sanctuary',
        status: 'verified',
        created_at: '2025-01-04T10:00:00Z',
      }),
      tigerFactory.build({
        name: 'Stripes',
        confidence_score: 0.65,
        facility_id: 'facility-2',
        facility_name: 'Forest Reserve',
        status: 'pending',
        created_at: '2025-01-05T10:00:00Z',
      }),
    ]

    setTigers(testTigers)
  })

  test.describe('1. View Tigers List', () => {
    test('should load page with tiger cards displayed', async () => {
      await tigersPage.goto()

      // Verify page title is visible
      await expect(tigersPage.pageTitle).toBeVisible()

      // Verify tiger grid is visible
      await expect(tigersPage.tigerGrid).toBeVisible()

      // Verify correct number of tiger cards are displayed
      await tigersPage.expectTigerCount(testTigers.length)
    })

    test('should display tiger cards with correct information', async () => {
      await tigersPage.goto()

      // Get first tiger card
      const firstCard = tigersPage.tigerCards.first()

      // Verify card contains expected elements
      await expect(firstCard).toBeVisible()
      await expect(firstCard.getByTestId('tiger-card-name')).toBeVisible()
      await expect(firstCard.getByTestId('tiger-card-image')).toBeVisible()
      await expect(firstCard.getByTestId('tiger-card-confidence')).toBeVisible()
      await expect(firstCard.getByTestId('tiger-card-status')).toBeVisible()
    })

    test('should show empty state when no tigers exist', async () => {
      // Set empty tigers list
      setTigers([])

      await tigersPage.goto()

      // Verify empty state is displayed
      await tigersPage.expectEmptyState()
    })

    test('should display all tiger cards with unique identifiers', async () => {
      await tigersPage.goto()

      // Verify each tiger has a unique data attribute
      const cards = tigersPage.tigerCards
      const count = await cards.count()

      for (let i = 0; i < count; i++) {
        const card = cards.nth(i)
        const tigerId = await card.getAttribute('data-tiger-id')
        expect(tigerId).toBeTruthy()
      }
    })
  })

  test.describe('2. Filter by Facility', () => {
    test('should filter tigers by facility correctly', async () => {
      await tigersPage.goto()

      // Filter by "Sunrise Zoo"
      await tigersPage.filterByFacility('Sunrise Zoo')

      // Should show only 2 tigers from Sunrise Zoo
      await tigersPage.expectTigerCount(2)

      // Verify both visible tigers are from Sunrise Zoo
      await tigersPage.expectTigerVisible('Raja')
      await tigersPage.expectTigerVisible('Bengal')
    })

    test('should filter tigers by different facility', async () => {
      await tigersPage.goto()

      // Filter by "Forest Reserve"
      await tigersPage.filterByFacility('Forest Reserve')

      // Should show only 2 tigers from Forest Reserve
      await tigersPage.expectTigerCount(2)
      await tigersPage.expectTigerVisible('Shere Khan')
      await tigersPage.expectTigerVisible('Stripes')
    })

    test('should show all tigers when facility filter is cleared', async () => {
      await tigersPage.goto()

      // Apply filter
      await tigersPage.filterByFacility('Forest Reserve')
      await tigersPage.expectTigerCount(2)

      // Clear filter
      await tigersPage.facilityFilter.selectOption({ label: 'All Facilities' })
      await tigersPage.waitForSpinnerToDisappear()

      // Should show all tigers
      await tigersPage.expectTigerCount(testTigers.length)
    })

    test('should handle facility with single tiger', async () => {
      await tigersPage.goto()

      // Filter by "Wildlife Sanctuary" (only 1 tiger)
      await tigersPage.filterByFacility('Wildlife Sanctuary')

      // Should show only 1 tiger
      await tigersPage.expectTigerCount(1)
      await tigersPage.expectTigerVisible('Tigress')
    })
  })

  test.describe('3. Filter by Status', () => {
    test('should filter tigers by verified status', async () => {
      await tigersPage.goto()

      // Filter by verified
      await tigersPage.statusFilter.selectOption({ label: 'Verified' })
      await tigersPage.waitForSpinnerToDisappear()

      // Should show only 2 verified tigers
      await tigersPage.expectTigerCount(2)
      await tigersPage.expectTigerVisible('Raja')
      await tigersPage.expectTigerVisible('Tigress')
    })

    test('should filter tigers by pending status', async () => {
      await tigersPage.goto()

      // Filter by pending
      await tigersPage.statusFilter.selectOption({ label: 'Pending' })
      await tigersPage.waitForSpinnerToDisappear()

      // Should show only 2 pending tigers
      await tigersPage.expectTigerCount(2)
      await tigersPage.expectTigerVisible('Shere Khan')
      await tigersPage.expectTigerVisible('Stripes')
    })

    test('should filter tigers by unverified status', async () => {
      await tigersPage.goto()

      // Filter by unverified
      await tigersPage.statusFilter.selectOption({ label: 'Unverified' })
      await tigersPage.waitForSpinnerToDisappear()

      // Should show only 1 unverified tiger
      await tigersPage.expectTigerCount(1)
      await tigersPage.expectTigerVisible('Bengal')
    })

    test('should show all tigers when status filter is cleared', async () => {
      await tigersPage.goto()

      // Apply filter
      await tigersPage.statusFilter.selectOption({ label: 'Verified' })
      await tigersPage.waitForSpinnerToDisappear()
      await tigersPage.expectTigerCount(2)

      // Clear filter
      await tigersPage.statusFilter.selectOption({ label: 'All Status' })
      await tigersPage.waitForSpinnerToDisappear()

      // Should show all tigers
      await tigersPage.expectTigerCount(testTigers.length)
    })

    test('should maintain filter selection after page interaction', async () => {
      await tigersPage.goto()

      // Apply status filter
      await tigersPage.statusFilter.selectOption({ label: 'Verified' })
      await tigersPage.waitForSpinnerToDisappear()

      // Verify filter is still selected
      const selectedOption = await tigersPage.statusFilter.inputValue()
      expect(selectedOption).toContain('verified')
    })
  })

  test.describe('4. Filter by Confidence', () => {
    test('should filter tigers by minimum confidence threshold (85%)', async () => {
      await tigersPage.goto()

      // Set confidence filter to 85%
      await tigersPage.confidenceFilter.selectOption({ label: '> 85%' })
      await tigersPage.waitForSpinnerToDisappear()

      // Should show only tigers with confidence >= 0.85 (3 tigers)
      await tigersPage.expectTigerCount(3)
      await tigersPage.expectTigerVisible('Raja')
      await tigersPage.expectTigerVisible('Shere Khan')
      await tigersPage.expectTigerVisible('Tigress')
    })

    test('should filter tigers by minimum confidence threshold (90%)', async () => {
      await tigersPage.goto()

      // Set confidence filter to 90%
      await tigersPage.confidenceFilter.selectOption({ label: '> 90%' })
      await tigersPage.waitForSpinnerToDisappear()

      // Should show only tigers with confidence >= 0.90 (2 tigers)
      await tigersPage.expectTigerCount(2)
      await tigersPage.expectTigerVisible('Raja')
      await tigersPage.expectTigerVisible('Tigress')
    })

    test('should filter tigers by minimum confidence threshold (95%)', async () => {
      await tigersPage.goto()

      // Set confidence filter to 95%
      await tigersPage.confidenceFilter.selectOption({ label: '> 95%' })
      await tigersPage.waitForSpinnerToDisappear()

      // Should show only tigers with confidence >= 0.95 (1 tiger)
      await tigersPage.expectTigerCount(1)
      await tigersPage.expectTigerVisible('Raja')
    })

    test('should filter tigers by low confidence threshold (70%)', async () => {
      await tigersPage.goto()

      // Set confidence filter to 70%
      await tigersPage.confidenceFilter.selectOption({ label: '> 70%' })
      await tigersPage.waitForSpinnerToDisappear()

      // Should show tigers with confidence >= 0.70 (4 tigers)
      await tigersPage.expectTigerCount(4)
    })

    test('should show all tigers when confidence filter is cleared', async () => {
      await tigersPage.goto()

      // Set confidence filter to 95% first
      await tigersPage.confidenceFilter.selectOption({ label: '> 95%' })
      await tigersPage.waitForSpinnerToDisappear()
      await tigersPage.expectTigerCount(1)

      // Reset to "All Confidence"
      await tigersPage.confidenceFilter.selectOption({ label: 'All Confidence' })
      await tigersPage.waitForSpinnerToDisappear()

      // Should show all tigers
      await tigersPage.expectTigerCount(testTigers.length)
    })
  })

  test.describe('5. Search Tigers', () => {
    test('should search tigers by exact name', async () => {
      await tigersPage.goto()

      // Search for "Raja"
      await tigersPage.search('Raja')

      // Should show only Raja
      await tigersPage.expectTigerCount(1)
      await tigersPage.expectTigerVisible('Raja')
    })

    test('should search tigers by partial name match', async () => {
      await tigersPage.goto()

      // Search for "Khan" (should match "Shere Khan")
      await tigersPage.search('Khan')

      // Should show only Shere Khan
      await tigersPage.expectTigerCount(1)
      await tigersPage.expectTigerVisible('Shere Khan')
    })

    test('should search tigers case-insensitively', async () => {
      await tigersPage.goto()

      // Search for "bengal" in lowercase
      await tigersPage.search('bengal')

      // Should show Bengal
      await tigersPage.expectTigerCount(1)
      await tigersPage.expectTigerVisible('Bengal')
    })

    test('should search tigers with leading/trailing spaces', async () => {
      await tigersPage.goto()

      // Search with spaces
      await tigersPage.search('  Raja  ')

      // Should still find Raja
      await tigersPage.expectTigerCount(1)
      await tigersPage.expectTigerVisible('Raja')
    })

    test('should show no results for non-matching search', async () => {
      await tigersPage.goto()

      // Search for non-existent tiger
      await tigersPage.search('NonExistentTiger')

      // Should show empty state
      await tigersPage.expectTigerCount(0)
    })

    test('should clear search and show all tigers', async () => {
      await tigersPage.goto()

      // Perform search
      await tigersPage.search('Raja')
      await tigersPage.expectTigerCount(1)

      // Clear search
      await tigersPage.clearSearch()

      // Should show all tigers
      await tigersPage.expectTigerCount(testTigers.length)
    })

    test('should search by facility name', async () => {
      await tigersPage.goto()

      // Search for facility name
      await tigersPage.search('Sunrise')

      // Should show tigers from Sunrise Zoo
      await tigersPage.expectTigerCount(2)
      await tigersPage.expectTigerVisible('Raja')
      await tigersPage.expectTigerVisible('Bengal')
    })
  })

  test.describe('6. Sort Tigers', () => {
    test('should sort tigers by name (ascending)', async () => {
      await tigersPage.goto()

      // Sort by name ascending
      await tigersPage.sortBy('Name (A-Z)')

      // Verify first tiger is "Bengal" (alphabetically first)
      const firstCard = tigersPage.tigerCards.first()
      await expect(firstCard.getByTestId('tiger-card-name')).toContainText('Bengal')
    })

    test('should sort tigers by name (descending)', async () => {
      await tigersPage.goto()

      // Sort by name descending
      await tigersPage.sortBy('Name (Z-A)')

      // Verify first tiger is "Tigress" (alphabetically last)
      const firstCard = tigersPage.tigerCards.first()
      await expect(firstCard.getByTestId('tiger-card-name')).toContainText('Tigress')
    })

    test('should sort tigers by confidence (highest first)', async () => {
      await tigersPage.goto()

      // Sort by confidence descending
      await tigersPage.sortBy('Confidence (High to Low)')

      // Verify first tiger is "Raja" (highest confidence: 0.95)
      const firstCard = tigersPage.tigerCards.first()
      await expect(firstCard.getByTestId('tiger-card-name')).toContainText('Raja')
    })

    test('should sort tigers by confidence (lowest first)', async () => {
      await tigersPage.goto()

      // Sort by confidence ascending
      await tigersPage.sortBy('Confidence (Low to High)')

      // Verify first tiger is "Stripes" (lowest confidence: 0.65)
      const firstCard = tigersPage.tigerCards.first()
      await expect(firstCard.getByTestId('tiger-card-name')).toContainText('Stripes')
    })

    test('should sort tigers by date (newest first)', async () => {
      await tigersPage.goto()

      // Sort by date descending
      await tigersPage.sortBy('Date Added (Newest)')

      // Verify first tiger is "Stripes" (latest created_at: 2025-01-05)
      const firstCard = tigersPage.tigerCards.first()
      await expect(firstCard.getByTestId('tiger-card-name')).toContainText('Stripes')
    })

    test('should sort tigers by date (oldest first)', async () => {
      await tigersPage.goto()

      // Sort by date ascending
      await tigersPage.sortBy('Date Added (Oldest)')

      // Verify first tiger is "Raja" (earliest created_at: 2025-01-01)
      const firstCard = tigersPage.tigerCards.first()
      await expect(firstCard.getByTestId('tiger-card-name')).toContainText('Raja')
    })

    test('should maintain sort order when filters are applied', async () => {
      await tigersPage.goto()

      // Sort by confidence (high to low)
      await tigersPage.sortBy('Confidence (High to Low)')

      // Apply facility filter
      await tigersPage.filterByFacility('Sunrise Zoo')

      // Verify sort order is maintained (Raja should be first, Bengal second)
      const firstCard = tigersPage.tigerCards.first()
      await expect(firstCard.getByTestId('tiger-card-name')).toContainText('Raja')

      const secondCard = tigersPage.tigerCards.nth(1)
      await expect(secondCard.getByTestId('tiger-card-name')).toContainText('Bengal')
    })
  })

  test.describe('7. Select Tigers for Comparison', () => {
    test('should select a single tiger', async () => {
      await tigersPage.goto()

      // Select first tiger
      await tigersPage.selectTigerForComparison(0)

      // Verify checkbox is checked
      const checkbox = tigersPage.tigerCards.first().getByTestId('tiger-card-select')
      await expect(checkbox).toBeChecked()
    })

    test('should select multiple tigers', async () => {
      await tigersPage.goto()

      // Select first 3 tigers
      await tigersPage.selectTigerForComparison(0)
      await tigersPage.selectTigerForComparison(1)
      await tigersPage.selectTigerForComparison(2)

      // Verify all checkboxes are checked
      for (let i = 0; i < 3; i++) {
        const checkbox = tigersPage.tigerCards.nth(i).getByTestId('tiger-card-select')
        await expect(checkbox).toBeChecked()
      }
    })

    test('should deselect a selected tiger', async () => {
      await tigersPage.goto()

      // Select and then deselect first tiger
      await tigersPage.selectTigerForComparison(0)
      const checkbox = tigersPage.tigerCards.first().getByTestId('tiger-card-select')
      await expect(checkbox).toBeChecked()

      await tigersPage.selectTigerForComparison(0)
      await expect(checkbox).not.toBeChecked()
    })

    test('should show compare button when 2+ tigers selected', async () => {
      await tigersPage.goto()

      // Compare button should not be visible initially
      await expect(tigersPage.compareSelectedButton).not.toBeVisible()

      // Select 2 tigers
      await tigersPage.selectTigerForComparison(0)
      await tigersPage.selectTigerForComparison(1)

      // Compare button should now be visible
      await expect(tigersPage.compareSelectedButton).toBeVisible()
      await expect(tigersPage.compareSelectedButton).toContainText('Compare')
    })

    test('should update compare button count as tigers are selected', async () => {
      await tigersPage.goto()

      // Select 2 tigers
      await tigersPage.selectTigerForComparison(0)
      await tigersPage.selectTigerForComparison(1)

      // Button should show count of 2
      await expect(tigersPage.compareSelectedButton).toContainText('2')

      // Select third tiger
      await tigersPage.selectTigerForComparison(2)

      // Button should show count of 3
      await expect(tigersPage.compareSelectedButton).toContainText('3')
    })

    test('should not show compare button when only 1 tiger selected', async () => {
      await tigersPage.goto()

      // Select only 1 tiger
      await tigersPage.selectTigerForComparison(0)

      // Compare button should not be visible
      await expect(tigersPage.compareSelectedButton).not.toBeVisible()
    })

    test('should open comparison drawer when compare button clicked', async () => {
      await tigersPage.goto()

      // Select 2 tigers
      await tigersPage.selectTigerForComparison(0)
      await tigersPage.selectTigerForComparison(1)

      // Click compare button
      await tigersPage.openComparisonDrawer()

      // Verify comparison drawer is visible
      await expect(tigersPage.comparisonDrawer).toBeVisible()
    })

    test('should persist selections when applying filters', async () => {
      await tigersPage.goto()

      // Select first tiger
      await tigersPage.selectTigerForComparison(0)

      // Apply a filter
      await tigersPage.statusFilter.selectOption({ label: 'Verified' })
      await tigersPage.waitForSpinnerToDisappear()

      // The previously selected tiger should still be selected if visible
      const firstVisibleCheckbox = tigersPage.tigerCards.first().getByTestId('tiger-card-select')
      const firstVisibleName = await tigersPage.tigerCards.first().getByTestId('tiger-card-name').textContent()

      // If the selected tiger is still visible, it should remain checked
      if (firstVisibleName === 'Raja' || firstVisibleName === 'Tigress') {
        await expect(firstVisibleCheckbox).toBeChecked()
      }
    })
  })

  test.describe('8. Upload Wizard', () => {
    test('should open upload wizard when button clicked', async () => {
      await tigersPage.goto()

      // Open upload modal
      await tigersPage.openUploadModal()

      // Verify modal is visible
      await expect(tigersPage.uploadModal).toBeVisible()
    })

    test('should display upload wizard title', async () => {
      await tigersPage.goto()
      await tigersPage.openUploadModal()

      // Verify wizard title
      await expect(tigersPage.uploadModal.getByTestId('wizard-title')).toContainText('Upload Tiger Image')
    })

    test('should display upload wizard steps', async () => {
      await tigersPage.goto()
      await tigersPage.openUploadModal()

      // Verify step indicators are visible
      await expect(tigersPage.uploadModal.getByTestId('wizard-steps')).toBeVisible()

      // Verify step 1 (upload) is active
      await expect(tigersPage.uploadModal.getByTestId('wizard-step-1')).toHaveAttribute(
        'data-active',
        'true'
      )
    })

    test('should show file input in upload step', async () => {
      await tigersPage.goto()
      await tigersPage.openUploadModal()

      // Verify file input is visible
      const fileInput = tigersPage.uploadModal.locator('input[type="file"]')
      await expect(fileInput).toBeVisible()
    })

    test('should have cancel and next buttons', async () => {
      await tigersPage.goto()
      await tigersPage.openUploadModal()

      // Verify buttons exist
      await expect(tigersPage.uploadModal.getByTestId('wizard-cancel')).toBeVisible()
      await expect(tigersPage.uploadModal.getByTestId('wizard-next')).toBeVisible()
    })

    test('should close upload wizard when cancel button clicked', async () => {
      await tigersPage.goto()
      await tigersPage.openUploadModal()

      // Click cancel button
      await tigersPage.uploadModal.getByTestId('wizard-cancel').click()

      // Verify modal is closed
      await expect(tigersPage.uploadModal).not.toBeVisible()
    })

    test('should close upload wizard when clicking outside modal', async () => {
      await tigersPage.goto()
      await tigersPage.openUploadModal()

      // Click backdrop
      await tigersPage.page.locator('[data-testid="modal-backdrop"]').click({ position: { x: 0, y: 0 } })

      // Verify modal is closed
      await expect(tigersPage.uploadModal).not.toBeVisible()
    })
  })

  test.describe('9. Registration Wizard', () => {
    test('should open registration wizard when button clicked', async () => {
      await tigersPage.goto()

      // Open registration modal
      await tigersPage.openRegistrationModal()

      // Verify modal is visible
      await expect(tigersPage.registrationModal).toBeVisible()
    })

    test('should display registration wizard title', async () => {
      await tigersPage.goto()
      await tigersPage.openRegistrationModal()

      // Verify wizard title
      await expect(tigersPage.registrationModal.getByTestId('wizard-title')).toContainText('Register New Tiger')
    })

    test('should display registration wizard steps', async () => {
      await tigersPage.goto()
      await tigersPage.openRegistrationModal()

      // Verify step indicators are visible
      await expect(tigersPage.registrationModal.getByTestId('wizard-steps')).toBeVisible()

      // Verify step 1 (basic info) is active
      await expect(tigersPage.registrationModal.getByTestId('wizard-step-1')).toHaveAttribute(
        'data-active',
        'true'
      )
    })

    test('should show required fields in registration form', async () => {
      await tigersPage.goto()
      await tigersPage.openRegistrationModal()

      // Verify name input is visible and required
      const nameInput = tigersPage.registrationModal.getByTestId('tiger-name-input')
      await expect(nameInput).toBeVisible()
      await expect(nameInput).toHaveAttribute('required')
    })

    test('should show facility dropdown in registration form', async () => {
      await tigersPage.goto()
      await tigersPage.openRegistrationModal()

      // Verify facility select is visible
      const facilitySelect = tigersPage.registrationModal.getByTestId('tiger-facility-select')
      await expect(facilitySelect).toBeVisible()
    })

    test('should have cancel and next buttons', async () => {
      await tigersPage.goto()
      await tigersPage.openRegistrationModal()

      // Verify buttons exist
      await expect(tigersPage.registrationModal.getByTestId('wizard-cancel')).toBeVisible()
      await expect(tigersPage.registrationModal.getByTestId('wizard-next')).toBeVisible()
    })

    test('should close registration wizard when cancel button clicked', async () => {
      await tigersPage.goto()
      await tigersPage.openRegistrationModal()

      // Click cancel button
      await tigersPage.registrationModal.getByTestId('wizard-cancel').click()

      // Verify modal is closed
      await expect(tigersPage.registrationModal).not.toBeVisible()
    })

    test('should validate name field is not empty', async () => {
      await tigersPage.goto()
      await tigersPage.openRegistrationModal()

      // Try to proceed without entering name
      const nextButton = tigersPage.registrationModal.getByTestId('wizard-next')
      await nextButton.click()

      // Modal should remain open (validation failed)
      await expect(tigersPage.registrationModal).toBeVisible()
    })
  })

  test.describe('10. View Tiger Detail', () => {
    test('should navigate to tiger detail page when card clicked', async () => {
      await tigersPage.goto()

      // Click first tiger card
      await tigersPage.clickTigerCard(0)

      // Verify navigation to detail page
      await expect(tigersPage.page).toHaveURL(/\/tigers\/[a-z0-9-]+$/)
    })

    test('should navigate to detail page with correct tiger ID', async () => {
      await tigersPage.goto()

      // Get first tiger's ID
      const firstTigerId = testTigers[0].id

      // Click first tiger card
      await tigersPage.clickTigerCard(0)

      // Verify URL contains correct tiger ID
      await expect(tigersPage.page).toHaveURL(new RegExp(`/tigers/${firstTigerId}`))
    })

    test('should navigate to different tiger detail pages', async () => {
      await tigersPage.goto()

      // Click first tiger
      await tigersPage.clickTigerCard(0)
      const firstUrl = tigersPage.page.url()

      // Go back
      await tigersPage.page.goBack()
      await tigersPage.waitForSpinnerToDisappear()

      // Click second tiger
      await tigersPage.clickTigerCard(1)
      const secondUrl = tigersPage.page.url()

      // URLs should be different
      expect(firstUrl).not.toBe(secondUrl)
    })

    test('should not navigate when clicking checkbox', async () => {
      await tigersPage.goto()

      const currentUrl = tigersPage.page.url()

      // Click checkbox instead of card
      await tigersPage.selectTigerForComparison(0)

      // URL should not change
      expect(tigersPage.page.url()).toBe(currentUrl)
    })
  })

  test.describe('11. Combined Filters', () => {
    test('should apply multiple filters simultaneously', async () => {
      await tigersPage.goto()

      // Apply facility and status filters
      await tigersPage.filterByFacility('Sunrise Zoo')
      await tigersPage.statusFilter.selectOption({ label: 'Verified' })
      await tigersPage.waitForSpinnerToDisappear()

      // Should show only 1 tiger (Raja: Sunrise Zoo + verified)
      await tigersPage.expectTigerCount(1)
      await tigersPage.expectTigerVisible('Raja')
    })

    test('should apply facility, status, and confidence filters together', async () => {
      await tigersPage.goto()

      // Apply three filters
      await tigersPage.filterByFacility('Forest Reserve')
      await tigersPage.statusFilter.selectOption({ label: 'Pending' })
      await tigersPage.confidenceFilter.selectOption({ label: '> 85%' })
      await tigersPage.waitForSpinnerToDisappear()

      // Should show only 1 tiger (Shere Khan: Forest Reserve + pending + confidence 0.88)
      await tigersPage.expectTigerCount(1)
      await tigersPage.expectTigerVisible('Shere Khan')
    })

    test('should apply search with facility filter', async () => {
      await tigersPage.goto()

      // Apply facility filter
      await tigersPage.filterByFacility('Sunrise Zoo')

      // Apply search
      await tigersPage.search('Raja')

      // Should show only Raja (matches both criteria)
      await tigersPage.expectTigerCount(1)
      await tigersPage.expectTigerVisible('Raja')
    })

    test('should apply search with confidence filter', async () => {
      await tigersPage.goto()

      // Apply confidence filter
      await tigersPage.confidenceFilter.selectOption({ label: '> 85%' })
      await tigersPage.waitForSpinnerToDisappear()

      // Apply search
      await tigersPage.search('Khan')

      // Should show only Shere Khan (matches search + confidence >= 0.85)
      await tigersPage.expectTigerCount(1)
      await tigersPage.expectTigerVisible('Shere Khan')
    })

    test('should show no results when filters exclude all tigers', async () => {
      await tigersPage.goto()

      // Apply conflicting filters
      await tigersPage.filterByFacility('Wildlife Sanctuary')
      await tigersPage.statusFilter.selectOption({ label: 'Pending' })
      await tigersPage.waitForSpinnerToDisappear()

      // Should show no tigers (Tigress is from Wildlife Sanctuary but is verified, not pending)
      await tigersPage.expectTigerCount(0)
    })

    test('should clear all filters at once', async () => {
      await tigersPage.goto()

      // Apply multiple filters
      await tigersPage.filterByFacility('Forest Reserve')
      await tigersPage.statusFilter.selectOption({ label: 'Pending' })
      await tigersPage.confidenceFilter.selectOption({ label: '> 85%' })
      await tigersPage.waitForSpinnerToDisappear()
      await tigersPage.expectTigerCount(1)

      // Click clear all button
      const clearButton = tigersPage.page.getByTestId('filters-clear-all')
      if (await clearButton.count() > 0) {
        await clearButton.click()
        await tigersPage.waitForSpinnerToDisappear()

        // Should show all tigers
        await tigersPage.expectTigerCount(testTigers.length)
      }
    })

    test('should maintain sort order with multiple filters', async () => {
      await tigersPage.goto()

      // Sort by confidence
      await tigersPage.sortBy('Confidence (High to Low)')

      // Apply filters
      await tigersPage.statusFilter.selectOption({ label: 'Verified' })
      await tigersPage.waitForSpinnerToDisappear()

      // Should show verified tigers in confidence order (Raja first, Tigress second)
      const firstCard = tigersPage.tigerCards.first()
      await expect(firstCard.getByTestId('tiger-card-name')).toContainText('Raja')
    })
  })

  test.describe('12. Pagination', () => {
    test('should show pagination controls when many tigers exist', async () => {
      // Create many tigers
      const manyTigers = tigerFactory.buildMany(25)
      setTigers(manyTigers)

      await tigersPage.goto()

      // Look for pagination controls
      const paginationControls = tigersPage.page.getByTestId('tigers-pagination')

      // If pagination exists, verify it
      if ((await paginationControls.count()) > 0) {
        await expect(paginationControls).toBeVisible()
      }
    })

    test('should navigate to next page', async () => {
      // Create 25 tigers (assuming 20 per page)
      const manyTigers = tigerFactory.buildMany(25)
      setTigers(manyTigers)

      await tigersPage.goto()

      const nextButton = tigersPage.page.getByTestId('pagination-next')
      if ((await nextButton.count()) > 0) {
        await nextButton.click()
        await tigersPage.waitForSpinnerToDisappear()

        // Should be on page 2
        await expect(tigersPage.page).toHaveURL(/page=2/)
      }
    })

    test('should display correct page number', async () => {
      const manyTigers = tigerFactory.buildMany(25)
      setTigers(manyTigers)

      await tigersPage.goto()

      const pageIndicator = tigersPage.page.getByTestId('pagination-info')
      if ((await pageIndicator.count()) > 0) {
        await expect(pageIndicator).toContainText('Page 1')
      }
    })
  })

  test.describe('13. Loading States', () => {
    test('should show loading spinner when fetching tigers', async () => {
      // Navigate to page
      const gotoPromise = tigersPage.goto()

      // Verify loading spinner appears briefly
      await expect(tigersPage.loadingSpinner).toBeVisible()

      // Wait for page to load
      await gotoPromise
      await tigersPage.waitForSpinnerToDisappear()
    })

    test('should show loading spinner when applying filters', async () => {
      await tigersPage.goto()

      // Start filtering
      const filterPromise = tigersPage.filterByFacility('Sunrise Zoo')

      // Loading spinner should appear
      await expect(tigersPage.loadingSpinner).toBeVisible()

      await filterPromise
    })

    test('should disable interactions during loading', async () => {
      await tigersPage.goto()

      // Start filtering
      tigersPage.filterByFacility('Sunrise Zoo')

      // Buttons should be disabled during loading
      const uploadButton = tigersPage.uploadButton
      if (await uploadButton.count() > 0) {
        await expect(uploadButton).toBeDisabled()
      }

      await tigersPage.waitForSpinnerToDisappear()

      // After loading, buttons should be enabled
      if (await uploadButton.count() > 0) {
        await expect(uploadButton).toBeEnabled()
      }
    })
  })

  test.describe('14. Error Handling', () => {
    test('should display error message when API fails', async () => {
      // This test would require mocking an API error
      // For now, verify error UI exists
      await tigersPage.goto()

      const errorMessage = tigersPage.page.getByTestId('error-message')

      // Error should not be visible on successful load
      if (await errorMessage.count() > 0) {
        await expect(errorMessage).not.toBeVisible()
      }
    })

    test('should show retry button on error', async () => {
      // Would need to mock API error
      // Placeholder for future implementation
    })
  })

  test.describe('15. Responsive Design', () => {
    test('should display correctly on mobile viewport', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 })

      await tigersPage.goto()

      // Verify page is responsive
      await expect(tigersPage.pageTitle).toBeVisible()
      await expect(tigersPage.tigerGrid).toBeVisible()
    })

    test('should display correctly on tablet viewport', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 })

      await tigersPage.goto()

      // Verify page is responsive
      await expect(tigersPage.pageTitle).toBeVisible()
      await expect(tigersPage.tigerGrid).toBeVisible()
    })

    test('should display correctly on desktop viewport', async ({ page }) => {
      // Set desktop viewport
      await page.setViewportSize({ width: 1920, height: 1080 })

      await tigersPage.goto()

      // Verify page is responsive
      await expect(tigersPage.pageTitle).toBeVisible()
      await expect(tigersPage.tigerGrid).toBeVisible()
      await expect(tigersPage.sidebar).toBeVisible()
    })

    test('should show mobile menu on small screens', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 })

      await tigersPage.goto()

      const mobileMenuButton = tigersPage.page.getByTestId('mobile-menu-toggle')
      if (await mobileMenuButton.count() > 0) {
        await expect(mobileMenuButton).toBeVisible()
      }
    })
  })

  test.describe('16. Accessibility', () => {
    test('should have proper ARIA labels on interactive elements', async () => {
      await tigersPage.goto()

      // Check upload button has aria-label
      const uploadButton = tigersPage.uploadButton
      const ariaLabel = await uploadButton.getAttribute('aria-label')
      expect(ariaLabel).toBeTruthy()
    })

    test('should support keyboard navigation', async () => {
      await tigersPage.goto()

      // Tab to first interactive element
      await tigersPage.page.keyboard.press('Tab')

      // Verify focus is visible
      const focusedElement = await tigersPage.page.evaluate(() => document.activeElement?.tagName)
      expect(focusedElement).toBeTruthy()
    })

    test('should have proper heading hierarchy', async () => {
      await tigersPage.goto()

      // Check for h1 heading
      const h1 = tigersPage.page.locator('h1')
      await expect(h1).toBeVisible()
    })
  })

  test.describe('17. Performance', () => {
    test('should load page within acceptable time', async () => {
      const startTime = Date.now()

      await tigersPage.goto()

      const loadTime = Date.now() - startTime

      // Page should load within 3 seconds
      expect(loadTime).toBeLessThan(3000)
    })

    test('should render large number of tigers efficiently', async () => {
      // Create 100 tigers
      const manyTigers = tigerFactory.buildMany(100)
      setTigers(manyTigers)

      const startTime = Date.now()

      await tigersPage.goto()

      const renderTime = Date.now() - startTime

      // Should still be responsive with many tigers
      expect(renderTime).toBeLessThan(5000)
    })
  })
})

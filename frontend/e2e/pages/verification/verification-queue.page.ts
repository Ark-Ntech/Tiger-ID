import { Page, Locator, expect } from '@playwright/test'
import { BasePage } from '../base.page'

export class VerificationQueuePage extends BasePage {
  readonly url = '/verification'

  // Expose page for test access
  getPage(): Page {
    return this.page
  }

  // Locators
  get pageTitle(): Locator {
    return this.page.getByTestId('verification-page-title')
  }

  get pendingCount(): Locator {
    return this.page.getByTestId('verification-pending-count')
  }

  get bulkActionsDropdown(): Locator {
    return this.page.getByTestId('verification-bulk-actions')
  }

  get queueTable(): Locator {
    return this.page.getByTestId('verification-queue-table')
  }

  get queueRows(): Locator {
    return this.page.getByTestId('verification-queue-row')
  }

  get emptyState(): Locator {
    return this.page.getByTestId('empty-state')
  }

  // Filter locators
  get confidenceFilter(): Locator {
    return this.page.getByTestId('verification-filter-confidence')
  }

  get modelFilter(): Locator {
    return this.page.getByTestId('verification-filter-model')
  }

  get facilityFilter(): Locator {
    return this.page.getByTestId('verification-filter-facility')
  }

  get statusFilter(): Locator {
    return this.page.getByTestId('verification-filter-status')
  }

  // Comparison overlay
  get comparisonOverlay(): Locator {
    return this.page.getByTestId('verification-comparison-overlay')
  }

  get queryImage(): Locator {
    return this.page.getByTestId('comparison-query-image')
  }

  get matchImage(): Locator {
    return this.page.getByTestId('comparison-match-image')
  }

  get closeOverlayButton(): Locator {
    return this.page.getByTestId('comparison-close-button')
  }

  // Row action buttons
  getRowApproveButton(index: number): Locator {
    return this.queueRows.nth(index).getByTestId('verification-approve-button')
  }

  getRowRejectButton(index: number): Locator {
    return this.queueRows.nth(index).getByTestId('verification-reject-button')
  }

  getRowViewButton(index: number): Locator {
    return this.queueRows.nth(index).getByTestId('verification-view-button')
  }

  getRowCheckbox(index: number): Locator {
    return this.queueRows.nth(index).getByTestId('verification-row-checkbox')
  }

  // Model agreement badge
  getModelAgreementBadge(index: number): Locator {
    return this.queueRows.nth(index).getByTestId('model-agreement-badge')
  }

  // Actions
  async goto(): Promise<void> {
    await this.navigateTo(this.url)
  }

  async approveItem(index: number): Promise<void> {
    await this.getRowApproveButton(index).click()
    await this.waitForSpinnerToDisappear()
  }

  async rejectItem(index: number): Promise<void> {
    await this.getRowRejectButton(index).click()
    await this.waitForSpinnerToDisappear()
  }

  async viewComparison(index: number): Promise<void> {
    await this.getRowViewButton(index).click()
    await expect(this.comparisonOverlay).toBeVisible()
  }

  async closeComparison(): Promise<void> {
    await this.closeOverlayButton.click()
    await expect(this.comparisonOverlay).not.toBeVisible()
  }

  async selectRow(index: number): Promise<void> {
    await this.getRowCheckbox(index).click()
  }

  async selectAllRows(): Promise<void> {
    const selectAllCheckbox = this.page.getByTestId('verification-select-all')
    await selectAllCheckbox.click()
  }

  async bulkApprove(): Promise<void> {
    await this.bulkActionsDropdown.click()
    await this.page.getByTestId('bulk-approve-button').click()
    await this.waitForSpinnerToDisappear()
  }

  async bulkReject(): Promise<void> {
    await this.bulkActionsDropdown.click()
    await this.page.getByTestId('bulk-reject-button').click()
    await this.waitForSpinnerToDisappear()
  }

  async filterByConfidence(level: 'high' | 'medium' | 'low'): Promise<void> {
    await this.confidenceFilter.selectOption(level)
    await this.waitForSpinnerToDisappear()
  }

  async filterByModel(model: string): Promise<void> {
    await this.modelFilter.selectOption(model)
    await this.waitForSpinnerToDisappear()
  }

  // Assertions
  async expectQueueCount(count: number): Promise<void> {
    await expect(this.queueRows).toHaveCount(count)
  }

  async expectEmptyState(): Promise<void> {
    await expect(this.emptyState).toBeVisible()
  }

  async expectPendingCount(count: number): Promise<void> {
    await expect(this.pendingCount).toContainText(count.toString())
  }

  async expectComparisonVisible(): Promise<void> {
    await expect(this.comparisonOverlay).toBeVisible()
    await expect(this.queryImage).toBeVisible()
    await expect(this.matchImage).toBeVisible()
  }

  async expectModelAgreement(index: number, text: string | RegExp): Promise<void> {
    await expect(this.getModelAgreementBadge(index)).toContainText(text)
  }
}

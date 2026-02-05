import { Page, Locator, expect } from '@playwright/test'
import { BasePage } from '../base.page'

export class TigersListPage extends BasePage {
  readonly url = '/tigers'

  // Locators
  get pageTitle(): Locator {
    return this.page.getByTestId('tigers-page-title')
  }

  get searchInput(): Locator {
    return this.page.getByTestId('tigers-search-input')
  }

  get uploadButton(): Locator {
    return this.page.getByTestId('tigers-upload-button')
  }

  get registerButton(): Locator {
    return this.page.getByTestId('tigers-register-button')
  }

  get tigerGrid(): Locator {
    return this.page.getByTestId('tigers-grid')
  }

  get tigerCards(): Locator {
    return this.page.getByTestId('tiger-card')
  }

  get emptyState(): Locator {
    return this.page.getByTestId('empty-state')
  }

  // Filter locators
  get facilityFilter(): Locator {
    return this.page.getByTestId('tigers-filter-facility')
  }

  get statusFilter(): Locator {
    return this.page.getByTestId('tigers-filter-status')
  }

  get confidenceFilter(): Locator {
    return this.page.getByTestId('tigers-filter-confidence')
  }

  get sortDropdown(): Locator {
    return this.page.getByTestId('tigers-sort-dropdown')
  }

  // Modal locators
  get uploadModal(): Locator {
    return this.page.getByTestId('tiger-upload-modal')
  }

  get registrationModal(): Locator {
    return this.page.getByTestId('tiger-registration-modal')
  }

  // Comparison drawer
  get comparisonDrawer(): Locator {
    return this.page.getByTestId('tiger-comparison-drawer')
  }

  get compareSelectedButton(): Locator {
    return this.page.getByTestId('tigers-compare-selected')
  }

  // Actions
  async goto(): Promise<void> {
    await this.navigateTo(this.url)
  }

  async search(query: string): Promise<void> {
    await this.searchInput.fill(query)
    await this.page.keyboard.press('Enter')
    await this.waitForSpinnerToDisappear()
  }

  async clearSearch(): Promise<void> {
    await this.searchInput.clear()
    await this.page.keyboard.press('Enter')
    await this.waitForSpinnerToDisappear()
  }

  async openUploadModal(): Promise<void> {
    await this.uploadButton.click()
    await expect(this.uploadModal).toBeVisible()
  }

  async openRegistrationModal(): Promise<void> {
    await this.registerButton.click()
    await expect(this.registrationModal).toBeVisible()
  }

  async selectTigerForComparison(index: number): Promise<void> {
    const checkbox = this.tigerCards.nth(index).getByTestId('tiger-card-select')
    await checkbox.click()
  }

  async clickTigerCard(index: number): Promise<void> {
    await this.tigerCards.nth(index).click()
  }

  async getTigerCardByName(name: string): Promise<Locator> {
    return this.tigerGrid.locator(`[data-tiger-name="${name}"]`)
  }

  async filterByFacility(facilityName: string): Promise<void> {
    await this.facilityFilter.selectOption({ label: facilityName })
    await this.waitForSpinnerToDisappear()
  }

  async sortBy(option: string): Promise<void> {
    await this.sortDropdown.selectOption({ label: option })
    await this.waitForSpinnerToDisappear()
  }

  async openComparisonDrawer(): Promise<void> {
    await this.compareSelectedButton.click()
    await expect(this.comparisonDrawer).toBeVisible()
  }

  // Assertions
  async expectTigerCount(count: number): Promise<void> {
    await expect(this.tigerCards).toHaveCount(count)
  }

  async expectEmptyState(): Promise<void> {
    await expect(this.emptyState).toBeVisible()
  }

  async expectTigerVisible(name: string): Promise<void> {
    const card = await this.getTigerCardByName(name)
    await expect(card).toBeVisible()
  }
}

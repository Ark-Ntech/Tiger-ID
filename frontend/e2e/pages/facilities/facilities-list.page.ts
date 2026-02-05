import { Page, Locator, expect } from '@playwright/test'
import { BasePage } from '../base.page'

export class FacilitiesListPage extends BasePage {
  readonly url = '/facilities'

  // Locators
  get pageTitle(): Locator {
    return this.page.getByTestId('facilities-page-title')
  }

  get searchInput(): Locator {
    return this.page.getByTestId('facilities-search-input')
  }

  get addFacilityButton(): Locator {
    return this.page.getByTestId('facilities-add-button')
  }

  get facilitiesGrid(): Locator {
    return this.page.getByTestId('facilities-grid')
  }

  get facilityCards(): Locator {
    return this.page.getByTestId('facility-card')
  }

  get emptyState(): Locator {
    return this.page.getByTestId('empty-state')
  }

  // Map view
  get mapViewToggle(): Locator {
    return this.page.getByTestId('facilities-map-toggle')
  }

  get mapView(): Locator {
    return this.page.getByTestId('facilities-map')
  }

  get mapMarkers(): Locator {
    return this.page.locator('.leaflet-marker-icon')
  }

  // Filter locators
  get countryFilter(): Locator {
    return this.page.getByTestId('facilities-filter-country')
  }

  get statusFilter(): Locator {
    return this.page.getByTestId('facilities-filter-status')
  }

  get discoveryStatusFilter(): Locator {
    return this.page.getByTestId('facilities-filter-discovery')
  }

  // Modal locators
  get addFacilityModal(): Locator {
    return this.page.getByTestId('add-facility-modal')
  }

  get facilityNameInput(): Locator {
    return this.page.getByTestId('facility-name-input')
  }

  get facilityUrlInput(): Locator {
    return this.page.getByTestId('facility-url-input')
  }

  get facilityCountryInput(): Locator {
    return this.page.getByTestId('facility-country-input')
  }

  get facilityCoordinatesInput(): Locator {
    return this.page.getByTestId('facility-coordinates-input')
  }

  get saveFacilityButton(): Locator {
    return this.page.getByTestId('facility-save-button')
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

  async openAddFacilityModal(): Promise<void> {
    await this.addFacilityButton.click()
    await expect(this.addFacilityModal).toBeVisible()
  }

  async addFacility(name: string, url: string, country?: string, coordinates?: string): Promise<void> {
    await this.openAddFacilityModal()
    await this.facilityNameInput.fill(name)
    await this.facilityUrlInput.fill(url)
    if (country) await this.facilityCountryInput.fill(country)
    if (coordinates) await this.facilityCoordinatesInput.fill(coordinates)
    await this.saveFacilityButton.click()
    await this.waitForSpinnerToDisappear()
  }

  async clickFacilityCard(index: number): Promise<void> {
    await this.facilityCards.nth(index).click()
  }

  async getFacilityCardByName(name: string): Promise<Locator> {
    return this.facilitiesGrid.locator(`[data-facility-name="${name}"]`)
  }

  async toggleMapView(): Promise<void> {
    await this.mapViewToggle.click()
  }

  async filterByCountry(country: string): Promise<void> {
    await this.countryFilter.selectOption({ label: country })
    await this.waitForSpinnerToDisappear()
  }

  async filterByDiscoveryStatus(status: 'active' | 'paused' | 'error'): Promise<void> {
    await this.discoveryStatusFilter.selectOption(status)
    await this.waitForSpinnerToDisappear()
  }

  // Assertions
  async expectFacilityCount(count: number): Promise<void> {
    await expect(this.facilityCards).toHaveCount(count)
  }

  async expectEmptyState(): Promise<void> {
    await expect(this.emptyState).toBeVisible()
  }

  async expectFacilityVisible(name: string): Promise<void> {
    const card = await this.getFacilityCardByName(name)
    await expect(card).toBeVisible()
  }

  async expectMapVisible(): Promise<void> {
    await expect(this.mapView).toBeVisible()
  }

  async expectMarkerCount(count: number): Promise<void> {
    await expect(this.mapMarkers).toHaveCount(count)
  }
}

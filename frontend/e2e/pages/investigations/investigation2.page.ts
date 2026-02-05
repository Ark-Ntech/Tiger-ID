import { Page, Locator, expect } from '@playwright/test'
import { BasePage } from '../base.page'

export class Investigation2Page extends BasePage {
  readonly url = '/investigation2'

  // Upload section locators
  get uploadZone(): Locator {
    return this.page.getByTestId('investigation-upload-zone')
  }

  get imagePreview(): Locator {
    return this.page.getByTestId('investigation-image-preview')
  }

  get locationInput(): Locator {
    return this.page.getByTestId('investigation-location-input')
  }

  get dateInput(): Locator {
    return this.page.getByTestId('investigation-date-input')
  }

  get notesInput(): Locator {
    return this.page.getByTestId('investigation-notes-input')
  }

  get launchButton(): Locator {
    return this.page.getByTestId('investigation-launch-button')
  }

  // Progress section locators
  get progressTimeline(): Locator {
    return this.page.getByTestId('investigation-progress-timeline')
  }

  get modelProgressGrid(): Locator {
    return this.page.getByTestId('model-progress-grid')
  }

  get activityFeed(): Locator {
    return this.page.getByTestId('investigation-activity-feed')
  }

  // Results section locators
  get resultsSection(): Locator {
    return this.page.getByTestId('investigation-results')
  }

  get tabNav(): Locator {
    return this.page.getByTestId('investigation-tab-nav')
  }

  get overviewTab(): Locator {
    return this.page.getByTestId('results-tab-overview')
  }

  get detectionTab(): Locator {
    return this.page.getByTestId('results-tab-detection')
  }

  get matchingTab(): Locator {
    return this.page.getByTestId('results-tab-matching')
  }

  get verificationTab(): Locator {
    return this.page.getByTestId('results-tab-verification')
  }

  get methodologyTab(): Locator {
    return this.page.getByTestId('results-tab-methodology')
  }

  // Match cards
  get matchCards(): Locator {
    return this.page.getByTestId('match-card')
  }

  // Report section
  get reportSection(): Locator {
    return this.page.getByTestId('investigation-report')
  }

  get audienceSelect(): Locator {
    return this.page.getByTestId('report-audience-select')
  }

  get regenerateButton(): Locator {
    return this.page.getByTestId('report-regenerate-button')
  }

  get downloadButton(): Locator {
    return this.page.getByTestId('report-download-button')
  }

  // Error state
  get errorState(): Locator {
    return this.page.getByTestId('error-state')
  }

  get retryButton(): Locator {
    return this.page.getByTestId('error-state-retry')
  }

  // Actions
  async goto(): Promise<void> {
    await this.navigateTo(this.url)
  }

  async uploadImage(filePath: string): Promise<void> {
    const fileInput = this.page.locator('input[type="file"]')
    await fileInput.setInputFiles(filePath)
    await expect(this.imagePreview).toBeVisible()
  }

  async fillContext(location: string, date: string, notes: string): Promise<void> {
    if (location) await this.locationInput.fill(location)
    if (date) await this.dateInput.fill(date)
    if (notes) await this.notesInput.fill(notes)
  }

  async launchInvestigation(): Promise<void> {
    await this.launchButton.click()
  }

  async launchAndWait(filePath: string, context?: { location?: string; date?: string; notes?: string }): Promise<void> {
    await this.uploadImage(filePath)
    if (context) {
      await this.fillContext(context.location || '', context.date || '', context.notes || '')
    }
    await this.launchInvestigation()
    // Wait for progress to start
    await expect(this.progressTimeline).toBeVisible({ timeout: 10000 })
  }

  async waitForCompletion(timeout: number = 120000): Promise<void> {
    // Wait for results section to appear
    await expect(this.resultsSection).toBeVisible({ timeout })
  }

  async selectTab(tabName: 'overview' | 'detection' | 'matching' | 'verification' | 'methodology'): Promise<void> {
    await this.page.getByTestId(`results-tab-${tabName}`).click()
  }

  async changeReportAudience(audience: 'law_enforcement' | 'conservation' | 'internal' | 'public'): Promise<void> {
    await this.audienceSelect.selectOption(audience)
  }

  async regenerateReport(): Promise<void> {
    await this.regenerateButton.click()
    await this.waitForSpinnerToDisappear()
  }

  async downloadReport(): Promise<void> {
    await this.downloadButton.click()
  }

  async clickMatchCard(index: number): Promise<void> {
    await this.matchCards.nth(index).click()
  }

  async retryAfterError(): Promise<void> {
    await this.retryButton.click()
  }

  // Progress tracking
  async getPhaseStatus(phase: string): Promise<string | null> {
    const phaseElement = this.progressTimeline.locator(`[data-phase="${phase}"]`)
    return await phaseElement.getAttribute('data-status')
  }

  async waitForPhase(phase: string, status: 'completed' | 'running' | 'error', timeout: number = 60000): Promise<void> {
    const phaseElement = this.progressTimeline.locator(`[data-phase="${phase}"]`)
    await expect(phaseElement).toHaveAttribute('data-status', status, { timeout })
  }

  // Model progress
  async getModelProgress(modelName: string): Promise<number> {
    const modelElement = this.modelProgressGrid.locator(`[data-model="${modelName}"]`)
    const progressText = await modelElement.locator('.progress-value').textContent()
    return parseInt(progressText || '0', 10)
  }

  // Assertions
  async expectImageUploaded(): Promise<void> {
    await expect(this.imagePreview).toBeVisible()
  }

  async expectInProgress(): Promise<void> {
    await expect(this.progressTimeline).toBeVisible()
  }

  async expectCompleted(): Promise<void> {
    await expect(this.resultsSection).toBeVisible()
  }

  async expectError(): Promise<void> {
    await expect(this.errorState).toBeVisible()
  }

  async expectMatchCount(count: number): Promise<void> {
    await expect(this.matchCards).toHaveCount(count)
  }
}

import { Page, Locator, expect } from '@playwright/test'

export class ModalComponent {
  constructor(
    private readonly page: Page,
    private readonly testId: string = 'modal'
  ) {}

  get overlay(): Locator {
    return this.page.getByTestId(`${this.testId}-overlay`)
  }

  get content(): Locator {
    return this.page.getByTestId(`${this.testId}-content`)
  }

  get title(): Locator {
    return this.page.getByTestId(`${this.testId}-title`)
  }

  get closeButton(): Locator {
    return this.page.getByTestId(`${this.testId}-close`)
  }

  get confirmButton(): Locator {
    return this.page.getByTestId(`${this.testId}-confirm`)
  }

  get cancelButton(): Locator {
    return this.page.getByTestId(`${this.testId}-cancel`)
  }

  async close(): Promise<void> {
    await this.closeButton.click()
    await this.expectClosed()
  }

  async confirm(): Promise<void> {
    await this.confirmButton.click()
  }

  async cancel(): Promise<void> {
    await this.cancelButton.click()
    await this.expectClosed()
  }

  async clickOutside(): Promise<void> {
    await this.overlay.click({ position: { x: 10, y: 10 } })
  }

  async expectOpen(): Promise<void> {
    await expect(this.content).toBeVisible()
  }

  async expectClosed(): Promise<void> {
    await expect(this.content).not.toBeVisible()
  }

  async expectTitle(title: string): Promise<void> {
    await expect(this.title).toContainText(title)
  }
}

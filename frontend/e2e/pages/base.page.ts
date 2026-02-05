import { Page, Locator, expect } from '@playwright/test'

export abstract class BasePage {
  constructor(protected readonly page: Page) {}

  // Common locators
  get header(): Locator {
    return this.page.getByTestId('header')
  }

  get sidebar(): Locator {
    return this.page.getByTestId('sidebar')
  }

  get loadingSpinner(): Locator {
    return this.page.getByTestId('loading-spinner')
  }

  // Common actions
  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle')
  }

  async waitForSpinnerToDisappear(): Promise<void> {
    await expect(this.loadingSpinner).not.toBeVisible({ timeout: 30000 })
  }

  async navigateTo(path: string): Promise<void> {
    await this.page.goto(path)
    await this.waitForPageLoad()
  }

  async clickNavLink(name: string): Promise<void> {
    await this.sidebar.getByTestId(`sidebar-nav-${name.toLowerCase()}`).click()
    await this.waitForPageLoad()
  }

  async getToast(): Promise<Locator> {
    return this.page.getByTestId('toast')
  }

  async expectToastWithText(text: string | RegExp): Promise<void> {
    const toast = await this.getToast()
    await expect(toast).toBeVisible()
    await expect(toast).toContainText(text)
  }

  // Screenshot helper
  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({ path: `screenshots/${name}.png` })
  }
}

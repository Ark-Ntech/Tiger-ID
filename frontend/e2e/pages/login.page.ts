import { Page, Locator, expect } from '@playwright/test'
import { BasePage } from './base.page'

export class LoginPage extends BasePage {
  readonly url = '/login'

  // Locators
  get usernameInput(): Locator {
    return this.page.getByTestId('login-username-input')
  }

  get passwordInput(): Locator {
    return this.page.getByTestId('login-password-input')
  }

  get submitButton(): Locator {
    return this.page.getByTestId('login-submit-button')
  }

  get errorMessage(): Locator {
    return this.page.getByTestId('login-error')
  }

  get forgotPasswordLink(): Locator {
    return this.page.getByTestId('login-forgot-password')
  }

  // Actions
  async goto(): Promise<void> {
    await this.navigateTo(this.url)
  }

  async login(username: string, password: string): Promise<void> {
    await this.usernameInput.fill(username)
    await this.passwordInput.fill(password)
    await this.submitButton.click()
  }

  async loginAndWait(username: string, password: string): Promise<void> {
    await this.login(username, password)
    await this.waitForPageLoad()
    // Wait for redirect away from login page
    await expect(this.page).not.toHaveURL(/\/login/)
  }

  // Assertions
  async expectErrorMessage(message: string): Promise<void> {
    await expect(this.errorMessage).toBeVisible()
    await expect(this.errorMessage).toContainText(message)
  }

  async expectToBeOnLoginPage(): Promise<void> {
    await expect(this.page).toHaveURL(/\/login/)
    await expect(this.usernameInput).toBeVisible()
  }
}

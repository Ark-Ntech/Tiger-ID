import { Page, Locator, expect } from '@playwright/test'

export class HeaderComponent {
  constructor(private readonly page: Page) {}

  get container(): Locator {
    return this.page.getByTestId('header')
  }

  get logo(): Locator {
    return this.page.getByTestId('header-logo')
  }

  get userMenu(): Locator {
    return this.page.getByTestId('header-user-menu')
  }

  get userAvatar(): Locator {
    return this.page.getByTestId('header-user-avatar')
  }

  get logoutButton(): Locator {
    return this.page.getByTestId('header-logout-button')
  }

  get notificationBell(): Locator {
    return this.page.getByTestId('header-notifications')
  }

  get notificationBadge(): Locator {
    return this.page.getByTestId('header-notification-badge')
  }

  async openUserMenu(): Promise<void> {
    await this.userMenu.click()
  }

  async logout(): Promise<void> {
    await this.openUserMenu()
    await this.logoutButton.click()
  }

  async openNotifications(): Promise<void> {
    await this.notificationBell.click()
  }

  async expectNotificationCount(count: number): Promise<void> {
    if (count > 0) {
      await expect(this.notificationBadge).toContainText(count.toString())
    } else {
      await expect(this.notificationBadge).not.toBeVisible()
    }
  }
}

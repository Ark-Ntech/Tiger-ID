import { Page, Locator, expect } from '@playwright/test'

export class SidebarComponent {
  constructor(private readonly page: Page) {}

  get container(): Locator {
    return this.page.getByTestId('sidebar')
  }

  get logo(): Locator {
    return this.page.getByTestId('sidebar-logo')
  }

  get version(): Locator {
    return this.page.getByTestId('sidebar-version')
  }

  getNavLink(name: string): Locator {
    return this.page.getByTestId(`sidebar-nav-${name.toLowerCase()}`)
  }

  async navigateTo(name: string): Promise<void> {
    await this.getNavLink(name).click()
  }

  async expectActiveLink(name: string): Promise<void> {
    const link = this.getNavLink(name)
    await expect(link).toHaveClass(/bg-tiger-orange/)
  }

  async expectNavLinks(links: string[]): Promise<void> {
    for (const link of links) {
      await expect(this.getNavLink(link)).toBeVisible()
    }
  }
}

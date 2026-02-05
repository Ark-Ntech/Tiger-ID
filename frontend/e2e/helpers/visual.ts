import { Page } from '@playwright/test'

/**
 * Visual Regression Testing Helpers
 *
 * Utilities for consistent visual regression testing across the application.
 */

// Standard viewport sizes for testing
export const VIEWPORTS = {
  desktop: { width: 1920, height: 1080 },
  desktopSmall: { width: 1366, height: 768 },
  tablet: { width: 768, height: 1024 },
  tabletLandscape: { width: 1024, height: 768 },
  mobile: { width: 375, height: 667 },
  mobileLarge: { width: 414, height: 896 },
} as const

export type ViewportName = keyof typeof VIEWPORTS

/**
 * Toggle dark mode on/off for the page
 */
export async function toggleDarkMode(page: Page, enable: boolean): Promise<void> {
  await page.evaluate((enabled) => {
    if (enabled) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }, enable)

  // Wait for CSS transitions to complete
  await page.waitForTimeout(300)
}

/**
 * Wait for page to fully load including network requests and animations
 */
export async function waitForPageLoad(page: Page, options?: {
  timeout?: number
  additionalDelay?: number
}): Promise<void> {
  const { timeout = 30000, additionalDelay = 500 } = options || {}

  await page.waitForLoadState('networkidle', { timeout })
  await page.waitForLoadState('domcontentloaded', { timeout })

  // Additional buffer for animations and transitions
  if (additionalDelay > 0) {
    await page.waitForTimeout(additionalDelay)
  }
}

/**
 * Hide dynamic content that changes between test runs
 * (timestamps, animated elements, random IDs, etc.)
 */
export async function hideDynamicContent(page: Page): Promise<void> {
  await page.evaluate(() => {
    // Hide elements with timestamps
    const timeElements = document.querySelectorAll('[data-timestamp], .timestamp, time')
    timeElements.forEach((el) => {
      if (el instanceof HTMLElement) {
        el.style.visibility = 'hidden'
      }
    })

    // Hide animated spinners and loaders
    const loaders = document.querySelectorAll('.animate-spin, .animate-pulse')
    loaders.forEach((el) => {
      if (el instanceof HTMLElement) {
        el.style.visibility = 'hidden'
      }
    })

    // Pause all CSS animations
    const style = document.createElement('style')
    const textNode = document.createTextNode('* { animation-duration: 0s !important; transition-duration: 0s !important; }')
    style.appendChild(textNode)
    document.head.appendChild(style)
  })

  await page.waitForTimeout(100)
}

/**
 * Mask specific elements to prevent visual regression failures from dynamic content
 */
export async function maskElements(page: Page, selectors: string[]): Promise<void> {
  for (const selector of selectors) {
    const elements = page.locator(selector)
    const count = await elements.count()

    for (let i = 0; i < count; i++) {
      await elements.nth(i).evaluate((el) => {
        if (el instanceof HTMLElement) {
          el.style.backgroundColor = '#cccccc'
          el.style.color = 'transparent'
        }
      })
    }
  }
}

/**
 * Scroll page to element before taking screenshot
 */
export async function scrollToElement(page: Page, selector: string): Promise<void> {
  const element = page.locator(selector).first()
  if (await element.count() > 0) {
    await element.scrollIntoViewIfNeeded()
    await page.waitForTimeout(300)
  }
}

/**
 * Set viewport to specific device size
 */
export async function setViewport(page: Page, viewport: ViewportName): Promise<void> {
  await page.setViewportSize(VIEWPORTS[viewport])
  await page.waitForTimeout(200)
}

/**
 * Take a full page screenshot with consistent settings
 */
export async function takeFullPageScreenshot(
  page: Page,
  path: string,
  options?: {
    mask?: string[]
    hideDynamic?: boolean
  }
): Promise<Buffer> {
  const { mask = [], hideDynamic = false } = options || {}

  if (hideDynamic) {
    await hideDynamicContent(page)
  }

  if (mask.length > 0) {
    await maskElements(page, mask)
  }

  return await page.screenshot({
    path,
    fullPage: true,
    animations: 'disabled',
  })
}

/**
 * Take a component screenshot with consistent settings
 */
export async function takeComponentScreenshot(
  page: Page,
  selector: string,
  path: string,
  options?: {
    mask?: string[]
    hideDynamic?: boolean
  }
): Promise<Buffer | null> {
  const element = page.locator(selector).first()

  if (await element.count() === 0) {
    return null
  }

  const { mask = [], hideDynamic = false } = options || {}

  if (hideDynamic) {
    await hideDynamicContent(page)
  }

  if (mask.length > 0) {
    await maskElements(page, mask)
  }

  await scrollToElement(page, selector)

  return await element.screenshot({
    path,
    animations: 'disabled',
  })
}

/**
 * Generate screenshot name based on test context
 */
export function generateScreenshotName(options: {
  page: string
  state: string
  viewport?: ViewportName
  theme?: 'light' | 'dark'
  variant?: string
}): string {
  const { page, state, viewport, theme, variant } = options
  const parts = [page, state]

  if (viewport) parts.push(viewport)
  if (theme) parts.push(theme)
  if (variant) parts.push(variant)

  return `${parts.join('-')}.png`
}

/**
 * Compare two screenshots for visual differences
 * Returns true if screenshots match within threshold
 */
export async function compareScreenshots(
  screenshot1: Buffer,
  screenshot2: Buffer,
  threshold: number = 0.01
): Promise<boolean> {
  // This is a placeholder - Playwright handles snapshot comparison automatically
  // with toMatchSnapshot(). This function is here for reference if you need
  // custom comparison logic in the future.
  return true
}

/**
 * Wait for all images on page to load
 */
export async function waitForImages(page: Page): Promise<void> {
  await page.evaluate(async () => {
    const images = Array.from(document.querySelectorAll('img'))
    await Promise.all(
      images.map((img) => {
        if (img.complete) return Promise.resolve()
        return new Promise((resolve) => {
          img.addEventListener('load', () => resolve(null))
          img.addEventListener('error', () => resolve(null))
        })
      })
    )
  })
}

/**
 * Wait for all fonts to load
 */
export async function waitForFonts(page: Page): Promise<void> {
  await page.evaluate(async () => {
    await document.fonts.ready
  })
}

/**
 * Disable animations for consistent screenshots
 */
export async function disableAnimations(page: Page): Promise<void> {
  await page.addStyleTag({
    content: `
      *,
      *::before,
      *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
        transition-delay: 0s !important;
      }
    `,
  })
}

/**
 * Prepare page for visual regression testing
 * Combines multiple helpers for consistent setup
 */
export async function prepareForVisualTest(
  page: Page,
  options?: {
    viewport?: ViewportName
    darkMode?: boolean
    disableAnimations?: boolean
    waitForImages?: boolean
    waitForFonts?: boolean
  }
): Promise<void> {
  const {
    viewport = 'desktop',
    darkMode = false,
    disableAnimations: shouldDisableAnimations = true,
    waitForImages: shouldWaitForImages = true,
    waitForFonts: shouldWaitForFonts = true,
  } = options || {}

  // Set viewport
  await setViewport(page, viewport)

  // Set theme
  await toggleDarkMode(page, darkMode)

  // Disable animations
  if (shouldDisableAnimations) {
    await disableAnimations(page)
  }

  // Wait for content to load
  await waitForPageLoad(page)

  if (shouldWaitForImages) {
    await waitForImages(page)
  }

  if (shouldWaitForFonts) {
    await waitForFonts(page)
  }
}

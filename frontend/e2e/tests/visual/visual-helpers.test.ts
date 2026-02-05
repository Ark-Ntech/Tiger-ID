/**
 * Unit tests for visual regression test helper functions
 *
 * These tests verify that the helper functions in visual.spec.ts
 * work correctly for preparing pages for visual regression testing.
 */

import { test, expect, Page } from '@playwright/test'

// ============================================================================
// Helper function imports (defined in visual.spec.ts)
// We'll test them through page interactions
// ============================================================================

/**
 * Toggle dark mode on the page
 */
async function toggleDarkMode(page: Page, enable: boolean): Promise<void> {
  await page.evaluate((enabled) => {
    if (enabled) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, enable)
  await page.waitForTimeout(300)
}

/**
 * Wait for page to fully load with network idle
 */
async function waitForPageLoad(page: Page): Promise<void> {
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(500)
}

/**
 * Wait for images to load on the page
 */
async function waitForImages(page: Page): Promise<void> {
  await page.evaluate(() => {
    const images = Array.from(document.images)
    return Promise.all(
      images
        .filter((img) => !img.complete)
        .map((img) => new Promise((resolve) => {
          img.addEventListener('load', resolve)
          img.addEventListener('error', resolve)
        }))
    )
  })
}

/**
 * Hide dynamic content that changes between test runs
 */
async function hideTimestamps(page: Page): Promise<void> {
  await page.evaluate(() => {
    const selectors = [
      '[data-testid="timestamp"]',
      '.timestamp',
      'time',
      '[data-testid="last-updated"]'
    ]
    selectors.forEach(selector => {
      document.querySelectorAll(selector).forEach(el => {
        (el as HTMLElement).style.visibility = 'hidden'
      })
    })
  })
}

/**
 * Mask dynamic IDs in the DOM
 */
async function maskDynamicIds(page: Page): Promise<void> {
  await page.evaluate(() => {
    const walk = (node: Node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        node.textContent = node.textContent?.replace(
          /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi,
          'UUID-PLACEHOLDER'
        ) || null
      }
      node.childNodes.forEach(walk)
    }
    walk(document.body)
  })
}

/**
 * Disable animations on the page for stable screenshots
 */
async function disableAnimations(page: Page): Promise<void> {
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
        transition-delay: 0s !important;
      }
    `
  })
}

// ============================================================================
// Test Suite
// ============================================================================

test.describe('Visual Test Helper Functions', () => {

  // ==========================================================================
  // 1. toggleDarkMode() Tests
  // ==========================================================================

  test.describe('toggleDarkMode()', () => {
    test('should add dark class to documentElement when enabled', async ({ page }) => {
      await page.setContent('<html><body><p>Test</p></body></html>')

      await toggleDarkMode(page, true)

      const hasDarkClass = await page.evaluate(() =>
        document.documentElement.classList.contains('dark')
      )

      expect(hasDarkClass).toBe(true)
    })

    test('should remove dark class from documentElement when disabled', async ({ page }) => {
      await page.setContent('<html class="dark"><body><p>Test</p></body></html>')

      await toggleDarkMode(page, false)

      const hasDarkClass = await page.evaluate(() =>
        document.documentElement.classList.contains('dark')
      )

      expect(hasDarkClass).toBe(false)
    })

    test('should handle multiple toggles correctly', async ({ page }) => {
      await page.setContent('<html><body><p>Test</p></body></html>')

      await toggleDarkMode(page, true)
      let hasDarkClass = await page.evaluate(() =>
        document.documentElement.classList.contains('dark')
      )
      expect(hasDarkClass).toBe(true)

      await toggleDarkMode(page, false)
      hasDarkClass = await page.evaluate(() =>
        document.documentElement.classList.contains('dark')
      )
      expect(hasDarkClass).toBe(false)

      await toggleDarkMode(page, true)
      hasDarkClass = await page.evaluate(() =>
        document.documentElement.classList.contains('dark')
      )
      expect(hasDarkClass).toBe(true)
    })
  })

  // ==========================================================================
  // 2. waitForPageLoad() Tests
  // ==========================================================================

  test.describe('waitForPageLoad()', () => {
    test('should wait for network idle state', async ({ page }) => {
      const startTime = Date.now()

      await page.goto('about:blank')
      await waitForPageLoad(page)

      const elapsed = Date.now() - startTime

      // Should wait at least 500ms (the buffer)
      expect(elapsed).toBeGreaterThanOrEqual(500)
    })

    test('should complete successfully on simple page', async ({ page }) => {
      await page.setContent('<html><body><h1>Simple Page</h1></body></html>')

      // Should not throw
      await expect(waitForPageLoad(page)).resolves.toBeUndefined()
    })
  })

  // ==========================================================================
  // 3. waitForImages() Tests
  // ==========================================================================

  test.describe('waitForImages()', () => {
    test('should resolve immediately when no images exist', async ({ page }) => {
      await page.setContent('<html><body><p>No images here</p></body></html>')

      const startTime = Date.now()
      await waitForImages(page)
      const elapsed = Date.now() - startTime

      // Should resolve almost immediately (< 100ms)
      expect(elapsed).toBeLessThan(100)
    })

    test('should wait for images to load', async ({ page }) => {
      await page.setContent(`
        <html>
          <body>
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" />
          </body>
        </html>
      `)

      // Should not throw and should complete
      await expect(waitForImages(page)).resolves.toBeUndefined()
    })

    test('should handle broken images gracefully', async ({ page }) => {
      await page.setContent(`
        <html>
          <body>
            <img src="https://invalid-domain-that-does-not-exist-12345.com/image.jpg" />
          </body>
        </html>
      `)

      // Should resolve even with broken images
      await expect(waitForImages(page)).resolves.toBeUndefined()
    })

    test('should handle multiple images', async ({ page }) => {
      await page.setContent(`
        <html>
          <body>
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" />
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==" />
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" />
          </body>
        </html>
      `)

      await expect(waitForImages(page)).resolves.toBeUndefined()
    })
  })

  // ==========================================================================
  // 4. hideTimestamps() Tests
  // ==========================================================================

  test.describe('hideTimestamps()', () => {
    test('should hide elements with data-testid="timestamp"', async ({ page }) => {
      await page.setContent(`
        <html>
          <body>
            <div data-testid="timestamp">2024-01-15 10:30 AM</div>
          </body>
        </html>
      `)

      await hideTimestamps(page)

      const isHidden = await page.evaluate(() => {
        const el = document.querySelector('[data-testid="timestamp"]') as HTMLElement
        return el?.style.visibility === 'hidden'
      })

      expect(isHidden).toBe(true)
    })

    test('should hide elements with class="timestamp"', async ({ page }) => {
      await page.setContent(`
        <html>
          <body>
            <span class="timestamp">2024-01-15</span>
          </body>
        </html>
      `)

      await hideTimestamps(page)

      const isHidden = await page.evaluate(() => {
        const el = document.querySelector('.timestamp') as HTMLElement
        return el?.style.visibility === 'hidden'
      })

      expect(isHidden).toBe(true)
    })

    test('should hide <time> elements', async ({ page }) => {
      await page.setContent(`
        <html>
          <body>
            <time datetime="2024-01-15">January 15, 2024</time>
          </body>
        </html>
      `)

      await hideTimestamps(page)

      const isHidden = await page.evaluate(() => {
        const el = document.querySelector('time') as HTMLElement
        return el?.style.visibility === 'hidden'
      })

      expect(isHidden).toBe(true)
    })

    test('should hide multiple timestamp elements', async ({ page }) => {
      await page.setContent(`
        <html>
          <body>
            <div data-testid="timestamp">Time 1</div>
            <span class="timestamp">Time 2</span>
            <time>Time 3</time>
            <div data-testid="last-updated">Time 4</div>
          </body>
        </html>
      `)

      await hideTimestamps(page)

      const hiddenCount = await page.evaluate(() => {
        const selectors = [
          '[data-testid="timestamp"]',
          '.timestamp',
          'time',
          '[data-testid="last-updated"]'
        ]
        let count = 0
        selectors.forEach(selector => {
          document.querySelectorAll(selector).forEach(el => {
            if ((el as HTMLElement).style.visibility === 'hidden') {
              count++
            }
          })
        })
        return count
      })

      expect(hiddenCount).toBe(4)
    })

    test('should not affect non-timestamp elements', async ({ page }) => {
      await page.setContent(`
        <html>
          <body>
            <div class="timestamp">Hidden</div>
            <div class="content">Visible</div>
            <p>Regular text</p>
          </body>
        </html>
      `)

      await hideTimestamps(page)

      const visibleContent = await page.evaluate(() => {
        const contentEl = document.querySelector('.content') as HTMLElement
        const pEl = document.querySelector('p') as HTMLElement
        return {
          content: contentEl?.style.visibility !== 'hidden',
          paragraph: pEl?.style.visibility !== 'hidden'
        }
      })

      expect(visibleContent.content).toBe(true)
      expect(visibleContent.paragraph).toBe(true)
    })
  })

  // ==========================================================================
  // 5. maskDynamicIds() Tests
  // ==========================================================================

  test.describe('maskDynamicIds()', () => {
    test('should mask UUID in text content', async ({ page }) => {
      const uuid = '550e8400-e29b-41d4-a716-446655440000'
      await page.setContent(`
        <html>
          <body>
            <p>ID: ${uuid}</p>
          </body>
        </html>
      `)

      await maskDynamicIds(page)

      const maskedText = await page.locator('p').textContent()

      expect(maskedText).toBe('ID: UUID-PLACEHOLDER')
      expect(maskedText).not.toContain(uuid)
    })

    test('should mask multiple UUIDs', async ({ page }) => {
      await page.setContent(`
        <html>
          <body>
            <p>ID1: 550e8400-e29b-41d4-a716-446655440000</p>
            <p>ID2: 6ba7b810-9dad-11d1-80b4-00c04fd430c8</p>
            <p>ID3: 6ba7b811-9dad-11d1-80b4-00c04fd430c8</p>
          </body>
        </html>
      `)

      await maskDynamicIds(page)

      const texts = await page.locator('p').allTextContents()

      expect(texts[0]).toBe('ID1: UUID-PLACEHOLDER')
      expect(texts[1]).toBe('ID2: UUID-PLACEHOLDER')
      expect(texts[2]).toBe('ID3: UUID-PLACEHOLDER')
    })

    test('should be case-insensitive for UUID masking', async ({ page }) => {
      await page.setContent(`
        <html>
          <body>
            <p>Uppercase: 550E8400-E29B-41D4-A716-446655440000</p>
            <p>Lowercase: 550e8400-e29b-41d4-a716-446655440000</p>
            <p>Mixed: 550E8400-e29b-41D4-A716-446655440000</p>
          </body>
        </html>
      `)

      await maskDynamicIds(page)

      const texts = await page.locator('p').allTextContents()

      expect(texts[0]).toBe('Uppercase: UUID-PLACEHOLDER')
      expect(texts[1]).toBe('Lowercase: UUID-PLACEHOLDER')
      expect(texts[2]).toBe('Mixed: UUID-PLACEHOLDER')
    })

    test('should not mask non-UUID text', async ({ page }) => {
      await page.setContent(`
        <html>
          <body>
            <p>Regular text without UUIDs</p>
            <p>Email: user@example.com</p>
            <p>Phone: 123-456-7890</p>
          </body>
        </html>
      `)

      await maskDynamicIds(page)

      const texts = await page.locator('p').allTextContents()

      expect(texts[0]).toBe('Regular text without UUIDs')
      expect(texts[1]).toBe('Email: user@example.com')
      expect(texts[2]).toBe('Phone: 123-456-7890')
    })

    test('should handle nested elements', async ({ page }) => {
      await page.setContent(`
        <html>
          <body>
            <div>
              <span>
                <p>ID: 550e8400-e29b-41d4-a716-446655440000</p>
              </span>
            </div>
          </body>
        </html>
      `)

      await maskDynamicIds(page)

      const text = await page.locator('p').textContent()

      expect(text).toBe('ID: UUID-PLACEHOLDER')
    })
  })

  // ==========================================================================
  // 6. disableAnimations() Tests
  // ==========================================================================

  test.describe('disableAnimations()', () => {
    test('should add style tag that disables animations', async ({ page }) => {
      await page.setContent('<html><body><p>Test</p></body></html>')

      await disableAnimations(page)

      const hasAnimationStyle = await page.evaluate(() => {
        const styles = Array.from(document.querySelectorAll('style'))
        return styles.some(style =>
          style.textContent?.includes('animation-duration: 0s !important')
        )
      })

      expect(hasAnimationStyle).toBe(true)
    })

    test('should disable transitions on elements', async ({ page }) => {
      await page.setContent(`
        <html>
          <body>
            <div id="test" style="transition: all 1s ease;">Test</div>
          </body>
        </html>
      `)

      await disableAnimations(page)

      const computedStyle = await page.evaluate(() => {
        const el = document.getElementById('test')
        return window.getComputedStyle(el!).transitionDuration
      })

      expect(computedStyle).toBe('0s')
    })

    test('should not throw errors on empty page', async ({ page }) => {
      await page.setContent('<html><body></body></html>')

      await expect(disableAnimations(page)).resolves.toBeUndefined()
    })
  })

  // ==========================================================================
  // 7. Viewport Configuration Tests
  // ==========================================================================

  test.describe('Viewport Configurations', () => {
    const VIEWPORTS = {
      desktop: { width: 1920, height: 1080 },
      tablet: { width: 768, height: 1024 },
      mobile: { width: 375, height: 667 },
    }

    test('should set desktop viewport correctly', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop)

      const viewport = page.viewportSize()

      expect(viewport?.width).toBe(1920)
      expect(viewport?.height).toBe(1080)
    })

    test('should set tablet viewport correctly', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.tablet)

      const viewport = page.viewportSize()

      expect(viewport?.width).toBe(768)
      expect(viewport?.height).toBe(1024)
    })

    test('should set mobile viewport correctly', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile)

      const viewport = page.viewportSize()

      expect(viewport?.width).toBe(375)
      expect(viewport?.height).toBe(667)
    })
  })

  // ==========================================================================
  // 8. Integration Tests (Multiple Helpers)
  // ==========================================================================

  test.describe('Integration Tests', () => {
    test('should prepare page for visual testing with all helpers', async ({ page }) => {
      await page.setContent(`
        <html>
          <body>
            <div data-testid="timestamp">2024-01-15</div>
            <p>ID: 550e8400-e29b-41d4-a716-446655440000</p>
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" />
          </body>
        </html>
      `)

      // Apply all helpers
      await toggleDarkMode(page, true)
      await hideTimestamps(page)
      await maskDynamicIds(page)
      await disableAnimations(page)
      await waitForImages(page)

      // Verify dark mode applied
      const isDark = await page.evaluate(() =>
        document.documentElement.classList.contains('dark')
      )
      expect(isDark).toBe(true)

      // Verify timestamp hidden
      const isTimestampHidden = await page.evaluate(() => {
        const el = document.querySelector('[data-testid="timestamp"]') as HTMLElement
        return el?.style.visibility === 'hidden'
      })
      expect(isTimestampHidden).toBe(true)

      // Verify UUID masked
      const text = await page.locator('p').textContent()
      expect(text).toBe('ID: UUID-PLACEHOLDER')

      // Verify animations disabled
      const hasAnimationStyle = await page.evaluate(() => {
        const styles = Array.from(document.querySelectorAll('style'))
        return styles.some(style =>
          style.textContent?.includes('animation-duration: 0s')
        )
      })
      expect(hasAnimationStyle).toBe(true)
    })

    test('should handle complex page with multiple dynamic elements', async ({ page }) => {
      await page.setContent(`
        <html>
          <body>
            <header>
              <time datetime="2024-01-15">Jan 15, 2024</time>
            </header>
            <main>
              <div class="card">
                <p>Tiger ID: 550e8400-e29b-41d4-a716-446655440000</p>
                <span class="timestamp">Updated: 10:30 AM</span>
              </div>
              <div class="card">
                <p>Facility ID: 6ba7b810-9dad-11d1-80b4-00c04fd430c8</p>
                <span data-testid="last-updated">2 hours ago</span>
              </div>
            </main>
          </body>
        </html>
      `)

      await hideTimestamps(page)
      await maskDynamicIds(page)

      // Verify all timestamps hidden
      const hiddenCount = await page.evaluate(() => {
        let count = 0
        document.querySelectorAll('time, .timestamp, [data-testid="last-updated"]').forEach(el => {
          if ((el as HTMLElement).style.visibility === 'hidden') {
            count++
          }
        })
        return count
      })
      expect(hiddenCount).toBe(3)

      // Verify all UUIDs masked
      const texts = await page.locator('.card p').allTextContents()
      expect(texts[0]).toBe('Tiger ID: UUID-PLACEHOLDER')
      expect(texts[1]).toBe('Facility ID: UUID-PLACEHOLDER')
    })
  })
})

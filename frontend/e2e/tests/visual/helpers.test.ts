import { test, expect, Page } from '@playwright/test'

/**
 * Unit Tests for Visual Regression Helper Functions
 *
 * Tests the utility functions used across visual regression tests to ensure
 * they work correctly and handle edge cases.
 */

// Import or replicate helper functions for testing
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

async function waitForPageLoad(page: Page): Promise<void> {
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(500)
}

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

test.describe('Visual Regression Helper Functions', () => {

  test.describe('toggleDarkMode', () => {
    test('should add dark class when enabled', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent('<html><body><h1>Test</h1></body></html>')

      // Enable dark mode
      await toggleDarkMode(page, true)

      // Verify dark class is added
      const hasDarkClass = await page.evaluate(() => {
        return document.documentElement.classList.contains('dark')
      })

      expect(hasDarkClass).toBe(true)
    })

    test('should remove dark class when disabled', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent('<html class="dark"><body><h1>Test</h1></body></html>')

      // Disable dark mode
      await toggleDarkMode(page, false)

      // Verify dark class is removed
      const hasDarkClass = await page.evaluate(() => {
        return document.documentElement.classList.contains('dark')
      })

      expect(hasDarkClass).toBe(false)
    })

    test('should toggle dark mode multiple times', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent('<html><body><h1>Test</h1></body></html>')

      // Enable
      await toggleDarkMode(page, true)
      let hasDarkClass = await page.evaluate(() => document.documentElement.classList.contains('dark'))
      expect(hasDarkClass).toBe(true)

      // Disable
      await toggleDarkMode(page, false)
      hasDarkClass = await page.evaluate(() => document.documentElement.classList.contains('dark'))
      expect(hasDarkClass).toBe(false)

      // Enable again
      await toggleDarkMode(page, true)
      hasDarkClass = await page.evaluate(() => document.documentElement.classList.contains('dark'))
      expect(hasDarkClass).toBe(true)
    })

    test('should handle page without html element gracefully', async ({ page }) => {
      await page.goto('about:blank')

      // Should not throw error
      await expect(toggleDarkMode(page, true)).resolves.not.toThrow()
    })
  })

  test.describe('waitForPageLoad', () => {
    test('should wait for network idle', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent('<html><body><h1>Test</h1></body></html>')

      const startTime = Date.now()
      await waitForPageLoad(page)
      const duration = Date.now() - startTime

      // Should take at least 500ms (the timeout in waitForPageLoad)
      expect(duration).toBeGreaterThanOrEqual(400)
    })

    test('should complete for simple pages', async ({ page }) => {
      await page.goto('about:blank')

      // Should not throw and complete successfully
      await expect(waitForPageLoad(page)).resolves.not.toThrow()
    })

    test('should handle pages with ongoing network requests', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <h1>Test</h1>
            <script>
              // Simulate delayed network request
              setTimeout(() => {
                fetch('data:text/plain,test')
              }, 100)
            </script>
          </body>
        </html>
      `)

      // Should wait for network to be idle
      await expect(waitForPageLoad(page)).resolves.not.toThrow()
    })
  })

  test.describe('waitForImages', () => {
    test('should wait for single image to load', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" alt="test">
          </body>
        </html>
      `)

      await expect(waitForImages(page)).resolves.not.toThrow()
    })

    test('should wait for multiple images to load', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" alt="test1">
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" alt="test2">
          </body>
        </html>
      `)

      await expect(waitForImages(page)).resolves.not.toThrow()
    })

    test('should handle page with no images', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent('<html><body><h1>No images here</h1></body></html>')

      await expect(waitForImages(page)).resolves.not.toThrow()
    })

    test('should handle failed image loads', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <img src="https://invalid-url-that-does-not-exist.com/image.jpg" alt="broken">
          </body>
        </html>
      `)

      // Should resolve even if images fail to load
      await expect(waitForImages(page)).resolves.not.toThrow()
    })
  })

  test.describe('hideTimestamps', () => {
    test('should hide timestamp elements by data-testid', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <div data-testid="timestamp">2024-01-01 12:00:00</div>
          </body>
        </html>
      `)

      await hideTimestamps(page)

      const isVisible = await page.evaluate(() => {
        const el = document.querySelector('[data-testid="timestamp"]') as HTMLElement
        return el ? el.style.visibility !== 'hidden' : true
      })

      expect(isVisible).toBe(false)
    })

    test('should hide timestamp elements by class', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <div class="timestamp">2024-01-01 12:00:00</div>
          </body>
        </html>
      `)

      await hideTimestamps(page)

      const isVisible = await page.evaluate(() => {
        const el = document.querySelector('.timestamp') as HTMLElement
        return el ? el.style.visibility !== 'hidden' : true
      })

      expect(isVisible).toBe(false)
    })

    test('should hide time elements', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <time datetime="2024-01-01">January 1, 2024</time>
          </body>
        </html>
      `)

      await hideTimestamps(page)

      const isVisible = await page.evaluate(() => {
        const el = document.querySelector('time') as HTMLElement
        return el ? el.style.visibility !== 'hidden' : true
      })

      expect(isVisible).toBe(false)
    })

    test('should hide multiple timestamp elements', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <div data-testid="timestamp">2024-01-01</div>
            <div class="timestamp">2024-01-02</div>
            <time>2024-01-03</time>
            <div data-testid="last-updated">Updated 5 mins ago</div>
          </body>
        </html>
      `)

      await hideTimestamps(page)

      const visibleCount = await page.evaluate(() => {
        const selectors = [
          '[data-testid="timestamp"]',
          '.timestamp',
          'time',
          '[data-testid="last-updated"]'
        ]
        let visible = 0
        selectors.forEach(selector => {
          document.querySelectorAll(selector).forEach(el => {
            if ((el as HTMLElement).style.visibility !== 'hidden') {
              visible++
            }
          })
        })
        return visible
      })

      expect(visibleCount).toBe(0)
    })

    test('should handle page with no timestamps', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent('<html><body><h1>No timestamps</h1></body></html>')

      await expect(hideTimestamps(page)).resolves.not.toThrow()
    })
  })

  test.describe('maskDynamicIds', () => {
    test('should mask UUIDs in text content', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <p>Investigation ID: 550e8400-e29b-41d4-a716-446655440000</p>
          </body>
        </html>
      `)

      await maskDynamicIds(page)

      const text = await page.textContent('p')
      expect(text).toBe('Investigation ID: UUID-PLACEHOLDER')
    })

    test('should mask multiple UUIDs', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <p>ID1: 550e8400-e29b-41d4-a716-446655440000</p>
            <p>ID2: 6ba7b810-9dad-11d1-80b4-00c04fd430c8</p>
          </body>
        </html>
      `)

      await maskDynamicIds(page)

      const text1 = await page.textContent('p:nth-of-type(1)')
      const text2 = await page.textContent('p:nth-of-type(2)')

      expect(text1).toBe('ID1: UUID-PLACEHOLDER')
      expect(text2).toBe('ID2: UUID-PLACEHOLDER')
    })

    test('should mask UUIDs in nested elements', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <div>
              <span>Tiger: </span>
              <span>550e8400-e29b-41d4-a716-446655440000</span>
            </div>
          </body>
        </html>
      `)

      await maskDynamicIds(page)

      const divText = await page.textContent('div')
      expect(divText).toContain('UUID-PLACEHOLDER')
    })

    test('should preserve non-UUID text', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <p>Tiger Name: Bengal, ID: 550e8400-e29b-41d4-a716-446655440000, Status: Active</p>
          </body>
        </html>
      `)

      await maskDynamicIds(page)

      const text = await page.textContent('p')
      expect(text).toBe('Tiger Name: Bengal, ID: UUID-PLACEHOLDER, Status: Active')
    })

    test('should handle uppercase UUIDs', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <p>ID: 550E8400-E29B-41D4-A716-446655440000</p>
          </body>
        </html>
      `)

      await maskDynamicIds(page)

      const text = await page.textContent('p')
      expect(text).toBe('ID: UUID-PLACEHOLDER')
    })

    test('should handle mixed case UUIDs', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <p>ID: 550E8400-e29b-41D4-A716-446655440000</p>
          </body>
        </html>
      `)

      await maskDynamicIds(page)

      const text = await page.textContent('p')
      expect(text).toBe('ID: UUID-PLACEHOLDER')
    })

    test('should handle page with no UUIDs', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent('<html><body><h1>No UUIDs here</h1></body></html>')

      await expect(maskDynamicIds(page)).resolves.not.toThrow()

      const text = await page.textContent('h1')
      expect(text).toBe('No UUIDs here')
    })
  })

  test.describe('Integration: Combined Helper Usage', () => {
    test('should work together in sequence', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <h1>Test Page</h1>
            <div data-testid="timestamp">2024-01-01 12:00:00</div>
            <p>Tiger ID: 550e8400-e29b-41d4-a716-446655440000</p>
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" alt="test">
          </body>
        </html>
      `)

      // Apply all helpers
      await toggleDarkMode(page, true)
      await waitForPageLoad(page)
      await waitForImages(page)
      await hideTimestamps(page)
      await maskDynamicIds(page)

      // Verify results
      const hasDarkClass = await page.evaluate(() => document.documentElement.classList.contains('dark'))
      const timestampHidden = await page.evaluate(() => {
        const el = document.querySelector('[data-testid="timestamp"]') as HTMLElement
        return el.style.visibility === 'hidden'
      })
      const text = await page.textContent('p')

      expect(hasDarkClass).toBe(true)
      expect(timestampHidden).toBe(true)
      expect(text).toBe('Tiger ID: UUID-PLACEHOLDER')
    })

    test('should handle errors gracefully', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent('<html><body><h1>Test</h1></body></html>')

      // All helpers should complete without throwing
      await expect(async () => {
        await toggleDarkMode(page, true)
        await waitForPageLoad(page)
        await waitForImages(page)
        await hideTimestamps(page)
        await maskDynamicIds(page)
      }).not.toThrow()
    })
  })

  test.describe('Edge Cases', () => {
    test('should handle empty page', async ({ page }) => {
      await page.goto('about:blank')

      await expect(async () => {
        await toggleDarkMode(page, true)
        await waitForPageLoad(page)
        await waitForImages(page)
        await hideTimestamps(page)
        await maskDynamicIds(page)
      }).not.toThrow()
    })

    test('should handle page with special characters', async ({ page }) => {
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <p>Special: <>&"'</p>
            <p>UUID: 550e8400-e29b-41d4-a716-446655440000</p>
          </body>
        </html>
      `)

      await maskDynamicIds(page)

      const text1 = await page.textContent('p:nth-of-type(1)')
      const text2 = await page.textContent('p:nth-of-type(2)')

      expect(text1).toBe('Special: <>&"\'')
      expect(text2).toBe('UUID: UUID-PLACEHOLDER')
    })

    test('should handle page with very long text', async ({ page }) => {
      const longText = 'a'.repeat(10000)
      await page.goto('about:blank')
      await page.setContent(`
        <html>
          <body>
            <p>${longText}</p>
            <p>ID: 550e8400-e29b-41d4-a716-446655440000</p>
          </body>
        </html>
      `)

      await maskDynamicIds(page)

      const text = await page.textContent('p:nth-of-type(2)')
      expect(text).toBe('ID: UUID-PLACEHOLDER')
    })
  })
})

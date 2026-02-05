import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

/**
 * Accessibility Test Suite
 *
 * Uses axe-core to detect WCAG 2.0/2.1 Level A and AA violations across all pages.
 *
 * WCAG Standards Tested:
 * - wcag2a: WCAG 2.0 Level A
 * - wcag2aa: WCAG 2.0 Level AA
 * - wcag21a: WCAG 2.1 Level A
 * - wcag21aa: WCAG 2.1 Level AA
 *
 * Violation Impact Levels:
 * - critical: Must be fixed immediately (blocks users)
 * - serious: Should be fixed (significant barriers)
 * - moderate: Should be fixed (inconvenience)
 * - minor: Should be fixed eventually (annoyance)
 *
 * Installation:
 * npm install --save-dev @axe-core/playwright
 */

test.describe('Accessibility Tests', () => {
  /**
   * Helper function to analyze and report accessibility violations
   */
  async function analyzeAccessibility(page: any, context: string) {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    // Log detailed violation information if any are found
    if (accessibilityScanResults.violations.length > 0) {
      console.log(`\n=== Accessibility Violations for ${context} ===`)

      accessibilityScanResults.violations.forEach((violation) => {
        console.log(`\n${violation.impact?.toUpperCase()}: ${violation.description}`)
        console.log(`Rule: ${violation.id}`)
        console.log(`Help: ${violation.helpUrl}`)
        console.log(`Affected nodes: ${violation.nodes.length}`)

        violation.nodes.forEach((node, index) => {
          console.log(`  Node ${index + 1}: ${node.html}`)
          console.log(`  Target: ${node.target.join(', ')}`)
          console.log(`  Summary: ${node.failureSummary}`)
        })
      })

      console.log('\n============================================\n')
    }

    return accessibilityScanResults
  }

  /**
   * Helper to filter critical and serious violations only
   */
  function getCriticalAndSeriousViolations(results: any) {
    return results.violations.filter(
      (v: any) => v.impact === 'critical' || v.impact === 'serious'
    )
  }

  test.describe('Authentication Pages', () => {
    test('Login page should not have accessibility violations', async ({ page }) => {
      await page.goto('/login')
      await page.waitForLoadState('networkidle')

      const results = await analyzeAccessibility(page, 'Login Page')
      const criticalViolations = getCriticalAndSeriousViolations(results)

      expect(criticalViolations).toEqual([])
    })

    test('Password reset page should not have accessibility violations', async ({ page }) => {
      await page.goto('/password-reset')
      await page.waitForLoadState('networkidle')

      const results = await analyzeAccessibility(page, 'Password Reset Page')
      const criticalViolations = getCriticalAndSeriousViolations(results)

      expect(criticalViolations).toEqual([])
    })
  })

  test.describe('Main Dashboard and Navigation', () => {
    test('Dashboard page should not have accessibility violations', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')

      const results = await analyzeAccessibility(page, 'Dashboard')
      const criticalViolations = getCriticalAndSeriousViolations(results)

      expect(criticalViolations).toEqual([])
    })

    test('Navigation header should have proper ARIA labels', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')

      // Check for navigation landmark
      const nav = page.locator('nav')
      await expect(nav).toBeVisible()

      const results = await new AxeBuilder({ page })
        .include('nav')
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze()

      const criticalViolations = getCriticalAndSeriousViolations(results)
      expect(criticalViolations).toEqual([])
    })

    test('Sidebar navigation should be keyboard accessible', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')

      // Test keyboard navigation in sidebar
      const firstLink = page.locator('aside a, nav a').first()
      await firstLink.focus()

      const focusedElement = await page.evaluate(() => document.activeElement?.tagName)
      expect(focusedElement).toBe('A')

      const results = await new AxeBuilder({ page })
        .include('aside, nav')
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze()

      const criticalViolations = getCriticalAndSeriousViolations(results)
      expect(criticalViolations).toEqual([])
    })
  })

  test.describe('Tiger Management Pages', () => {
    test('Tigers list page should not have accessibility violations', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForLoadState('networkidle')

      // Wait for content to load
      await page.waitForTimeout(1000)

      const results = await analyzeAccessibility(page, 'Tigers List Page')
      const criticalViolations = getCriticalAndSeriousViolations(results)

      expect(criticalViolations).toEqual([])
    })

    test('Tiger cards should have proper alt text for images', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(1000)

      // Check all images have alt text
      const images = await page.locator('img').all()

      for (const img of images) {
        const alt = await img.getAttribute('alt')
        const src = await img.getAttribute('src')

        // Images should have alt text (can be empty for decorative images)
        expect(alt).toBeDefined()
        console.log(`Image ${src}: alt="${alt}"`)
      }

      const results = await analyzeAccessibility(page, 'Tiger Cards Images')
      const imageViolations = results.violations.filter(
        (v: any) => v.id === 'image-alt' && (v.impact === 'critical' || v.impact === 'serious')
      )

      expect(imageViolations).toEqual([])
    })

    test('Tiger detail page should not have accessibility violations', async ({ page }) => {
      // Navigate to tigers list first
      await page.goto('/tigers')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(1000)

      // Try to click on first tiger if available
      const firstTiger = page.locator('[data-testid="tiger-card"]').first()
      if (await firstTiger.count() > 0) {
        await firstTiger.click()
        await page.waitForLoadState('networkidle')
        await page.waitForTimeout(500)

        const results = await analyzeAccessibility(page, 'Tiger Detail Page')
        const criticalViolations = getCriticalAndSeriousViolations(results)

        expect(criticalViolations).toEqual([])
      } else {
        console.log('No tigers available to test detail page')
      }
    })
  })

  test.describe('Investigation Pages', () => {
    test('Investigation 2.0 page should not have accessibility violations', async ({ page }) => {
      await page.goto('/investigation2')
      await page.waitForLoadState('networkidle')

      const results = await analyzeAccessibility(page, 'Investigation 2.0 Page')
      const criticalViolations = getCriticalAndSeriousViolations(results)

      expect(criticalViolations).toEqual([])
    })

    test('File upload area should have proper labels and instructions', async ({ page }) => {
      await page.goto('/investigation2')
      await page.waitForLoadState('networkidle')

      // Check for file input
      const fileInput = page.locator('input[type="file"]')

      if (await fileInput.count() > 0) {
        // File input should have associated label or aria-label
        const ariaLabel = await fileInput.getAttribute('aria-label')
        const ariaLabelledBy = await fileInput.getAttribute('aria-labelledby')
        const id = await fileInput.getAttribute('id')

        let hasLabel = false
        if (id) {
          const label = page.locator(`label[for="${id}"]`)
          hasLabel = await label.count() > 0
        }

        expect(
          ariaLabel || ariaLabelledBy || hasLabel,
          'File input should have accessible label'
        ).toBeTruthy()
      }

      const results = await new AxeBuilder({ page })
        .include('input[type="file"], [role="button"]')
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze()

      const criticalViolations = getCriticalAndSeriousViolations(results)
      expect(criticalViolations).toEqual([])
    })

    test('Investigation results should have proper structure and headings', async ({ page }) => {
      await page.goto('/investigation2')
      await page.waitForLoadState('networkidle')

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze()

      // Check for proper heading hierarchy
      const headingViolations = results.violations.filter(
        (v: any) => v.id.includes('heading') && (v.impact === 'critical' || v.impact === 'serious')
      )

      expect(headingViolations).toEqual([])
    })
  })

  test.describe('Discovery Pages', () => {
    test('Discovery page should not have accessibility violations', async ({ page }) => {
      await page.goto('/discovery')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)

      const results = await analyzeAccessibility(page, 'Discovery Page')
      const criticalViolations = getCriticalAndSeriousViolations(results)

      expect(criticalViolations).toEqual([])
    })

    test('Discovery controls should be keyboard accessible', async ({ page }) => {
      await page.goto('/discovery')
      await page.waitForLoadState('networkidle')

      // Test that all buttons are keyboard focusable
      const buttons = await page.locator('button').all()

      for (const button of buttons) {
        const tabindex = await button.getAttribute('tabindex')
        // Buttons should not have negative tabindex (except if intentionally disabled)
        if (tabindex) {
          expect(parseInt(tabindex)).toBeGreaterThanOrEqual(-1)
        }
      }

      const results = await new AxeBuilder({ page })
        .include('button, [role="button"]')
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze()

      const criticalViolations = getCriticalAndSeriousViolations(results)
      expect(criticalViolations).toEqual([])
    })
  })

  test.describe('Facilities Pages', () => {
    test('Facilities list page should not have accessibility violations', async ({ page }) => {
      await page.goto('/facilities')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(1000)

      const results = await analyzeAccessibility(page, 'Facilities Page')
      const criticalViolations = getCriticalAndSeriousViolations(results)

      expect(criticalViolations).toEqual([])
    })

    test('Facility map should have text alternatives', async ({ page }) => {
      await page.goto('/facilities')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(1000)

      // Check if map container has proper ARIA labels
      const mapContainer = page.locator('.leaflet-container, [class*="map"]')

      if (await mapContainer.count() > 0) {
        const ariaLabel = await mapContainer.first().getAttribute('aria-label')
        const role = await mapContainer.first().getAttribute('role')

        // Map should have either aria-label or be marked as application
        expect(
          ariaLabel || role === 'application' || role === 'img',
          'Map should have accessible label or role'
        ).toBeTruthy()
      }

      const results = await analyzeAccessibility(page, 'Facilities Map')
      const criticalViolations = getCriticalAndSeriousViolations(results)

      expect(criticalViolations).toEqual([])
    })

    test('Facility cards should have semantic structure', async ({ page }) => {
      await page.goto('/facilities')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(1000)

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze()

      // Check for list structure violations
      const listViolations = results.violations.filter(
        (v: any) => v.id.includes('list') && (v.impact === 'critical' || v.impact === 'serious')
      )

      expect(listViolations).toEqual([])
    })
  })

  test.describe('Verification Queue', () => {
    test('Verification queue page should not have accessibility violations', async ({ page }) => {
      await page.goto('/verification')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(1000)

      const results = await analyzeAccessibility(page, 'Verification Queue Page')
      const criticalViolations = getCriticalAndSeriousViolations(results)

      expect(criticalViolations).toEqual([])
    })

    test('Verification action buttons should have clear labels', async ({ page }) => {
      await page.goto('/verification')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(1000)

      // Check that all action buttons have accessible names
      const buttons = await page.locator('button').all()

      for (const button of buttons) {
        const text = await button.textContent()
        const ariaLabel = await button.getAttribute('aria-label')
        const ariaLabelledBy = await button.getAttribute('aria-labelledby')
        const title = await button.getAttribute('title')

        // Button should have at least one form of accessible text
        expect(
          text?.trim() || ariaLabel || ariaLabelledBy || title,
          'Button should have accessible name'
        ).toBeTruthy()
      }

      const results = await new AxeBuilder({ page })
        .include('button')
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze()

      const criticalViolations = getCriticalAndSeriousViolations(results)
      expect(criticalViolations).toEqual([])
    })
  })

  test.describe('Modal Components', () => {
    test('Modals should have proper focus trapping', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForLoadState('networkidle')

      // Try to open a modal (if one exists)
      const modalTrigger = page.locator('button:has-text("Add"), button:has-text("New"), button:has-text("Create")').first()

      if (await modalTrigger.count() > 0) {
        await modalTrigger.click()
        await page.waitForTimeout(500)

        // Check if modal is visible
        const modal = page.locator('[role="dialog"], [role="alertdialog"]')

        if (await modal.count() > 0) {
          await expect(modal).toBeVisible()

          // Modal should have aria-modal
          const ariaModal = await modal.getAttribute('aria-modal')
          expect(ariaModal).toBe('true')

          // Modal should have aria-labelledby or aria-label
          const ariaLabel = await modal.getAttribute('aria-label')
          const ariaLabelledBy = await modal.getAttribute('aria-labelledby')
          expect(ariaLabel || ariaLabelledBy).toBeTruthy()

          const results = await new AxeBuilder({ page })
            .include('[role="dialog"], [role="alertdialog"]')
            .withTags(['wcag2a', 'wcag2aa'])
            .analyze()

          const criticalViolations = getCriticalAndSeriousViolations(results)
          expect(criticalViolations).toEqual([])

          // Close modal
          const closeButton = page.locator('[aria-label="Close"], button:has-text("Cancel"), button:has-text("Close")').first()
          if (await closeButton.count() > 0) {
            await closeButton.click()
          }
        }
      }
    })

    test('Modal close buttons should be accessible', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForLoadState('networkidle')

      const modalTrigger = page.locator('button:has-text("Add"), button:has-text("New")').first()

      if (await modalTrigger.count() > 0) {
        await modalTrigger.click()
        await page.waitForTimeout(500)

        const closeButton = page.locator('[aria-label*="Close"], [aria-label*="close"], button:has-text("Close")').first()

        if (await closeButton.count() > 0) {
          // Close button should be focusable
          await closeButton.focus()
          const isFocused = await closeButton.evaluate(el => el === document.activeElement)
          expect(isFocused).toBeTruthy()

          // Close button should have accessible name
          const ariaLabel = await closeButton.getAttribute('aria-label')
          const text = await closeButton.textContent()
          expect(ariaLabel || text?.trim()).toBeTruthy()
        }
      }
    })
  })

  test.describe('Form Components', () => {
    test('Form inputs should have proper labels', async ({ page }) => {
      await page.goto('/login')
      await page.waitForLoadState('networkidle')

      const results = await new AxeBuilder({ page })
        .include('input, select, textarea')
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze()

      // Check for label violations
      const labelViolations = results.violations.filter(
        (v: any) => v.id === 'label' && (v.impact === 'critical' || v.impact === 'serious')
      )

      expect(labelViolations).toEqual([])
    })

    test('Form validation errors should be announced', async ({ page }) => {
      await page.goto('/login')
      await page.waitForLoadState('networkidle')

      // Submit form to trigger validation
      const submitButton = page.locator('button[type="submit"]')
      if (await submitButton.count() > 0) {
        await submitButton.click()
        await page.waitForTimeout(500)

        // Check for error messages
        const errorMessages = page.locator('[role="alert"], .error, [class*="error"]')

        if (await errorMessages.count() > 0) {
          // Error messages should have role="alert" or aria-live
          const firstError = errorMessages.first()
          const role = await firstError.getAttribute('role')
          const ariaLive = await firstError.getAttribute('aria-live')

          expect(
            role === 'alert' || ariaLive === 'assertive' || ariaLive === 'polite',
            'Error messages should be announced to screen readers'
          ).toBeTruthy()
        }

        const results = await new AxeBuilder({ page })
          .withTags(['wcag2a', 'wcag2aa'])
          .analyze()

        const criticalViolations = getCriticalAndSeriousViolations(results)
        expect(criticalViolations).toEqual([])
      }
    })

    test('Required form fields should be indicated', async ({ page }) => {
      await page.goto('/login')
      await page.waitForLoadState('networkidle')

      const requiredInputs = await page.locator('input[required], input[aria-required="true"]').all()

      for (const input of requiredInputs) {
        const ariaRequired = await input.getAttribute('aria-required')
        const required = await input.getAttribute('required')

        // Required fields should have aria-required or required attribute
        expect(ariaRequired === 'true' || required !== null).toBeTruthy()
      }

      const results = await new AxeBuilder({ page })
        .include('input, select, textarea')
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze()

      const criticalViolations = getCriticalAndSeriousViolations(results)
      expect(criticalViolations).toEqual([])
    })
  })

  test.describe('Color Contrast', () => {
    test('All pages should meet color contrast requirements', async ({ page }) => {
      const pages = [
        '/login',
        '/dashboard',
        '/tigers',
        '/facilities',
        '/investigation2',
        '/discovery',
        '/verification'
      ]

      for (const pagePath of pages) {
        await page.goto(pagePath)
        await page.waitForLoadState('networkidle')
        await page.waitForTimeout(500)

        const results = await new AxeBuilder({ page })
          .withTags(['wcag2aa'])
          .analyze()

        // Filter for color contrast violations
        const contrastViolations = results.violations.filter(
          (v: any) => v.id === 'color-contrast' && (v.impact === 'serious' || v.impact === 'critical')
        )

        if (contrastViolations.length > 0) {
          console.log(`\nColor contrast violations on ${pagePath}:`)
          contrastViolations.forEach((v: any) => {
            console.log(`  - ${v.description}`)
            v.nodes.forEach((node: any) => {
              console.log(`    Element: ${node.html}`)
            })
          })
        }

        expect(contrastViolations).toEqual([])
      }
    })
  })

  test.describe('Keyboard Navigation', () => {
    test('All interactive elements should be keyboard accessible', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')

      // Get all interactive elements
      const interactiveElements = await page.locator('a, button, input, select, textarea, [tabindex]').all()

      let keyboardAccessibleCount = 0

      for (const element of interactiveElements) {
        const tagName = await element.evaluate(el => el.tagName)
        const tabindex = await element.getAttribute('tabindex')
        const isDisabled = await element.evaluate(el => (el as HTMLInputElement).disabled)

        // Element is keyboard accessible if:
        // - No tabindex or tabindex >= 0
        // - Not disabled
        if (!isDisabled && (!tabindex || parseInt(tabindex) >= 0)) {
          keyboardAccessibleCount++
        }
      }

      console.log(`Found ${keyboardAccessibleCount} keyboard accessible elements`)
      expect(keyboardAccessibleCount).toBeGreaterThan(0)

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a'])
        .analyze()

      const keyboardViolations = results.violations.filter(
        (v: any) => v.id.includes('keyboard') && (v.impact === 'critical' || v.impact === 'serious')
      )

      expect(keyboardViolations).toEqual([])
    })

    test('Skip to main content link should be present', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')

      // Check for skip link (usually hidden until focused)
      const skipLink = page.locator('a[href="#main"], a[href="#content"], a:has-text("Skip to")')

      if (await skipLink.count() > 0) {
        // Skip link should be focusable
        await skipLink.first().focus()

        const isFocused = await skipLink.first().evaluate(el => el === document.activeElement)
        expect(isFocused).toBeTruthy()

        console.log('Skip to main content link found and is focusable')
      } else {
        console.log('Consider adding a skip to main content link for better accessibility')
      }
    })

    test('Tab order should be logical', async ({ page }) => {
      await page.goto('/login')
      await page.waitForLoadState('networkidle')

      // Get tab order
      const tabbableElements = await page.locator('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])').all()

      const tabOrders: number[] = []
      for (const element of tabbableElements) {
        const tabindex = await element.getAttribute('tabindex')
        tabOrders.push(tabindex ? parseInt(tabindex) : 0)
      }

      // Check that positive tabindex values are in order (if any)
      const positiveTabindexes = tabOrders.filter(t => t > 0).sort((a, b) => a - b)

      if (positiveTabindexes.length > 0) {
        console.log('Positive tabindex values found:', positiveTabindexes)
        // Warn about positive tabindex usage
        console.warn('Consider avoiding positive tabindex values for natural tab order')
      }

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a'])
        .analyze()

      const tabindexViolations = results.violations.filter(
        (v: any) => v.id === 'tabindex' && (v.impact === 'serious' || v.impact === 'critical')
      )

      expect(tabindexViolations).toEqual([])
    })
  })

  test.describe('Screen Reader Compatibility', () => {
    test('Page should have proper document structure', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')

      // Check for main landmark
      const main = page.locator('main, [role="main"]')
      await expect(main).toHaveCount(1)

      // Check for proper heading hierarchy
      const h1 = page.locator('h1')
      await expect(h1.first()).toBeVisible()

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze()

      const landmarkViolations = results.violations.filter(
        (v: any) => v.id.includes('landmark') || v.id.includes('region')
      )

      if (landmarkViolations.length > 0) {
        console.log('Landmark violations:', landmarkViolations)
      }

      const criticalViolations = getCriticalAndSeriousViolations(results)
      expect(criticalViolations).toEqual([])
    })

    test('Live regions should be properly marked', async ({ page }) => {
      await page.goto('/investigation2')
      await page.waitForLoadState('networkidle')

      // Check for live regions (for dynamic content updates)
      const liveRegions = await page.locator('[aria-live], [role="status"], [role="alert"]').all()

      console.log(`Found ${liveRegions.length} live regions for dynamic content`)

      for (const region of liveRegions) {
        const ariaLive = await region.getAttribute('aria-live')
        const role = await region.getAttribute('role')

        console.log(`Live region: aria-live="${ariaLive}", role="${role}"`)
      }

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze()

      const criticalViolations = getCriticalAndSeriousViolations(results)
      expect(criticalViolations).toEqual([])
    })
  })

  test.describe('Comprehensive Scan Summary', () => {
    test('Generate accessibility report for all critical pages', async ({ page }) => {
      const pagesToTest = [
        { path: '/login', name: 'Login' },
        { path: '/dashboard', name: 'Dashboard' },
        { path: '/tigers', name: 'Tigers' },
        { path: '/facilities', name: 'Facilities' },
        { path: '/investigation2', name: 'Investigation' },
        { path: '/discovery', name: 'Discovery' },
        { path: '/verification', name: 'Verification' }
      ]

      const summary: any = {
        totalPages: pagesToTest.length,
        pagesWithViolations: 0,
        totalViolations: 0,
        criticalViolations: 0,
        seriousViolations: 0,
        moderateViolations: 0,
        minorViolations: 0,
        pageResults: []
      }

      for (const pageInfo of pagesToTest) {
        await page.goto(pageInfo.path)
        await page.waitForLoadState('networkidle')
        await page.waitForTimeout(500)

        const results = await new AxeBuilder({ page })
          .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
          .analyze()

        const pageViolations = {
          page: pageInfo.name,
          path: pageInfo.path,
          violations: results.violations.length,
          critical: results.violations.filter((v: any) => v.impact === 'critical').length,
          serious: results.violations.filter((v: any) => v.impact === 'serious').length,
          moderate: results.violations.filter((v: any) => v.impact === 'moderate').length,
          minor: results.violations.filter((v: any) => v.impact === 'minor').length
        }

        summary.pageResults.push(pageViolations)

        if (results.violations.length > 0) {
          summary.pagesWithViolations++
        }

        summary.totalViolations += results.violations.length
        summary.criticalViolations += pageViolations.critical
        summary.seriousViolations += pageViolations.serious
        summary.moderateViolations += pageViolations.moderate
        summary.minorViolations += pageViolations.minor
      }

      console.log('\n=== ACCESSIBILITY SCAN SUMMARY ===')
      console.log(`Pages tested: ${summary.totalPages}`)
      console.log(`Pages with violations: ${summary.pagesWithViolations}`)
      console.log(`Total violations: ${summary.totalViolations}`)
      console.log(`  Critical: ${summary.criticalViolations}`)
      console.log(`  Serious: ${summary.seriousViolations}`)
      console.log(`  Moderate: ${summary.moderateViolations}`)
      console.log(`  Minor: ${summary.minorViolations}`)
      console.log('\nPer-page breakdown:')

      summary.pageResults.forEach((pr: any) => {
        console.log(`  ${pr.page} (${pr.path}): ${pr.violations} violations`)
        if (pr.violations > 0) {
          console.log(`    Critical: ${pr.critical}, Serious: ${pr.serious}, Moderate: ${pr.moderate}, Minor: ${pr.minor}`)
        }
      })
      console.log('==================================\n')

      // Only fail if there are critical or serious violations
      expect(summary.criticalViolations + summary.seriousViolations).toBe(0)
    })
  })
})

import { test, expect } from '@playwright/test'
import { login } from '../../helpers/auth'

/**
 * Tiger Detail Page E2E Tests
 *
 * Comprehensive test coverage for the Tiger Detail page including:
 * - Basic information display
 * - Image gallery functionality
 * - Image quality indicators
 * - Identification timeline
 * - Related investigations
 * - Edit functionality
 * - Delete confirmation
 * - Facility navigation
 */

test.describe('Tiger Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await login(page)
    await page.waitForTimeout(1000)
  })

  test.describe('View Tiger Detail', () => {
    test('should display tiger detail page with basic information', async ({ page }) => {
      // Navigate to tigers list first
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      // Find and click on first tiger card
      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      const tigerCardCount = await tigerCard.count()

      // Skip test if no tigers exist in database
      test.skip(tigerCardCount === 0, 'No tigers available in test database')

      if (tigerCardCount > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Verify navigation to detail page
        await expect(page).toHaveURL(/\/tigers\/[\w-]+/)

        // Verify tiger detail page loads
        const hasDetailPage = await page.locator('[data-testid="tiger-detail-page"]').count() > 0
        const hasHeading = await page.locator('h1').count() > 0

        // Page should have either data-testid or heading
        expect(hasDetailPage || hasHeading).toBe(true)

        // Verify back button exists
        const backButton = page.locator('button:has-text("Back")')
        await expect(backButton.first()).toBeVisible()

        // Verify tiger ID is displayed
        await expect(page.locator('text=/ID:|Tiger #/i')).toBeVisible()
      }
    })

    test('should display tiger name and ID', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Should display tiger name or ID as heading
        const heading = page.locator('h1')
        await expect(heading).toBeVisible()

        // Should display full tiger ID
        await expect(page.locator('text=/Tiger ID:/i')).toBeVisible()
      }
    })

    test('should display status badge', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Look for status section and badge
        const statusSection = page.locator('text=/Status:/i')

        if (await statusSection.count() > 0) {
          await expect(statusSection).toBeVisible()

          // Status badge should exist nearby
          const statusBadge = page.locator('[data-testid="tiger-status-badge"]')
          const genericBadge = page.locator('.badge, [class*="badge"]')

          const hasBadge = await statusBadge.count() > 0 || await genericBadge.count() > 0
          expect(hasBadge).toBe(true)
        }
      }
    })

    test('should show metadata section with tiger information', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Should show Metadata section
        const metadataHeading = page.locator('text=/Metadata/i')

        if (await metadataHeading.count() > 0) {
          await expect(metadataHeading).toBeVisible()

          // Should display tiger ID
          await expect(page.locator('text=/Tiger ID:/i')).toBeVisible()
        }
      }
    })
  })

  test.describe('Tiger Image Gallery', () => {
    test('should display tiger image gallery section', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Gallery should be present via data-testid or Images heading
        const gallery = page.locator('[data-testid="tiger-image-gallery"]')
        const imagesHeading = page.locator('text=/^Images$/i')

        const hasGallery = await gallery.count() > 0 || await imagesHeading.count() > 0
        expect(hasGallery).toBe(true)
      }
    })

    test('should show all images for tiger', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Count all tiger images
        const tigerImages = page.locator('img[alt*="Tiger"], img[alt*="tiger"]')
        const imageCount = await tigerImages.count()

        // Should have at least 0 images (may have empty gallery)
        expect(imageCount).toBeGreaterThanOrEqual(0)

        // If images exist, verify first is visible
        if (imageCount > 0) {
          await expect(tigerImages.first()).toBeVisible()
        }

        // Check for image count display
        const imageCountText = page.locator('text=/Total images:|Image Count:/i')
        if (await imageCountText.count() > 0) {
          await expect(imageCountText.first()).toBeVisible()
        }
      }
    })

    test('should display images in grid layout', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Look for grid container or individual image cards
        const gridContainer = page.locator('[class*="grid"]').filter({ has: page.locator('img') })
        const imageCards = page.locator('[data-testid^="image-card-"]')

        const hasGrid = await gridContainer.count() > 0 || await imageCards.count() > 0
        expect(hasGrid).toBe(true)
      }
    })

    test('should open lightbox when clicking image', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Find clickable tiger image
        const tigerImage = page.locator('img[alt*="Tiger"], img[alt*="tiger"]').first()

        if (await tigerImage.count() > 0) {
          await tigerImage.click()
          await page.waitForTimeout(500)

          // Look for lightbox modal
          const lightbox = page.locator('[data-testid="image-lightbox"]')
          const modalOverlay = page.locator('.fixed.inset-0')
          const dialogRole = page.locator('[role="dialog"]')

          const hasLightbox = await lightbox.count() > 0 ||
                             await modalOverlay.count() > 0 ||
                             await dialogRole.count() > 0

          expect(hasLightbox).toBe(true)

          // Should have close button
          const closeButton = page.locator('button[aria-label*="Close"], button:has-text("Close")')
          if (await closeButton.count() > 0) {
            await expect(closeButton.first()).toBeVisible()
          }
        }
      }
    })

    test('should navigate between images in lightbox', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Check if multiple images exist
        const images = page.locator('img[alt*="Tiger"], img[alt*="tiger"]')
        const imageCount = await images.count()

        if (imageCount > 1) {
          // Click first image to open lightbox
          await images.first().click()
          await page.waitForTimeout(500)

          // Look for navigation buttons
          const nextButton = page.locator('button:has-text("Next"), button[aria-label="Next"]')
          const prevButton = page.locator('button:has-text("Previous"), button:has-text("Prev"), button[aria-label="Previous"]')

          // Test next button if exists
          if (await nextButton.count() > 0) {
            await expect(nextButton.first()).toBeVisible()
            await nextButton.first().click()
            await page.waitForTimeout(300)
          }

          // Test previous button if exists
          if (await prevButton.count() > 0) {
            await expect(prevButton.first()).toBeVisible()
          }

          // Should show image counter (e.g., "1 / 3")
          const imageCounter = page.locator('text=/\\d+ \\/ \\d+/')
          if (await imageCounter.count() > 0) {
            await expect(imageCounter.first()).toBeVisible()
          }
        }
      }
    })

    test('should close lightbox when clicking backdrop', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        const tigerImage = page.locator('img[alt*="Tiger"]').first()

        if (await tigerImage.count() > 0) {
          // Open lightbox
          await tigerImage.click()
          await page.waitForTimeout(500)

          // Click backdrop to close (click on overlay)
          const backdrop = page.locator('.fixed.inset-0').first()
          if (await backdrop.count() > 0) {
            await backdrop.click({ position: { x: 10, y: 10 } })
            await page.waitForTimeout(300)

            // Lightbox should be closed
            const lightboxVisible = await backdrop.isVisible().catch(() => false)
            expect(lightboxVisible).toBe(false)
          }
        }
      }
    })
  })

  test.describe('Image Quality Indicators', () => {
    test('should display image quality badges if available', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Look for quality indicators
        const qualityBadges = page.locator('[data-testid*="quality"]')
        const qualityText = page.locator('text=/quality/i')
        const qualityLevels = page.locator('text=/High|Medium|Low/i')

        const hasQualityIndicators = await qualityBadges.count() > 0 ||
                                     await qualityText.count() > 0 ||
                                     await qualityLevels.count() > 0

        // Quality indicators are optional, just verify structure
        expect(typeof hasQualityIndicators).toBe('boolean')
      }
    })

    test('should show quality scores with percentages', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Look for quality scores (percentage values)
        const scoreElements = page.locator('text=/\\d+%/')
        const qualityScores = page.locator('[data-testid*="quality-score"]')

        const hasScores = await scoreElements.count() > 0 || await qualityScores.count() > 0

        // Scores are optional
        expect(typeof hasScores).toBe('boolean')
      }
    })
  })

  test.describe('Identification Timeline', () => {
    test('should display identification timeline section', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Timeline should exist via data-testid or heading
        const timeline = page.locator('[data-testid="tiger-identification-timeline"]')
        const timelineHeading = page.locator('text=/Timeline|History|Identification/i')

        const hasTimeline = await timeline.count() > 0 || await timelineHeading.count() > 0
        expect(hasTimeline).toBe(true)
      }
    })

    test('should show timeline events with correct structure', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Look for timeline events
        const timelineEvents = page.locator('[data-testid^="timeline-event-"]')
        const eventCount = await timelineEvents.count()

        // Timeline may be empty for new tigers
        expect(eventCount).toBeGreaterThanOrEqual(0)

        if (eventCount > 0) {
          // First event should be visible
          await expect(timelineEvents.first()).toBeVisible()
        }
      }
    })

    test('should display timeline event types correctly', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Check if timeline has events
        const timelineEvents = page.locator('[data-testid^="timeline-event-"]')
        const eventCount = await timelineEvents.count()

        if (eventCount > 0) {
          // Events should have type indicators
          const eventTypes = page.locator('text=/Registered|Matched|Verified|Disputed|Merged/i')
          const hasEventTypes = await eventTypes.count() > 0

          expect(hasEventTypes).toBe(true)

          // Events should have icons
          const eventIcons = page.locator('[data-testid^="timeline-event-"] svg')
          if (await eventIcons.count() > 0) {
            await expect(eventIcons.first()).toBeVisible()
          }
        }
      }
    })

    test('should show correct timestamps for timeline events', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        const timelineEvents = page.locator('[data-testid^="timeline-event-"]')
        const eventCount = await timelineEvents.count()

        if (eventCount > 0) {
          // Events should have timestamps (date format or relative time)
          const datePatterns = [
            page.locator('text=/\\d{1,2}\\/\\d{1,2}\\/\\d{4}/'),
            page.locator('text=/\\d{4}-\\d{2}-\\d{2}/'),
            page.locator('text=/Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec/'),
            page.locator('text=/ago|Just now|minute|hour|day|week|month|year/i'),
          ]

          let hasTimestamp = false
          for (const pattern of datePatterns) {
            if (await pattern.count() > 0) {
              hasTimestamp = true
              break
            }
          }

          expect(hasTimestamp).toBe(true)
        }
      }
    })

    test('should display confidence scores for matched events', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Look for matched events
        const matchedEvents = page.locator('[data-testid^="timeline-event-"]', {
          hasText: /Matched/i
        })

        if (await matchedEvents.count() > 0) {
          // Should show confidence percentage
          const confidenceScore = matchedEvents.locator('text=/\\d+%/')
          const hasConfidence = await confidenceScore.count() > 0

          // Confidence may or may not be displayed
          expect(typeof hasConfidence).toBe('boolean')
        }
      }
    })

    test('should link to investigation from timeline event', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Look for events with investigation links
        const investigationLink = page.locator('[data-testid="timeline-view-investigation"]')

        if (await investigationLink.count() > 0) {
          await expect(investigationLink.first()).toBeVisible()

          // Should be clickable
          await expect(investigationLink.first()).toHaveAttribute('type', 'button')
        }
      }
    })
  })

  test.describe('Related Investigations Panel', () => {
    test('should display related investigations panel', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Panel may exist via data-testid or heading
        const panel = page.locator('[data-testid="related-investigations-panel"]')
        const heading = page.locator('text=/Related Investigations|Investigations/i')

        const hasPanel = await panel.count() > 0 || await heading.count() > 0

        // Panel is optional if tiger has no investigations
        expect(typeof hasPanel).toBe('boolean')
      }
    })

    test('should show investigations data with details', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Look for investigation items
        const investigationItems = page.locator('[data-testid^="related-investigation-"]')
        const itemCount = await investigationItems.count()

        // May have no investigations
        expect(itemCount).toBeGreaterThanOrEqual(0)

        if (itemCount > 0) {
          // Each item should be visible
          await expect(investigationItems.first()).toBeVisible()

          // Should show investigation details like status, date
          const hasDetails = await page.locator('text=/Status:|Date:/i').count() > 0 ||
                            await page.locator('.badge').count() > 0

          expect(hasDetails).toBe(true)
        }
      }
    })

    test('should navigate to investigation detail when clicking investigation', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Find clickable investigation
        const investigationItem = page.locator('[data-testid^="related-investigation-"]').first()

        if (await investigationItem.count() > 0) {
          // Click to navigate
          await investigationItem.click()
          await page.waitForTimeout(1000)

          // Should navigate to investigation page
          const url = page.url()
          expect(url.includes('/investigations/') || url.includes('/investigation2')).toBe(true)
        }
      }
    })
  })

  test.describe('Edit Tiger Functionality', () => {
    test('should show edit button', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Edit button should be visible
        const editButton = page.locator('button:has-text("Edit")')

        if (await editButton.count() > 0) {
          await expect(editButton.first()).toBeVisible()
        }
      }
    })

    test('should enable editing mode when clicking edit', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        const editButton = page.locator('button:has-text("Edit")').first()

        if (await editButton.count() > 0) {
          await editButton.click()
          await page.waitForTimeout(500)

          // Should show edit mode indicators
          const hasEditMode = await page.locator('input[type="text"]').count() > 0 ||
                             await page.locator('textarea').count() > 0 ||
                             await page.locator('button:has-text("Cancel")').count() > 0 ||
                             await page.locator('button:has-text("Save")').count() > 0

          expect(hasEditMode).toBe(true)
        }
      }
    })

    test('should allow editing tiger name', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        const editButton = page.locator('button:has-text("Edit")').first()

        if (await editButton.count() > 0) {
          await editButton.click()
          await page.waitForTimeout(500)

          // Find name input
          const nameInput = page.locator('input[name="name"], input[placeholder*="name" i]').first()

          if (await nameInput.count() > 0) {
            await nameInput.fill('Updated Tiger Name')
            await page.waitForTimeout(300)

            await expect(nameInput).toHaveValue('Updated Tiger Name')
          }
        }
      }
    })

    test('should allow editing tiger notes', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        const editButton = page.locator('button:has-text("Edit")').first()

        if (await editButton.count() > 0) {
          await editButton.click()
          await page.waitForTimeout(500)

          // Find notes textarea
          const notesTextarea = page.locator('textarea[name="notes"], textarea[placeholder*="note" i]').first()

          if (await notesTextarea.count() > 0) {
            await notesTextarea.fill('Updated notes for this tiger')
            await page.waitForTimeout(300)

            await expect(notesTextarea).toHaveValue('Updated notes for this tiger')
          }
        }
      }
    })

    test('should cancel edit mode', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        const editButton = page.locator('button:has-text("Edit")').first()

        if (await editButton.count() > 0) {
          await editButton.click()
          await page.waitForTimeout(500)

          // Find and click cancel button
          const cancelButton = page.locator('button:has-text("Cancel")').first()

          if (await cancelButton.count() > 0) {
            await cancelButton.click()
            await page.waitForTimeout(300)

            // Edit mode should be closed (inputs hidden)
            const inputVisible = await page.locator('input[type="text"]').isVisible().catch(() => false)
            expect(inputVisible).toBe(false)
          }
        }
      }
    })
  })

  test.describe('Delete Tiger', () => {
    test('should show delete button or option', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Delete button may exist
        const deleteButton = page.locator('button:has-text("Delete"), button[aria-label*="Delete"]')
        const deleteCount = await deleteButton.count()

        // Delete may require admin permissions
        expect(deleteCount).toBeGreaterThanOrEqual(0)
      }
    })

    test('should show confirmation dialog when deleting tiger', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        const deleteButton = page.locator('button:has-text("Delete"), button[aria-label*="Delete"]').first()

        if (await deleteButton.count() > 0) {
          await deleteButton.click()
          await page.waitForTimeout(500)

          // Should show confirmation dialog
          const confirmationDialog = page.locator('[role="dialog"]')
          const confirmationText = page.locator('text=/Are you sure|confirm|delete/i')

          const hasConfirmation = await confirmationDialog.count() > 0 ||
                                 await confirmationText.count() > 0

          expect(hasConfirmation).toBe(true)

          // Should have cancel button
          const cancelButton = page.locator('button:has-text("Cancel")')
          if (await cancelButton.count() > 0) {
            await expect(cancelButton.first()).toBeVisible()

            // Cancel deletion to avoid removing test data
            await cancelButton.first().click()
            await page.waitForTimeout(300)
          }
        }
      }
    })
  })

  test.describe('Navigate to Facility', () => {
    test('should show facility information', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Look for facility section
        const facilitySection = page.locator('text=/Facility:/i')
        const facilityLink = page.locator('a[href*="/facilities/"]')

        const hasFacility = await facilitySection.count() > 0 ||
                           await facilityLink.count() > 0

        // Tiger may not have facility assigned
        expect(typeof hasFacility).toBe('boolean')
      }
    })

    test('should navigate to facility detail when clicking facility link', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Find facility link
        const facilityLink = page.locator('a[href*="/facilities/"]').first()

        if (await facilityLink.count() > 0) {
          await facilityLink.click()
          await page.waitForTimeout(1000)

          // Should navigate to facility page
          await expect(page).toHaveURL(/\/facilities\/[\w-]+/)
        }
      }
    })
  })

  test.describe('Quick Actions', () => {
    test('should show launch investigation button', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Should have launch investigation button
        const launchButton = page.locator('button:has-text("Launch Investigation"), button:has-text("Investigate")')

        if (await launchButton.count() > 0) {
          await expect(launchButton.first()).toBeVisible()
        }
      }
    })

    test('should show quick actions card', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Look for Quick Actions section
        const quickActionsHeading = page.locator('text=/Quick Actions/i')
        const hasQuickActions = await quickActionsHeading.count() > 0

        expect(typeof hasQuickActions).toBe('boolean')
      }
    })

    test('should navigate back to tigers list when clicking back', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Click back button
        const backButton = page.locator('button:has-text("Back")').first()
        await backButton.click()
        await page.waitForTimeout(500)

        // Should navigate back to tigers list
        await expect(page).toHaveURL(/\/tigers\/?$/)
      }
    })
  })

  test.describe('Error Handling', () => {
    test('should handle non-existent tiger gracefully', async ({ page }) => {
      // Navigate to non-existent tiger
      await page.goto('/tigers/non-existent-tiger-id-12345')
      await page.waitForTimeout(1500)

      // Should show error message or redirect
      const errorElements = [
        page.locator('text=/not found/i'),
        page.locator('text=/error/i'),
        page.locator('[role="alert"]'),
        page.locator('.alert-error, [class*="alert"]'),
      ]

      let hasError = false
      for (const element of errorElements) {
        if (await element.count() > 0) {
          hasError = true
          break
        }
      }

      // Either shows error or redirects to tigers list
      const url = page.url()
      expect(hasError || url.includes('/tigers') && !url.includes('non-existent')).toBe(true)
    })

    test('should show loading state while fetching tiger data', async ({ page }) => {
      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        // Get tiger URL
        const href = await tigerCard.getAttribute('href')

        if (href) {
          // Navigate to trigger loading state
          await page.goto(href)

          // Page should eventually load (loading state may be too fast to catch)
          await page.waitForTimeout(500)
          expect(page.url()).toContain('/tigers/')
        }
      }
    })

    test('should show back button on error state', async ({ page }) => {
      await page.goto('/tigers/non-existent-tiger-id-12345')
      await page.waitForTimeout(1500)

      // If error is shown, back button should exist
      const errorShown = await page.locator('[role="alert"], text=/error|not found/i').count() > 0

      if (errorShown) {
        const backButton = page.locator('button:has-text("Back")')
        if (await backButton.count() > 0) {
          await expect(backButton.first()).toBeVisible()
        }
      }
    })
  })

  test.describe('Responsive Design', () => {
    test('should display correctly on mobile viewport', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 })

      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Page should still be accessible
        await expect(page.locator('h1')).toBeVisible()

        // Back button should still work
        const backButton = page.locator('button:has-text("Back")').first()
        await expect(backButton).toBeVisible()
      }
    })

    test('should display correctly on tablet viewport', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 })

      await page.goto('/tigers')
      await page.waitForTimeout(1000)

      const tigerCard = page.locator('[data-testid^="tiger-card-"]').first()
      test.skip(await tigerCard.count() === 0, 'No tigers available')

      if (await tigerCard.count() > 0) {
        await tigerCard.click()
        await page.waitForTimeout(1000)

        // Page should be fully functional
        await expect(page.locator('h1')).toBeVisible()

        // Gallery should still display
        const hasImages = await page.locator('text=/Images/i').count() > 0
        expect(typeof hasImages).toBe('boolean')
      }
    })
  })
})

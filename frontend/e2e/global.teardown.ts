import { FullConfig } from '@playwright/test'
import * as fs from 'fs'
import * as path from 'path'

/**
 * Global teardown for Playwright tests
 *
 * This function runs once after all tests to:
 * 1. Clean up test data created during tests
 * 2. Clear authentication storage state files
 * 3. Remove temporary test artifacts
 */
async function globalTeardown(config: FullConfig) {
  console.log('\n🧹 Running global teardown...')

  const authDir = path.join(process.cwd(), '.auth')

  try {
    // Clean up authentication storage state files
    if (fs.existsSync(authDir)) {
      const files = fs.readdirSync(authDir)

      for (const file of files) {
        // Only delete JSON storage state files and error screenshots
        if (file.endsWith('.json') || file.endsWith('.png')) {
          const filePath = path.join(authDir, file)
          try {
            fs.unlinkSync(filePath)
            console.log(`✅ Deleted: ${file}`)
          } catch (error) {
            console.warn(`⚠️  Failed to delete ${file}:`, error)
          }
        }
      }

      // Remove .auth directory if empty
      const remainingFiles = fs.readdirSync(authDir)
      if (remainingFiles.length === 0) {
        fs.rmdirSync(authDir)
        console.log('✅ Removed .auth directory')
      }
    }

    // Clean up test data from database
    await cleanupTestData(config)

    console.log('✅ Global teardown completed successfully\n')
  } catch (error) {
    console.error('❌ Global teardown failed:', error)
    // Don't throw - teardown failures shouldn't fail the test run
  }
}

/**
 * Clean up test data created during tests
 *
 * This should remove:
 * - Test tigers created with IDs starting with 'test_'
 * - Test facilities created with names starting with 'Test '
 * - Test investigations created during test runs
 * - Uploaded test images and their embeddings
 */
async function cleanupTestData(config: FullConfig) {
  console.log('🗑️  Cleaning up test data...')

  try {
    const apiURL = process.env.API_URL || 'http://localhost:8000'

    // TODO: Implement API calls to clean up test data
    // This would typically call DELETE endpoints with test data identifiers

    // Example implementation:
    // const response = await fetch(`${apiURL}/api/test-cleanup`, {
    //   method: 'DELETE',
    //   headers: {
    //     'Content-Type': 'application/json',
    //     'Authorization': `Bearer ${adminToken}`
    //   }
    // })

    // For now, just log that cleanup is available
    console.log('   Test data cleanup available via API (implement as needed)')
  } catch (error) {
    console.warn('⚠️  Failed to clean up test data:', error)
    // Don't throw - data cleanup failures shouldn't fail teardown
  }
}

export default globalTeardown

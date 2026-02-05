import * as path from 'path'
import * as fs from 'fs'

/**
 * Helper functions for managing test fixtures
 */

export const FIXTURES_DIR = path.join(__dirname, '../fixtures')

export const FIXTURE_PATHS = {
  tiger: path.join(FIXTURES_DIR, 'tiger.jpg'),
  tiger2: path.join(FIXTURES_DIR, 'tiger2.jpg'),
  invalidFile: path.join(FIXTURES_DIR, 'test.txt'),
}

/**
 * Check if a fixture file exists
 */
export function fixtureExists(fixtureName: keyof typeof FIXTURE_PATHS): boolean {
  return fs.existsSync(FIXTURE_PATHS[fixtureName])
}

/**
 * Get fixture path, returns null if not found
 */
export function getFixturePath(fixtureName: keyof typeof FIXTURE_PATHS): string | null {
  const fixturePath = FIXTURE_PATHS[fixtureName]
  return fs.existsSync(fixturePath) ? fixturePath : null
}

/**
 * Create a minimal valid JPEG file for testing if fixtures are missing
 * This creates a 1x1 pixel JPEG that's valid but minimal
 */
export function createMinimalJpeg(outputPath: string): void {
  // Minimal valid JPEG (1x1 pixel, black)
  const minimalJpeg = Buffer.from([
    0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10, 0x4a, 0x46,
    0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01,
    0x00, 0x01, 0x00, 0x00, 0xff, 0xdb, 0x00, 0x43,
    0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
    0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0a, 0x0c,
    0x14, 0x0d, 0x0c, 0x0b, 0x0b, 0x0c, 0x19, 0x12,
    0x13, 0x0f, 0x14, 0x1d, 0x1a, 0x1f, 0x1e, 0x1d,
    0x1a, 0x1c, 0x1c, 0x20, 0x24, 0x2e, 0x27, 0x20,
    0x22, 0x2c, 0x23, 0x1c, 0x1c, 0x28, 0x37, 0x29,
    0x2c, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1f, 0x27,
    0x39, 0x3d, 0x38, 0x32, 0x3c, 0x2e, 0x33, 0x34,
    0x32, 0xff, 0xc0, 0x00, 0x0b, 0x08, 0x00, 0x01,
    0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xff, 0xc4,
    0x00, 0x14, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x08, 0xff, 0xc4, 0x00, 0x14,
    0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xff, 0xda, 0x00, 0x08, 0x01, 0x01,
    0x00, 0x00, 0x3f, 0x00, 0x7f, 0x18, 0xff, 0xd9,
  ])

  fs.writeFileSync(outputPath, minimalJpeg)
}

/**
 * Ensure test fixtures exist, creating minimal ones if needed
 */
export function ensureFixtures(): void {
  // Ensure fixtures directory exists
  if (!fs.existsSync(FIXTURES_DIR)) {
    fs.mkdirSync(FIXTURES_DIR, { recursive: true })
  }

  // Create minimal JPEGs if they don't exist
  if (!fixtureExists('tiger')) {
    console.log('Creating minimal tiger.jpg fixture...')
    createMinimalJpeg(FIXTURE_PATHS.tiger)
  }

  if (!fixtureExists('tiger2')) {
    console.log('Creating minimal tiger2.jpg fixture...')
    createMinimalJpeg(FIXTURE_PATHS.tiger2)
  }

  // Ensure test.txt exists
  if (!fixtureExists('invalidFile')) {
    console.log('Creating test.txt fixture...')
    fs.writeFileSync(FIXTURE_PATHS.invalidFile, 'This is not an image file.')
  }
}

/**
 * Clean up generated fixtures (call in afterAll if needed)
 */
export function cleanupGeneratedFixtures(): void {
  // Only remove if they are minimal (< 1KB)
  Object.values(FIXTURE_PATHS).forEach((fixturePath) => {
    if (fs.existsSync(fixturePath)) {
      const stats = fs.statSync(fixturePath)
      if (stats.size < 1024) {
        // Less than 1KB, likely generated
        fs.unlinkSync(fixturePath)
      }
    }
  })
}

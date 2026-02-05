#!/usr/bin/env node

/**
 * Visual Regression Test Validation Script
 *
 * Validates that visual regression test setup is correct before running tests.
 * Checks for required files, configuration, and provides helpful guidance.
 */

const fs = require('fs')
const path = require('path')

const COLORS = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
}

function log(message, color = 'reset') {
  console.log(`${COLORS[color]}${message}${COLORS.reset}`)
}

function checkFileExists(filePath, description) {
  if (fs.existsSync(filePath)) {
    log(`✓ ${description}`, 'green')
    return true
  } else {
    log(`✗ ${description} - NOT FOUND: ${filePath}`, 'red')
    return false
  }
}

function checkDirectoryExists(dirPath, description) {
  if (fs.existsSync(dirPath) && fs.statSync(dirPath).isDirectory()) {
    log(`✓ ${description}`, 'green')
    return true
  } else {
    log(`✗ ${description} - NOT FOUND: ${dirPath}`, 'red')
    return false
  }
}

function main() {
  log('\n=== Visual Regression Test Validation ===\n', 'blue')

  let allChecksPass = true

  // Check test file
  log('Checking test files:', 'blue')
  allChecksPass &= checkFileExists('e2e/visual.spec.ts', 'Visual test file')
  allChecksPass &= checkFileExists('e2e/visual-config.ts', 'Visual config file')
  allChecksPass &= checkFileExists('e2e/helpers/visual.ts', 'Visual helpers file')
  allChecksPass &= checkFileExists('e2e/helpers/auth.ts', 'Auth helpers file')
  console.log()

  // Check configuration
  log('Checking configuration:', 'blue')
  allChecksPass &= checkFileExists('playwright.config.ts', 'Playwright config')
  allChecksPass &= checkFileExists('package.json', 'package.json')
  console.log()

  // Check package.json scripts
  log('Checking npm scripts:', 'blue')
  try {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf-8'))
    if (packageJson.scripts['test:e2e:visual']) {
      log('✓ npm script test:e2e:visual exists', 'green')
    } else {
      log('✗ npm script test:e2e:visual missing', 'red')
      allChecksPass = false
    }
    if (packageJson.scripts['test:e2e:visual:update']) {
      log('✓ npm script test:e2e:visual:update exists', 'green')
    } else {
      log('✗ npm script test:e2e:visual:update missing', 'red')
      allChecksPass = false
    }
  } catch (error) {
    log('✗ Error reading package.json', 'red')
    allChecksPass = false
  }
  console.log()

  // Check directories
  log('Checking directories:', 'blue')
  checkDirectoryExists('e2e', 'e2e directory')
  checkDirectoryExists('e2e/helpers', 'e2e/helpers directory')
  checkDirectoryExists('e2e/fixtures', 'e2e/fixtures directory')

  // Check/create screenshots directory
  if (!fs.existsSync('screenshots')) {
    fs.mkdirSync('screenshots', { recursive: true })
    log('✓ Created screenshots directory', 'yellow')
  } else {
    log('✓ screenshots directory exists', 'green')
  }

  console.log()

  // Check for baseline snapshots
  log('Checking baseline snapshots:', 'blue')
  if (fs.existsSync('e2e/__snapshots__')) {
    const files = fs.readdirSync('e2e/__snapshots__')
    if (files.length > 0) {
      log(`✓ Found ${files.length} snapshot directories`, 'green')
    } else {
      log('⚠ No baseline snapshots found - run with --update-snapshots first', 'yellow')
    }
  } else {
    log('⚠ No snapshots directory - run tests with --update-snapshots to create', 'yellow')
  }
  console.log()

  // Check documentation
  log('Checking documentation:', 'blue')
  allChecksPass &= checkFileExists(
    'e2e/VISUAL_REGRESSION_TESTING.md',
    'Visual regression testing guide'
  )
  allChecksPass &= checkFileExists('e2e/README.md', 'E2E test README')
  console.log()

  // Final summary
  if (allChecksPass) {
    log('=== All checks passed! ===', 'green')
    log('\nTo run visual tests:', 'blue')
    log('  npm run test:e2e:visual', 'yellow')
    log('\nTo create/update baseline snapshots:', 'blue')
    log('  npm run test:e2e:visual:update', 'yellow')
    log('\nTo run in UI mode:', 'blue')
    log('  npm run test:e2e:visual:ui', 'yellow')
    process.exit(0)
  } else {
    log('\n=== Some checks failed ===', 'red')
    log('Please fix the issues above before running visual tests.', 'yellow')
    process.exit(1)
  }
}

main()

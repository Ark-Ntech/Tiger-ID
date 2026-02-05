#!/usr/bin/env node

/**
 * Visual Regression Test Runner
 *
 * Comprehensive test runner for visual regression tests with options for:
 * - Running all visual tests
 * - Updating baseline snapshots
 * - Running specific test groups
 * - Generating reports
 * - Running tests in different browsers
 */

const { spawn } = require('child_process')
const fs = require('fs')
const path = require('path')

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
}

const log = {
  info: (msg) => console.log(`${colors.blue}ℹ${colors.reset} ${msg}`),
  success: (msg) => console.log(`${colors.green}✓${colors.reset} ${msg}`),
  error: (msg) => console.log(`${colors.red}✗${colors.reset} ${msg}`),
  warning: (msg) => console.log(`${colors.yellow}⚠${colors.reset} ${msg}`),
  header: (msg) => console.log(`\n${colors.bright}${colors.cyan}${msg}${colors.reset}\n`),
}

// Parse command line arguments
const args = process.argv.slice(2)
const command = args[0] || 'run'

// Test groups available
const testGroups = {
  auth: 'Authentication Pages',
  dashboard: 'Dashboard',
  tigers: 'Tigers',
  investigation: 'Investigation',
  discovery: 'Discovery',
  facilities: 'Facilities',
  verification: 'Verification',
  templates: 'Templates',
  components: 'Component',
  responsive: 'Responsive',
}

/**
 * Run Playwright command
 */
function runPlaywright(args, options = {}) {
  return new Promise((resolve, reject) => {
    const isWindows = process.platform === 'win32'
    const cmd = isWindows ? 'npx.cmd' : 'npx'

    log.info(`Running: npx playwright ${args.join(' ')}`)

    const proc = spawn(cmd, ['playwright', ...args], {
      stdio: 'inherit',
      cwd: __dirname,
      ...options,
    })

    proc.on('close', (code) => {
      if (code === 0) {
        resolve()
      } else {
        reject(new Error(`Process exited with code ${code}`))
      }
    })

    proc.on('error', (err) => {
      reject(err)
    })
  })
}

/**
 * Display usage information
 */
function showUsage() {
  log.header('Visual Regression Test Runner')

  console.log('Usage: node run-visual-tests.js [command] [options]\n')

  console.log('Commands:')
  console.log('  run              Run all visual regression tests (default)')
  console.log('  update           Update baseline snapshots')
  console.log('  ui               Run tests in UI mode (interactive)')
  console.log('  headed           Run tests in headed mode (see browser)')
  console.log('  report           Show test report')
  console.log('  group <name>     Run specific test group')
  console.log('  browser <name>   Run tests on specific browser')
  console.log('  help             Show this help message\n')

  console.log('Test Groups:')
  Object.entries(testGroups).forEach(([key, value]) => {
    console.log(`  ${key.padEnd(15)} ${value}`)
  })
  console.log()

  console.log('Browsers:')
  console.log('  chromium         Google Chrome/Edge')
  console.log('  firefox          Mozilla Firefox')
  console.log('  webkit           Apple Safari\n')

  console.log('Examples:')
  console.log('  node run-visual-tests.js run')
  console.log('  node run-visual-tests.js update')
  console.log('  node run-visual-tests.js group auth')
  console.log('  node run-visual-tests.js browser firefox')
  console.log('  node run-visual-tests.js ui')
  console.log()
}

/**
 * Run all visual regression tests
 */
async function runTests() {
  log.header('Running All Visual Regression Tests')

  try {
    await runPlaywright(['test', 'tests/visual'])
    log.success('All visual tests completed')
    return true
  } catch (error) {
    log.error('Visual tests failed')
    return false
  }
}

/**
 * Update baseline snapshots
 */
async function updateSnapshots() {
  log.header('Updating Baseline Snapshots')
  log.warning('This will overwrite existing baseline snapshots')

  try {
    await runPlaywright(['test', 'tests/visual', '--update-snapshots'])
    log.success('Baseline snapshots updated')
    log.info('Please review and commit the updated snapshots')
    return true
  } catch (error) {
    log.error('Failed to update snapshots')
    return false
  }
}

/**
 * Run tests in UI mode
 */
async function runUI() {
  log.header('Starting Tests in UI Mode')

  try {
    await runPlaywright(['test', 'tests/visual', '--ui'])
    return true
  } catch (error) {
    log.error('UI mode failed')
    return false
  }
}

/**
 * Run tests in headed mode
 */
async function runHeaded() {
  log.header('Running Tests in Headed Mode')

  try {
    await runPlaywright(['test', 'tests/visual', '--headed'])
    log.success('Headed tests completed')
    return true
  } catch (error) {
    log.error('Headed tests failed')
    return false
  }
}

/**
 * Show test report
 */
async function showReport() {
  log.header('Opening Test Report')

  try {
    await runPlaywright(['show-report'])
    return true
  } catch (error) {
    log.error('Failed to open report')
    return false
  }
}

/**
 * Run specific test group
 */
async function runGroup(groupName) {
  const groupPattern = testGroups[groupName]

  if (!groupPattern) {
    log.error(`Unknown test group: ${groupName}`)
    log.info('Available groups: ' + Object.keys(testGroups).join(', '))
    return false
  }

  log.header(`Running ${groupPattern} Tests`)

  try {
    await runPlaywright(['test', 'tests/visual', '-g', groupPattern])
    log.success(`${groupPattern} tests completed`)
    return true
  } catch (error) {
    log.error(`${groupPattern} tests failed`)
    return false
  }
}

/**
 * Run tests on specific browser
 */
async function runBrowser(browserName) {
  const validBrowsers = ['chromium', 'firefox', 'webkit']

  if (!validBrowsers.includes(browserName)) {
    log.error(`Unknown browser: ${browserName}`)
    log.info('Available browsers: ' + validBrowsers.join(', '))
    return false
  }

  log.header(`Running Tests on ${browserName}`)

  try {
    await runPlaywright(['test', 'tests/visual', `--project=${browserName}`])
    log.success(`${browserName} tests completed`)
    return true
  } catch (error) {
    log.error(`${browserName} tests failed`)
    return false
  }
}

/**
 * Check prerequisites
 */
function checkPrerequisites() {
  log.info('Checking prerequisites...')

  // Check if Playwright is installed
  const nodeModulesPath = path.join(__dirname, 'node_modules', '@playwright', 'test')
  if (!fs.existsSync(nodeModulesPath)) {
    log.error('Playwright is not installed')
    log.info('Run: npm install')
    return false
  }

  // Check if test file exists
  const testFilePath = path.join(__dirname, 'e2e', 'tests', 'visual', 'visual.spec.ts')
  if (!fs.existsSync(testFilePath)) {
    log.error('Visual test file not found: e2e/tests/visual/visual.spec.ts')
    return false
  }

  log.success('Prerequisites check passed')
  return true
}

/**
 * Main execution
 */
async function main() {
  // Check prerequisites first
  if (!checkPrerequisites()) {
    process.exit(1)
  }

  let success = false

  switch (command) {
    case 'run':
      success = await runTests()
      break

    case 'update':
      success = await updateSnapshots()
      break

    case 'ui':
      success = await runUI()
      break

    case 'headed':
      success = await runHeaded()
      break

    case 'report':
      success = await showReport()
      break

    case 'group':
      if (args.length < 2) {
        log.error('Please specify a test group')
        log.info('Usage: node run-visual-tests.js group <name>')
        showUsage()
        process.exit(1)
      }
      success = await runGroup(args[1])
      break

    case 'browser':
      if (args.length < 2) {
        log.error('Please specify a browser')
        log.info('Usage: node run-visual-tests.js browser <name>')
        showUsage()
        process.exit(1)
      }
      success = await runBrowser(args[1])
      break

    case 'help':
    case '--help':
    case '-h':
      showUsage()
      process.exit(0)
      break

    default:
      log.error(`Unknown command: ${command}`)
      showUsage()
      process.exit(1)
  }

  if (success) {
    log.success('\nTest run completed successfully')
    process.exit(0)
  } else {
    log.error('\nTest run failed')
    process.exit(1)
  }
}

// Run the script
main().catch((error) => {
  log.error(`Unexpected error: ${error.message}`)
  process.exit(1)
})

#!/usr/bin/env node

/**
 * Tiger ID E2E Test Runner
 *
 * Executes Playwright E2E tests and generates a summary report.
 *
 * Usage:
 *   node run-e2e-tests.js [options]
 *
 * Options:
 *   --suite <name>   Run specific test suite (auth, investigation, tiger, facility, verification, discovery)
 *   --browser <name> Run on specific browser (chromium, firefox, webkit)
 *   --headed        Run tests in headed mode (visible browser)
 *   --ui            Run tests in UI mode (interactive)
 *   --debug         Run tests in debug mode
 */

const { spawn } = require('child_process')
const path = require('path')

// Parse command line arguments
const args = process.argv.slice(2)
const options = {
  suite: null,
  browser: null,
  headed: false,
  ui: false,
  debug: false
}

// Parse arguments
for (let i = 0; i < args.length; i++) {
  switch (args[i]) {
    case '--suite':
      options.suite = args[++i]
      break
    case '--browser':
      options.browser = args[++i]
      break
    case '--headed':
      options.headed = true
      break
    case '--ui':
      options.ui = true
      break
    case '--debug':
      options.debug = true
      break
  }
}

// Build Playwright command
const playwrightArgs = ['test']

// Add suite filter
if (options.suite) {
  const suiteMap = {
    'auth': 'auth-flow',
    'investigation': 'investigation-flow',
    'tiger': 'tiger-management',
    'facility': 'facility-management',
    'verification': 'verification-flow',
    'discovery': 'discovery-flow'
  }
  const suiteName = suiteMap[options.suite] || options.suite
  playwrightArgs.push(suiteName)
}

// Add browser filter
if (options.browser) {
  playwrightArgs.push('--project', options.browser)
}

// Add mode options
if (options.headed) {
  playwrightArgs.push('--headed')
}

if (options.ui) {
  playwrightArgs.push('--ui')
}

if (options.debug) {
  playwrightArgs.push('--debug')
}

// Log test execution info
console.log('\n' + '='.repeat(60))
console.log('Tiger ID E2E Test Runner')
console.log('='.repeat(60))
console.log('\nConfiguration:')
console.log(`  Suite: ${options.suite || 'all'}`)
console.log(`  Browser: ${options.browser || 'all (chromium, firefox, webkit)'}`)
console.log(`  Mode: ${options.ui ? 'UI' : options.debug ? 'Debug' : options.headed ? 'Headed' : 'Headless'}`)
console.log('\n' + '-'.repeat(60) + '\n')

// Execute Playwright
const playwright = spawn('npx', ['playwright', ...playwrightArgs], {
  stdio: 'inherit',
  shell: true,
  cwd: __dirname
})

playwright.on('error', (error) => {
  console.error('\n❌ Failed to start Playwright:', error.message)
  process.exit(1)
})

playwright.on('close', (code) => {
  console.log('\n' + '-'.repeat(60))

  if (code === 0) {
    console.log('\n✅ All tests passed!')
    console.log('\nTo view the HTML report, run:')
    console.log('  npx playwright show-report')
  } else {
    console.log(`\n❌ Tests failed with exit code ${code}`)
    console.log('\nTo debug failures:')
    console.log('  1. Check test-results/ directory for screenshots')
    console.log('  2. Run with --debug flag for step-by-step debugging')
    console.log('  3. Run with --ui flag for interactive test UI')
  }

  console.log('\n' + '='.repeat(60) + '\n')
  process.exit(code)
})

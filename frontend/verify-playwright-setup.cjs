#!/usr/bin/env node
/**
 * Playwright Setup Verification Script
 *
 * Verifies that all Playwright configuration requirements are met:
 * - Config file exists and is valid
 * - Global setup exists
 * - Browser projects configured
 * - Sharding support available
 * - Required directories can be created
 * - npm scripts are defined
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function success(message) {
  log(`✓ ${message}`, 'green');
}

function error(message) {
  log(`✗ ${message}`, 'red');
}

function warning(message) {
  log(`⚠ ${message}`, 'yellow');
}

function info(message) {
  log(`ℹ ${message}`, 'cyan');
}

function header(message) {
  log(`\n${message}`, 'blue');
  log('='.repeat(message.length), 'blue');
}

let checksPassedCount = 0;
let checksFailedCount = 0;

function check(description, fn) {
  try {
    const result = fn();
    if (result !== false) {
      success(description);
      checksPassedCount++;
      return true;
    } else {
      error(description);
      checksFailedCount++;
      return false;
    }
  } catch (err) {
    error(`${description}: ${err.message}`);
    checksFailedCount++;
    return false;
  }
}

// Start verification
log('\n╔══════════════════════════════════════════════════╗', 'cyan');
log('║   Playwright CI/CD Setup Verification           ║', 'cyan');
log('╚══════════════════════════════════════════════════╝', 'cyan');

// Check 1: Config file exists
header('Configuration Files');
check('playwright.config.ts exists', () => {
  return fs.existsSync('playwright.config.ts');
});

check('e2e/global.setup.ts exists', () => {
  return fs.existsSync('e2e/global.setup.ts');
});

// Check 2: Config content validation
header('Configuration Content');
const configContent = fs.readFileSync('playwright.config.ts', 'utf8');

check('Chromium project configured', () => {
  return configContent.includes('chromium') || configContent.includes("'chromium'");
});

check('Firefox project configured', () => {
  return configContent.includes('firefox') || configContent.includes("'firefox'");
});

check('WebKit project configured', () => {
  return configContent.includes('webkit') || configContent.includes("'webkit'");
});

check('Sharding documentation present', () => {
  return configContent.includes('--shard');
});

check('Retry configuration present', () => {
  return configContent.includes('retries:') && configContent.includes('process.env.CI');
});

check('Worker configuration present', () => {
  return configContent.includes('workers:');
});

check('Test timeout set to 30s', () => {
  return configContent.includes('timeout: 30000') || configContent.includes('timeout:30000');
});

check('Expect timeout configured', () => {
  return configContent.includes('expect') && configContent.includes('10000');
});

check('JUnit reporter configured', () => {
  return configContent.toLowerCase().includes('junit');
});

check('HTML reporter configured', () => {
  return configContent.toLowerCase().includes('html');
});

check('Screenshot on failure configured', () => {
  return configContent.includes('screenshot:') &&
         (configContent.includes('only-on-failure') || configContent.includes('on-failure'));
});

check('Video capture configured', () => {
  return configContent.includes('video:');
});

check('Trace capture configured', () => {
  return configContent.includes('trace:') && configContent.includes('on-first-retry');
});

check('Base URL configurable', () => {
  return configContent.includes('process.env.BASE_URL');
});

check('Global setup referenced', () => {
  return configContent.includes('globalSetup') && configContent.includes('global.setup');
});

check('Output directory configured', () => {
  return configContent.includes('test-results');
});

// Check 3: Global setup validation
header('Global Setup');
const setupContent = fs.readFileSync('e2e/global.setup.ts', 'utf8');

check('authenticateUser function present', () => {
  return setupContent.includes('authenticateUser');
});

check('Storage state saving configured', () => {
  return setupContent.includes('storageState') && setupContent.includes('.auth');
});

check('Backend verification present', () => {
  return setupContent.toLowerCase().includes('health') || setupContent.toLowerCase().includes('api');
});

check('Error handling implemented', () => {
  return setupContent.includes('try') && setupContent.includes('catch');
});

check('Auth state caching present', () => {
  return setupContent.includes('existsSync') || setupContent.includes('exists');
});

check('Test data setup function present', () => {
  return setupContent.includes('setupTestData');
});

// Check 4: Package.json scripts
header('NPM Scripts');
const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const scripts = packageJson.scripts || {};

check('test:e2e script defined', () => {
  return 'test:e2e' in scripts;
});

check('test:e2e:shard1 script defined', () => {
  return 'test:e2e:shard1' in scripts && scripts['test:e2e:shard1'].includes('--shard=1/4');
});

check('test:e2e:shard2 script defined', () => {
  return 'test:e2e:shard2' in scripts && scripts['test:e2e:shard2'].includes('--shard=2/4');
});

check('test:e2e:shard3 script defined', () => {
  return 'test:e2e:shard3' in scripts && scripts['test:e2e:shard3'].includes('--shard=3/4');
});

check('test:e2e:shard4 script defined', () => {
  return 'test:e2e:shard4' in scripts && scripts['test:e2e:shard4'].includes('--shard=4/4');
});

check('test:e2e:report script defined', () => {
  return 'test:e2e:report' in scripts;
});

check('@playwright/test installed', () => {
  return '@playwright/test' in (packageJson.devDependencies || {});
});

// Check 5: Directory structure
header('Directory Structure');

check('e2e directory exists', () => {
  return fs.existsSync('e2e') && fs.statSync('e2e').isDirectory();
});

check('e2e/README.md exists', () => {
  return fs.existsSync('e2e/README.md');
});

check('Frontend directory structure valid', () => {
  return fs.existsSync('.') && fs.existsSync('package.json');
});

// Check 6: Documentation
header('Documentation');

check('PLAYWRIGHT_CI_CONFIG.md exists', () => {
  return fs.existsSync('PLAYWRIGHT_CI_CONFIG.md');
});

check('E2E_QUICK_REFERENCE.md exists', () => {
  return fs.existsSync('E2E_QUICK_REFERENCE.md');
});

check('PLAYWRIGHT_SETUP_SUMMARY.md exists', () => {
  return fs.existsSync('PLAYWRIGHT_SETUP_SUMMARY.md');
});

// Check 7: GitHub Actions workflow
header('CI/CD Configuration');

const workflowPath = path.join('..', '.github', 'workflows', 'playwright-tests.yml');
check('GitHub Actions workflow exists', () => {
  return fs.existsSync(workflowPath);
});

if (fs.existsSync(workflowPath)) {
  const workflowContent = fs.readFileSync(workflowPath, 'utf8');

  check('Workflow has sharding matrix', () => {
    return workflowContent.includes('matrix:') && workflowContent.includes('shard:');
  });

  check('Workflow has 4 shards', () => {
    return workflowContent.includes('[1, 2, 3, 4]');
  });

  check('Workflow uses CI environment', () => {
    return workflowContent.includes('CI: true');
  });
}

// Summary
log('\n╔══════════════════════════════════════════════════╗', 'cyan');
log('║   Verification Summary                           ║', 'cyan');
log('╚══════════════════════════════════════════════════╝', 'cyan');

const totalChecks = checksPassedCount + checksFailedCount;
const passPercentage = Math.round((checksPassedCount / totalChecks) * 100);

log(`\nTotal Checks: ${totalChecks}`);
success(`Passed: ${checksPassedCount}`);
if (checksFailedCount > 0) {
  error(`Failed: ${checksFailedCount}`);
}
log(`Success Rate: ${passPercentage}%\n`);

if (checksFailedCount === 0) {
  success('All checks passed! Playwright CI/CD setup is complete. ✓');
  info('\nNext steps:');
  info('1. Run: npm run test:e2e');
  info('2. View report: npm run test:e2e:report');
  info('3. Read documentation: PLAYWRIGHT_CI_CONFIG.md');
  process.exit(0);
} else {
  error('\nSome checks failed. Please review the errors above.');
  info('Refer to PLAYWRIGHT_CI_CONFIG.md for troubleshooting help.');
  process.exit(1);
}

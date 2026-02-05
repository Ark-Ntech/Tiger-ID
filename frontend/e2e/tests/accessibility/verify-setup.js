#!/usr/bin/env node

/**
 * Verification script for accessibility test setup
 *
 * Checks:
 * 1. @axe-core/playwright is installed
 * 2. Test files exist
 * 3. npm scripts are configured
 * 4. Playwright is installed
 *
 * Usage: node verify-setup.js
 */

const fs = require('fs');
const path = require('path');

const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const RESET = '\x1b[0m';

function checkFile(filePath, description) {
  if (fs.existsSync(filePath)) {
    console.log(`${GREEN}✓${RESET} ${description}`);
    return true;
  } else {
    console.log(`${RED}✗${RESET} ${description}`);
    return false;
  }
}

function checkPackage(packageName) {
  const packageJsonPath = path.join(__dirname, '..', '..', '..', 'package.json');

  if (!fs.existsSync(packageJsonPath)) {
    console.log(`${RED}✗${RESET} package.json not found`);
    return false;
  }

  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  const devDeps = packageJson.devDependencies || {};

  if (devDeps[packageName]) {
    console.log(`${GREEN}✓${RESET} ${packageName} installed (${devDeps[packageName]})`);
    return true;
  } else {
    console.log(`${RED}✗${RESET} ${packageName} not installed`);
    console.log(`  Run: npm install --save-dev ${packageName}`);
    return false;
  }
}

function checkNpmScript(scriptName) {
  const packageJsonPath = path.join(__dirname, '..', '..', '..', 'package.json');

  if (!fs.existsSync(packageJsonPath)) {
    return false;
  }

  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  const scripts = packageJson.scripts || {};

  if (scripts[scriptName]) {
    console.log(`${GREEN}✓${RESET} npm script '${scriptName}' configured`);
    return true;
  } else {
    console.log(`${RED}✗${RESET} npm script '${scriptName}' not configured`);
    return false;
  }
}

console.log('\n=== Accessibility Test Setup Verification ===\n');

console.log('Checking packages...');
const axeCoreInstalled = checkPackage('@axe-core/playwright');
const playwrightInstalled = checkPackage('@playwright/test');

console.log('\nChecking test files...');
const testFile = checkFile(
  path.join(__dirname, 'accessibility.spec.ts'),
  'accessibility.spec.ts exists'
);
const readmeFile = checkFile(
  path.join(__dirname, 'README.md'),
  'README.md exists'
);
const installFile = checkFile(
  path.join(__dirname, 'INSTALLATION.md'),
  'INSTALLATION.md exists'
);
const scenariosFile = checkFile(
  path.join(__dirname, 'TEST_SCENARIOS.md'),
  'TEST_SCENARIOS.md exists'
);
const summaryFile = checkFile(
  path.join(__dirname, 'SUMMARY.md'),
  'SUMMARY.md exists'
);

console.log('\nChecking npm scripts...');
const scriptConfigured = checkNpmScript('test:e2e:accessibility');

console.log('\n===========================================\n');

const allChecks = [
  axeCoreInstalled,
  playwrightInstalled,
  testFile,
  readmeFile,
  installFile,
  scenariosFile,
  summaryFile,
  scriptConfigured
];

const passedChecks = allChecks.filter(c => c).length;
const totalChecks = allChecks.length;

if (passedChecks === totalChecks) {
  console.log(`${GREEN}✓ All checks passed (${passedChecks}/${totalChecks})${RESET}`);
  console.log('\nYou can now run accessibility tests:');
  console.log('  npm run test:e2e:accessibility');
  console.log('  npx playwright test accessibility --ui');
  process.exit(0);
} else {
  console.log(`${YELLOW}⚠ ${passedChecks}/${totalChecks} checks passed${RESET}`);

  if (!axeCoreInstalled) {
    console.log('\nTo install @axe-core/playwright:');
    console.log('  cd frontend');
    console.log('  npm install --save-dev @axe-core/playwright');
  }

  console.log('\nSee INSTALLATION.md for complete setup instructions.');
  process.exit(1);
}

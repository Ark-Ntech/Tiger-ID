#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

console.log('Validating test files...\n');

let totalIssues = 0;
const issues = [];

function validateTestFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const fileName = path.basename(filePath);
  const fileIssues = [];

  // Check for proper imports
  if (content.includes("'@testing-library/jest-dom/vitest'") && !content.includes("import '@testing-library/jest-dom/vitest'")) {
    // This is actually correct usage
  }

  // Check for afterEach without import
  if (content.includes('afterEach(') && !content.includes('afterEach } from')) {
    fileIssues.push('Uses afterEach but does not import it');
  }

  // Check for beforeEach without import
  if (content.includes('beforeEach(') && !content.includes('beforeEach } from')) {
    fileIssues.push('Uses beforeEach but does not import it');
  }

  // Check for toHaveBeenCalledOnce without proper setup
  if (content.includes('toHaveBeenCalledOnce()') || content.includes('toHaveBeenCalled()')) {
    // This is fine with vitest's vi.fn()
  }

  return fileIssues;
}

// Find all test files
function findTestFiles(dir) {
  const files = [];
  const items = fs.readdirSync(dir);

  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory() && item === '__tests__') {
      const testFiles = fs.readdirSync(fullPath)
        .filter(f => f.endsWith('.test.tsx') || f.endsWith('.test.ts'))
        .map(f => path.join(fullPath, f));
      files.push(...testFiles);
    } else if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
      files.push(...findTestFiles(fullPath));
    }
  }

  return files;
}

const testFiles = findTestFiles(path.join(__dirname, 'src', 'components'));

console.log(`Found ${testFiles.length} test files\n`);

for (const file of testFiles) {
  const fileIssues = validateTestFile(file);
  if (fileIssues.length > 0) {
    issues.push({ file: path.relative(__dirname, file), issues: fileIssues });
    totalIssues += fileIssues.length;
  }
}

if (totalIssues === 0) {
  console.log('✓ All test files validated successfully!');
} else {
  console.log(`Found ${totalIssues} issues:\n`);
  for (const { file, issues: fileIssues } of issues) {
    console.log(`${file}:`);
    fileIssues.forEach(issue => console.log(`  - ${issue}`));
    console.log('');
  }
}

process.exit(totalIssues);

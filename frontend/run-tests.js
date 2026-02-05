#!/usr/bin/env node

// Simple test runner that executes vitest and captures output
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const outputFile = path.join(__dirname, 'test-results.txt');

console.log('Running frontend component tests...');

const testProcess = spawn('npm', ['test', '--', '--run', 'src/components/'], {
  cwd: __dirname,
  shell: true,
  stdio: 'pipe'
});

let output = '';

testProcess.stdout.on('data', (data) => {
  const text = data.toString();
  output += text;
  process.stdout.write(text);
});

testProcess.stderr.on('data', (data) => {
  const text = data.toString();
  output += text;
  process.stderr.write(text);
});

testProcess.on('close', (code) => {
  fs.writeFileSync(outputFile, output);
  console.log(`\nTest results written to: ${outputFile}`);
  console.log(`Exit code: ${code}`);
  process.exit(code);
});

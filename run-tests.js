const { spawn } = require('child_process');
const path = require('path');

const frontendDir = path.join(__dirname, 'frontend');
const testFiles = [
  'src/pages/__tests__/PasswordReset.test.tsx',
  'src/pages/__tests__/DatasetManagement.test.tsx'
];

const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const args = ['test', '--', '--run', ...testFiles];

console.log('Running tests in:', frontendDir);
console.log('Command:', npm, args.join(' '));

const proc = spawn(npm, args, {
  cwd: frontendDir,
  stdio: 'inherit',
  shell: true
});

proc.on('close', (code) => {
  process.exit(code);
});

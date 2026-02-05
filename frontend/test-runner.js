// Temporary test runner to execute tests
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

async function runTests() {
  try {
    const { stdout, stderr } = await execAsync(
      'npm test -- --run src/pages/__tests__/Login.test.tsx src/pages/__tests__/NotFound.test.tsx src/pages/__tests__/Home.test.tsx src/pages/__tests__/Dashboard.test.tsx',
      { cwd: process.cwd(), maxBuffer: 10 * 1024 * 1024 }
    );

    console.log('STDOUT:', stdout);
    if (stderr) console.error('STDERR:', stderr);
  } catch (error) {
    console.log('Test output:', error.stdout);
    console.error('Test errors:', error.stderr);
    process.exit(error.code || 1);
  }
}

runTests();

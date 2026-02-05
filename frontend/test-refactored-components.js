/**
 * Test runner for refactored frontend components.
 * 
 * Tests verify:
 * 1. API split and domain modules
 * 2. Auth migration to RTK Query
 * 3. Investigation2Context functionality
 * 4. Type safety (no any types)
 */

const { execSync } = require('child_process');

console.log('Running refactored component tests...\n');

const testSuites = [
  {
    name: 'API Module Tests',
    pattern: 'src/app/__tests__/api.test.ts',
  },
  {
    name: 'Auth RTK Query Tests',
    pattern: 'src/features/auth/__tests__/authSlice.rtk.test.ts',
  },
  {
    name: 'Investigation2Context Tests',
    pattern: 'src/context/__tests__/Investigation2Context.test.tsx',
  },
  {
    name: 'Type Safety Tests',
    pattern: 'src/types/__tests__/investigation2.test.ts',
  },
  {
    name: 'Investigation2ResultsEnhanced Tests',
    pattern: 'src/components/investigations/__tests__/Investigation2ResultsEnhanced.test.tsx',
  },
];

let allPassed = true;

testSuites.forEach((suite) => {
  console.log(`\n--- ${suite.name} ---`);
  try {
    execSync(`npm run test -- ${suite.pattern}`, {
      stdio: 'inherit',
      cwd: __dirname,
    });
    console.log(`✓ ${suite.name} passed`);
  } catch (error) {
    console.error(`✗ ${suite.name} failed`);
    allPassed = false;
  }
});

console.log('\n--- TypeScript Type Check ---');
try {
  execSync('npx tsc --noEmit', {
    stdio: 'inherit',
    cwd: __dirname,
  });
  console.log('✓ TypeScript check passed');
} catch (error) {
  console.error('✗ TypeScript check failed');
  allPassed = false;
}

if (allPassed) {
  console.log('\n✓ All refactored component tests passed!');
  process.exit(0);
} else {
  console.error('\n✗ Some tests failed');
  process.exit(1);
}

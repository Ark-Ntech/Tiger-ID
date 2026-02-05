#!/usr/bin/env node

/**
 * Helper script to run Playwright tests with sharding locally
 *
 * Usage:
 *   node run-sharded-tests.js              # Run all 4 shards sequentially
 *   node run-sharded-tests.js --parallel   # Run all 4 shards in parallel
 *   node run-sharded-tests.js --shard=2/4  # Run specific shard
 */

import { spawn } from 'child_process';
import { parseArgs } from 'util';

// Parse command line arguments
const { values } = parseArgs({
  options: {
    parallel: {
      type: 'boolean',
      short: 'p',
      default: false,
    },
    shard: {
      type: 'string',
      short: 's',
    },
    help: {
      type: 'boolean',
      short: 'h',
    },
  },
  strict: false,
});

if (values.help) {
  console.log(`
Playwright Sharded Test Runner

Usage:
  node run-sharded-tests.js [options]

Options:
  --parallel, -p        Run all shards in parallel (default: sequential)
  --shard=N/T, -s N/T   Run specific shard (e.g., --shard=2/4)
  --help, -h            Show this help message

Examples:
  node run-sharded-tests.js              # Run all 4 shards sequentially
  node run-sharded-tests.js --parallel   # Run all 4 shards in parallel
  node run-sharded-tests.js --shard=2/4  # Run shard 2 of 4
  `);
  process.exit(0);
}

const TOTAL_SHARDS = 4;

/**
 * Run a single shard
 */
function runShard(shardIndex, totalShards) {
  return new Promise((resolve, reject) => {
    const args = ['playwright', 'test', `--shard=${shardIndex}/${totalShards}`];

    console.log(`\n🧪 Running shard ${shardIndex}/${totalShards}...`);

    const child = spawn('npx', args, {
      stdio: 'inherit',
      shell: true,
    });

    child.on('close', (code) => {
      if (code === 0) {
        console.log(`✅ Shard ${shardIndex}/${totalShards} completed successfully`);
        resolve({ shard: shardIndex, success: true });
      } else {
        console.error(`❌ Shard ${shardIndex}/${totalShards} failed with code ${code}`);
        resolve({ shard: shardIndex, success: false, code });
      }
    });

    child.on('error', (error) => {
      console.error(`❌ Error running shard ${shardIndex}/${totalShards}:`, error);
      reject(error);
    });
  });
}

/**
 * Run all shards sequentially
 */
async function runSequential() {
  console.log(`\n🚀 Running ${TOTAL_SHARDS} shards sequentially...\n`);

  const results = [];
  for (let i = 1; i <= TOTAL_SHARDS; i++) {
    const result = await runShard(i, TOTAL_SHARDS);
    results.push(result);
  }

  return results;
}

/**
 * Run all shards in parallel
 */
async function runParallel() {
  console.log(`\n🚀 Running ${TOTAL_SHARDS} shards in parallel...\n`);

  const promises = [];
  for (let i = 1; i <= TOTAL_SHARDS; i++) {
    promises.push(runShard(i, TOTAL_SHARDS));
  }

  const results = await Promise.all(promises);
  return results;
}

/**
 * Print summary of results
 */
function printSummary(results) {
  console.log('\n' + '='.repeat(60));
  console.log('📊 Test Summary');
  console.log('='.repeat(60));

  const successful = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;

  results.forEach(result => {
    const icon = result.success ? '✅' : '❌';
    const status = result.success ? 'PASSED' : `FAILED (code ${result.code})`;
    console.log(`${icon} Shard ${result.shard}/${TOTAL_SHARDS}: ${status}`);
  });

  console.log('='.repeat(60));
  console.log(`Total: ${results.length} shards | Passed: ${successful} | Failed: ${failed}`);
  console.log('='.repeat(60) + '\n');

  if (failed > 0) {
    console.log('❌ Some shards failed. View the test results above for details.');
    console.log('💡 Tip: Run failed shards individually with --shard=N/4 for debugging\n');
  } else {
    console.log('✅ All shards passed successfully!\n');
  }
}

/**
 * Main execution
 */
async function main() {
  const startTime = Date.now();

  try {
    let results;

    if (values.shard) {
      // Run specific shard
      const [shardIndex, totalShards] = values.shard.split('/').map(Number);

      if (!shardIndex || !totalShards || shardIndex < 1 || shardIndex > totalShards) {
        console.error('❌ Invalid shard format. Use --shard=N/T (e.g., --shard=2/4)');
        process.exit(1);
      }

      const result = await runShard(shardIndex, totalShards);
      results = [result];
    } else if (values.parallel) {
      // Run all shards in parallel
      results = await runParallel();
    } else {
      // Run all shards sequentially
      results = await runSequential();
    }

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);

    printSummary(results);

    console.log(`⏱️  Total execution time: ${duration}s\n`);

    // Exit with failure if any shard failed
    const hasFailures = results.some(r => !r.success);
    process.exit(hasFailures ? 1 : 0);

  } catch (error) {
    console.error('\n❌ Fatal error:', error);
    process.exit(1);
  }
}

// Run main function
main();

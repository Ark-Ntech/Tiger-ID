import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for Tiger ID E2E tests
 *
 * Features:
 * - Multi-browser support (Chromium, Firefox, WebKit)
 * - CI/CD optimizations with sharding support (4 shards)
 * - Retry logic and parallel execution
 * - Global authentication setup
 * - Trace/video/screenshot capture on failures
 * - JUnit and HTML reporting for CI
 *
 * Sharding Usage:
 * - Local: npm run test:e2e (no sharding)
 * - CI: playwright test --shard=1/4 (run shard 1 of 4)
 *
 * CI/CD Environment Variables:
 * - CI=true - Enables CI-specific settings
 * - BASE_URL - Application base URL (default: http://localhost:5173)
 * - API_URL - Backend API URL (default: http://localhost:8000)
 */
export default defineConfig({
  // Test directory
  testDir: './e2e',

  // Run tests in files in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry configuration
  // CI: 2 retries (3 total attempts) to handle flaky tests
  // Local: 0 retries (1 attempt) for faster feedback
  retries: process.env.CI ? 2 : 0,

  // Worker configuration based on environment
  // CI: Use 4 workers to match shard count for optimal parallelization
  // Local: Use half of available CPUs for balanced resource usage
  workers: process.env.CI ? 4 : '50%',

  // Reporter configuration
  // CI: JUnit XML (for CI dashboards) + HTML report + line output
  // Local: Line reporter + HTML report opened on failure only
  reporter: process.env.CI
    ? [
        ['junit', { outputFile: 'test-results/junit.xml' }],
        ['html', { outputFolder: 'playwright-report', open: 'never' }],
        ['list']
      ]
    : [
        ['line'],
        ['html', { outputFolder: 'playwright-report', open: 'on-failure' }]
      ],

  // Shared settings for all tests
  use: {
    // Base URL for navigation (configurable via environment variable)
    // Override in CI/CD with BASE_URL env var
    baseURL: process.env.BASE_URL || 'http://localhost:5173',

    // Collect trace on first retry only (saves disk space while debugging failures)
    trace: 'on-first-retry',

    // Screenshot configuration
    // Only capture on failure to save storage and improve performance
    screenshot: 'only-on-failure',

    // Video configuration
    // Record on first retry only to help debug intermittent failures
    video: 'on-first-retry',

    // Action timeout (individual actions like click, fill, etc.)
    // Set to 30 seconds to handle slow-loading dynamic content
    actionTimeout: 30000,

    // Navigation timeout
    navigationTimeout: 30000,
  },

  // Expect timeout configuration (10 seconds)
  // This affects assertions like expect(page).toHaveText()
  // Lower than action timeout for faster failure feedback
  expect: {
    timeout: 10000,
    // Visual regression snapshot comparison settings
    toMatchSnapshot: {
      threshold: 0.01, // 1% pixel difference threshold
      maxDiffPixelRatio: 0.01,
    },
  },

  // Global test timeout (30 seconds per test)
  // Individual tests should complete within this timeframe
  timeout: 30000,

  // Output directory for test artifacts (screenshots, videos, traces)
  outputDir: 'test-results',

  // Global setup script - runs once before all tests
  // Creates authenticated state for reuse across tests
  // Reference: ./e2e/global.setup.ts
  globalSetup: './e2e/global.setup.ts',

  // Global teardown script - runs once after all tests
  // Cleans up test data and auth state files
  globalTeardown: './e2e/global.teardown.ts',

  // Configure projects for major browsers
  // Each project can be run independently or all together
  // Sharding is supported: playwright test --shard=1/4 --project=chromium
  projects: [
    // Setup project - runs first to create authenticated state
    // Dependency: All other projects depend on this completing successfully
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
    },

    // Chromium (Chrome/Edge)
    // Most widely used browser, good for primary testing
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // Use prepared auth state from setup to skip login in tests
        storageState: '.auth/admin.json',
      },
      dependencies: ['setup'],
    },

    // Firefox
    // Second most popular browser, different rendering engine
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        // Use prepared auth state from setup to skip login in tests
        storageState: '.auth/admin.json',
      },
      dependencies: ['setup'],
    },

    // WebKit (Safari)
    // Important for cross-browser compatibility, especially macOS/iOS
    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        // Use prepared auth state from setup to skip login in tests
        storageState: '.auth/admin.json',
      },
      dependencies: ['setup'],
    },

    // Mobile viewports (optional - uncomment if needed)
    // Useful for testing responsive design and mobile-specific features
    // {
    //   name: 'Mobile Chrome',
    //   use: {
    //     ...devices['Pixel 5'],
    //     storageState: '.auth/admin.json',
    //   },
    //   dependencies: ['setup'],
    // },
    // {
    //   name: 'Mobile Safari',
    //   use: {
    //     ...devices['iPhone 12'],
    //     storageState: '.auth/admin.json',
    //   },
    //   dependencies: ['setup'],
    // },
  ],

  // Run your local dev server before starting the tests
  // Only used when running locally (not in CI where server is already running)
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    stdout: 'ignore',
    stderr: 'pipe',
    timeout: 120000,
  },
});

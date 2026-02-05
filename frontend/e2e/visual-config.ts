/**
 * Visual Regression Test Configuration
 *
 * Configuration for Playwright visual regression testing including
 * snapshot thresholds, screenshot settings, and update modes.
 */

export const visualConfig = {
  /**
   * Snapshot comparison threshold
   * 0.0 = exact match, 1.0 = completely different
   */
  threshold: 0.01,

  /**
   * Maximum allowed pixel difference ratio
   */
  maxDiffPixelRatio: 0.01,

  /**
   * Screenshot timeout in milliseconds
   */
  screenshotTimeout: 10000,

  /**
   * Directories for screenshots
   */
  paths: {
    screenshots: 'screenshots',
    snapshots: 'e2e/__snapshots__',
    diffs: 'test-results/visual-diffs',
  },

  /**
   * Viewport configurations for responsive testing
   */
  viewports: {
    desktop: { width: 1920, height: 1080 },
    desktopSmall: { width: 1366, height: 768 },
    tablet: { width: 768, height: 1024 },
    tabletLandscape: { width: 1024, height: 768 },
    mobile: { width: 375, height: 667 },
    mobileLarge: { width: 414, height: 896 },
  },

  /**
   * Pages to test with their routes
   */
  pages: {
    auth: {
      login: '/login',
      passwordReset: '/password-reset',
    },
    main: {
      dashboard: '/dashboard',
      tigers: '/tigers',
      facilities: '/facilities',
      investigation: '/investigation2',
      discovery: '/discovery',
      verification: '/verification',
      templates: '/templates',
    },
  },

  /**
   * Test scenarios configuration
   */
  scenarios: {
    // Test both light and dark themes
    testBothThemes: true,

    // Test responsive layouts
    testResponsive: true,

    // Test component states
    testComponentStates: true,

    // Test empty states
    testEmptyStates: true,

    // Test error states
    testErrorStates: true,

    // Test loading states
    testLoadingStates: true,
  },

  /**
   * Elements to mask in screenshots (dynamic content)
   * These selectors will have their content hidden to prevent false positives
   */
  maskSelectors: [
    '[data-timestamp]',
    '.timestamp',
    'time',
    '[data-dynamic]',
  ],

  /**
   * Elements to hide completely (animated elements that cause flakiness)
   */
  hideSelectors: [
    '.animate-spin',
    '.animate-pulse',
  ],

  /**
   * Playwright screenshot options
   */
  screenshotOptions: {
    animations: 'disabled' as const,
    scale: 'css' as const,
    type: 'png' as const,
  },

  /**
   * Snapshot comparison options for toMatchSnapshot
   */
  snapshotOptions: {
    threshold: 0.01,
    maxDiffPixelRatio: 0.01,
  },
}

export type VisualConfig = typeof visualConfig

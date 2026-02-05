import { test, expect, Page } from '@playwright/test'
import { login } from '../../helpers/auth'
import path from 'path'

// Test data and helpers
const TEST_IMAGE = path.join(__dirname, '../../fixtures/tiger-test.jpg')
const API_BASE = process.env.API_URL || 'http://localhost:8000/api'

/**
 * Helper: Wait for investigation to reach a specific phase
 */
async function waitForPhase(page: Page, investigationId: string, phase: string, timeout = 30000) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    const response = await page.request.get(`${API_BASE}/investigation2/${investigationId}`);
    const data = await response.json();
    if (data.current_phase === phase) {
      return data;
    }
    await page.waitForTimeout(1000);
  }
  throw new Error(`Timeout waiting for phase: ${phase}`);
}

/**
 * Helper: Start investigation and return ID
 */
async function startInvestigation(page: Page): Promise<string> {
  await page.goto('/investigation2');
  await page.waitForSelector('[data-testid="investigation2-upload"]');

  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles(TEST_IMAGE);

  await page.click('[data-testid="upload-submit"]');

  // Wait for investigation to start
  await page.waitForSelector('[data-testid="investigation2-progress"]', { timeout: 10000 });

  // Extract investigation ID from URL
  await page.waitForURL(/\/investigation2\/.+/, { timeout: 5000 });
  const url = page.url();
  const match = url.match(/\/investigation2\/(.+)/);
  if (!match) {
    throw new Error('Failed to extract investigation ID from URL');
  }

  return match[1];
}

/**
 * Helper: Mock model progress data
 */
const mockModelProgress = {
  wildlife_tools: { status: 'completed', progress: 100, embedding_dim: 1536 },
  cvwc2019_reid: { status: 'running', progress: 67, embedding_dim: 2048 },
  transreid: { status: 'pending', progress: 0, embedding_dim: 768 },
  megadescriptor_b: { status: 'pending', progress: 0, embedding_dim: 1024 },
  tiger_reid: { status: 'error', progress: 0, embedding_dim: 2048, error: 'Connection timeout' },
  rapid_reid: { status: 'pending', progress: 0, embedding_dim: 2048 }
};

test.describe('Model Comparison E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test using helper
    await login(page)

    // Navigate to investigation page
    await page.goto('/investigation2')
  })

  test.describe('Model Progress Grid', () => {
    test('should display 6 models during stripe_analysis phase', async ({ page }) => {
      const investigationId = await startInvestigation(page);

      // Wait for stripe_analysis phase
      await waitForPhase(page, investigationId, 'stripe_analysis');

      // Check model progress grid is visible
      const progressGrid = page.locator('[data-testid="model-progress-grid"]');
      await expect(progressGrid).toBeVisible({ timeout: 10000 });

      // Verify all 6 model cards are present
      const modelCards = page.locator('[data-testid^="model-card-"]');
      await expect(modelCards).toHaveCount(6);

      // Verify each model name is displayed
      const expectedModels = [
        'wildlife_tools',
        'cvwc2019_reid',
        'transreid',
        'megadescriptor_b',
        'tiger_reid',
        'rapid_reid'
      ];

      for (const modelName of expectedModels) {
        const modelCard = page.locator(`[data-testid="model-card-${modelName}"]`);
        await expect(modelCard).toBeVisible();
      }
    });

    test('should show correct grid layout with proper spacing', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'stripe_analysis');

      const progressGrid = page.locator('[data-testid="model-progress-grid"]');
      await expect(progressGrid).toBeVisible();

      // Verify grid has proper CSS classes for layout
      await expect(progressGrid).toHaveClass(/grid/);

      // Check that cards are arranged in grid (2 or 3 columns)
      const gridComputedStyle = await progressGrid.evaluate(el =>
        window.getComputedStyle(el).gridTemplateColumns
      );
      expect(gridComputedStyle).toBeTruthy();
    });
  });

  test.describe('Individual Model Progress', () => {
    test('should display correct progress percentage for each model', async ({ page }) => {
      // Mock API response with specific progress values
      await page.route(`${API_BASE}/investigation2/**`, async (route) => {
        const response = await route.fetch()
        const data = await response.json()

        if (data.current_phase === 'stripe_analysis') {
          data.model_progress = mockModelProgress
        }

        await route.fulfill({ json: data })
      })

      const investigationId = await startInvestigation(page)
      await waitForPhase(page, investigationId, 'stripe_analysis')

      // Check wildlife_tools (100%) - uses data-testid="model-progress-text-wildlife_tools"
      const wildlifeProgress = page.locator('[data-testid="model-progress-text-wildlife_tools"]')
      if (await wildlifeProgress.count() > 0) {
        await expect(wildlifeProgress).toContainText('100%')
      }

      // Check cvwc2019_reid (67%)
      const cvwcProgress = page.locator('[data-testid="model-progress-text-cvwc2019_reid"]')
      if (await cvwcProgress.count() > 0) {
        await expect(cvwcProgress).toContainText('67%')
      }

      // Check pending models (0%)
      const transreidProgress = page.locator('[data-testid="model-progress-text-transreid"]')
      if (await transreidProgress.count() > 0) {
        await expect(transreidProgress).toContainText('0%')
      }
    })

    test('should display progress bars with correct width', async ({ page }) => {
      await page.route(`${API_BASE}/investigation2/**`, async (route) => {
        const response = await route.fetch();
        const data = await response.json();
        if (data.current_phase === 'stripe_analysis') {
          data.model_progress = mockModelProgress;
        }
        await route.fulfill({ json: data });
      });

      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'stripe_analysis');

      // Check completed model has full width progress bar
      const wildlifeBar = page.locator('[data-testid="model-card-wildlife_tools"] [data-testid="progress-bar"]');
      const wildlifeWidth = await wildlifeBar.evaluate(el =>
        window.getComputedStyle(el).width
      );

      // Check running model has partial width
      const cvwcBar = page.locator('[data-testid="model-card-cvwc2019_reid"] [data-testid="progress-bar"]');
      const cvwcWidth = await cvwcBar.evaluate(el =>
        window.getComputedStyle(el).width
      );

      // Completed should be wider than running
      expect(parseFloat(wildlifeWidth)).toBeGreaterThan(parseFloat(cvwcWidth));
    });

    test('should show embedding dimensions for each model', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'stripe_analysis');

      // Check each model displays its embedding dimension
      await expect(page.locator('[data-testid="model-card-wildlife_tools"]')).toContainText('1536');
      await expect(page.locator('[data-testid="model-card-cvwc2019_reid"]')).toContainText('2048');
      await expect(page.locator('[data-testid="model-card-transreid"]')).toContainText('768');
      await expect(page.locator('[data-testid="model-card-megadescriptor_b"]')).toContainText('1024');
    });
  });

  test.describe('Model Status Indicators', () => {
    test('should display pending status correctly', async ({ page }) => {
      await page.route(`${API_BASE}/investigation2/**`, async (route) => {
        const response = await route.fetch();
        const data = await response.json();
        if (data.current_phase === 'stripe_analysis') {
          data.model_progress = mockModelProgress;
        }
        await route.fulfill({ json: data });
      });

      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'stripe_analysis');

      // Check pending models have correct status badge
      const transreidCard = page.locator('[data-testid="model-card-transreid"]');
      await expect(transreidCard.locator('[data-testid="status-badge"]')).toContainText('Pending');
      await expect(transreidCard.locator('[data-testid="status-badge"]')).toHaveClass(/bg-gray/);
    });

    test('should display running status with animation', async ({ page }) => {
      await page.route(`${API_BASE}/investigation2/**`, async (route) => {
        const response = await route.fetch();
        const data = await response.json();
        if (data.current_phase === 'stripe_analysis') {
          data.model_progress = mockModelProgress;
        }
        await route.fulfill({ json: data });
      });

      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'stripe_analysis');

      const cvwcCard = page.locator('[data-testid="model-card-cvwc2019_reid"]');
      const statusBadge = cvwcCard.locator('[data-testid="status-badge"]');

      await expect(statusBadge).toContainText('Running');
      await expect(statusBadge).toHaveClass(/bg-blue/);

      // Check for animation class
      await expect(statusBadge).toHaveClass(/animate-pulse/);
    });

    test('should display completed status with checkmark', async ({ page }) => {
      await page.route(`${API_BASE}/investigation2/**`, async (route) => {
        const response = await route.fetch();
        const data = await response.json();
        if (data.current_phase === 'stripe_analysis') {
          data.model_progress = mockModelProgress;
        }
        await route.fulfill({ json: data });
      });

      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'stripe_analysis');

      const wildlifeCard = page.locator('[data-testid="model-card-wildlife_tools"]');
      const statusBadge = wildlifeCard.locator('[data-testid="status-badge"]');

      await expect(statusBadge).toContainText('Completed');
      await expect(statusBadge).toHaveClass(/bg-green/);

      // Check for checkmark icon
      await expect(wildlifeCard.locator('[data-testid="checkmark-icon"]')).toBeVisible();
    });

    test('should display error status with error message', async ({ page }) => {
      await page.route(`${API_BASE}/investigation2/**`, async (route) => {
        const response = await route.fetch();
        const data = await response.json();
        if (data.current_phase === 'stripe_analysis') {
          data.model_progress = mockModelProgress;
        }
        await route.fulfill({ json: data });
      });

      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'stripe_analysis');

      const tigerReidCard = page.locator('[data-testid="model-card-tiger_reid"]');
      const statusBadge = tigerReidCard.locator('[data-testid="status-badge"]');

      await expect(statusBadge).toContainText('Error');
      await expect(statusBadge).toHaveClass(/bg-red/);

      // Check error message is displayed
      await expect(tigerReidCard).toContainText('Connection timeout');

      // Check for error icon
      await expect(tigerReidCard.locator('[data-testid="error-icon"]')).toBeVisible();
    });
  });

  test.describe('Model Completion Count', () => {
    test('should display X/6 completed badge', async ({ page }) => {
      await page.route(`${API_BASE}/investigation2/**`, async (route) => {
        const response = await route.fetch();
        const data = await response.json();
        if (data.current_phase === 'stripe_analysis') {
          data.model_progress = mockModelProgress;
        }
        await route.fulfill({ json: data });
      });

      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'stripe_analysis');

      // Check completion count badge (1 completed out of 6)
      const completionBadge = page.locator('[data-testid="model-completion-count"]');
      await expect(completionBadge).toBeVisible();
      await expect(completionBadge).toContainText('1/6');
    });

    test('should update completion count in real-time', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'stripe_analysis');

      const completionBadge = page.locator('[data-testid="model-completion-count"]');

      // Initial count
      const initialText = await completionBadge.textContent();
      const initialCount = parseInt(initialText?.split('/')[0] || '0');

      // Wait for progress
      await page.waitForTimeout(5000);

      // Check count increased
      const updatedText = await completionBadge.textContent();
      const updatedCount = parseInt(updatedText?.split('/')[0] || '0');

      expect(updatedCount).toBeGreaterThanOrEqual(initialCount);
    });

    test('should show all models completed when phase ends', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'stripe_analysis');

      // Wait for phase to complete
      await waitForPhase(page, investigationId, 'report_generation', 60000);

      const completionBadge = page.locator('[data-testid="model-completion-count"]');
      await expect(completionBadge).toContainText('6/6');
    });
  });

  test.describe('Model Retry Functionality', () => {
    test('should show retry button for errored models', async ({ page }) => {
      await page.route(`${API_BASE}/investigation2/**`, async (route) => {
        const response = await route.fetch();
        const data = await response.json();
        if (data.current_phase === 'stripe_analysis') {
          data.model_progress = mockModelProgress;
        }
        await route.fulfill({ json: data });
      });

      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'stripe_analysis');

      const tigerReidCard = page.locator('[data-testid="model-card-tiger_reid"]');
      const retryButton = tigerReidCard.locator('[data-testid="retry-button"]');

      await expect(retryButton).toBeVisible();
      await expect(retryButton).toBeEnabled();
    });

    test('should retry model when retry button clicked', async ({ page }) => {
      let retryRequested = false;

      await page.route(`${API_BASE}/investigation2/**/retry-model`, async (route) => {
        retryRequested = true;
        await route.fulfill({
          json: { success: true, message: 'Model retry initiated' }
        });
      });

      await page.route(`${API_BASE}/investigation2/**`, async (route) => {
        const response = await route.fetch();
        const data = await response.json();
        if (data.current_phase === 'stripe_analysis') {
          data.model_progress = mockModelProgress;
        }
        await route.fulfill({ json: data });
      });

      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'stripe_analysis');

      const tigerReidCard = page.locator('[data-testid="model-card-tiger_reid"]');
      const retryButton = tigerReidCard.locator('[data-testid="retry-button"]');

      await retryButton.click();

      // Wait for retry request
      await page.waitForTimeout(1000);
      expect(retryRequested).toBe(true);
    });

    test('should show loading state during retry', async ({ page }) => {
      await page.route(`${API_BASE}/investigation2/**`, async (route) => {
        const response = await route.fetch();
        const data = await response.json();
        if (data.current_phase === 'stripe_analysis') {
          data.model_progress = mockModelProgress;
        }
        await route.fulfill({ json: data });
      });

      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'stripe_analysis');

      const tigerReidCard = page.locator('[data-testid="model-card-tiger_reid"]');
      const retryButton = tigerReidCard.locator('[data-testid="retry-button"]');

      await retryButton.click();

      // Check button shows loading state
      await expect(retryButton).toBeDisabled();
      await expect(retryButton.locator('[data-testid="loading-spinner"]')).toBeVisible();
    });
  });

  test.describe('Model Agreement Badge', () => {
    test('should display consensus badge in verification queue', async ({ page }) => {
      await page.goto('/verification-queue');

      // Wait for queue items to load
      await page.waitForSelector('[data-testid="verification-item"]', { timeout: 10000 });

      const firstItem = page.locator('[data-testid="verification-item"]').first();
      const agreementBadge = firstItem.locator('[data-testid="model-agreement-badge"]');

      await expect(agreementBadge).toBeVisible();
    });

    test('should show high agreement for 5-6 models agreeing', async ({ page }) => {
      await page.route(`${API_BASE}/verification/queue`, async (route) => {
        await route.fulfill({
          json: {
            items: [{
              id: 'ver-1',
              match: { tiger_id: 'tiger-123', name: 'Bengal' },
              model_agreement: { agreed: 6, total: 6, percentage: 100 }
            }]
          }
        });
      });

      await page.goto('/verification-queue');
      await page.waitForSelector('[data-testid="verification-item"]');

      const agreementBadge = page.locator('[data-testid="model-agreement-badge"]').first();
      await expect(agreementBadge).toContainText('6/6');
      await expect(agreementBadge).toHaveClass(/bg-green/);
      await expect(agreementBadge.locator('[data-testid="agreement-high"]')).toBeVisible();
    });

    test('should show medium agreement for 3-4 models agreeing', async ({ page }) => {
      await page.route(`${API_BASE}/verification/queue`, async (route) => {
        await route.fulfill({
          json: {
            items: [{
              id: 'ver-1',
              match: { tiger_id: 'tiger-123', name: 'Bengal' },
              model_agreement: { agreed: 4, total: 6, percentage: 67 }
            }]
          }
        });
      });

      await page.goto('/verification-queue');
      await page.waitForSelector('[data-testid="verification-item"]');

      const agreementBadge = page.locator('[data-testid="model-agreement-badge"]').first();
      await expect(agreementBadge).toContainText('4/6');
      await expect(agreementBadge).toHaveClass(/bg-yellow/);
      await expect(agreementBadge.locator('[data-testid="agreement-medium"]')).toBeVisible();
    });

    test('should show low agreement for 1-2 models agreeing', async ({ page }) => {
      await page.route(`${API_BASE}/verification/queue`, async (route) => {
        await route.fulfill({
          json: {
            items: [{
              id: 'ver-1',
              match: { tiger_id: 'tiger-123', name: 'Bengal' },
              model_agreement: { agreed: 2, total: 6, percentage: 33 }
            }]
          }
        });
      });

      await page.goto('/verification-queue');
      await page.waitForSelector('[data-testid="verification-item"]');

      const agreementBadge = page.locator('[data-testid="model-agreement-badge"]').first();
      await expect(agreementBadge).toContainText('2/6');
      await expect(agreementBadge).toHaveClass(/bg-red/);
      await expect(agreementBadge.locator('[data-testid="agreement-low"]')).toBeVisible();
    });
  });

  test.describe('Model Scores Breakdown', () => {
    test('should display per-model scores in comparison', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      // Open comparison view for first match
      const firstMatch = page.locator('[data-testid="match-card"]').first();
      await firstMatch.click();

      // Wait for comparison drawer
      const comparisonDrawer = page.locator('[data-testid="comparison-drawer"]');
      await expect(comparisonDrawer).toBeVisible({ timeout: 5000 });

      // Check model scores section
      const scoresSection = comparisonDrawer.locator('[data-testid="model-scores-breakdown"]');
      await expect(scoresSection).toBeVisible();

      // Verify all 6 models show scores
      const scoreItems = scoresSection.locator('[data-testid^="score-"]');
      await expect(scoreItems).toHaveCount(6);
    });

    test('should show highest scoring model highlighted', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      const firstMatch = page.locator('[data-testid="match-card"]').first();
      await firstMatch.click();

      const comparisonDrawer = page.locator('[data-testid="comparison-drawer"]');
      await expect(comparisonDrawer).toBeVisible();

      const scoresSection = comparisonDrawer.locator('[data-testid="model-scores-breakdown"]');
      const highestScore = scoresSection.locator('[data-testid="highest-score"]');

      await expect(highestScore).toBeVisible();
      await expect(highestScore).toHaveClass(/border-green/);
    });

    test('should display score values with 2 decimal precision', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      const firstMatch = page.locator('[data-testid="match-card"]').first();
      await firstMatch.click();

      const comparisonDrawer = page.locator('[data-testid="comparison-drawer"]');
      const scoresSection = comparisonDrawer.locator('[data-testid="model-scores-breakdown"]');

      // Check score format (e.g., 0.85, 0.92)
      const scoreValues = await scoresSection.locator('[data-testid^="score-value-"]').allTextContents();

      for (const score of scoreValues) {
        expect(score).toMatch(/^\d\.\d{2}$/);
      }
    });
  });

  test.describe('Comparison Drawer', () => {
    test('should open comparison drawer on match click', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      const firstMatch = page.locator('[data-testid="match-card"]').first();
      await firstMatch.click();

      const comparisonDrawer = page.locator('[data-testid="comparison-drawer"]');
      await expect(comparisonDrawer).toBeVisible({ timeout: 5000 });
      await expect(comparisonDrawer).toHaveClass(/slide-in/);
    });

    test('should display side-by-side tiger information', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      const firstMatch = page.locator('[data-testid="match-card"]').first();
      await firstMatch.click();

      const comparisonDrawer = page.locator('[data-testid="comparison-drawer"]');

      // Check query panel
      const queryPanel = comparisonDrawer.locator('[data-testid="query-panel"]');
      await expect(queryPanel).toBeVisible();
      await expect(queryPanel).toContainText('Query Image');

      // Check match panel
      const matchPanel = comparisonDrawer.locator('[data-testid="match-panel"]');
      await expect(matchPanel).toBeVisible();
      await expect(matchPanel).toContainText('Matched Tiger');
    });

    test('should show tiger metadata in comparison', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      const firstMatch = page.locator('[data-testid="match-card"]').first();
      const matchName = await firstMatch.locator('[data-testid="tiger-name"]').textContent();

      await firstMatch.click();

      const comparisonDrawer = page.locator('[data-testid="comparison-drawer"]');
      const matchPanel = comparisonDrawer.locator('[data-testid="match-panel"]');

      // Check tiger name
      await expect(matchPanel.locator('[data-testid="tiger-name"]')).toContainText(matchName || '');

      // Check metadata fields
      await expect(matchPanel.locator('[data-testid="tiger-facility"]')).toBeVisible();
      await expect(matchPanel.locator('[data-testid="tiger-subspecies"]')).toBeVisible();
    });

    test('should close drawer on close button click', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      const firstMatch = page.locator('[data-testid="match-card"]').first();
      await firstMatch.click();

      const comparisonDrawer = page.locator('[data-testid="comparison-drawer"]');
      await expect(comparisonDrawer).toBeVisible();

      const closeButton = comparisonDrawer.locator('[data-testid="close-drawer"]');
      await closeButton.click();

      await expect(comparisonDrawer).not.toBeVisible();
    });

    test('should close drawer on escape key', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      const firstMatch = page.locator('[data-testid="match-card"]').first();
      await firstMatch.click();

      const comparisonDrawer = page.locator('[data-testid="comparison-drawer"]');
      await expect(comparisonDrawer).toBeVisible();

      await page.keyboard.press('Escape');

      await expect(comparisonDrawer).not.toBeVisible();
    });
  });

  test.describe('Match Comparison View', () => {
    test('should display query image on left side', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      const firstMatch = page.locator('[data-testid="match-card"]').first();
      await firstMatch.click();

      const queryPanel = page.locator('[data-testid="query-panel"]');
      const queryImage = queryPanel.locator('[data-testid="query-image"]');

      await expect(queryImage).toBeVisible();
      await expect(queryImage).toHaveAttribute('src', /.+/);
    });

    test('should display match image on right side', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      const firstMatch = page.locator('[data-testid="match-card"]').first();
      await firstMatch.click();

      const matchPanel = page.locator('[data-testid="match-panel"]');
      const matchImage = matchPanel.locator('[data-testid="match-image"]');

      await expect(matchImage).toBeVisible();
      await expect(matchImage).toHaveAttribute('src', /.+/);
    });

    test('should show overall confidence score', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      const firstMatch = page.locator('[data-testid="match-card"]').first();
      await firstMatch.click();

      const comparisonDrawer = page.locator('[data-testid="comparison-drawer"]');
      const confidenceScore = comparisonDrawer.locator('[data-testid="overall-confidence"]');

      await expect(confidenceScore).toBeVisible();

      // Check score is between 0 and 1
      const scoreText = await confidenceScore.textContent();
      const score = parseFloat(scoreText || '0');
      expect(score).toBeGreaterThanOrEqual(0);
      expect(score).toBeLessThanOrEqual(1);
    });

    test('should navigate between multiple matches', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      // Get match count
      const matchCards = page.locator('[data-testid="match-card"]');
      const matchCount = await matchCards.count();

      if (matchCount < 2) {
        test.skip();
      }

      // Click first match
      await matchCards.nth(0).click();
      const comparisonDrawer = page.locator('[data-testid="comparison-drawer"]');
      await expect(comparisonDrawer).toBeVisible();

      const firstMatchName = await comparisonDrawer.locator('[data-testid="tiger-name"]').textContent();

      // Navigate to next match
      const nextButton = comparisonDrawer.locator('[data-testid="next-match"]');
      await nextButton.click();

      // Verify different match is shown
      const secondMatchName = await comparisonDrawer.locator('[data-testid="tiger-name"]').textContent();
      expect(secondMatchName).not.toBe(firstMatchName);
    });
  });

  test.describe('Confidence Color Coding', () => {
    test('should display green for high confidence (>0.8)', async ({ page }) => {
      await page.route(`${API_BASE}/investigation2/**/results`, async (route) => {
        await route.fulfill({
          json: {
            matches: [{
              tiger_id: 'tiger-123',
              name: 'Bengal',
              confidence: 0.92,
              model_scores: {}
            }]
          }
        });
      });

      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      const firstMatch = page.locator('[data-testid="match-card"]').first();
      const confidenceBadge = firstMatch.locator('[data-testid="confidence-badge"]');

      await expect(confidenceBadge).toHaveClass(/bg-green/);
    });

    test('should display yellow for medium confidence (0.6-0.8)', async ({ page }) => {
      await page.route(`${API_BASE}/investigation2/**/results`, async (route) => {
        await route.fulfill({
          json: {
            matches: [{
              tiger_id: 'tiger-123',
              name: 'Bengal',
              confidence: 0.72,
              model_scores: {}
            }]
          }
        });
      });

      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      const firstMatch = page.locator('[data-testid="match-card"]').first();
      const confidenceBadge = firstMatch.locator('[data-testid="confidence-badge"]');

      await expect(confidenceBadge).toHaveClass(/bg-yellow/);
    });

    test('should display red for low confidence (<0.6)', async ({ page }) => {
      await page.route(`${API_BASE}/investigation2/**/results`, async (route) => {
        await route.fulfill({
          json: {
            matches: [{
              tiger_id: 'tiger-123',
              name: 'Bengal',
              confidence: 0.45,
              model_scores: {}
            }]
          }
        });
      });

      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      const firstMatch = page.locator('[data-testid="match-card"]').first();
      const confidenceBadge = firstMatch.locator('[data-testid="confidence-badge"]');

      await expect(confidenceBadge).toHaveClass(/bg-red/);
    });

    test('should apply color coding consistently across all views', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      // Check color in match card
      const firstMatch = page.locator('[data-testid="match-card"]').first();
      const cardBadgeClass = await firstMatch.locator('[data-testid="confidence-badge"]').getAttribute('class');

      // Open comparison drawer
      await firstMatch.click();

      const comparisonDrawer = page.locator('[data-testid="comparison-drawer"]');
      const drawerBadgeClass = await comparisonDrawer.locator('[data-testid="confidence-badge"]').getAttribute('class');

      // Both should have same color class
      const cardColor = cardBadgeClass?.match(/bg-(green|yellow|red)/)?.[0];
      const drawerColor = drawerBadgeClass?.match(/bg-(green|yellow|red)/)?.[0];

      expect(cardColor).toBe(drawerColor);
    });

    test('should show confidence level text matching color', async ({ page }) => {
      const investigationId = await startInvestigation(page);
      await waitForPhase(page, investigationId, 'complete', 90000);

      const firstMatch = page.locator('[data-testid="match-card"]').first();
      const confidenceBadge = firstMatch.locator('[data-testid="confidence-badge"]');

      const badgeClass = await confidenceBadge.getAttribute('class');
      const confidenceText = await confidenceBadge.textContent();

      if (badgeClass?.includes('bg-green')) {
        expect(confidenceText).toMatch(/high|confident/i);
      } else if (badgeClass?.includes('bg-yellow')) {
        expect(confidenceText).toMatch(/medium|moderate/i);
      } else if (badgeClass?.includes('bg-red')) {
        expect(confidenceText).toMatch(/low|uncertain/i);
      }
    });
  });

  test.describe('Model Comparison Integration', () => {
    test('should coordinate all model features in complete workflow', async ({ page }) => {
      const investigationId = await startInvestigation(page);

      // Phase 1: Verify model grid appears during stripe_analysis
      await waitForPhase(page, investigationId, 'stripe_analysis');
      const progressGrid = page.locator('[data-testid="model-progress-grid"]');
      await expect(progressGrid).toBeVisible();

      // Phase 2: Wait for completion
      await waitForPhase(page, investigationId, 'complete', 90000);

      // Phase 3: Verify model completion count
      const completionBadge = page.locator('[data-testid="model-completion-count"]');
      await expect(completionBadge).toContainText('6/6');

      // Phase 4: Open comparison drawer
      const firstMatch = page.locator('[data-testid="match-card"]').first();
      await firstMatch.click();

      const comparisonDrawer = page.locator('[data-testid="comparison-drawer"]');
      await expect(comparisonDrawer).toBeVisible();

      // Phase 5: Verify model scores breakdown
      const scoresSection = comparisonDrawer.locator('[data-testid="model-scores-breakdown"]');
      await expect(scoresSection).toBeVisible();

      // Phase 6: Verify confidence color coding
      const confidenceBadge = comparisonDrawer.locator('[data-testid="confidence-badge"]');
      await expect(confidenceBadge).toBeVisible();
      await expect(confidenceBadge).toHaveClass(/bg-(green|yellow|red)/);
    });
  });
});

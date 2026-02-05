import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ModelProgressGrid, ModelProgress, ModelStatus } from './ModelProgressGrid'

/**
 * Test utilities
 */
function createMockModels(statuses: ModelStatus[]): ModelProgress[] {
  const modelNames = [
    'wildlife_tools',
    'cvwc2019_reid',
    'transreid',
    'megadescriptor_b',
    'tiger_reid',
    'rapid_reid',
  ]

  return modelNames.slice(0, statuses.length).map((model, index) => ({
    model,
    progress: statuses[index] === 'completed' ? 100 : statuses[index] === 'running' ? 50 : 0,
    status: statuses[index],
    ...(statuses[index] === 'completed' && {
      embeddings: 1536,
      processingTime: 1234,
    }),
    ...(statuses[index] === 'error' && {
      errorMessage: `Error processing ${model}`,
    }),
  }))
}

describe('ModelProgressGrid', () => {
  describe('rendering', () => {
    it('renders with default title', () => {
      const models = createMockModels(['pending', 'pending', 'pending', 'pending', 'pending', 'pending'])
      render(<ModelProgressGrid models={models} />)

      expect(screen.getByTestId('model-progress-grid')).toBeInTheDocument()
      expect(screen.getByTestId('model-progress-title')).toHaveTextContent('Stripe Analysis')
    })

    it('renders with custom title', () => {
      const models = createMockModels(['pending'])
      render(<ModelProgressGrid models={models} title="Custom Title" />)

      expect(screen.getByTestId('model-progress-title')).toHaveTextContent('Custom Title')
    })

    it('renders all 6 model cards', () => {
      const models = createMockModels(['pending', 'pending', 'pending', 'pending', 'pending', 'pending'])
      render(<ModelProgressGrid models={models} />)

      expect(screen.getByTestId('model-card-wildlife_tools')).toBeInTheDocument()
      expect(screen.getByTestId('model-card-cvwc2019_reid')).toBeInTheDocument()
      expect(screen.getByTestId('model-card-transreid')).toBeInTheDocument()
      expect(screen.getByTestId('model-card-megadescriptor_b')).toBeInTheDocument()
      expect(screen.getByTestId('model-card-tiger_reid')).toBeInTheDocument()
      expect(screen.getByTestId('model-card-rapid_reid')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      const models = createMockModels(['pending'])
      render(<ModelProgressGrid models={models} className="custom-class" />)

      expect(screen.getByTestId('model-progress-grid')).toHaveClass('custom-class')
    })
  })

  describe('completion badge', () => {
    it('shows 0/6 when no models completed', () => {
      const models = createMockModels(['pending', 'pending', 'pending', 'pending', 'pending', 'pending'])
      render(<ModelProgressGrid models={models} />)

      expect(screen.getByTestId('model-progress-badge')).toHaveTextContent('0/6')
    })

    it('shows 3/6 when 3 models completed', () => {
      const models = createMockModels(['completed', 'completed', 'completed', 'pending', 'pending', 'pending'])
      render(<ModelProgressGrid models={models} />)

      expect(screen.getByTestId('model-progress-badge')).toHaveTextContent('3/6')
    })

    it('shows 6/6 with checkmark when all completed', () => {
      const models = createMockModels(['completed', 'completed', 'completed', 'completed', 'completed', 'completed'])
      render(<ModelProgressGrid models={models} />)

      const badge = screen.getByTestId('model-progress-badge')
      expect(badge).toHaveTextContent('6/6')
      // Badge should have success variant when all completed
      expect(badge).toHaveClass('bg-emerald-100')
    })

    it('shows error indicator when models have errors', () => {
      const models = createMockModels(['completed', 'error', 'pending', 'pending', 'pending', 'pending'])
      render(<ModelProgressGrid models={models} />)

      const badge = screen.getByTestId('model-progress-badge')
      // Badge should have danger variant when there are errors
      expect(badge).toHaveClass('bg-red-100')
    })
  })

  describe('model card statuses', () => {
    it('renders pending status correctly', () => {
      const models = createMockModels(['pending'])
      render(<ModelProgressGrid models={models} />)

      const card = screen.getByTestId('model-card-wildlife_tools')
      expect(card).toBeInTheDocument()

      const progressText = screen.getByTestId('model-progress-text-wildlife_tools')
      expect(progressText).toHaveTextContent('0%')
    })

    it('renders running status with animation', () => {
      const models: ModelProgress[] = [{
        model: 'wildlife_tools',
        progress: 50,
        status: 'running',
      }]
      render(<ModelProgressGrid models={models} />)

      const card = screen.getByTestId('model-card-wildlife_tools')
      expect(card).toHaveClass('shadow-tiger')

      const progressText = screen.getByTestId('model-progress-text-wildlife_tools')
      expect(progressText).toHaveTextContent('50%')
    })

    it('renders completed status with metadata', () => {
      const models: ModelProgress[] = [{
        model: 'wildlife_tools',
        progress: 100,
        status: 'completed',
        embeddings: 1536,
        processingTime: 2500,
      }]
      render(<ModelProgressGrid models={models} />)

      expect(screen.getByTestId('model-embeddings-wildlife_tools')).toHaveTextContent('1536 emb')
      expect(screen.getByTestId('model-time-wildlife_tools')).toHaveTextContent('2.5s')
    })

    it('renders error status with error message', () => {
      const models: ModelProgress[] = [{
        model: 'wildlife_tools',
        progress: 30,
        status: 'error',
        errorMessage: 'Connection timeout',
      }]
      render(<ModelProgressGrid models={models} />)

      expect(screen.getByTestId('model-error-wildlife_tools')).toHaveTextContent('Connection timeout')
    })
  })

  describe('progress bars', () => {
    it('renders progress bar with correct width', () => {
      const models: ModelProgress[] = [{
        model: 'wildlife_tools',
        progress: 75,
        status: 'running',
      }]
      render(<ModelProgressGrid models={models} />)

      const progressBar = screen.getByTestId('model-progress-bar-wildlife_tools')
      const fill = progressBar.querySelector('[role="progressbar"]')
      expect(fill).toHaveStyle({ width: '75%' })
    })

    it('clamps progress to 0-100 range', () => {
      const models: ModelProgress[] = [{
        model: 'wildlife_tools',
        progress: 150, // Over 100
        status: 'running',
      }]
      render(<ModelProgressGrid models={models} />)

      const progressBar = screen.getByTestId('model-progress-bar-wildlife_tools')
      const fill = progressBar.querySelector('[role="progressbar"]')
      expect(fill).toHaveStyle({ width: '100%' })
    })

    it('renders overall progress bar', () => {
      const models = createMockModels(['completed', 'completed', 'pending', 'pending', 'pending', 'pending'])
      render(<ModelProgressGrid models={models} />)

      expect(screen.getByTestId('model-overall-progress-bar')).toBeInTheDocument()
      expect(screen.getByTestId('model-overall-percent')).toHaveTextContent('33%')
    })
  })

  describe('model weights', () => {
    it('displays model weights for known models', () => {
      const models = createMockModels(['pending', 'pending'])
      render(<ModelProgressGrid models={models} />)

      expect(screen.getByTestId('model-weight-wildlife_tools')).toHaveTextContent('40%')
      expect(screen.getByTestId('model-weight-cvwc2019_reid')).toHaveTextContent('30%')
    })
  })

  describe('retry functionality', () => {
    it('shows retry button for error status', () => {
      const models: ModelProgress[] = [{
        model: 'wildlife_tools',
        progress: 0,
        status: 'error',
        errorMessage: 'Failed',
      }]
      render(<ModelProgressGrid models={models} onRetry={() => {}} />)

      expect(screen.getByTestId('model-retry-wildlife_tools')).toBeInTheDocument()
    })

    it('does not show retry button when onRetry is not provided', () => {
      const models: ModelProgress[] = [{
        model: 'wildlife_tools',
        progress: 0,
        status: 'error',
        errorMessage: 'Failed',
      }]
      render(<ModelProgressGrid models={models} />)

      expect(screen.queryByTestId('model-retry-wildlife_tools')).not.toBeInTheDocument()
    })

    it('calls onRetry with model name when retry clicked', () => {
      const onRetry = vi.fn()
      const models: ModelProgress[] = [{
        model: 'wildlife_tools',
        progress: 0,
        status: 'error',
        errorMessage: 'Failed',
      }]
      render(<ModelProgressGrid models={models} onRetry={onRetry} />)

      fireEvent.click(screen.getByTestId('model-retry-wildlife_tools'))
      expect(onRetry).toHaveBeenCalledWith('wildlife_tools')
    })

    it('calls onRetry on keyboard enter', () => {
      const onRetry = vi.fn()
      const models: ModelProgress[] = [{
        model: 'wildlife_tools',
        progress: 0,
        status: 'error',
        errorMessage: 'Failed',
      }]
      render(<ModelProgressGrid models={models} onRetry={onRetry} />)

      fireEvent.keyDown(screen.getByTestId('model-retry-wildlife_tools'), { key: 'Enter' })
      expect(onRetry).toHaveBeenCalledWith('wildlife_tools')
    })
  })

  describe('accessibility', () => {
    it('has proper aria labels on progress bars', () => {
      const models: ModelProgress[] = [{
        model: 'wildlife_tools',
        progress: 50,
        status: 'running',
      }]
      render(<ModelProgressGrid models={models} />)

      const progressBar = screen.getByTestId('model-progress-bar-wildlife_tools')
      const fill = progressBar.querySelector('[role="progressbar"]')
      expect(fill).toHaveAttribute('aria-valuenow', '50')
      expect(fill).toHaveAttribute('aria-valuemin', '0')
      expect(fill).toHaveAttribute('aria-valuemax', '100')
      expect(fill).toHaveAttribute('aria-label', 'Wildlife Tools progress')
    })

    it('has proper aria label on overall progress bar', () => {
      const models = createMockModels(['completed', 'pending'])
      render(<ModelProgressGrid models={models} />)

      const overallBar = screen.getByTestId('model-overall-progress-bar')
      const fill = overallBar.querySelector('[role="progressbar"]')
      expect(fill).toHaveAttribute('aria-label', 'Overall model progress')
    })
  })

  describe('processing time formatting', () => {
    it('formats milliseconds correctly', () => {
      const models: ModelProgress[] = [{
        model: 'wildlife_tools',
        progress: 100,
        status: 'completed',
        processingTime: 500,
      }]
      render(<ModelProgressGrid models={models} />)

      expect(screen.getByTestId('model-time-wildlife_tools')).toHaveTextContent('500ms')
    })

    it('formats seconds correctly', () => {
      const models: ModelProgress[] = [{
        model: 'wildlife_tools',
        progress: 100,
        status: 'completed',
        processingTime: 3500,
      }]
      render(<ModelProgressGrid models={models} />)

      expect(screen.getByTestId('model-time-wildlife_tools')).toHaveTextContent('3.5s')
    })
  })
})

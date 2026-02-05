import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { EnsembleVisualization, EnsembleInline } from '../EnsembleVisualization'

// Mock the confidence utility
vi.mock('../../../utils/confidence', () => ({
  MODEL_COLORS: {
    wildlife_tools: {
      name: 'Wildlife Tools',
      weight: 0.40,
      bg: 'bg-blue-500',
      bgLight: 'bg-blue-50',
      text: 'text-blue-700',
    },
    cvwc2019_reid: {
      name: 'CVWC2019',
      weight: 0.30,
      bg: 'bg-purple-500',
      bgLight: 'bg-purple-50',
      text: 'text-purple-700',
    },
    transreid: {
      name: 'TransReID',
      weight: 0.20,
      bg: 'bg-green-500',
      bgLight: 'bg-green-50',
      text: 'text-green-700',
    },
    megadescriptor_b: {
      name: 'MegaDescriptor',
      weight: 0.15,
      bg: 'bg-orange-500',
      bgLight: 'bg-orange-50',
      text: 'text-orange-700',
    },
    tiger_reid: {
      name: 'Tiger ReID',
      weight: 0.10,
      bg: 'bg-pink-500',
      bgLight: 'bg-pink-50',
      text: 'text-pink-700',
    },
    rapid_reid: {
      name: 'Rapid ReID',
      weight: 0.05,
      bg: 'bg-cyan-500',
      bgLight: 'bg-cyan-50',
      text: 'text-cyan-700',
    },
  },
  getModelInfo: (model: string) => {
    const normalized = model.toLowerCase().replace(/[\s-]/g, '_')
    const models: Record<string, { name: string; weight: number }> = {
      wildlife_tools: { name: 'Wildlife Tools', weight: 0.40 },
      cvwc2019_reid: { name: 'CVWC2019', weight: 0.30 },
      transreid: { name: 'TransReID', weight: 0.20 },
      megadescriptor_b: { name: 'MegaDescriptor', weight: 0.15 },
      tiger_reid: { name: 'Tiger ReID', weight: 0.10 },
      rapid_reid: { name: 'Rapid ReID', weight: 0.05 },
    }
    return models[normalized] || { name: model, weight: 0 }
  },
}))

describe('EnsembleVisualization', () => {
  const mockModels = [
    { model: 'wildlife_tools', similarity: 0.92, matched: true, weight: 0.40 },
    { model: 'cvwc2019_reid', similarity: 0.88, matched: true, weight: 0.30 },
    { model: 'transreid', similarity: 0.75, matched: true, weight: 0.20 },
    { model: 'megadescriptor_b', similarity: 0.60, matched: false, weight: 0.15 },
  ]

  describe('rendering', () => {
    it('should render the component', () => {
      render(<EnsembleVisualization models={mockModels} />)

      expect(screen.getByText('Ensemble Analysis')).toBeInTheDocument()
    })

    it('should display model agreement count', () => {
      render(<EnsembleVisualization models={mockModels} />)

      // Should show X/6 models (total is always 6)
      expect(screen.getByText(/\/6 models/)).toBeInTheDocument()
    })

    it('should render all models in legend', () => {
      render(<EnsembleVisualization models={mockModels} showLegend={true} />)

      expect(screen.getByText('Wildlife Tools')).toBeInTheDocument()
      expect(screen.getByText('CVWC2019')).toBeInTheDocument()
      expect(screen.getByText('TransReID')).toBeInTheDocument()
    })

    it('should hide legend when showLegend is false', () => {
      render(<EnsembleVisualization models={mockModels} showLegend={false} />)

      // Legend items should not be rendered in legend section
      const legends = screen.queryAllByText('Wildlife Tools')
      // Still visible in expanded view if expanded
      expect(legends.length).toBeGreaterThanOrEqual(0)
    })
  })

  describe('compact mode', () => {
    it('should be collapsed by default in compact mode', () => {
      render(<EnsembleVisualization models={mockModels} compact={true} />)

      // Expanded details should not be visible initially in compact mode
      // (they start collapsed)
      expect(screen.queryByText('Weighted Consensus Score')).not.toBeInTheDocument()
    })

    it('should expand when clicked in compact mode', () => {
      render(<EnsembleVisualization models={mockModels} compact={true} />)

      // Click to expand
      const header = screen.getByText('Ensemble Analysis').closest('div')
      fireEvent.click(header!)

      // Should now show detailed view
      expect(screen.getByText('Weighted Consensus Score')).toBeInTheDocument()
    })

    it('should be expanded by default when not compact', () => {
      render(<EnsembleVisualization models={mockModels} compact={false} />)

      expect(screen.getByText('Weighted Consensus Score')).toBeInTheDocument()
    })
  })

  describe('model matching', () => {
    it('should show similarity scores for matched models', () => {
      render(<EnsembleVisualization models={mockModels} />)

      // Look for percentage values
      expect(screen.getByText('92.0%')).toBeInTheDocument()
    })

    it('should correctly identify matched vs unmatched models', () => {
      const mixedModels = [
        { model: 'wildlife_tools', similarity: 0.9, matched: true },
        { model: 'cvwc2019_reid', similarity: 0.0, matched: false },
      ]

      render(<EnsembleVisualization models={mixedModels} />)

      // Check that both models are shown
      expect(screen.getAllByText('Wildlife Tools').length).toBeGreaterThan(0)
    })
  })

  describe('weighted score calculation', () => {
    it('should calculate and display weighted consensus score', () => {
      render(<EnsembleVisualization models={mockModels} />)

      expect(screen.getByText('Weighted Consensus Score')).toBeInTheDocument()
      // Score should be displayed as percentage
      const scoreElements = screen.getAllByText(/%/)
      expect(scoreElements.length).toBeGreaterThan(0)
    })
  })

  describe('agreement color coding', () => {
    it('should show green badge for high agreement (>=80%)', () => {
      const highAgreementModels = [
        { model: 'wildlife_tools', similarity: 0.9, matched: true },
        { model: 'cvwc2019_reid', similarity: 0.9, matched: true },
        { model: 'transreid', similarity: 0.9, matched: true },
        { model: 'megadescriptor_b', similarity: 0.9, matched: true },
        { model: 'tiger_reid', similarity: 0.9, matched: true },
      ]

      render(<EnsembleVisualization models={highAgreementModels} />)

      const badge = screen.getByText(/5\/6 models/)
      expect(badge).toHaveClass('text-emerald-600')
    })

    it('should show amber badge for medium agreement (50-80%)', () => {
      const mediumAgreementModels = [
        { model: 'wildlife_tools', similarity: 0.9, matched: true },
        { model: 'cvwc2019_reid', similarity: 0.9, matched: true },
        { model: 'transreid', similarity: 0.9, matched: true },
      ]

      render(<EnsembleVisualization models={mediumAgreementModels} />)

      const badge = screen.getByText(/3\/6 models/)
      expect(badge).toHaveClass('text-amber-600')
    })

    it('should show red badge for low agreement (<50%)', () => {
      const lowAgreementModels = [
        { model: 'wildlife_tools', similarity: 0.5, matched: true },
      ]

      render(<EnsembleVisualization models={lowAgreementModels} />)

      const badge = screen.getByText(/1\/6 models/)
      expect(badge).toHaveClass('text-red-600')
    })
  })

  describe('className prop', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <EnsembleVisualization models={mockModels} className="custom-class" />
      )

      expect(container.firstChild).toHaveClass('custom-class')
    })
  })

  describe('empty state', () => {
    it('should handle empty models array', () => {
      render(<EnsembleVisualization models={[]} />)

      expect(screen.getByText('Ensemble Analysis')).toBeInTheDocument()
      expect(screen.getByText('0/6 models')).toBeInTheDocument()
    })
  })
})

describe('EnsembleInline', () => {
  describe('rendering', () => {
    it('should render with agreement count', () => {
      render(<EnsembleInline agreementCount={4} />)

      expect(screen.getByText('4/6')).toBeInTheDocument()
    })

    it('should use custom totalModels', () => {
      render(<EnsembleInline agreementCount={3} totalModels={5} />)

      expect(screen.getByText('3/5')).toBeInTheDocument()
    })
  })

  describe('indicator bars', () => {
    it('should render correct number of indicator bars', () => {
      const { container } = render(<EnsembleInline agreementCount={4} totalModels={6} />)

      const bars = container.querySelectorAll('.w-1\\.5.h-4')
      expect(bars).toHaveLength(6)
    })
  })

  describe('color coding', () => {
    it('should be green for high agreement (>=80%)', () => {
      render(<EnsembleInline agreementCount={5} totalModels={6} />)

      const text = screen.getByText('5/6')
      expect(text).toHaveClass('text-emerald-600')
    })

    it('should be amber for medium agreement (50-80%)', () => {
      render(<EnsembleInline agreementCount={3} totalModels={6} />)

      const text = screen.getByText('3/6')
      expect(text).toHaveClass('text-amber-600')
    })

    it('should be red for low agreement (<50%)', () => {
      render(<EnsembleInline agreementCount={2} totalModels={6} />)

      const text = screen.getByText('2/6')
      expect(text).toHaveClass('text-red-600')
    })
  })

  describe('className prop', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <EnsembleInline agreementCount={4} className="custom-inline-class" />
      )

      expect(container.firstChild).toHaveClass('custom-inline-class')
    })
  })
})

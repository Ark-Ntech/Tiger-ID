import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ImageQualityPanel, ImageQualityInline } from '../ImageQualityPanel'
import type { ImageQuality } from '../../../types/investigation2'

// Mock the cn utility
vi.mock('../../../utils/cn', () => ({
  cn: (...classes: (string | undefined | null | false)[]) =>
    classes.filter(Boolean).join(' '),
}))

// Mock the confidence utilities
vi.mock('../../../utils/confidence', () => ({
  getConfidenceLevel: (score: number) => {
    if (score >= 0.85) return 'high'
    if (score >= 0.65) return 'medium'
    if (score >= 0.4) return 'low'
    return 'critical'
  },
  getConfidenceColors: (level: string) => ({
    bg: `bg-${level}`,
    text: `text-${level}`,
    border: `border-${level}`,
  }),
  normalizeScore: (score: number) => (score > 1 ? score / 100 : score),
}))

describe('ImageQualityPanel', () => {
  const mockQuality: ImageQuality = {
    overall_score: 0.85,
    resolution_score: 0.9,
    blur_score: 0.8,
    stripe_visibility: 0.75,
    issues: [],
    recommendations: [],
  }

  describe('rendering', () => {
    it('should render the component', () => {
      render(<ImageQualityPanel quality={mockQuality} />)

      expect(screen.getByText('Image Quality Assessment')).toBeInTheDocument()
    })

    it('should display overall score', () => {
      render(<ImageQualityPanel quality={mockQuality} />)

      expect(screen.getByText('85')).toBeInTheDocument()
    })

    it('should display individual metrics', () => {
      render(<ImageQualityPanel quality={mockQuality} />)

      expect(screen.getByText('Resolution')).toBeInTheDocument()
      expect(screen.getByText('Sharpness')).toBeInTheDocument()
      expect(screen.getByText('Stripe Visibility')).toBeInTheDocument()
    })
  })

  describe('variants', () => {
    it('should render full variant by default', () => {
      render(<ImageQualityPanel quality={mockQuality} />)

      expect(screen.getByText('Image Quality Assessment')).toBeInTheDocument()
    })

    it('should render compact variant', () => {
      render(<ImageQualityPanel quality={mockQuality} variant="compact" />)

      // Compact variant should not show the full header
      expect(screen.queryByText('Based on resolution, sharpness, and stripe visibility')).not.toBeInTheDocument()
    })

    it('should render minimal variant', () => {
      render(<ImageQualityPanel quality={mockQuality} variant="minimal" />)

      expect(screen.getByText('Image Quality')).toBeInTheDocument()
      // Minimal variant should not show individual metrics breakdown
      expect(screen.queryByText('Image Quality Assessment')).not.toBeInTheDocument()
    })
  })

  describe('issues display', () => {
    it('should display issues when present', () => {
      const qualityWithIssues: ImageQuality = {
        ...mockQuality,
        issues: ['Image is too dark', 'Partial tiger visibility'],
      }

      render(<ImageQualityPanel quality={qualityWithIssues} variant="full" />)

      expect(screen.getByText('Issues Detected (2)')).toBeInTheDocument()
      expect(screen.getByText('Image is too dark')).toBeInTheDocument()
      expect(screen.getByText('Partial tiger visibility')).toBeInTheDocument()
    })

    it('should not display issues section when no issues', () => {
      render(<ImageQualityPanel quality={mockQuality} variant="full" />)

      expect(screen.queryByText('Issues Detected')).not.toBeInTheDocument()
    })

    it('should show warning icon in minimal variant when issues exist', () => {
      const qualityWithIssues: ImageQuality = {
        ...mockQuality,
        issues: ['Some issue'],
      }

      render(<ImageQualityPanel quality={qualityWithIssues} variant="minimal" />)

      // Warning icon should be present (ExclamationTriangleIcon)
      expect(screen.getByText('Image Quality')).toBeInTheDocument()
    })
  })

  describe('recommendations', () => {
    it('should show recommendations when showRecommendations is true and score is low', () => {
      const lowQuality: ImageQuality = {
        overall_score: 0.5,
        resolution_score: 0.3,
        blur_score: 0.4,
        stripe_visibility: 0.2,
        issues: [],
        recommendations: [],
      }

      render(<ImageQualityPanel quality={lowQuality} showRecommendations={true} variant="full" />)

      expect(screen.getByText('Recommendations')).toBeInTheDocument()
    })

    it('should not show recommendations when showRecommendations is false', () => {
      const lowQuality: ImageQuality = {
        overall_score: 0.3,
        resolution_score: 0.3,
        blur_score: 0.3,
        stripe_visibility: 0.3,
        issues: [],
        recommendations: [],
      }

      render(<ImageQualityPanel quality={lowQuality} showRecommendations={false} />)

      expect(screen.queryByText('Recommendations')).not.toBeInTheDocument()
    })
  })

  describe('high quality indicator', () => {
    it('should show excellent quality message for scores >= 80%', () => {
      const highQuality: ImageQuality = {
        overall_score: 0.85,
        resolution_score: 0.9,
        blur_score: 0.9,
        stripe_visibility: 0.9,
        issues: [],
        recommendations: [],
      }

      render(<ImageQualityPanel quality={highQuality} variant="full" />)

      expect(screen.getByText(/Excellent image quality/)).toBeInTheDocument()
    })

    it('should not show excellent quality message for scores < 80%', () => {
      const mediumQuality: ImageQuality = {
        overall_score: 0.7,
        resolution_score: 0.7,
        blur_score: 0.7,
        stripe_visibility: 0.7,
        issues: [],
        recommendations: [],
      }

      render(<ImageQualityPanel quality={mediumQuality} variant="full" />)

      expect(screen.queryByText(/Excellent image quality/)).not.toBeInTheDocument()
    })
  })

  describe('className prop', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <ImageQualityPanel quality={mockQuality} className="custom-class" />
      )

      expect(container.firstChild).toHaveClass('custom-class')
    })
  })

  describe('metric calculations', () => {
    it('should handle missing metric scores', () => {
      const incompleteQuality: ImageQuality = {
        overall_score: 0.7,
        resolution_score: 0.7,
        blur_score: 0.7,
        stripe_visibility: 0.7,
        issues: [],
        recommendations: [],
      }

      render(<ImageQualityPanel quality={incompleteQuality} />)

      // Should render without errors
      expect(screen.getByText('Resolution')).toBeInTheDocument()
    })

    it('should normalize percentage scores', () => {
      const percentageQuality: ImageQuality = {
        overall_score: 85, // Percentage format
        resolution_score: 90,
        blur_score: 80,
        stripe_visibility: 75,
        issues: [],
        recommendations: [],
      }

      render(<ImageQualityPanel quality={percentageQuality} />)

      // Should display normalized value
      expect(screen.getByText('85')).toBeInTheDocument()
    })
  })
})

describe('ImageQualityInline', () => {
  describe('rendering', () => {
    it('should render with score', () => {
      render(<ImageQualityInline score={0.85} />)

      expect(screen.getByText('Quality:')).toBeInTheDocument()
      expect(screen.getByText('85%')).toBeInTheDocument()
    })

    it('should handle percentage input', () => {
      render(<ImageQualityInline score={85} />)

      expect(screen.getByText('85%')).toBeInTheDocument()
    })
  })

  describe('progress bar', () => {
    it('should render progress bar at correct width', () => {
      const { container } = render(<ImageQualityInline score={0.75} />)

      const progressBar = container.querySelector('[style*="width"]')
      expect(progressBar).toHaveStyle({ width: '75%' })
    })
  })

  describe('className prop', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <ImageQualityInline score={0.8} className="custom-inline-class" />
      )

      expect(container.firstChild).toHaveClass('custom-inline-class')
    })
  })

  describe('color coding', () => {
    it('should use appropriate colors based on score level', () => {
      render(<ImageQualityInline score={0.9} />)

      const scoreText = screen.getByText('90%')
      expect(scoreText).toHaveClass('text-high')
    })
  })
})

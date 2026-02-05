import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { VerificationComparison } from '../VerificationComparison'
import type { VerifiedCandidate } from '../../../types/investigation2'

// Mock headlessui
vi.mock('@headlessui/react', () => {
  const MockDialog = ({ children, onClose }: { children: React.ReactNode; onClose: () => void }) => (
    <div data-testid="dialog" onClick={onClose}>
      {children}
    </div>
  )
  MockDialog.Panel = ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dialog-panel">{children}</div>
  )
  MockDialog.Title = ({ children }: { children: React.ReactNode }) => (
    <h2 data-testid="dialog-title">{children}</h2>
  )

  const MockTransition = ({ children, show }: { children: React.ReactNode; show: boolean }) =>
    show ? <div data-testid="transition">{children}</div> : null
  MockTransition.Child = ({ children }: { children: React.ReactNode }) => (
    <div data-testid="transition-child">{children}</div>
  )

  return {
    Dialog: MockDialog,
    Transition: MockTransition,
  }
})

// Mock the cn utility
vi.mock('../../../utils/cn', () => ({
  cn: (...classes: (string | undefined | null | false)[]) =>
    classes.filter(Boolean).join(' '),
}))

// Mock confidence utilities
vi.mock('../../../utils/confidence', () => ({
  getConfidenceLevel: (score: number) => {
    if (score >= 0.85) return 'high'
    if (score >= 0.65) return 'medium'
    if (score >= 0.4) return 'low'
    return 'critical'
  },
  getConfidenceColors: () => ({
    bg: 'bg-test',
    text: 'text-test',
    border: 'border-test',
  }),
  normalizeScore: (score: number) => (score > 1 ? score / 100 : score),
}))

describe('VerificationComparison', () => {
  const mockReidMatches = [
    { tiger_id: 't1', tiger_name: 'Raja', similarity: 0.92, model: 'wildlife_tools', rank: 1 },
    { tiger_id: 't2', tiger_name: 'Sher', similarity: 0.85, model: 'cvwc2019', rank: 2 },
    { tiger_id: 't3', tiger_name: 'Bagheera', similarity: 0.78, model: 'transreid', rank: 3 },
  ]

  const mockVerifiedCandidates: VerifiedCandidate[] = [
    {
      tiger_id: 't1',
      tiger_name: 'Raja',
      combined_score: 0.95,
      num_matches: 42,
      normalized_match_score: 0.88,
    },
    {
      tiger_id: 't3',
      tiger_name: 'Bagheera',
      combined_score: 0.82,
      num_matches: 35,
      normalized_match_score: 0.75,
    },
    {
      tiger_id: 't2',
      tiger_name: 'Sher',
      combined_score: 0.72,
      num_matches: 28,
      normalized_match_score: 0.65,
    },
  ]

  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    reidMatches: mockReidMatches,
    verifiedCandidates: mockVerifiedCandidates,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('should render when isOpen is true', () => {
      render(<VerificationComparison {...defaultProps} />)

      expect(screen.getByText('Verification Comparison')).toBeInTheDocument()
    })

    it('should not render when isOpen is false', () => {
      render(<VerificationComparison {...defaultProps} isOpen={false} />)

      expect(screen.queryByText('Verification Comparison')).not.toBeInTheDocument()
    })

    it('should display ReID rankings section', () => {
      render(<VerificationComparison {...defaultProps} />)

      expect(screen.getByText('ReID Rankings')).toBeInTheDocument()
      expect(screen.getByText('(Before Verification)')).toBeInTheDocument()
    })

    it('should display Verified rankings section', () => {
      render(<VerificationComparison {...defaultProps} />)

      expect(screen.getByText('Verified Rankings')).toBeInTheDocument()
      expect(screen.getByText('(After Verification)')).toBeInTheDocument()
    })
  })

  describe('tiger list display', () => {
    it('should display top 3 tigers from ReID matches', () => {
      render(<VerificationComparison {...defaultProps} />)

      const rajaElements = screen.getAllByText('Raja')
      expect(rajaElements.length).toBeGreaterThan(0)
      const sherElements = screen.getAllByText('Sher')
      expect(sherElements.length).toBeGreaterThan(0)
      const bagheeraElements = screen.getAllByText('Bagheera')
      expect(bagheeraElements.length).toBeGreaterThan(0)
    })

    it('should display tiger similarity scores', () => {
      render(<VerificationComparison {...defaultProps} />)

      // Check for percentage display (92.0%)
      expect(screen.getByText('92.0%')).toBeInTheDocument()
    })

    it('should display rank badges', () => {
      render(<VerificationComparison {...defaultProps} />)

      const rank1Elements = screen.getAllByText('#1')
      expect(rank1Elements.length).toBeGreaterThan(0)
      const rank2Elements = screen.getAllByText('#2')
      expect(rank2Elements.length).toBeGreaterThan(0)
      const rank3Elements = screen.getAllByText('#3')
      expect(rank3Elements.length).toBeGreaterThan(0)
    })
  })

  describe('top match changed alert', () => {
    it('should show alert when top match changed', () => {
      const changedVerified: VerifiedCandidate[] = [
        {
          tiger_id: 't2', // Different from ReID top (t1)
          tiger_name: 'Sher',
          combined_score: 0.95,
          num_matches: 42,
          normalized_match_score: 0.88,
        },
        ...mockVerifiedCandidates.slice(1),
      ]

      render(
        <VerificationComparison
          {...defaultProps}
          verifiedCandidates={changedVerified}
        />
      )

      expect(screen.getByText('Top Match Changed After Verification')).toBeInTheDocument()
    })

    it('should not show alert when top match is same', () => {
      render(<VerificationComparison {...defaultProps} />)

      expect(screen.queryByText('Top Match Changed After Verification')).not.toBeInTheDocument()
    })
  })

  describe('rank change indicators', () => {
    it('should show rank changes for tigers', () => {
      render(<VerificationComparison {...defaultProps} />)

      // Bagheera moved from #3 to #2 (up)
      // Sher moved from #2 to #3 (down)
      // Look for rank change indicators
      const rankChanges = screen.getAllByText(/\+|\-/)
      expect(rankChanges.length).toBeGreaterThan(0)
    })
  })

  describe('tiger selection', () => {
    it('should show detail panel when tiger is selected', () => {
      render(<VerificationComparison {...defaultProps} />)

      // Click on a tiger
      const tigerButton = screen.getAllByRole('button').find(
        btn => btn.textContent?.includes('Raja')
      )
      if (tigerButton) {
        fireEvent.click(tigerButton)

        expect(screen.getByText(/Detailed Comparison/)).toBeInTheDocument()
      }
    })

    it('should deselect tiger when clicked again', () => {
      render(<VerificationComparison {...defaultProps} />)

      // Click on a tiger
      const tigerButton = screen.getAllByRole('button').find(
        btn => btn.textContent?.includes('Raja')
      )
      if (tigerButton) {
        fireEvent.click(tigerButton)
        fireEvent.click(tigerButton)

        // Detail panel should be hidden
        expect(screen.queryByText(/Detailed Comparison:/)).not.toBeInTheDocument()
      }
    })
  })

  describe('explanation section', () => {
    it('should display explanation of ranking differences', () => {
      render(<VerificationComparison {...defaultProps} />)

      expect(screen.getByText('Why Rankings May Differ')).toBeInTheDocument()
      expect(screen.getByText(/ReID models/)).toBeInTheDocument()
      expect(screen.getByText(/Geometric verification/)).toBeInTheDocument()
    })
  })

  describe('close functionality', () => {
    it('should call onClose when close button is clicked', () => {
      const onClose = vi.fn()
      render(<VerificationComparison {...defaultProps} onClose={onClose} />)

      const closeButton = screen.getByText('Close')
      fireEvent.click(closeButton)

      expect(onClose).toHaveBeenCalled()
    })
  })

  describe('keypoint matches display', () => {
    it('should display keypoint match counts for verified candidates', () => {
      render(<VerificationComparison {...defaultProps} />)

      expect(screen.getByText(/42 keypoint matches/)).toBeInTheDocument()
      expect(screen.getByText(/35 keypoint matches/)).toBeInTheDocument()
    })
  })

  describe('className prop', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <VerificationComparison {...defaultProps} className="custom-class" />
      )

      // Dialog should have the className
      const dialog = container.querySelector('[data-testid="dialog"]')
      expect(dialog).toHaveClass('custom-class')
    })
  })

  describe('empty states', () => {
    it('should handle empty reidMatches', () => {
      render(
        <VerificationComparison
          {...defaultProps}
          reidMatches={[]}
        />
      )

      // Should still render the component
      expect(screen.getByText('ReID Rankings')).toBeInTheDocument()
    })

    it('should handle empty verifiedCandidates', () => {
      render(
        <VerificationComparison
          {...defaultProps}
          verifiedCandidates={[]}
        />
      )

      // Should still render the component
      expect(screen.getByText('Verified Rankings')).toBeInTheDocument()
    })
  })
})

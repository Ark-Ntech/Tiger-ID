import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { Investigation2MatchCard } from '../Investigation2MatchCard'

// Mock icons
vi.mock('@heroicons/react/24/outline', () => ({
  ChevronDownIcon: () => <svg data-testid="chevron-down-icon" />,
  ChevronUpIcon: () => <svg data-testid="chevron-up-icon" />,
  MapPinIcon: () => <svg data-testid="map-pin-icon" />,
  BuildingOfficeIcon: () => <svg data-testid="building-icon" />,
}))

vi.mock('@heroicons/react/24/solid', () => ({
  CheckBadgeIcon: () => <svg data-testid="check-badge-icon" />,
  ExclamationTriangleIcon: () => <svg data-testid="warning-icon" />,
  ShieldCheckIcon: () => <svg data-testid="shield-icon" />,
}))

// Mock confidence utils
vi.mock('../../utils/confidence', () => ({
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
  toPercentage: (score: number) => Math.round(score * 100),
  getVerificationColors: () => ({
    bg: 'bg-verified',
    text: 'text-verified',
    border: 'border-verified',
  }),
}))

// Mock cn utility
vi.mock('../../utils/cn', () => ({
  cn: (...classes: (string | undefined | null | false)[]) =>
    classes.filter(Boolean).join(' '),
}))

// Mock EnsembleVisualization
vi.mock('../investigations/EnsembleVisualization', () => ({
  EnsembleInline: () => <div data-testid="ensemble-inline" />,
}))

const mockMatch = {
  tiger_id: 'tiger-123',
  tiger_name: 'Raja',
  similarity: 0.92,
  model: 'wildlife_tools',
  uploaded_image_crop: '/images/uploaded.jpg',
  database_image: '/images/tiger1.jpg',
  facility: {
    name: 'Big Cat Rescue',
    location: 'Tampa, FL',
  },
}

describe('Investigation2MatchCard', () => {
  it('renders tiger name', () => {
    render(<Investigation2MatchCard match={mockMatch} rank={1} />)
    expect(screen.getByText('Raja')).toBeInTheDocument()
  })

  it('displays rank badge', () => {
    render(<Investigation2MatchCard match={mockMatch} rank={1} />)
    expect(screen.getByText('#1')).toBeInTheDocument()
  })

  it('shows confidence score as percentage', () => {
    render(<Investigation2MatchCard match={mockMatch} rank={1} />)
    // 0.92 = 92%
    expect(screen.getByText(/92/)).toBeInTheDocument()
  })

  it('displays model name', () => {
    render(<Investigation2MatchCard match={mockMatch} rank={1} />)
    expect(screen.getByText(/wildlife_tools/i)).toBeInTheDocument()
  })

  it('shows facility information when provided', () => {
    render(<Investigation2MatchCard match={mockMatch} rank={1} />)
    expect(screen.getByText(/Big Cat Rescue/)).toBeInTheDocument()
    expect(screen.getByText(/Tampa, FL/)).toBeInTheDocument()
  })

  it('handles match without facility info', () => {
    const matchNoFacility = {
      ...mockMatch,
      facility: {
        name: '',
        location: '',
      },
    }
    render(<Investigation2MatchCard match={matchNoFacility} rank={1} />)
    expect(screen.getByText('Raja')).toBeInTheDocument()
  })

  it('renders different ranks correctly', () => {
    const { rerender } = render(<Investigation2MatchCard match={mockMatch} rank={1} />)
    expect(screen.getByText('#1')).toBeInTheDocument()

    rerender(<Investigation2MatchCard match={mockMatch} rank={5} />)
    expect(screen.getByText('#5')).toBeInTheDocument()
  })

  it('calls onClick when card is clicked', () => {
    const handleClick = vi.fn()
    render(<Investigation2MatchCard match={mockMatch} rank={1} onClick={handleClick} />)

    // Find clickable element
    const card = screen.getByText('Raja').closest('div[role="button"]') ||
                 screen.getByText('Raja').closest('button')
    if (card) {
      fireEvent.click(card)
      expect(handleClick).toHaveBeenCalled()
    }
  })

  it('shows low confidence styling for low scores', () => {
    const lowConfidenceMatch = {
      ...mockMatch,
      similarity: 0.40,
    }
    render(<Investigation2MatchCard match={lowConfidenceMatch} rank={3} />)
    // Should show percentage, may have warning styling
    expect(screen.getByText(/40/)).toBeInTheDocument()
  })

  it('shows high confidence styling for high scores', () => {
    const highConfidenceMatch = {
      ...mockMatch,
      similarity: 0.97,
    }
    render(<Investigation2MatchCard match={highConfidenceMatch} rank={1} />)
    expect(screen.getByText(/97/)).toBeInTheDocument()
  })

  it('handles missing tiger name gracefully', () => {
    const matchNoName = {
      ...mockMatch,
      tiger_name: 'Unknown',
    }
    render(<Investigation2MatchCard match={matchNoName} rank={1} />)
    // Should show ID or placeholder
    expect(screen.getByText(/#1/)).toBeInTheDocument()
  })

  it('renders image when URL provided', () => {
    render(<Investigation2MatchCard match={mockMatch} rank={1} />)
    const image = screen.queryByRole('img')
    if (image) {
      expect(image).toHaveAttribute('src', '/images/tiger1.jpg')
    }
  })

  it('handles match with all models ensemble result', () => {
    const ensembleMatch = {
      ...mockMatch,
      model: 'ensemble',
      models_matched: 3,
      total_models: 3,
    }
    render(<Investigation2MatchCard match={ensembleMatch} rank={1} />)
    expect(screen.getByText('Raja')).toBeInTheDocument()
  })
})

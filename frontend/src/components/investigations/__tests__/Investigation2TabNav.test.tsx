import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import { Investigation2TabNav } from '../Investigation2TabNav'

// Mock cn utility
vi.mock('../../../utils/cn', () => ({
  cn: (...classes: (string | undefined | null | false)[]) =>
    classes.filter(Boolean).join(' '),
}))

// Mock Badge component
vi.mock('../../common/Badge', () => ({
  default: ({ children, variant }: { children: React.ReactNode; variant?: string }) => (
    <span data-testid="badge" data-variant={variant}>{children}</span>
  ),
}))

// Mock heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  InformationCircleIcon: () => <span data-testid="info-icon">Info</span>,
  DocumentTextIcon: () => <span data-testid="doc-icon">Doc</span>,
  EyeIcon: () => <span data-testid="eye-icon">Eye</span>,
  BeakerIcon: () => <span data-testid="beaker-icon">Beaker</span>,
  ShieldCheckIcon: () => <span data-testid="shield-icon">Shield</span>,
  LightBulbIcon: () => <span data-testid="lightbulb-icon">Lightbulb</span>,
  GlobeAltIcon: () => <span data-testid="globe-icon">Globe</span>,
  LinkIcon: () => <span data-testid="link-icon">Link</span>,
  MapIcon: () => <span data-testid="map-icon">Map</span>,
  ChevronDownIcon: () => <span data-testid="chevron-icon">Chevron</span>,
  ExclamationTriangleIcon: () => <span data-testid="warning-icon">Warning</span>,
}))

describe('Investigation2TabNav', () => {
  const defaultProps = {
    activeTab: 'overview',
    onTabChange: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('should render tab navigation', () => {
      const { container } = render(<Investigation2TabNav {...defaultProps} />)

      expect(container.firstChild).toBeInTheDocument()
    })

    it('should render all tab groups on desktop', () => {
      render(<Investigation2TabNav {...defaultProps} />)

      expect(screen.getByText('Investigation')).toBeInTheDocument()
      expect(screen.getByText('Analysis')).toBeInTheDocument()
      expect(screen.getByText('Intelligence')).toBeInTheDocument()
    })

    it('should render Overview tab', () => {
      render(<Investigation2TabNav {...defaultProps} />)

      expect(screen.getAllByText('Overview')[0]).toBeInTheDocument()
    })

    it('should render Full Report tab', () => {
      render(<Investigation2TabNav {...defaultProps} />)

      expect(screen.getAllByText('Full Report')[0]).toBeInTheDocument()
    })

    it('should render Detection tab', () => {
      render(<Investigation2TabNav {...defaultProps} />)

      expect(screen.getAllByText('Detection')[0]).toBeInTheDocument()
    })

    it('should render Matches tab', () => {
      render(<Investigation2TabNav {...defaultProps} />)

      expect(screen.getAllByText('Matches')[0]).toBeInTheDocument()
    })

    it('should render Verification tab', () => {
      render(<Investigation2TabNav {...defaultProps} />)

      expect(screen.getAllByText('Verification')[0]).toBeInTheDocument()
    })

    it('should render Methodology tab', () => {
      render(<Investigation2TabNav {...defaultProps} />)

      expect(screen.getAllByText('Methodology')[0]).toBeInTheDocument()
    })

    it('should render External Intel tab', () => {
      render(<Investigation2TabNav {...defaultProps} />)

      expect(screen.getAllByText('External Intel')[0]).toBeInTheDocument()
    })

    it('should render Citations tab', () => {
      render(<Investigation2TabNav {...defaultProps} />)

      expect(screen.getAllByText('Citations')[0]).toBeInTheDocument()
    })

    it('should render Location tab', () => {
      render(<Investigation2TabNav {...defaultProps} />)

      expect(screen.getAllByText('Location')[0]).toBeInTheDocument()
    })
  })

  describe('tab selection', () => {
    it('should call onTabChange when tab is clicked', () => {
      const onTabChange = vi.fn()
      render(<Investigation2TabNav {...defaultProps} onTabChange={onTabChange} />)

      const reportTab = screen.getAllByText('Full Report')[0]
      fireEvent.click(reportTab)

      expect(onTabChange).toHaveBeenCalledWith('report')
    })

    it('should highlight active tab', () => {
      render(<Investigation2TabNav {...defaultProps} activeTab="detection" />)

      const detectionButtons = screen.getAllByText('Detection')
      const detectionButton = detectionButtons[0].closest('button')

      // Active tabs have shadow-sm class
      expect(detectionButton).toHaveClass('shadow-sm')
    })
  })

  describe('counts', () => {
    it('should display detection count', () => {
      render(
        <Investigation2TabNav
          {...defaultProps}
          counts={{ detection: 5 }}
        />
      )

      const badges = screen.getAllByTestId('badge')
      expect(badges.some(b => b.textContent === '5')).toBe(true)
    })

    it('should display matches count', () => {
      render(
        <Investigation2TabNav
          {...defaultProps}
          counts={{ matches: 10 }}
        />
      )

      const badges = screen.getAllByTestId('badge')
      expect(badges.some(b => b.textContent === '10')).toBe(true)
    })

    it('should display verification count', () => {
      render(
        <Investigation2TabNav
          {...defaultProps}
          counts={{ verification: 3 }}
        />
      )

      const badges = screen.getAllByTestId('badge')
      expect(badges.some(b => b.textContent === '3')).toBe(true)
    })

    it('should display external count', () => {
      render(
        <Investigation2TabNav
          {...defaultProps}
          counts={{ external: 7 }}
        />
      )

      const badges = screen.getAllByTestId('badge')
      expect(badges.some(b => b.textContent === '7')).toBe(true)
    })

    it('should display citations count', () => {
      render(
        <Investigation2TabNav
          {...defaultProps}
          counts={{ citations: 12 }}
        />
      )

      const badges = screen.getAllByTestId('badge')
      expect(badges.some(b => b.textContent === '12')).toBe(true)
    })

    it('should not show badge when count is undefined', () => {
      render(<Investigation2TabNav {...defaultProps} counts={{}} />)

      const badges = screen.queryAllByTestId('badge')
      expect(badges.length).toBe(0)
    })
  })

  describe('verification disagreement', () => {
    it('should show alert banner when verificationDisagreement is true', () => {
      render(
        <Investigation2TabNav
          {...defaultProps}
          verificationDisagreement={true}
        />
      )

      expect(screen.getByText('Verification Disagreement Detected')).toBeInTheDocument()
    })

    it('should show description in alert banner', () => {
      render(
        <Investigation2TabNav
          {...defaultProps}
          verificationDisagreement={true}
        />
      )

      expect(screen.getByText(/Geometric verification results differ from ReID rankings/)).toBeInTheDocument()
    })

    it('should have View Details button in alert banner', () => {
      render(
        <Investigation2TabNav
          {...defaultProps}
          verificationDisagreement={true}
        />
      )

      expect(screen.getByText('View Details')).toBeInTheDocument()
    })

    it('should navigate to verification tab when View Details clicked', () => {
      const onTabChange = vi.fn()
      render(
        <Investigation2TabNav
          {...defaultProps}
          onTabChange={onTabChange}
          verificationDisagreement={true}
        />
      )

      fireEvent.click(screen.getByText('View Details'))

      expect(onTabChange).toHaveBeenCalledWith('verification')
    })

    it('should not show alert banner when verificationDisagreement is false', () => {
      render(
        <Investigation2TabNav
          {...defaultProps}
          verificationDisagreement={false}
        />
      )

      expect(screen.queryByText('Verification Disagreement Detected')).not.toBeInTheDocument()
    })
  })

  describe('className prop', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <Investigation2TabNav {...defaultProps} className="custom-class" />
      )

      expect(container.firstChild).toHaveClass('custom-class')
    })
  })

  describe('tab groups', () => {
    it('should have Investigation group as primary', () => {
      render(<Investigation2TabNav {...defaultProps} />)

      // Primary tabs have larger padding
      const overviewButtons = screen.getAllByText('Overview')
      const overviewButton = overviewButtons[0].closest('button')
      expect(overviewButton).toHaveClass('px-4')
    })

    it('should have Analysis group as secondary', () => {
      render(<Investigation2TabNav {...defaultProps} />)

      // Secondary tabs have medium padding
      const detectionButtons = screen.getAllByText('Detection')
      const detectionButton = detectionButtons[0].closest('button')
      expect(detectionButton).toHaveClass('px-3')
    })

    it('should have Intelligence group as tertiary', () => {
      render(<Investigation2TabNav {...defaultProps} />)

      // Tertiary tabs have smaller padding
      const locationButtons = screen.getAllByText('Location')
      const locationButton = locationButtons[0].closest('button')
      expect(locationButton).toHaveClass('px-2.5')
    })
  })

  describe('disabled state', () => {
    it('should handle disabled tabs', () => {
      // This tests the disabled styling logic
      render(<Investigation2TabNav {...defaultProps} />)

      // Tabs should be clickable by default (not disabled)
      const overviewButtons = screen.getAllByText('Overview')
      const overviewButton = overviewButtons[0].closest('button')
      expect(overviewButton).not.toBeDisabled()
    })
  })

  describe('icons', () => {
    it('should render icons for each tab', () => {
      render(<Investigation2TabNav {...defaultProps} />)

      expect(screen.getAllByTestId('info-icon').length).toBeGreaterThan(0)
      expect(screen.getAllByTestId('doc-icon').length).toBeGreaterThan(0)
      expect(screen.getAllByTestId('eye-icon').length).toBeGreaterThan(0)
    })
  })
})

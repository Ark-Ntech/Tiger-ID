import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import InvestigationLayout, {
  CollapsibleSection,
  StatusIndicator,
} from './InvestigationLayout'

describe('InvestigationLayout', () => {
  const mockUploadPanel = <div data-testid="mock-upload-panel">Upload Panel</div>
  const mockProgressPanel = <div data-testid="mock-progress-panel">Progress Panel</div>
  const mockResultsPanel = <div data-testid="mock-results-panel">Results Panel</div>

  describe('Desktop Layout (lg+)', () => {
    beforeEach(() => {
      // Mock matchMedia for desktop viewport
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation((query: string) => ({
          matches: query.includes('min-width: 1024px'),
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        })),
      })
    })

    it('renders upload panel in left column', () => {
      render(
        <InvestigationLayout
          uploadPanel={mockUploadPanel}
          progressPanel={mockProgressPanel}
        />
      )

      expect(screen.getByTestId('mock-upload-panel')).toBeInTheDocument()
      expect(screen.getByTestId('investigation-layout-upload-column')).toBeInTheDocument()
    })

    it('renders progress panel in right column when not complete', () => {
      render(
        <InvestigationLayout
          uploadPanel={mockUploadPanel}
          progressPanel={mockProgressPanel}
          isComplete={false}
        />
      )

      expect(screen.getByTestId('mock-progress-panel')).toBeInTheDocument()
      expect(screen.getByTestId('investigation-layout-right-column')).toBeInTheDocument()
    })

    it('renders results panel in right column when complete', () => {
      render(
        <InvestigationLayout
          uploadPanel={mockUploadPanel}
          progressPanel={mockProgressPanel}
          resultsPanel={mockResultsPanel}
          isComplete={true}
        />
      )

      // Results panel should be shown instead of progress
      expect(screen.getByTestId('mock-results-panel')).toBeInTheDocument()
    })

    it('renders desktop layout container', () => {
      render(
        <InvestigationLayout
          uploadPanel={mockUploadPanel}
          progressPanel={mockProgressPanel}
        />
      )

      expect(screen.getByTestId('investigation-layout-desktop')).toBeInTheDocument()
    })
  })

  describe('Mobile Layout (sm)', () => {
    beforeEach(() => {
      // Mock matchMedia for mobile viewport
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation((query: string) => ({
          matches: false, // Always return false for min-width queries
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        })),
      })
    })

    it('renders mobile layout container', () => {
      render(
        <InvestigationLayout
          uploadPanel={mockUploadPanel}
          progressPanel={mockProgressPanel}
        />
      )

      expect(screen.getByTestId('investigation-layout-mobile')).toBeInTheDocument()
    })

    it('renders collapsible upload section', () => {
      render(
        <InvestigationLayout
          uploadPanel={mockUploadPanel}
          progressPanel={mockProgressPanel}
        />
      )

      expect(screen.getByTestId('investigation-layout-mobile-upload')).toBeInTheDocument()
    })

    it('auto-collapses upload section when hasImage is true', async () => {
      vi.useFakeTimers()

      const { rerender } = render(
        <InvestigationLayout
          uploadPanel={mockUploadPanel}
          progressPanel={mockProgressPanel}
          hasImage={false}
        />
      )

      // Initially expanded (hasImage is false)
      expect(screen.getByTestId('investigation-layout-mobile-upload-content')).toHaveClass('opacity-100')

      // Rerender with hasImage=true
      rerender(
        <InvestigationLayout
          uploadPanel={mockUploadPanel}
          progressPanel={mockProgressPanel}
          hasImage={true}
        />
      )

      // Fast forward past the 500ms delay
      vi.advanceTimersByTime(600)

      await waitFor(() => {
        expect(screen.getByTestId('investigation-layout-mobile-upload-content')).toHaveClass('opacity-0')
      })

      vi.useRealTimers()
    })

    it('shows progress section when hasImage is true', () => {
      render(
        <InvestigationLayout
          uploadPanel={mockUploadPanel}
          progressPanel={mockProgressPanel}
          hasImage={true}
        />
      )

      expect(screen.getByTestId('investigation-layout-mobile-progress')).toBeInTheDocument()
    })

    it('renders mobile sticky header', () => {
      render(
        <InvestigationLayout
          uploadPanel={mockUploadPanel}
          progressPanel={mockProgressPanel}
        />
      )

      expect(screen.getByTestId('investigation-layout-mobile-header')).toBeInTheDocument()
    })
  })

  describe('CollapsibleSection', () => {
    it('toggles content visibility on button click', () => {
      const onToggle = vi.fn()

      render(
        <CollapsibleSection
          title="Test Section"
          isOpen={true}
          onToggle={onToggle}
          testId="test-section"
        >
          <div>Content</div>
        </CollapsibleSection>
      )

      const toggleButton = screen.getByTestId('test-section-toggle')
      fireEvent.click(toggleButton)

      expect(onToggle).toHaveBeenCalledTimes(1)
    })

    it('renders title and badge', () => {
      render(
        <CollapsibleSection
          title="Upload Image"
          isOpen={true}
          onToggle={vi.fn()}
          testId="upload-section"
          badge="Ready"
        >
          <div>Content</div>
        </CollapsibleSection>
      )

      expect(screen.getByText('Upload Image')).toBeInTheDocument()
      expect(screen.getByText('Ready')).toBeInTheDocument()
    })

    it('shows expanded content when isOpen is true', () => {
      render(
        <CollapsibleSection
          title="Test Section"
          isOpen={true}
          onToggle={vi.fn()}
          testId="test-section"
        >
          <div data-testid="section-content">Content</div>
        </CollapsibleSection>
      )

      const contentContainer = screen.getByTestId('test-section-content')
      expect(contentContainer).toHaveClass('opacity-100')
    })

    it('hides content when isOpen is false', () => {
      render(
        <CollapsibleSection
          title="Test Section"
          isOpen={false}
          onToggle={vi.fn()}
          testId="test-section"
        >
          <div data-testid="section-content">Content</div>
        </CollapsibleSection>
      )

      const contentContainer = screen.getByTestId('test-section-content')
      expect(contentContainer).toHaveClass('opacity-0')
    })

    it('has correct aria-expanded attribute', () => {
      const { rerender } = render(
        <CollapsibleSection
          title="Test Section"
          isOpen={true}
          onToggle={vi.fn()}
          testId="test-section"
        >
          <div>Content</div>
        </CollapsibleSection>
      )

      const toggleButton = screen.getByTestId('test-section-toggle')
      expect(toggleButton).toHaveAttribute('aria-expanded', 'true')

      rerender(
        <CollapsibleSection
          title="Test Section"
          isOpen={false}
          onToggle={vi.fn()}
          testId="test-section"
        >
          <div>Content</div>
        </CollapsibleSection>
      )

      expect(toggleButton).toHaveAttribute('aria-expanded', 'false')
    })
  })

  describe('StatusIndicator', () => {
    it('shows "Awaiting Image" when no image and not complete', () => {
      render(<StatusIndicator hasImage={false} isComplete={false} />)

      expect(screen.getByText('Awaiting Image')).toBeInTheDocument()
    })

    it('shows "In Progress" when has image and not complete', () => {
      render(<StatusIndicator hasImage={true} isComplete={false} />)

      expect(screen.getByText('In Progress')).toBeInTheDocument()
    })

    it('shows "Complete" when investigation is complete', () => {
      render(<StatusIndicator hasImage={true} isComplete={true} />)

      expect(screen.getByText('Complete')).toBeInTheDocument()
    })
  })

  describe('Swipe Gestures', () => {
    it('handles touch events for swipe gestures', () => {
      render(
        <InvestigationLayout
          uploadPanel={mockUploadPanel}
          progressPanel={mockProgressPanel}
          hasImage={true}
        />
      )

      const container = screen.getByTestId('investigation-layout')

      // Simulate touch start
      fireEvent.touchStart(container, {
        touches: [{ clientX: 200, clientY: 100 }],
      })

      // Simulate touch end (swipe left)
      fireEvent.touchEnd(container, {
        changedTouches: [{ clientX: 50, clientY: 100 }],
      })

      // The component should handle the swipe without errors
      expect(container).toBeInTheDocument()
    })
  })

  describe('Data Test IDs', () => {
    it('has all required data-testid attributes', () => {
      render(
        <InvestigationLayout
          uploadPanel={mockUploadPanel}
          progressPanel={mockProgressPanel}
          hasImage={true}
          isComplete={false}
        />
      )

      // Root container
      expect(screen.getByTestId('investigation-layout')).toBeInTheDocument()

      // Desktop layout
      expect(screen.getByTestId('investigation-layout-desktop')).toBeInTheDocument()
      expect(screen.getByTestId('investigation-layout-upload-column')).toBeInTheDocument()
      expect(screen.getByTestId('investigation-layout-right-column')).toBeInTheDocument()

      // Tablet layout
      expect(screen.getByTestId('investigation-layout-tablet')).toBeInTheDocument()
      expect(screen.getByTestId('investigation-layout-tablet-upload')).toBeInTheDocument()
      expect(screen.getByTestId('investigation-layout-tablet-progress')).toBeInTheDocument()

      // Mobile layout
      expect(screen.getByTestId('investigation-layout-mobile')).toBeInTheDocument()
      expect(screen.getByTestId('investigation-layout-mobile-header')).toBeInTheDocument()
      expect(screen.getByTestId('investigation-layout-mobile-upload')).toBeInTheDocument()
      expect(screen.getByTestId('investigation-layout-mobile-progress')).toBeInTheDocument()
    })
  })

  describe('Custom className', () => {
    it('applies custom className to root element', () => {
      render(
        <InvestigationLayout
          uploadPanel={mockUploadPanel}
          progressPanel={mockProgressPanel}
          className="custom-class"
        />
      )

      const container = screen.getByTestId('investigation-layout')
      expect(container).toHaveClass('custom-class')
    })
  })
})

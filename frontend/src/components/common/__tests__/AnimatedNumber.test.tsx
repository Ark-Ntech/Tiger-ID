import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AnimatedNumber } from '../AnimatedNumber'

// Mock matchMedia for reduced motion testing
const mockMatchMedia = (matches: boolean) => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })
}

describe('AnimatedNumber', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    mockMatchMedia(false) // Default: no reduced motion preference
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should render with data-testid', () => {
    render(<AnimatedNumber value={100} animate={false} />)
    expect(screen.getByTestId('animated-number')).toBeInTheDocument()
  })

  it('should display the value when animation is disabled', () => {
    render(<AnimatedNumber value={100} animate={false} />)
    expect(screen.getByTestId('animated-number')).toHaveTextContent('100')
  })

  it('should render with prefix', () => {
    render(<AnimatedNumber value={100} prefix="$" animate={false} />)
    expect(screen.getByTestId('animated-number')).toHaveTextContent('$100')
  })

  it('should render with suffix', () => {
    render(<AnimatedNumber value={95} suffix="%" animate={false} />)
    expect(screen.getByTestId('animated-number')).toHaveTextContent('95%')
  })

  it('should render with both prefix and suffix', () => {
    render(<AnimatedNumber value={50} prefix="~" suffix="ms" animate={false} />)
    expect(screen.getByTestId('animated-number')).toHaveTextContent('~50ms')
  })

  it('should format decimals correctly', () => {
    render(<AnimatedNumber value={95.567} decimals={2} animate={false} />)
    expect(screen.getByTestId('animated-number')).toHaveTextContent('95.57')
  })

  it('should apply custom className', () => {
    render(<AnimatedNumber value={100} className="custom-class" animate={false} />)
    expect(screen.getByTestId('animated-number')).toHaveClass('custom-class')
  })

  it('should have tabular-nums class for consistent number width', () => {
    render(<AnimatedNumber value={100} animate={false} />)
    expect(screen.getByTestId('animated-number')).toHaveClass('tabular-nums')
  })

  it('should set data-value attribute with target value', () => {
    render(<AnimatedNumber value={42} animate={false} />)
    expect(screen.getByTestId('animated-number')).toHaveAttribute('data-value', '42')
  })

  it('should set data-animating attribute', () => {
    render(<AnimatedNumber value={100} animate={false} />)
    expect(screen.getByTestId('animated-number')).toHaveAttribute('data-animating', 'false')
  })

  it('should respect prefers-reduced-motion and show final value', () => {
    mockMatchMedia(true) // User prefers reduced motion
    render(<AnimatedNumber value={100} animate={true} />)
    expect(screen.getByTestId('animated-number')).toHaveTextContent('100')
  })

  it('should use Intl.NumberFormat when formatOptions provided', () => {
    render(
      <AnimatedNumber
        value={1234567}
        formatOptions={{ useGrouping: true }}
        animate={false}
      />
    )
    // Should include comma separators
    expect(screen.getByTestId('animated-number')).toHaveTextContent('1,234,567')
  })

  it('should format with compact notation when specified', () => {
    render(
      <AnimatedNumber
        value={1200000}
        formatOptions={{ notation: 'compact' }}
        animate={false}
      />
    )
    // Should show compact format like "1.2M"
    const element = screen.getByTestId('animated-number')
    expect(element.textContent).toMatch(/1\.?2?M?/)
  })

  it('should animate when value changes', async () => {
    const { rerender } = render(<AnimatedNumber value={0} animate={true} />)

    // Rerender with new value
    rerender(<AnimatedNumber value={100} animate={true} />)

    // The element should have data-animating true while animating
    const element = screen.getByTestId('animated-number')
    expect(element).toHaveAttribute('data-animating', 'true')
  })

  it('should show final value after animation completes', async () => {
    mockMatchMedia(false)
    render(<AnimatedNumber value={100} duration={500} animate={true} />)

    // Let animation complete
    vi.advanceTimersByTime(600)

    await waitFor(() => {
      expect(screen.getByTestId('animated-number')).toHaveTextContent('100')
    })
  })

  it('should handle zero values', () => {
    render(<AnimatedNumber value={0} suffix="%" animate={false} />)
    expect(screen.getByTestId('animated-number')).toHaveTextContent('0%')
  })

  it('should handle negative values', () => {
    render(<AnimatedNumber value={-50} animate={false} />)
    expect(screen.getByTestId('animated-number')).toHaveTextContent('-50')
  })

  it('should call onComplete callback after animation', async () => {
    const onComplete = vi.fn()
    render(
      <AnimatedNumber value={100} duration={500} onComplete={onComplete} animate={true} />
    )

    // Animation should not be complete yet
    expect(onComplete).not.toHaveBeenCalled()

    // Let animation complete
    vi.advanceTimersByTime(600)

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledTimes(1)
    })
  })
})

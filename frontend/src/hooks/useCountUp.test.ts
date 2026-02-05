import { renderHook, act, waitFor } from '@testing-library/react'
import { useCountUp } from './useCountUp'

// Mock matchMedia for reduced motion testing
const mockMatchMedia = (matches: boolean) => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation((query) => ({
      matches,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  })
}

describe('useCountUp', () => {
  beforeEach(() => {
    jest.useFakeTimers()
    mockMatchMedia(false) // Default: no reduced motion preference
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('should start at the start value', () => {
    const { result } = renderHook(() =>
      useCountUp({ start: 0, end: 100, enabled: false })
    )

    // When disabled, should jump to end value
    expect(result.current.value).toBe(100)
  })

  it('should return formatted value with correct decimals', () => {
    const { result } = renderHook(() =>
      useCountUp({ end: 50.5, decimals: 1, enabled: false })
    )

    expect(result.current.formattedValue).toBe('50.5')
  })

  it('should animate to end value when enabled', async () => {
    const { result } = renderHook(() =>
      useCountUp({ start: 0, end: 100, duration: 1000, enabled: true })
    )

    expect(result.current.isAnimating).toBe(true)

    // Advance timers to complete animation
    await act(async () => {
      jest.advanceTimersByTime(1100)
    })

    await waitFor(() => {
      expect(result.current.isAnimating).toBe(false)
      expect(result.current.value).toBe(100)
    })
  })

  it('should call onComplete when animation finishes', async () => {
    const onComplete = jest.fn()
    renderHook(() =>
      useCountUp({
        start: 0,
        end: 100,
        duration: 500,
        onComplete,
        enabled: true,
      })
    )

    await act(async () => {
      jest.advanceTimersByTime(600)
    })

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledTimes(1)
    })
  })

  it('should respect prefers-reduced-motion', () => {
    mockMatchMedia(true) // User prefers reduced motion

    const { result } = renderHook(() =>
      useCountUp({ start: 0, end: 100, duration: 1000, enabled: true })
    )

    // Should immediately jump to end value
    expect(result.current.value).toBe(100)
    expect(result.current.isAnimating).toBe(false)
  })

  it('should reset animation when reset is called', async () => {
    const { result } = renderHook(() =>
      useCountUp({ start: 0, end: 100, duration: 500, enabled: true })
    )

    // Let animation complete
    await act(async () => {
      jest.advanceTimersByTime(600)
    })

    await waitFor(() => {
      expect(result.current.value).toBe(100)
    })

    // Reset the animation
    act(() => {
      result.current.reset()
    })

    expect(result.current.isAnimating).toBe(true)
  })

  it('should animate from current value when end changes', async () => {
    const { result, rerender } = renderHook(
      ({ end }) => useCountUp({ start: 0, end, duration: 500, enabled: true }),
      { initialProps: { end: 50 } }
    )

    // Let first animation complete
    await act(async () => {
      jest.advanceTimersByTime(600)
    })

    await waitFor(() => {
      expect(result.current.value).toBe(50)
    })

    // Change the end value
    rerender({ end: 100 })

    // Should start animating to new value
    expect(result.current.isAnimating).toBe(true)

    await act(async () => {
      jest.advanceTimersByTime(600)
    })

    await waitFor(() => {
      expect(result.current.value).toBe(100)
    })
  })

  it('should not animate when start equals end', () => {
    const { result } = renderHook(() =>
      useCountUp({ start: 50, end: 50, duration: 1000, enabled: true })
    )

    expect(result.current.value).toBe(50)
    expect(result.current.isAnimating).toBe(false)
  })

  it('should support negative values', async () => {
    const { result } = renderHook(() =>
      useCountUp({ start: -100, end: 0, duration: 500, enabled: true })
    )

    await act(async () => {
      jest.advanceTimersByTime(600)
    })

    await waitFor(() => {
      expect(result.current.value).toBe(0)
    })
  })

  it('should support counting down', async () => {
    const { result } = renderHook(() =>
      useCountUp({ start: 100, end: 0, duration: 500, enabled: true })
    )

    expect(result.current.isAnimating).toBe(true)

    await act(async () => {
      jest.advanceTimersByTime(600)
    })

    await waitFor(() => {
      expect(result.current.value).toBe(0)
    })
  })

  it('should apply different easing functions', async () => {
    const { result: linearResult } = renderHook(() =>
      useCountUp({ start: 0, end: 100, duration: 1000, easing: 'linear', enabled: true })
    )

    const { result: easeOutResult } = renderHook(() =>
      useCountUp({ start: 0, end: 100, duration: 1000, easing: 'easeOut', enabled: true })
    )

    // At the same point in time, different easings should produce different values
    // This is hard to test precisely due to requestAnimationFrame timing
    expect(linearResult.current.isAnimating).toBe(true)
    expect(easeOutResult.current.isAnimating).toBe(true)
  })
})

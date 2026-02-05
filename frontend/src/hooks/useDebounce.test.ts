import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useDebounce } from './useDebounce'

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('initial value', () => {
    it('should return initial value immediately', () => {
      const { result } = renderHook(() => useDebounce('initial', 500))

      expect(result.current).toBe('initial')
    })

    it('should work with different types', () => {
      const { result: stringResult } = renderHook(() => useDebounce('test', 500))
      const { result: numberResult } = renderHook(() => useDebounce(42, 500))
      const { result: objectResult } = renderHook(() => useDebounce({ a: 1 }, 500))
      const { result: arrayResult } = renderHook(() => useDebounce([1, 2, 3], 500))

      expect(stringResult.current).toBe('test')
      expect(numberResult.current).toBe(42)
      expect(objectResult.current).toEqual({ a: 1 })
      expect(arrayResult.current).toEqual([1, 2, 3])
    })

    it('should handle null and undefined', () => {
      const { result: nullResult } = renderHook(() => useDebounce(null, 500))
      const { result: undefinedResult } = renderHook(() => useDebounce(undefined, 500))

      expect(nullResult.current).toBeNull()
      expect(undefinedResult.current).toBeUndefined()
    })
  })

  describe('debounce behavior', () => {
    it('should not update value before delay', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 500),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'updated' })

      // Value should still be initial
      expect(result.current).toBe('initial')
    })

    it('should update value after delay', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 500),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'updated' })

      act(() => {
        vi.advanceTimersByTime(500)
      })

      expect(result.current).toBe('updated')
    })

    it('should use default delay of 500ms', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'updated' })

      act(() => {
        vi.advanceTimersByTime(499)
      })
      expect(result.current).toBe('initial')

      act(() => {
        vi.advanceTimersByTime(1)
      })
      expect(result.current).toBe('updated')
    })

    it('should respect custom delay', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 1000),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'updated' })

      act(() => {
        vi.advanceTimersByTime(999)
      })
      expect(result.current).toBe('initial')

      act(() => {
        vi.advanceTimersByTime(1)
      })
      expect(result.current).toBe('updated')
    })
  })

  describe('rapid value changes', () => {
    it('should only update with last value after rapid changes', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 500),
        { initialProps: { value: 'initial' } }
      )

      // Rapid changes
      rerender({ value: 'change1' })
      act(() => vi.advanceTimersByTime(100))

      rerender({ value: 'change2' })
      act(() => vi.advanceTimersByTime(100))

      rerender({ value: 'change3' })
      act(() => vi.advanceTimersByTime(100))

      rerender({ value: 'final' })

      // Still initial because timer keeps getting reset
      expect(result.current).toBe('initial')

      // Wait for final debounce
      act(() => vi.advanceTimersByTime(500))

      // Should be final value only
      expect(result.current).toBe('final')
    })

    it('should cancel pending updates on unmount', () => {
      const { result, rerender, unmount } = renderHook(
        ({ value }) => useDebounce(value, 500),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'updated' })

      // Unmount before timer fires
      unmount()

      // This should not throw
      act(() => vi.advanceTimersByTime(500))
    })
  })

  describe('delay changes', () => {
    it('should reset timer when delay changes', () => {
      const { result, rerender } = renderHook(
        ({ value, delay }) => useDebounce(value, delay),
        { initialProps: { value: 'initial', delay: 500 } }
      )

      rerender({ value: 'updated', delay: 1000 })

      act(() => vi.advanceTimersByTime(500))
      expect(result.current).toBe('initial')

      act(() => vi.advanceTimersByTime(500))
      expect(result.current).toBe('updated')
    })
  })

  describe('edge cases', () => {
    it('should handle zero delay', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 0),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'updated' })

      act(() => vi.advanceTimersByTime(0))

      expect(result.current).toBe('updated')
    })

    it('should handle same value updates', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 500),
        { initialProps: { value: 'same' } }
      )

      rerender({ value: 'same' })

      act(() => vi.advanceTimersByTime(500))

      expect(result.current).toBe('same')
    })

    it('should handle boolean values', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 500),
        { initialProps: { value: false } }
      )

      rerender({ value: true })

      act(() => vi.advanceTimersByTime(500))

      expect(result.current).toBe(true)
    })
  })
})

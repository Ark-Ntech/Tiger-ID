import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useDebounce } from '../useDebounce'

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('initial behavior', () => {
    it('should return initial value immediately', () => {
      const { result } = renderHook(() => useDebounce('initial', 500))

      expect(result.current).toBe('initial')
    })

    it('should return initial number value', () => {
      const { result } = renderHook(() => useDebounce(42, 500))

      expect(result.current).toBe(42)
    })

    it('should return initial object value', () => {
      const obj = { key: 'value' }
      const { result } = renderHook(() => useDebounce(obj, 500))

      expect(result.current).toEqual(obj)
    })

    it('should return initial array value', () => {
      const arr = [1, 2, 3]
      const { result } = renderHook(() => useDebounce(arr, 500))

      expect(result.current).toEqual(arr)
    })

    it('should return null value', () => {
      const { result } = renderHook(() => useDebounce(null, 500))

      expect(result.current).toBeNull()
    })

    it('should return undefined value', () => {
      const { result } = renderHook(() => useDebounce(undefined, 500))

      expect(result.current).toBeUndefined()
    })
  })

  describe('debounce behavior', () => {
    it('should not update immediately when value changes', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 500),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'updated' })

      expect(result.current).toBe('initial')
    })

    it('should update after delay', () => {
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

    it('should reset timer on rapid changes', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 500),
        { initialProps: { value: 'initial' } }
      )

      // First change
      rerender({ value: 'first' })

      act(() => {
        vi.advanceTimersByTime(300)
      })

      // Second change before delay completes
      rerender({ value: 'second' })

      act(() => {
        vi.advanceTimersByTime(300)
      })

      // Still should be initial because timer reset
      expect(result.current).toBe('initial')

      // Advance remaining time
      act(() => {
        vi.advanceTimersByTime(200)
      })

      expect(result.current).toBe('second')
    })

    it('should only return final value after rapid changes', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 500),
        { initialProps: { value: 'a' } }
      )

      rerender({ value: 'b' })
      rerender({ value: 'c' })
      rerender({ value: 'd' })
      rerender({ value: 'final' })

      act(() => {
        vi.advanceTimersByTime(500)
      })

      expect(result.current).toBe('final')
    })
  })

  describe('custom delay', () => {
    it('should use default delay of 500ms when not specified', () => {
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

    it('should use custom delay when specified', () => {
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

    it('should handle zero delay', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 0),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'updated' })

      act(() => {
        vi.advanceTimersByTime(0)
      })

      expect(result.current).toBe('updated')
    })

    it('should handle very short delay', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 10),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'updated' })

      act(() => {
        vi.advanceTimersByTime(10)
      })

      expect(result.current).toBe('updated')
    })

    it('should handle very long delay', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 10000),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'updated' })

      act(() => {
        vi.advanceTimersByTime(9999)
      })

      expect(result.current).toBe('initial')

      act(() => {
        vi.advanceTimersByTime(1)
      })

      expect(result.current).toBe('updated')
    })
  })

  describe('cleanup', () => {
    it('should clear timeout on unmount', () => {
      const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout')

      const { unmount, rerender } = renderHook(
        ({ value }) => useDebounce(value, 500),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'updated' })

      unmount()

      expect(clearTimeoutSpy).toHaveBeenCalled()

      clearTimeoutSpy.mockRestore()
    })

    it('should clear timeout on value change', () => {
      const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout')

      const { rerender } = renderHook(
        ({ value }) => useDebounce(value, 500),
        { initialProps: { value: 'first' } }
      )

      rerender({ value: 'second' })

      // clearTimeout is called when value changes
      expect(clearTimeoutSpy).toHaveBeenCalled()

      clearTimeoutSpy.mockRestore()
    })
  })

  describe('type preservation', () => {
    it('should preserve string type', () => {
      const { result } = renderHook(() => useDebounce<string>('test', 500))

      expect(typeof result.current).toBe('string')
    })

    it('should preserve number type', () => {
      const { result } = renderHook(() => useDebounce<number>(123, 500))

      expect(typeof result.current).toBe('number')
    })

    it('should preserve boolean type', () => {
      const { result } = renderHook(() => useDebounce<boolean>(true, 500))

      expect(typeof result.current).toBe('boolean')
    })

    it('should preserve object type', () => {
      const { result } = renderHook(() =>
        useDebounce<{ name: string }>({ name: 'test' }, 500)
      )

      expect(typeof result.current).toBe('object')
      expect(result.current).toHaveProperty('name')
    })
  })

  describe('edge cases', () => {
    it('should handle same value updates', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 500),
        { initialProps: { value: 'same' } }
      )

      rerender({ value: 'same' })

      expect(result.current).toBe('same')

      act(() => {
        vi.advanceTimersByTime(500)
      })

      expect(result.current).toBe('same')
    })

    it('should handle empty string', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 500),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: '' })

      act(() => {
        vi.advanceTimersByTime(500)
      })

      expect(result.current).toBe('')
    })

    it('should handle NaN', () => {
      const { result } = renderHook(() => useDebounce(NaN, 500))

      expect(Number.isNaN(result.current)).toBe(true)
    })

    it('should handle Infinity', () => {
      const { result } = renderHook(() => useDebounce(Infinity, 500))

      expect(result.current).toBe(Infinity)
    })
  })
})

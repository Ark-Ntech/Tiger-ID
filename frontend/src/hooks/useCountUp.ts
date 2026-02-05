import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Easing functions for smooth count-up animations
 */
const easingFunctions = {
  linear: (t: number): number => t,
  easeOut: (t: number): number => 1 - Math.pow(1 - t, 3),
  easeInOut: (t: number): number =>
    t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
} as const

export type EasingType = keyof typeof easingFunctions

export interface UseCountUpOptions {
  /** Starting value (default: 0) */
  start?: number
  /** Target end value */
  end: number
  /** Animation duration in milliseconds (default: 1000) */
  duration?: number
  /** Number of decimal places (default: 0) */
  decimals?: number
  /** Easing function type (default: 'easeOut') */
  easing?: EasingType
  /** Callback fired when animation completes */
  onComplete?: () => void
  /** Whether to animate (default: true). Set false to disable animation entirely */
  enabled?: boolean
}

export interface UseCountUpReturn {
  /** Current animated value */
  value: number
  /** Formatted string value with proper decimal places */
  formattedValue: string
  /** Whether the animation is currently running */
  isAnimating: boolean
  /** Reset and restart the animation */
  reset: () => void
}

/**
 * Check if user prefers reduced motion
 */
function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * useCountUp - A React hook for animating number count-ups
 *
 * Features:
 * - Smooth animations using requestAnimationFrame
 * - Multiple easing functions (linear, easeOut, easeInOut)
 * - Respects prefers-reduced-motion
 * - Configurable duration and decimal places
 * - Reset functionality
 *
 * @example
 * ```tsx
 * const { value, formattedValue, isAnimating, reset } = useCountUp({
 *   end: 95.5,
 *   duration: 1500,
 *   decimals: 1,
 *   easing: 'easeOut',
 *   onComplete: () => console.log('Animation complete'),
 * })
 * ```
 */
export function useCountUp({
  start = 0,
  end,
  duration = 1000,
  decimals = 0,
  easing = 'easeOut',
  onComplete,
  enabled = true,
}: UseCountUpOptions): UseCountUpReturn {
  const [value, setValue] = useState(start)
  const [isAnimating, setIsAnimating] = useState(false)

  // Refs to track animation state without causing re-renders
  const startTimeRef = useRef<number | null>(null)
  const rafIdRef = useRef<number | null>(null)
  const startValueRef = useRef(start)
  const endValueRef = useRef(end)
  const prevEndRef = useRef(end)

  // Get easing function
  const easingFn = easingFunctions[easing]

  /**
   * Format value with specified decimal places
   */
  const formatValue = useCallback(
    (val: number): string => {
      return val.toFixed(decimals)
    },
    [decimals]
  )

  /**
   * Animation frame callback
   */
  const animate = useCallback(
    (timestamp: number) => {
      if (startTimeRef.current === null) {
        startTimeRef.current = timestamp
      }

      const elapsed = timestamp - startTimeRef.current
      const progress = Math.min(elapsed / duration, 1)
      const easedProgress = easingFn(progress)

      const currentValue =
        startValueRef.current +
        (endValueRef.current - startValueRef.current) * easedProgress

      setValue(currentValue)

      if (progress < 1) {
        rafIdRef.current = requestAnimationFrame(animate)
      } else {
        // Animation complete
        setValue(endValueRef.current)
        setIsAnimating(false)
        startTimeRef.current = null
        rafIdRef.current = null
        onComplete?.()
      }
    },
    [duration, easingFn, onComplete]
  )

  /**
   * Start or restart the animation
   */
  const startAnimation = useCallback(
    (fromValue: number, toValue: number) => {
      // Cancel any existing animation
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current)
      }

      // If reduced motion is preferred or animation is disabled, jump to end value
      if (prefersReducedMotion() || !enabled) {
        setValue(toValue)
        return
      }

      // Don't animate if values are the same
      if (fromValue === toValue) {
        setValue(toValue)
        return
      }

      startValueRef.current = fromValue
      endValueRef.current = toValue
      startTimeRef.current = null
      setIsAnimating(true)
      rafIdRef.current = requestAnimationFrame(animate)
    },
    [animate, enabled]
  )

  /**
   * Reset and restart animation from start value
   */
  const reset = useCallback(() => {
    startAnimation(start, end)
  }, [start, end, startAnimation])

  // Start animation on mount and when end value changes
  useEffect(() => {
    // Check if end value has changed
    if (prevEndRef.current !== end) {
      // Animate from current value to new end value
      startAnimation(value, end)
      prevEndRef.current = end
    } else {
      // Initial mount - animate from start
      startAnimation(start, end)
    }

    // Cleanup on unmount
    return () => {
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [end, enabled])

  // Listen for reduced motion preference changes
  useEffect(() => {
    if (typeof window === 'undefined') return

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')

    const handleChange = (e: MediaQueryListEvent) => {
      if (e.matches && isAnimating) {
        // User enabled reduced motion while animating - jump to end
        if (rafIdRef.current !== null) {
          cancelAnimationFrame(rafIdRef.current)
        }
        setValue(endValueRef.current)
        setIsAnimating(false)
      }
    }

    mediaQuery.addEventListener('change', handleChange)

    return () => {
      mediaQuery.removeEventListener('change', handleChange)
    }
  }, [isAnimating])

  return {
    value,
    formattedValue: formatValue(value),
    isAnimating,
    reset,
  }
}

export default useCountUp

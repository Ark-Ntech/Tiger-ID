import React, { useMemo } from 'react'
import { cn } from '../../utils/cn'
import { useCountUp, type EasingType } from '../../hooks/useCountUp'

export interface AnimatedNumberProps {
  /** The target value to animate to */
  value: number
  /** Animation duration in milliseconds (default: 1000) */
  duration?: number
  /** Number of decimal places to display (default: 0) */
  decimals?: number
  /** Prefix to display before the number (e.g., "$") */
  prefix?: string
  /** Suffix to display after the number (e.g., "%") */
  suffix?: string
  /** Additional CSS classes for the container */
  className?: string
  /** Intl.NumberFormat options for advanced formatting */
  formatOptions?: Intl.NumberFormatOptions
  /** Easing function type (default: 'easeOut') */
  easing?: EasingType
  /** Callback fired when animation completes */
  onComplete?: () => void
  /** Starting value for animation (default: 0) */
  startFrom?: number
  /** Whether to animate (default: true) */
  animate?: boolean
}

/**
 * AnimatedNumber - Displays a number with a smooth count-up animation
 *
 * Features:
 * - Smooth animations using requestAnimationFrame
 * - Respects prefers-reduced-motion media query
 * - Multiple easing options (linear, easeOut, easeInOut)
 * - Supports prefix/suffix (e.g., "$100", "95%")
 * - Intl.NumberFormat support for localization
 * - Re-animates when value changes
 *
 * @example
 * ```tsx
 * // Basic percentage
 * <AnimatedNumber value={95.5} suffix="%" decimals={1} />
 *
 * // Currency with formatting
 * <AnimatedNumber
 *   value={1234.56}
 *   prefix="$"
 *   formatOptions={{ useGrouping: true }}
 *   decimals={2}
 * />
 *
 * // Large number with locale formatting
 * <AnimatedNumber
 *   value={1234567}
 *   formatOptions={{ notation: 'compact' }}
 * />
 * ```
 */
export const AnimatedNumber: React.FC<AnimatedNumberProps> = ({
  value,
  duration = 1000,
  decimals = 0,
  prefix = '',
  suffix = '',
  className,
  formatOptions,
  easing = 'easeOut',
  onComplete,
  startFrom = 0,
  animate = true,
}) => {
  const { value: animatedValue, isAnimating } = useCountUp({
    start: startFrom,
    end: value,
    duration,
    decimals,
    easing,
    onComplete,
    enabled: animate,
  })

  /**
   * Format the animated value using Intl.NumberFormat if options provided,
   * otherwise use simple toFixed formatting
   */
  const formattedValue = useMemo(() => {
    if (formatOptions) {
      return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
        ...formatOptions,
      }).format(animatedValue)
    }
    return animatedValue.toFixed(decimals)
  }, [animatedValue, decimals, formatOptions])

  return (
    <span
      data-testid="animated-number"
      data-value={value}
      data-animating={isAnimating}
      className={cn(
        'tabular-nums',
        // Add subtle transition for color changes
        'transition-colors duration-200',
        className
      )}
    >
      {prefix}
      {formattedValue}
      {suffix}
    </span>
  )
}

export default AnimatedNumber

import React from 'react'
import { Link } from 'react-router-dom'
import { cn } from '../../utils/cn'
import Card from '../common/Card'
import { Skeleton } from '../common/Skeleton'
import { AnimatedNumber } from '../common/AnimatedNumber'

/**
 * Represents a change/trend indicator for a statistic
 */
interface StatChange {
  /** The numeric change value (e.g., 12 for "+12%") */
  value: number
  /** Direction of the change */
  type: 'increase' | 'decrease' | 'neutral'
  /** Time period description (e.g., "vs last week") */
  period: string
}

/**
 * Individual stat item configuration
 */
export interface StatItem {
  /** Display label for the stat */
  label: string
  /** The main value to display (number or string like "89%") */
  value: number | string
  /** Optional trend/change indicator */
  change?: StatChange
  /** Optional icon to display in top corner */
  icon?: React.ReactNode
  /** Color theme for the stat card */
  color?: 'default' | 'success' | 'warning' | 'danger' | 'info'
  /** Optional link - makes the card clickable */
  href?: string
}

/**
 * Props for the QuickStatsGrid component
 */
export interface QuickStatsGridProps {
  /** Array of stat items to display */
  stats: StatItem[]
  /** Number of columns in the grid (default: 4) */
  columns?: 2 | 3 | 4
  /** Show loading skeleton state */
  loading?: boolean
  /** Additional CSS classes */
  className?: string
}

/**
 * Check if a value is a string representation of a percentage (e.g., "89%")
 */
const isPercentageString = (value: string): boolean => {
  return /^[\d.]+%$/.test(value)
}

/**
 * Extract numeric value from a string (e.g., "89%" -> 89)
 */
const extractNumericValue = (value: string): number | null => {
  const match = value.match(/^([\d.]+)/)
  return match ? parseFloat(match[1]) : null
}

/**
 * Format a number with comma separators (e.g., 1234 -> "1,234")
 */
const formatNumber = (value: number | string): string => {
  if (typeof value === 'string') {
    return value
  }
  return value.toLocaleString('en-US')
}

/**
 * Get the color classes for different stat colors
 */
const getColorClasses = (color: StatItem['color'] = 'default') => {
  const colorMap = {
    default: {
      iconBg: 'bg-tactical-100 dark:bg-tactical-700/50',
      iconText: 'text-tactical-600 dark:text-tactical-300',
    },
    success: {
      iconBg: 'bg-emerald-100 dark:bg-emerald-900/30',
      iconText: 'text-emerald-600 dark:text-emerald-400',
    },
    warning: {
      iconBg: 'bg-amber-100 dark:bg-amber-900/30',
      iconText: 'text-amber-600 dark:text-amber-400',
    },
    danger: {
      iconBg: 'bg-red-100 dark:bg-red-900/30',
      iconText: 'text-red-600 dark:text-red-400',
    },
    info: {
      iconBg: 'bg-blue-100 dark:bg-blue-900/30',
      iconText: 'text-blue-600 dark:text-blue-400',
    },
  }
  return colorMap[color]
}

/**
 * Get the change indicator color classes
 */
const getChangeClasses = (type: StatChange['type']) => {
  switch (type) {
    case 'increase':
      return 'text-emerald-600 dark:text-emerald-400'
    case 'decrease':
      return 'text-red-600 dark:text-red-400'
    case 'neutral':
    default:
      return 'text-tactical-500 dark:text-tactical-400'
  }
}

/**
 * Get the arrow indicator based on change type
 */
const getChangeArrow = (type: StatChange['type']) => {
  switch (type) {
    case 'increase':
      return (
        <svg
          className="w-3.5 h-3.5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 10l7-7m0 0l7 7m-7-7v18"
          />
        </svg>
      )
    case 'decrease':
      return (
        <svg
          className="w-3.5 h-3.5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 14l-7 7m0 0l-7-7m7 7V3"
          />
        </svg>
      )
    case 'neutral':
    default:
      return (
        <svg
          className="w-3.5 h-3.5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 12h14"
          />
        </svg>
      )
  }
}

/**
 * Loading skeleton for a single stat card with shimmer animation
 */
const StatCardSkeleton: React.FC = () => (
  <Card padding="md" className="relative" data-testid="stat-card-skeleton">
    <div className="flex items-start justify-between">
      <div className="flex-1 min-w-0">
        <Skeleton variant="text" className="h-4 w-20 mb-2" animation="shimmer" />
        <Skeleton variant="text" className="h-9 w-24 mb-2" animation="shimmer" />
        <div className="flex items-center gap-1">
          <Skeleton variant="circular" className="w-3.5 h-3.5" animation="shimmer" />
          <Skeleton variant="text" className="h-4 w-12" animation="shimmer" />
          <Skeleton variant="text" className="h-4 w-16 ml-1" animation="shimmer" />
        </div>
      </div>
      <Skeleton variant="circular" className="w-10 h-10 flex-shrink-0" animation="shimmer" />
    </div>
  </Card>
)

/**
 * Individual stat card component
 */
interface StatCardProps {
  stat: StatItem
}

const StatCard: React.FC<StatCardProps> = ({ stat }) => {
  const { label, value, change, icon, color = 'default', href } = stat
  const colorClasses = getColorClasses(color)
  const testId = `stat-${label.toLowerCase().replace(/\s/g, '-')}`

  const cardContent = (
    <div className="flex items-start justify-between">
      <div className="flex-1 min-w-0">
        {/* Label */}
        <p className="text-sm font-medium text-tactical-600 dark:text-tactical-400 mb-1 truncate">
          {label}
        </p>

        {/* Value - Animated for numeric values */}
        <p
          data-testid="stat-value"
          className="text-3xl font-bold text-tactical-900 dark:text-tactical-100 tracking-tight"
        >
          {typeof value === 'number' ? (
            <AnimatedNumber
              value={value}
              duration={1200}
              easing="easeOut"
              formatOptions={{ useGrouping: true }}
            />
          ) : typeof value === 'string' && isPercentageString(value) ? (
            <AnimatedNumber
              value={extractNumericValue(value) || 0}
              duration={1200}
              decimals={value.includes('.') ? 1 : 0}
              suffix="%"
              easing="easeOut"
            />
          ) : (
            formatNumber(value)
          )}
        </p>

        {/* Change indicator */}
        {change && (
          <div
            data-testid="stat-change"
            className={cn(
              'flex items-center gap-1 mt-1 text-sm font-medium',
              getChangeClasses(change.type)
            )}
          >
            {getChangeArrow(change.type)}
            <span>
              {change.type === 'increase' && '+'}
              {change.type === 'decrease' && '-'}
              {Math.abs(change.value)}
            </span>
            <span className="text-tactical-500 dark:text-tactical-400 font-normal ml-1">
              {change.period}
            </span>
          </div>
        )}
      </div>

      {/* Icon */}
      {icon && (
        <div
          className={cn(
            'flex-shrink-0 p-2.5 rounded-full',
            colorClasses.iconBg,
            colorClasses.iconText
          )}
        >
          {icon}
        </div>
      )}
    </div>
  )

  // Wrap in Link if href is provided
  if (href) {
    return (
      <Link to={href} className="block" data-testid={testId}>
        <Card
          padding="md"
          hoverable
          className={cn(
            'h-full transition-all duration-200',
            'hover:translate-y-[-2px]'
          )}
        >
          {cardContent}
        </Card>
      </Link>
    )
  }

  return (
    <Card padding="md" className="h-full" data-testid={testId}>
      {cardContent}
    </Card>
  )
}

/**
 * QuickStatsGrid - Displays key metrics in a responsive grid layout
 *
 * Features:
 * - Responsive grid (4 cols on lg, 2 on sm)
 * - Large value display with number formatting
 * - Optional icon in top corner with color themes
 * - Change indicators with arrows and colors
 * - Loading skeleton state
 * - Clickable cards when href is provided
 * - Hover effects for interactive cards
 *
 * @example
 * ```tsx
 * <QuickStatsGrid
 *   stats={[
 *     { label: 'Tigers', value: 156, change: { value: 12, type: 'increase', period: 'vs last week' } },
 *     { label: 'Facilities', value: 47, icon: <BuildingIcon /> },
 *     { label: 'ID Rate', value: '89%', color: 'success' },
 *     { label: 'Pending', value: 12, href: '/verifications', color: 'warning' },
 *   ]}
 *   columns={4}
 * />
 * ```
 */
export const QuickStatsGrid: React.FC<QuickStatsGridProps> = ({
  stats,
  columns = 4,
  loading = false,
  className,
}) => {
  const gridColsClass = {
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
  }

  if (loading) {
    return (
      <div
        data-testid="quick-stats-grid-skeleton"
        className={cn('grid gap-4', gridColsClass[columns], className)}
      >
        {Array.from({ length: columns }).map((_, index) => (
          <StatCardSkeleton key={index} />
        ))}
      </div>
    )
  }

  return (
    <div
      data-testid="quick-stats-grid"
      className={cn('grid gap-4', gridColsClass[columns], className)}
    >
      {stats.map((stat) => (
        <StatCard key={stat.label} stat={stat} />
      ))}
    </div>
  )
}

export default QuickStatsGrid

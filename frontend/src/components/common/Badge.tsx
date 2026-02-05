import { ReactNode } from 'react'
import { cn } from '../../utils/cn'

export type BadgeVariant =
  | 'default'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'primary'
  | 'outline'
  | 'error'
  | 'purple'
  | 'cyan'
  | 'emerald'
  | 'amber'
  | 'orange'
  | 'tiger'

export type BadgeColor = 'green' | 'blue' | 'yellow' | 'red' | 'gray' | 'purple'

interface BadgeProps {
  children: ReactNode
  variant?: BadgeVariant
  /** Alias for variant - supports color names */
  color?: BadgeColor
  size?: 'xs' | 'sm' | 'md' | 'lg'
  className?: string
  dot?: boolean
  removable?: boolean
  onRemove?: () => void
}

const Badge = ({
  children,
  variant,
  color,
  size = 'md',
  className,
  dot = false,
  removable = false,
  onRemove,
}: BadgeProps) => {
  // Map color prop to variant if provided
  const colorToVariant: Record<BadgeColor, BadgeVariant> = {
    green: 'success',
    blue: 'info',
    yellow: 'warning',
    red: 'danger',
    gray: 'default',
    purple: 'purple',
  }

  const variants: Record<BadgeVariant, string> = {
    default: cn(
      'bg-tactical-100 text-tactical-700',
      'dark:bg-tactical-700 dark:text-tactical-300'
    ),
    success: cn(
      'bg-emerald-100 text-emerald-800',
      'dark:bg-emerald-900/50 dark:text-emerald-300'
    ),
    warning: cn(
      'bg-amber-100 text-amber-800',
      'dark:bg-amber-900/50 dark:text-amber-300'
    ),
    danger: cn(
      'bg-red-100 text-red-800',
      'dark:bg-red-900/50 dark:text-red-300'
    ),
    error: cn(
      'bg-red-100 text-red-800',
      'dark:bg-red-900/50 dark:text-red-300'
    ),
    info: cn(
      'bg-blue-100 text-blue-800',
      'dark:bg-blue-900/50 dark:text-blue-300'
    ),
    primary: cn(
      'bg-tiger-orange text-white',
      'dark:bg-tiger-orange-dark'
    ),
    outline: cn(
      'bg-transparent text-tactical-700',
      'border border-tactical-300',
      'dark:text-tactical-300 dark:border-tactical-600'
    ),
    purple: cn(
      'bg-purple-100 text-purple-800',
      'dark:bg-purple-900/50 dark:text-purple-300'
    ),
    cyan: cn(
      'bg-cyan-100 text-cyan-800',
      'dark:bg-cyan-900/50 dark:text-cyan-300'
    ),
    emerald: cn(
      'bg-emerald-100 text-emerald-800',
      'dark:bg-emerald-900/50 dark:text-emerald-300'
    ),
    amber: cn(
      'bg-amber-100 text-amber-800',
      'dark:bg-amber-900/50 dark:text-amber-300'
    ),
    orange: cn(
      'bg-orange-100 text-orange-800',
      'dark:bg-orange-900/50 dark:text-orange-300'
    ),
    tiger: cn(
      'bg-tiger-orange/20 text-tiger-orange',
      'dark:bg-tiger-orange/30 dark:text-tiger-orange-light'
    ),
  }

  const dotColors: Record<BadgeVariant, string> = {
    default: 'bg-tactical-500',
    success: 'bg-emerald-500',
    warning: 'bg-amber-500',
    danger: 'bg-red-500',
    error: 'bg-red-500',
    info: 'bg-blue-500',
    primary: 'bg-white',
    outline: 'bg-tactical-500',
    purple: 'bg-purple-500',
    cyan: 'bg-cyan-500',
    emerald: 'bg-emerald-500',
    amber: 'bg-amber-500',
    orange: 'bg-orange-500',
    tiger: 'bg-tiger-orange',
  }

  // Determine which variant to use: explicit variant > mapped color > default
  const effectiveVariant = variant || (color ? colorToVariant[color] : 'default')

  const sizes = {
    xs: 'px-1.5 py-0.5 text-2xs',
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-sm',
  }

  return (
    <span
      data-testid="badge"
      className={cn(
        'inline-flex items-center font-medium rounded-full',
        'transition-colors',
        variants[effectiveVariant],
        sizes[size],
        className
      )}
    >
      {dot && (
        <span
          className={cn(
            'w-1.5 h-1.5 rounded-full mr-1.5',
            dotColors[effectiveVariant]
          )}
        />
      )}
      {children}
      {removable && onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
          className={cn(
            'ml-1.5 -mr-1 p-0.5 rounded-full',
            'hover:bg-black/10 dark:hover:bg-white/10',
            'transition-colors'
          )}
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </span>
  )
}

// Confidence Badge - specialized badge for confidence levels
interface ConfidenceBadgeProps {
  score: number
  size?: 'xs' | 'sm' | 'md' | 'lg'
  showLabel?: boolean
  className?: string
}

export const ConfidenceBadge = ({
  score,
  size = 'md',
  showLabel = true,
  className,
}: ConfidenceBadgeProps) => {
  // Normalize score
  const normalizedScore = score > 1 ? score / 100 : score

  // Determine level
  let level: BadgeVariant = 'default'
  let label = 'Unknown'

  if (normalizedScore >= 0.85) {
    level = 'success'
    label = 'High'
  } else if (normalizedScore >= 0.65) {
    level = 'warning'
    label = 'Medium'
  } else if (normalizedScore >= 0.4) {
    level = 'orange'
    label = 'Low'
  } else {
    level = 'danger'
    label = 'Critical'
  }

  return (
    <Badge variant={level} size={size} className={className}>
      {showLabel && `${label} `}
      {(normalizedScore * 100).toFixed(0)}%
    </Badge>
  )
}

// Status Badge - specialized badge for status indicators
interface StatusBadgeProps {
  status: 'active' | 'pending' | 'completed' | 'failed' | 'cancelled' | 'processing'
  size?: 'xs' | 'sm' | 'md' | 'lg'
  showDot?: boolean
  className?: string
}

export const StatusBadge = ({
  status,
  size = 'md',
  showDot = true,
  className,
}: StatusBadgeProps) => {
  const statusConfig: Record<string, { variant: BadgeVariant; label: string }> = {
    active: { variant: 'success', label: 'Active' },
    pending: { variant: 'warning', label: 'Pending' },
    completed: { variant: 'success', label: 'Completed' },
    failed: { variant: 'danger', label: 'Failed' },
    cancelled: { variant: 'default', label: 'Cancelled' },
    processing: { variant: 'info', label: 'Processing' },
  }

  const config = statusConfig[status] || statusConfig.pending

  return (
    <Badge variant={config.variant} size={size} dot={showDot} className={className}>
      {config.label}
    </Badge>
  )
}

export default Badge

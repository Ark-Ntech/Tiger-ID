import { cn } from '../../utils/cn'
import { AnimatedNumber } from '../common/AnimatedNumber'
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/solid'

export interface ModelAgreementBadgeProps {
  /** Number of models that agree on the match */
  agreementCount: number
  /** Total number of models used in the ensemble */
  totalModels: number
  /** Show detailed count (e.g., "4/6") vs just visual indicator */
  showDetails?: boolean
  /** Size variant affecting layout and typography */
  size?: 'sm' | 'md' | 'lg'
  /** Click handler to show model details */
  onClick?: () => void
  /** Additional CSS classes */
  className?: string
  /** Optional list of model names for tooltip */
  modelNames?: string[]
  /** Whether to animate the count (default: false) */
  animate?: boolean
}

type AgreementLevel = 'high' | 'good' | 'warning' | 'low'

/**
 * Determines the agreement level based on the ratio of agreeing models
 */
const getAgreementLevel = (agreementCount: number, totalModels: number): AgreementLevel => {
  if (totalModels === 0) return 'low'

  const ratio = agreementCount / totalModels

  // 5/6 or 6/6 (83%+) = high confidence
  if (ratio >= 0.83) return 'high'
  // 4/6 (67%) = good
  if (ratio >= 0.67) return 'good'
  // 3/6 (50%) = warning - split decision
  if (ratio >= 0.5) return 'warning'
  // 2/6 or less = low confidence
  return 'low'
}

/**
 * Color configuration for each agreement level
 */
const levelColors: Record<AgreementLevel, {
  bg: string
  text: string
  border: string
  dot: string
  dotFilled: string
  dotEmpty: string
  progress: string
  progressBg: string
  icon: string
}> = {
  high: {
    bg: 'bg-emerald-50 dark:bg-emerald-900/20',
    text: 'text-emerald-700 dark:text-emerald-300',
    border: 'border-emerald-200 dark:border-emerald-800',
    dot: 'text-emerald-500',
    dotFilled: 'bg-emerald-500',
    dotEmpty: 'bg-emerald-200 dark:bg-emerald-800',
    progress: 'bg-emerald-500',
    progressBg: 'bg-emerald-100 dark:bg-emerald-900/50',
    icon: 'text-emerald-500',
  },
  good: {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    text: 'text-blue-700 dark:text-blue-300',
    border: 'border-blue-200 dark:border-blue-800',
    dot: 'text-blue-500',
    dotFilled: 'bg-blue-500',
    dotEmpty: 'bg-blue-200 dark:bg-blue-800',
    progress: 'bg-blue-500',
    progressBg: 'bg-blue-100 dark:bg-blue-900/50',
    icon: 'text-blue-500',
  },
  warning: {
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    text: 'text-amber-700 dark:text-amber-300',
    border: 'border-amber-200 dark:border-amber-800',
    dot: 'text-amber-500',
    dotFilled: 'bg-amber-500',
    dotEmpty: 'bg-amber-200 dark:bg-amber-800',
    progress: 'bg-amber-500',
    progressBg: 'bg-amber-100 dark:bg-amber-900/50',
    icon: 'text-amber-500',
  },
  low: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    text: 'text-red-700 dark:text-red-300',
    border: 'border-red-200 dark:border-red-800',
    dot: 'text-red-500',
    dotFilled: 'bg-red-500',
    dotEmpty: 'bg-red-200 dark:bg-red-800',
    progress: 'bg-red-500',
    progressBg: 'bg-red-100 dark:bg-red-900/50',
    icon: 'text-red-500',
  },
}

/**
 * Get the appropriate icon for the agreement level
 */
const getLevelIcon = (level: AgreementLevel, className: string) => {
  switch (level) {
    case 'high':
      return <CheckCircleIcon className={className} />
    case 'good':
      return <InformationCircleIcon className={className} />
    case 'warning':
      return <ExclamationTriangleIcon className={className} />
    case 'low':
      return <XCircleIcon className={className} />
  }
}

/**
 * Small size variant - displays colored dots
 */
const SmallVariant = ({
  agreementCount,
  totalModels,
  colors,
}: {
  agreementCount: number
  totalModels: number
  colors: typeof levelColors[AgreementLevel]
}) => {
  return (
    <div
      data-testid="agreement-indicator"
      className="flex items-center gap-0.5"
      aria-label={`${agreementCount} of ${totalModels} models agree`}
    >
      {Array.from({ length: totalModels }).map((_, index) => (
        <span
          key={index}
          className={cn(
            'w-2 h-2 rounded-full transition-colors',
            index < agreementCount ? colors.dotFilled : colors.dotEmpty
          )}
        />
      ))}
    </div>
  )
}

/**
 * Medium size variant - displays fraction with check icon
 */
const MediumVariant = ({
  agreementCount,
  totalModels,
  level,
  colors,
  showDetails,
  animate = false,
}: {
  agreementCount: number
  totalModels: number
  level: AgreementLevel
  colors: typeof levelColors[AgreementLevel]
  showDetails: boolean
  animate?: boolean
}) => {
  return (
    <div
      data-testid="agreement-indicator"
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-1 rounded-md',
        colors.bg,
        colors.text
      )}
    >
      {showDetails && (
        <span data-testid="agreement-count" className="font-medium text-sm">
          {animate ? (
            <AnimatedNumber value={agreementCount} duration={600} easing="easeOut" />
          ) : (
            agreementCount
          )}
          /{totalModels}
        </span>
      )}
      {getLevelIcon(level, cn('w-4 h-4', colors.icon))}
    </div>
  )
}

/**
 * Large size variant - displays text with progress bar
 */
const LargeVariant = ({
  agreementCount,
  totalModels,
  level,
  colors,
  animate = false,
}: {
  agreementCount: number
  totalModels: number
  level: AgreementLevel
  colors: typeof levelColors[AgreementLevel]
  animate?: boolean
}) => {
  const percentage = totalModels > 0 ? (agreementCount / totalModels) * 100 : 0

  return (
    <div
      data-testid="agreement-indicator"
      className={cn(
        'flex flex-col gap-2 px-3 py-2 rounded-lg border',
        colors.bg,
        colors.border
      )}
    >
      <div className="flex items-center justify-between">
        <span className={cn('text-sm font-medium', colors.text)}>
          <span data-testid="agreement-count">
            {animate ? (
              <AnimatedNumber value={agreementCount} duration={600} easing="easeOut" />
            ) : (
              agreementCount
            )}
          </span> of {totalModels} models agree
        </span>
        {getLevelIcon(level, cn('w-5 h-5', colors.icon))}
      </div>
      <div className={cn('h-2 rounded-full overflow-hidden', colors.progressBg)}>
        <div
          className={cn('h-full rounded-full transition-all duration-300', colors.progress)}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

/**
 * ModelAgreementBadge displays a visual indicator of how many ML models
 * agree on a match during tiger re-identification verification.
 *
 * The component supports three size variants:
 * - Small: Colored dots showing agreement ratio
 * - Medium: Fraction with status icon
 * - Large: Text description with progress bar
 *
 * Color coding indicates confidence level:
 * - Emerald (5-6/6): High confidence
 * - Blue (4/6): Good confidence
 * - Amber (3/6): Warning - split decision
 * - Red (1-2/6): Low confidence
 */
export const ModelAgreementBadge = ({
  agreementCount,
  totalModels,
  showDetails = true,
  size = 'md',
  onClick,
  className,
  modelNames,
  animate = false,
}: ModelAgreementBadgeProps) => {
  const level = getAgreementLevel(agreementCount, totalModels)
  const colors = levelColors[level]

  // Build tooltip content if model names are provided
  const tooltipContent = modelNames?.length
    ? `Models agreeing: ${modelNames.slice(0, agreementCount).join(', ')}`
    : `${agreementCount} of ${totalModels} models agree`

  const renderContent = () => {
    switch (size) {
      case 'sm':
        return (
          <SmallVariant
            agreementCount={agreementCount}
            totalModels={totalModels}
            colors={colors}
          />
        )
      case 'lg':
        return (
          <LargeVariant
            agreementCount={agreementCount}
            totalModels={totalModels}
            level={level}
            colors={colors}
            animate={animate}
          />
        )
      case 'md':
      default:
        return (
          <MediumVariant
            agreementCount={agreementCount}
            totalModels={totalModels}
            level={level}
            colors={colors}
            showDetails={showDetails}
            animate={animate}
          />
        )
    }
  }

  const baseClasses = cn(
    'inline-block',
    onClick && 'cursor-pointer hover:opacity-80 transition-opacity',
    className
  )

  if (onClick) {
    return (
      <button
        type="button"
        data-testid="model-agreement-badge"
        className={baseClasses}
        onClick={onClick}
        title={tooltipContent}
        aria-label={tooltipContent}
      >
        {renderContent()}
      </button>
    )
  }

  return (
    <div
      data-testid="model-agreement-badge"
      className={baseClasses}
      title={tooltipContent}
      role="status"
      aria-label={tooltipContent}
    >
      {renderContent()}
    </div>
  )
}

export default ModelAgreementBadge

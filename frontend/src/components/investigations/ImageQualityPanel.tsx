import { cn } from '../../utils/cn'
import {
  getConfidenceLevel,
  getConfidenceColors,
  normalizeScore,
} from '../../utils/confidence'
import {
  PhotoIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  CameraIcon,
  EyeIcon,
  FingerPrintIcon,
} from '@heroicons/react/24/outline'
import type { ImageQuality } from '../../types/investigation2'

interface ImageQualityPanelProps {
  quality: ImageQuality
  className?: string
  variant?: 'full' | 'compact' | 'minimal'
  showRecommendations?: boolean
}

// Quality metric definitions
const QUALITY_METRICS = {
  resolution: {
    label: 'Resolution',
    icon: CameraIcon,
    description: 'Image resolution and pixel density',
    goodThreshold: 0.8,
    recommendations: {
      low: 'Use higher resolution source images (at least 1920x1080)',
      medium: 'Resolution is acceptable but higher resolution may improve accuracy',
    },
  },
  sharpness: {
    label: 'Sharpness',
    icon: EyeIcon,
    description: 'Image clarity and focus quality',
    goodThreshold: 0.7,
    recommendations: {
      low: 'Image appears blurry - use a sharper, well-focused image',
      medium: 'Some blur detected - consider a sharper image for better results',
    },
  },
  stripe_visibility: {
    label: 'Stripe Visibility',
    icon: FingerPrintIcon,
    description: 'Tiger stripe pattern clarity',
    goodThreshold: 0.6,
    recommendations: {
      low: 'Stripe patterns are not clearly visible - use an image with better stripe visibility',
      medium: 'Stripes partially visible - a clearer side view may improve matching',
    },
  },
} as const

export const ImageQualityPanel = ({
  quality,
  className,
  variant = 'full',
  showRecommendations = true,
}: ImageQualityPanelProps) => {
  const overallScore = normalizeScore(quality.overall_score)
  const confidenceLevel = getConfidenceLevel(overallScore)
  const colors = getConfidenceColors(confidenceLevel)

  // Extract individual metrics from quality object
  const metrics = {
    resolution: quality.resolution_score || 0,
    sharpness: quality.blur_score || 0,
    stripe_visibility: quality.stripe_visibility || 0,
  }

  // Generate recommendations based on low scores
  const recommendations: string[] = []
  if (showRecommendations) {
    Object.entries(metrics).forEach(([key, value]) => {
      const metric = QUALITY_METRICS[key as keyof typeof QUALITY_METRICS]
      const normalizedValue = normalizeScore(value)
      if (normalizedValue < metric.goodThreshold * 0.5) {
        recommendations.push(metric.recommendations.low)
      } else if (normalizedValue < metric.goodThreshold) {
        recommendations.push(metric.recommendations.medium)
      }
    })
  }

  // Circular progress SVG parameters
  const size = variant === 'full' ? 100 : variant === 'compact' ? 72 : 48
  const strokeWidth = variant === 'full' ? 8 : variant === 'compact' ? 6 : 4
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - overallScore * circumference

  // Minimal variant
  if (variant === 'minimal') {
    return (
      <div className={cn(
        'flex items-center gap-3 px-3 py-2 rounded-lg',
        colors.bg,
        colors.border,
        'border',
        className
      )}>
        <PhotoIcon className={cn('w-5 h-5', colors.text)} />
        <div className="flex-1 min-w-0">
          <div className="text-xs font-medium text-tactical-600 dark:text-tactical-400">
            Image Quality
          </div>
          <div className={cn('text-sm font-bold', colors.text)}>
            {Math.round(overallScore * 100)}%
          </div>
        </div>
        {quality.issues && quality.issues.length > 0 && (
          <ExclamationTriangleIcon className="w-5 h-5 text-amber-500" />
        )}
      </div>
    )
  }

  return (
    <div className={cn(
      'rounded-xl border',
      'bg-white dark:bg-tactical-800',
      'border-tactical-200 dark:border-tactical-700',
      variant === 'full' ? 'p-6' : 'p-4',
      className
    )}>
      {/* Header */}
      <div className="flex items-start gap-4 sm:gap-6">
        {/* Circular score indicator */}
        <div className="flex-shrink-0 relative">
          <svg
            width={size}
            height={size}
            className="transform -rotate-90"
          >
            {/* Background circle */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              strokeWidth={strokeWidth}
              className="stroke-tactical-200 dark:stroke-tactical-700"
            />
            {/* Progress circle */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              className={cn(
                'transition-all duration-700 ease-out',
                confidenceLevel === 'high' && 'stroke-emerald-500',
                confidenceLevel === 'medium' && 'stroke-amber-500',
                confidenceLevel === 'low' && 'stroke-orange-500',
                confidenceLevel === 'critical' && 'stroke-red-500'
              )}
            />
          </svg>
          {/* Center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={cn(
              'font-bold',
              variant === 'full' ? 'text-2xl' : 'text-lg',
              colors.text
            )}>
              {Math.round(overallScore * 100)}
            </span>
            {variant === 'full' && (
              <span className="text-xs text-tactical-500 dark:text-tactical-400">%</span>
            )}
          </div>
        </div>

        {/* Metrics breakdown */}
        <div className="flex-1 min-w-0 space-y-3">
          {variant === 'full' && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-tactical-900 dark:text-tactical-100">
                Image Quality Assessment
              </h4>
              <p className="text-xs text-tactical-600 dark:text-tactical-400 mt-0.5">
                Based on resolution, sharpness, and stripe visibility
              </p>
            </div>
          )}

          {Object.entries(metrics).map(([key, value]) => {
            const metric = QUALITY_METRICS[key as keyof typeof QUALITY_METRICS]
            const normalizedValue = normalizeScore(value)
            const metricLevel = getConfidenceLevel(normalizedValue)
            const metricColors = getConfidenceColors(metricLevel)
            const Icon = metric.icon

            return (
              <div key={key} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4 text-tactical-500 dark:text-tactical-400" />
                    <span className="font-medium text-tactical-700 dark:text-tactical-300">
                      {metric.label}
                    </span>
                  </div>
                  <span className={cn('font-bold tabular-nums', metricColors.text)}>
                    {Math.round(normalizedValue * 100)}%
                  </span>
                </div>
                <div className="progress-bar">
                  <div
                    className={cn(
                      'progress-bar-fill',
                      metricLevel === 'high' && 'bg-emerald-500',
                      metricLevel === 'medium' && 'bg-amber-500',
                      metricLevel === 'low' && 'bg-orange-500',
                      metricLevel === 'critical' && 'bg-red-500'
                    )}
                    style={{ width: `${normalizedValue * 100}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Issues list */}
      {quality.issues && quality.issues.length > 0 && (
        <div className="mt-4 pt-4 border-t border-tactical-200 dark:border-tactical-700">
          <div className="flex items-center gap-2 text-sm font-medium text-amber-700 dark:text-amber-400 mb-2">
            <ExclamationTriangleIcon className="w-4 h-4" />
            <span>Issues Detected ({quality.issues.length})</span>
          </div>
          <ul className="space-y-1">
            {quality.issues.map((issue, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-sm text-tactical-600 dark:text-tactical-400"
              >
                <span className="text-amber-500 mt-1">•</span>
                <span>{issue}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {showRecommendations && recommendations.length > 0 && variant === 'full' && (
        <div className={cn(
          'mt-4 p-4 rounded-lg',
          'bg-blue-50 dark:bg-blue-900/20',
          'border border-blue-200 dark:border-blue-800'
        )}>
          <div className="flex items-center gap-2 text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">
            <CheckCircleIcon className="w-4 h-4" />
            <span>Recommendations</span>
          </div>
          <ul className="space-y-1">
            {recommendations.map((rec, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-sm text-blue-600 dark:text-blue-400"
              >
                <span className="text-blue-400 mt-1">→</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Good quality indicator */}
      {overallScore >= 0.8 && (
        <div className={cn(
          'mt-4 flex items-center gap-2 px-3 py-2 rounded-lg',
          'bg-emerald-50 dark:bg-emerald-900/20',
          'border border-emerald-200 dark:border-emerald-800'
        )}>
          <CheckCircleIcon className="w-5 h-5 text-emerald-500" />
          <span className="text-sm font-medium text-emerald-700 dark:text-emerald-300">
            Excellent image quality - optimal for accurate identification
          </span>
        </div>
      )}
    </div>
  )
}

// Inline quality indicator for headers
interface ImageQualityInlineProps {
  score: number
  className?: string
}

export const ImageQualityInline = ({ score, className }: ImageQualityInlineProps) => {
  const normalizedScore = normalizeScore(score)
  const level = getConfidenceLevel(normalizedScore)
  const colors = getConfidenceColors(level)

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className="flex items-center gap-1.5">
        <PhotoIcon className={cn('w-4 h-4', colors.text)} />
        <span className="text-sm text-tactical-600 dark:text-tactical-400">Quality:</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-16 h-1.5 bg-tactical-200 dark:bg-tactical-700 rounded-full overflow-hidden">
          <div
            className={cn(
              'h-full rounded-full transition-all',
              level === 'high' && 'bg-emerald-500',
              level === 'medium' && 'bg-amber-500',
              level === 'low' && 'bg-orange-500',
              level === 'critical' && 'bg-red-500'
            )}
            style={{ width: `${normalizedScore * 100}%` }}
          />
        </div>
        <span className={cn('text-sm font-bold tabular-nums', colors.text)}>
          {Math.round(normalizedScore * 100)}%
        </span>
      </div>
    </div>
  )
}

export default ImageQualityPanel

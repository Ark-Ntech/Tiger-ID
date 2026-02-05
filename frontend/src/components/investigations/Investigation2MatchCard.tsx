import React, { useState } from 'react'
import { cn } from '../../utils/cn'
import { Skeleton } from '../common/Skeleton'
import { AnimatedNumber } from '../common/AnimatedNumber'
import {
  getConfidenceLevel,
  getConfidenceColors,
  normalizeScore,
  toPercentage,
  getVerificationColors,
} from '../../utils/confidence'
import { EnsembleInline } from './EnsembleVisualization'
import {
  ChevronDownIcon,
  ChevronUpIcon,
  MapPinIcon,
  BuildingOfficeIcon,
} from '@heroicons/react/24/outline'
import {
  CheckBadgeIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/solid'
import type {
  VerificationStatus,
  Investigation2MatchCardProps,
} from '../../types/investigation2'

interface ProgressBarProps {
  label: string
  value: number
  color?: string
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  label,
  value,
  color,
}) => {
  const normalizedValue = normalizeScore(value)
  const level = getConfidenceLevel(normalizedValue)
  const defaultColor = level === 'high' ? 'bg-emerald-500' :
                       level === 'medium' ? 'bg-amber-500' :
                       level === 'low' ? 'bg-orange-500' : 'bg-red-500'

  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-tactical-600 dark:text-tactical-400">{label}</span>
        <span className="font-semibold text-tactical-900 dark:text-tactical-100 tabular-nums">
          <AnimatedNumber
            value={normalizedValue * 100}
            duration={800}
            decimals={1}
            suffix="%"
            easing="easeOut"
          />
        </span>
      </div>
      <div className="progress-bar">
        <div
          className={cn('progress-bar-fill', color || defaultColor)}
          style={{ width: `${normalizedValue * 100}%` }}
        />
      </div>
    </div>
  )
}

const getVerificationBadge = (status: VerificationStatus | undefined) => {
  if (!status) return null

  const configs: Record<VerificationStatus, {
    colors: ReturnType<typeof getVerificationColors>
    text: string
    Icon: React.ComponentType<{ className?: string }>
  }> = {
    high_confidence: {
      colors: getVerificationColors('high_confidence'),
      text: 'High Confidence',
      Icon: ShieldCheckIcon,
    },
    verified: {
      colors: getVerificationColors('verified'),
      text: 'Verified',
      Icon: CheckBadgeIcon,
    },
    low_confidence: {
      colors: getVerificationColors('low_confidence'),
      text: 'Low Confidence',
      Icon: ExclamationTriangleIcon,
    },
    insufficient_matches: {
      colors: getVerificationColors('insufficient_matches'),
      text: 'Insufficient Data',
      Icon: ExclamationTriangleIcon,
    },
    skipped: {
      colors: getVerificationColors('skipped'),
      text: 'Not Verified',
      Icon: ExclamationTriangleIcon,
    },
    error: {
      colors: getVerificationColors('error'),
      text: 'Error',
      Icon: ExclamationTriangleIcon,
    },
  }

  const config = configs[status]
  if (!config) return null

  const { colors, text, Icon } = config

  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-full',
      colors.badge
    )}>
      <Icon className="w-3.5 h-3.5" />
      {text}
    </span>
  )
}

/**
 * Match card skeleton for loading state
 */
export const Investigation2MatchCardSkeleton = ({ className }: { className?: string }) => {
  return (
    <div
      data-testid="investigation2-match-card-skeleton"
      className={cn(
        'match-card border rounded-xl p-4 mb-4',
        'bg-white dark:bg-tactical-800',
        'border-tactical-200 dark:border-tactical-700',
        className
      )}
    >
      <div className="flex items-center gap-4">
        {/* Rank badge */}
        <Skeleton variant="circular" className="w-8 h-8 flex-shrink-0" />

        {/* Tiger image */}
        <Skeleton variant="rounded" className="w-20 h-20 flex-shrink-0" />

        {/* Tiger info */}
        <div className="flex-1 min-w-0 space-y-2">
          <div className="flex items-center flex-wrap gap-2">
            <Skeleton variant="text" className="h-6 w-32" />
            <Skeleton variant="rounded" className="h-6 w-20" />
            <Skeleton variant="rounded" className="h-6 w-16" />
          </div>

          {/* Facility info */}
          <div className="flex items-center gap-2">
            <Skeleton variant="rounded" className="w-4 h-4" />
            <Skeleton variant="text" className="h-4 w-40" />
          </div>

          {/* Ensemble indicator */}
          <div className="flex gap-1 items-center">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Skeleton key={i} variant="circular" className="w-3 h-3" />
            ))}
            <Skeleton variant="text" className="h-3 w-20 ml-1" />
          </div>
        </div>

        {/* Expand toggle */}
        <Skeleton variant="rounded" className="w-9 h-9 flex-shrink-0" />
      </div>
    </div>
  )
}

export interface Investigation2MatchCardWithLoadingProps extends Omit<Investigation2MatchCardProps, 'match'> {
  match?: Investigation2MatchCardProps['match']
  isLoading?: boolean
  className?: string
}

export const Investigation2MatchCard: React.FC<Investigation2MatchCardWithLoadingProps> = ({
  match,
  rank,
  showEnsemble = true,
  isLoading = false,
  className,
}: Investigation2MatchCardWithLoadingProps) => {
  // Show skeleton when loading
  if (isLoading || !match) {
    return <Investigation2MatchCardSkeleton className={className} />
  }
  const [expanded, setExpanded] = useState(false)

  const normalizedSimilarity = normalizeScore(match.similarity)
  const level = getConfidenceLevel(normalizedSimilarity)
  const colors = getConfidenceColors(level)

  return (
    <div className={cn(
      'match-card border rounded-xl p-4 mb-4 transition-all duration-200',
      'bg-white dark:bg-tactical-800',
      'border-tactical-200 dark:border-tactical-700',
      'hover:shadow-match hover:border-blue-300 dark:hover:border-blue-600',
      expanded && 'shadow-match-hover'
    )}>
      {/* Summary */}
      <div
        className="flex items-center gap-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        {/* Rank badge (if provided) */}
        {rank !== undefined && (
          <div className={cn(
            'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
            'text-sm font-bold',
            rank === 1
              ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-400'
              : 'bg-tactical-100 text-tactical-600 dark:bg-tactical-700 dark:text-tactical-400'
          )}>
            #{rank}
          </div>
        )}

        {/* Tiger image */}
        <img
          src={match.database_image}
          alt={match.tiger_name}
          className={cn(
            'w-20 h-20 object-cover rounded-xl flex-shrink-0',
            'border-2 border-tactical-200 dark:border-tactical-600'
          )}
          onError={(e) => {
            (e.target as HTMLImageElement).src = '/placeholder-tiger.png'
          }}
        />

        {/* Tiger info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center flex-wrap gap-2">
            <h4 className="font-semibold text-lg text-tactical-900 dark:text-tactical-100">
              {match.tiger_name || 'Unknown Tiger'}
            </h4>
            <span className={cn(
              'inline-flex items-center px-2.5 py-1 text-xs font-semibold rounded-full',
              colors.bg, colors.text
            )}>
              <AnimatedNumber
                value={normalizedSimilarity * 100}
                duration={1000}
                decimals={1}
                suffix="%"
                easing="easeOut"
              />{' '}
              match
            </span>
            <span className={cn(
              'inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-full',
              'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300'
            )}>
              {match.model}
            </span>
            {getVerificationBadge(match.verification_status)}
          </div>

          {/* Facility info */}
          <div className="flex items-center gap-2 mt-2 text-sm text-tactical-600 dark:text-tactical-400">
            <BuildingOfficeIcon className="w-4 h-4" />
            <span>{match.facility.name}</span>
          </div>

          {/* Ensemble indicator */}
          {showEnsemble && match.models_matched !== undefined && (
            <div className="mt-2">
              <EnsembleInline
                agreementCount={match.models_matched}
                totalModels={match.total_models || 6}
              />
            </div>
          )}
        </div>

        {/* Expand toggle */}
        <button
          className={cn(
            'p-2 rounded-lg transition-colors',
            'text-tactical-400 hover:text-tactical-600 hover:bg-tactical-100',
            'dark:hover:text-tactical-300 dark:hover:bg-tactical-700'
          )}
          onClick={(e) => {
            e.stopPropagation()
            setExpanded(!expanded)
          }}
        >
          {expanded ? (
            <ChevronUpIcon className="w-5 h-5" />
          ) : (
            <ChevronDownIcon className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="mt-4 pt-4 border-t border-tactical-200 dark:border-tactical-700 animate-fade-in-up">
          {/* Image Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {match.uploaded_image_crop && (
              <div>
                <h5 className="font-medium text-sm mb-2 text-tactical-700 dark:text-tactical-300">
                  Uploaded Image
                </h5>
                <img
                  src={match.uploaded_image_crop}
                  alt="Uploaded"
                  className="w-full rounded-xl border border-tactical-200 dark:border-tactical-700"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/placeholder-tiger.png'
                  }}
                />
              </div>
            )}
            <div>
              <h5 className="font-medium text-sm mb-2 text-tactical-700 dark:text-tactical-300">
                Database Match
              </h5>
              <img
                src={match.database_image}
                alt="Database"
                className="w-full rounded-xl border border-tactical-200 dark:border-tactical-700"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = '/placeholder-tiger.png'
                }}
              />
            </div>
          </div>

          {/* Verification Details */}
          {match.verification_status && match.verification_status !== 'skipped' && (
            <div className={cn(
              'mb-4 p-4 rounded-xl',
              'bg-gradient-to-r from-blue-50 to-purple-50',
              'dark:from-blue-900/20 dark:to-purple-900/20',
              'border border-blue-200 dark:border-blue-800'
            )}>
              <div className="flex items-center justify-between mb-4">
                <h5 className="font-medium text-sm text-tactical-700 dark:text-tactical-300 flex items-center gap-2">
                  <ShieldCheckIcon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  Geometric Verification (MatchAnything)
                </h5>
                {getVerificationBadge(match.verification_status)}
              </div>

              {match.combined_score !== undefined && (
                <ProgressBar
                  label="Combined Score (ReID + Verification)"
                  value={match.combined_score}
                  color="bg-purple-500"
                />
              )}

              {match.normalized_match_score !== undefined && (
                <ProgressBar
                  label="Keypoint Match Score"
                  value={match.normalized_match_score}
                  color="bg-blue-500"
                />
              )}

              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-4">
                {match.num_matches !== undefined && (
                  <div className="bg-white dark:bg-tactical-800 rounded-lg p-2.5 text-center">
                    <span className="text-xs text-tactical-500 block">Keypoint Matches</span>
                    <span className="text-lg font-bold text-tactical-900 dark:text-tactical-100">
                      {match.num_matches}
                    </span>
                  </div>
                )}
                {match.gallery_images_tested !== undefined && (
                  <div className="bg-white dark:bg-tactical-800 rounded-lg p-2.5 text-center">
                    <span className="text-xs text-tactical-500 block">Gallery Images</span>
                    <span className="text-lg font-bold text-tactical-900 dark:text-tactical-100">
                      {match.gallery_images_tested}
                    </span>
                  </div>
                )}
                {match.reid_weight_used !== undefined && (
                  <div className="bg-white dark:bg-tactical-800 rounded-lg p-2.5 text-center">
                    <span className="text-xs text-tactical-500 block">ReID Weight</span>
                    <span className="text-lg font-bold text-tactical-900 dark:text-tactical-100">
                      {toPercentage(match.reid_weight_used, 0)}
                    </span>
                  </div>
                )}
                {match.match_weight_used !== undefined && (
                  <div className="bg-white dark:bg-tactical-800 rounded-lg p-2.5 text-center">
                    <span className="text-xs text-tactical-500 block">Match Weight</span>
                    <span className="text-lg font-bold text-tactical-900 dark:text-tactical-100">
                      {toPercentage(match.match_weight_used, 0)}
                    </span>
                  </div>
                )}
              </div>

              {match.verification_error && (
                <div className="mt-3 p-2 rounded-lg bg-red-50 dark:bg-red-900/30 text-xs text-red-600 dark:text-red-400">
                  Error: {match.verification_error}
                </div>
              )}
            </div>
          )}

          {/* Ensemble Breakdown (if model scores available) */}
          {match.model_scores && match.model_scores.length > 0 && (
            <div className={cn(
              'mb-4 p-4 rounded-xl',
              'bg-tactical-50 dark:bg-tactical-900/50',
              'border border-tactical-200 dark:border-tactical-700'
            )}>
              <h5 className="font-medium text-sm mb-3 text-tactical-700 dark:text-tactical-300">
                Ensemble Model Breakdown ({match.models_matched || 0}/{match.total_models || 6} models matched)
              </h5>
              <div className="space-y-2">
                {match.model_scores.map((ms, idx) => (
                  <div key={idx} className="flex items-center gap-3">
                    <div className={cn(
                      'w-2 h-2 rounded-full',
                      ms.matched ? 'bg-emerald-500' : 'bg-tactical-300'
                    )} />
                    <span className={cn(
                      'text-sm flex-1',
                      ms.matched
                        ? 'text-tactical-900 dark:text-tactical-100'
                        : 'text-tactical-400'
                    )}>
                      {ms.model}
                    </span>
                    <span className={cn(
                      'text-sm font-mono tabular-nums',
                      ms.matched
                        ? 'text-tactical-900 dark:text-tactical-100'
                        : 'text-tactical-400'
                    )}>
                      {toPercentage(ms.score)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Confidence Breakdown */}
          {match.confidence_breakdown && (
            <div className={cn(
              'mb-4 p-4 rounded-xl',
              'bg-tactical-50 dark:bg-tactical-900/50',
              'border border-tactical-200 dark:border-tactical-700'
            )}>
              <h5 className="font-medium text-sm mb-3 text-tactical-700 dark:text-tactical-300">
                Confidence Breakdown
              </h5>
              <ProgressBar
                label="Stripe Similarity"
                value={match.confidence_breakdown.stripe_similarity}
              />
              <ProgressBar
                label="Visual Features"
                value={match.confidence_breakdown.visual_features}
              />
              <ProgressBar
                label="Historical Context"
                value={match.confidence_breakdown.historical_context}
              />
            </div>
          )}

          {/* Facility Information */}
          <div className={cn(
            'p-4 rounded-xl',
            'bg-tactical-50 dark:bg-tactical-900/50',
            'border border-tactical-200 dark:border-tactical-700'
          )}>
            <h5 className="font-medium text-sm mb-3 text-tactical-700 dark:text-tactical-300">
              Facility Information
            </h5>
            <div className="flex items-start gap-3">
              <BuildingOfficeIcon className="w-5 h-5 text-tactical-400 mt-0.5" />
              <div>
                <p className="font-semibold text-tactical-900 dark:text-tactical-100">
                  {match.facility.name}
                </p>
                <p className="text-sm text-tactical-600 dark:text-tactical-400">
                  {match.facility.location}
                </p>
                {match.facility.coordinates && (
                  <p className="flex items-center gap-1 text-xs text-tactical-400 mt-2">
                    <MapPinIcon className="w-3 h-3" />
                    {match.facility.coordinates.lat.toFixed(4)}, {match.facility.coordinates.lon.toFixed(4)}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Tiger ID */}
          <div className="mt-3 text-xs text-tactical-400 dark:text-tactical-500 font-mono">
            Tiger ID: {match.tiger_id}
          </div>
        </div>
      )}
    </div>
  )
}

export default Investigation2MatchCard

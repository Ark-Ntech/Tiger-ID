import { useState } from 'react'
import { cn } from '../../utils/cn'
import { MODEL_COLORS, getModelInfo, type ModelKey } from '../../utils/confidence'
import { ChevronDownIcon, ChevronUpIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline'

// Model result from ensemble
interface ModelResult {
  model: string
  similarity: number
  matched?: boolean
  weight?: number
  contribution?: number
}

interface EnsembleVisualizationProps {
  models: ModelResult[]
  className?: string
  compact?: boolean
  showLegend?: boolean
  animateOnLoad?: boolean
}

// All possible models in the ensemble
const ALL_MODELS: ModelKey[] = [
  'wildlife_tools',
  'cvwc2019_reid',
  'transreid',
  'megadescriptor_b',
  'tiger_reid',
  'rapid_reid',
]

export const EnsembleVisualization = ({
  models,
  className,
  compact = false,
  showLegend = true,
  animateOnLoad = true,
}: EnsembleVisualizationProps) => {
  const [expanded, setExpanded] = useState(!compact)

  // Map model results by normalized key
  const modelMap = new Map<string, ModelResult>()
  models.forEach(m => {
    const key = m.model.toLowerCase().replace(/[\s-]/g, '_')
    modelMap.set(key, m)
  })

  // Calculate agreement
  const matchedModels = models.filter(m => m.matched !== false && m.similarity > 0)
  const agreementCount = matchedModels.length
  const totalModels = ALL_MODELS.length

  // Calculate weighted score if we have contributions
  const hasContributions = models.some(m => m.contribution !== undefined)
  const weightedScore = hasContributions
    ? models.reduce((sum, m) => sum + (m.contribution || 0), 0)
    : matchedModels.reduce((sum, m) => sum + (m.similarity * (m.weight || getModelInfo(m.model).weight)), 0) /
      matchedModels.reduce((sum, m) => sum + (m.weight || getModelInfo(m.model).weight), 0)

  // Get agreement badge color
  const getAgreementColor = () => {
    const ratio = agreementCount / totalModels
    if (ratio >= 0.8) return 'text-emerald-600 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-900/30'
    if (ratio >= 0.5) return 'text-amber-600 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30'
    return 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30'
  }

  return (
    <div className={cn('', className)}>
      {/* Header */}
      <div
        className={cn(
          'flex items-center justify-between gap-4',
          compact && 'cursor-pointer'
        )}
        onClick={compact ? () => setExpanded(!expanded) : undefined}
      >
        <div className="flex items-center gap-3">
          <h4 className="text-sm font-semibold text-tactical-900 dark:text-tactical-100">
            Ensemble Analysis
          </h4>
          <span className={cn(
            'px-2 py-0.5 rounded-full text-xs font-bold',
            getAgreementColor()
          )}>
            {agreementCount}/{totalModels} models
          </span>
        </div>

        {compact && (
          <button className="p-1 hover:bg-tactical-100 dark:hover:bg-tactical-700 rounded transition-colors">
            {expanded ? (
              <ChevronUpIcon className="w-4 h-4 text-tactical-500" />
            ) : (
              <ChevronDownIcon className="w-4 h-4 text-tactical-500" />
            )}
          </button>
        )}
      </div>

      {/* Stacked bar visualization */}
      <div className={cn(
        'mt-3 space-y-2',
        animateOnLoad && 'animate-fade-in-up'
      )}>
        {/* Weight distribution bar */}
        <div className="relative h-4 rounded-full overflow-hidden bg-tactical-200 dark:bg-tactical-700">
          <div className="absolute inset-0 flex">
            {ALL_MODELS.map((modelKey, index) => {
              const modelInfo = MODEL_COLORS[modelKey]
              const result = modelMap.get(modelKey)
              const isMatched = result && result.matched !== false && result.similarity > 0
              const widthPercent = modelInfo.weight * 100

              return (
                <div
                  key={modelKey}
                  className={cn(
                    'h-full transition-all duration-500 ease-out relative group',
                    isMatched ? modelInfo.bg : 'bg-tactical-300 dark:bg-tactical-600',
                    !isMatched && 'opacity-40'
                  )}
                  style={{
                    width: `${widthPercent}%`,
                    animationDelay: animateOnLoad ? `${index * 100}ms` : undefined,
                  }}
                  title={`${modelInfo.name}: ${(modelInfo.weight * 100).toFixed(0)}% weight`}
                >
                  {/* Hover tooltip */}
                  <div className={cn(
                    'absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 rounded text-xs font-medium',
                    'bg-tactical-900 text-white dark:bg-tactical-100 dark:text-tactical-900',
                    'opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10'
                  )}>
                    {modelInfo.name}: {(modelInfo.weight * 100).toFixed(0)}%
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Legend */}
        {showLegend && (
          <div className="flex flex-wrap gap-2">
            {ALL_MODELS.map(modelKey => {
              const modelInfo = MODEL_COLORS[modelKey]
              const result = modelMap.get(modelKey)
              const isMatched = result && result.matched !== false && result.similarity > 0

              return (
                <div
                  key={modelKey}
                  className={cn(
                    'flex items-center gap-1.5 px-2 py-1 rounded-md text-xs',
                    isMatched
                      ? modelInfo.bgLight
                      : 'bg-tactical-100 dark:bg-tactical-800 opacity-60'
                  )}
                >
                  <div className={cn(
                    'w-2.5 h-2.5 rounded-full',
                    isMatched ? modelInfo.bg : 'bg-tactical-400'
                  )} />
                  <span className={cn(
                    'font-medium',
                    isMatched ? modelInfo.text : 'text-tactical-500 dark:text-tactical-400'
                  )}>
                    {modelInfo.name}
                  </span>
                  {result && (
                    <span className="text-tactical-500 dark:text-tactical-400 ml-1">
                      {(result.similarity * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className={cn(
          'mt-4 space-y-2',
          animateOnLoad && 'animate-fade-in-up'
        )}>
          {/* Individual model scores */}
          {ALL_MODELS.map(modelKey => {
            const modelInfo = MODEL_COLORS[modelKey]
            const result = modelMap.get(modelKey)
            const isMatched = result && result.matched !== false && result.similarity > 0
            const similarity = result?.similarity || 0

            return (
              <div
                key={modelKey}
                className={cn(
                  'flex items-center gap-3 p-2 rounded-lg',
                  'bg-tactical-50 dark:bg-tactical-800/50'
                )}
              >
                {/* Status icon */}
                {isMatched ? (
                  <CheckCircleIcon className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                ) : (
                  <XCircleIcon className="w-4 h-4 text-tactical-400 flex-shrink-0" />
                )}

                {/* Model name */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={cn(
                      'text-sm font-medium',
                      isMatched ? 'text-tactical-900 dark:text-tactical-100' : 'text-tactical-500'
                    )}>
                      {modelInfo.name}
                    </span>
                    <span className="text-xs text-tactical-400">
                      {(modelInfo.weight * 100).toFixed(0)}% weight
                    </span>
                  </div>

                  {/* Score bar */}
                  <div className="mt-1 h-1.5 bg-tactical-200 dark:bg-tactical-700 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        'h-full rounded-full transition-all duration-500',
                        isMatched ? modelInfo.bg : 'bg-tactical-300'
                      )}
                      style={{ width: `${similarity * 100}%` }}
                    />
                  </div>
                </div>

                {/* Score */}
                <div className={cn(
                  'text-sm font-bold tabular-nums',
                  isMatched
                    ? 'text-tactical-900 dark:text-tactical-100'
                    : 'text-tactical-400'
                )}>
                  {(similarity * 100).toFixed(1)}%
                </div>
              </div>
            )
          })}

          {/* Weighted consensus score */}
          <div className={cn(
            'mt-3 p-3 rounded-lg',
            'bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20',
            'border border-blue-200 dark:border-blue-800'
          )}>
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-semibold text-blue-800 dark:text-blue-200">
                  Weighted Consensus Score
                </span>
                <p className="text-xs text-blue-600 dark:text-blue-400 mt-0.5">
                  Based on model weights and individual similarity scores
                </p>
              </div>
              <div className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                {(weightedScore * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Compact inline version for match cards
interface EnsembleInlineProps {
  agreementCount: number
  totalModels?: number
  className?: string
}

export const EnsembleInline = ({
  agreementCount,
  totalModels = 6,
  className,
}: EnsembleInlineProps) => {
  const ratio = agreementCount / totalModels

  return (
    <div className={cn('flex items-center gap-1.5', className)}>
      {/* Model indicators */}
      <div className="flex gap-0.5">
        {Array.from({ length: totalModels }).map((_, i) => (
          <div
            key={i}
            className={cn(
              'w-1.5 h-4 rounded-sm transition-colors',
              i < agreementCount
                ? ratio >= 0.8
                  ? 'bg-emerald-500'
                  : ratio >= 0.5
                  ? 'bg-amber-500'
                  : 'bg-red-500'
                : 'bg-tactical-300 dark:bg-tactical-600'
            )}
          />
        ))}
      </div>

      {/* Text */}
      <span className={cn(
        'text-xs font-medium',
        ratio >= 0.8
          ? 'text-emerald-600 dark:text-emerald-400'
          : ratio >= 0.5
          ? 'text-amber-600 dark:text-amber-400'
          : 'text-red-600 dark:text-red-400'
      )}>
        {agreementCount}/{totalModels}
      </span>
    </div>
  )
}

export default EnsembleVisualization

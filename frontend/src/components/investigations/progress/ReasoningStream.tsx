import { useState } from 'react'
import { cn } from '../../../utils/cn'
import { ChevronDownIcon, LightBulbIcon } from '@heroicons/react/24/outline'
import type { ReasoningStepEvent } from '../../../types/activity'

export interface ReasoningStreamProps {
  steps: ReasoningStepEvent[]
  className?: string
}

/**
 * ReasoningStream displays real-time reasoning steps from the investigation workflow.
 * Collapsible panel showing each step's phase, conclusion, and confidence.
 */
export function ReasoningStream({ steps, className }: ReasoningStreamProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  if (steps.length === 0) return null

  return (
    <div
      className={cn(
        'rounded-xl border',
        'bg-white dark:bg-tactical-800',
        'border-tactical-200 dark:border-tactical-700',
        'shadow-tactical',
        className
      )}
    >
      {/* Header */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          'w-full flex items-center justify-between px-4 py-3',
          'border-b border-tactical-200 dark:border-tactical-700',
          'hover:bg-tactical-50 dark:hover:bg-tactical-700/50',
          'transition-colors rounded-t-xl'
        )}
      >
        <div className="flex items-center gap-2">
          <LightBulbIcon className="w-5 h-5 text-amber-500" />
          <h3 className="font-semibold text-tactical-900 dark:text-tactical-100 text-sm">
            Reasoning Chain
          </h3>
          <span className="text-xs text-tactical-500 dark:text-tactical-400">
            {steps.length} step{steps.length !== 1 ? 's' : ''}
          </span>
        </div>
        <ChevronDownIcon
          className={cn(
            'w-4 h-4 text-tactical-400 transition-transform duration-200',
            isExpanded && 'rotate-180'
          )}
        />
      </button>

      {/* Steps */}
      {isExpanded && (
        <div className="p-3 space-y-2">
          {steps.map((step, idx) => (
            <div
              key={`${step.step}-${step.phase}`}
              className={cn(
                'flex items-start gap-3 p-3 rounded-lg',
                'bg-tactical-50 dark:bg-tactical-900/50',
                idx === steps.length - 1 && 'animate-fade-in-up'
              )}
            >
              {/* Step number */}
              <span className={cn(
                'flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center',
                'bg-amber-100 dark:bg-amber-900/50',
                'text-amber-700 dark:text-amber-300',
                'text-xs font-bold'
              )}>
                {step.step}
              </span>

              <div className="flex-1 min-w-0">
                {/* Phase badge */}
                <span className={cn(
                  'inline-block px-2 py-0.5 rounded text-xs font-medium mb-1',
                  'bg-tactical-200 dark:bg-tactical-700',
                  'text-tactical-700 dark:text-tactical-300'
                )}>
                  {step.phase}
                </span>

                {/* Conclusion */}
                <p className="text-sm text-tactical-800 dark:text-tactical-200 mt-1">
                  {step.conclusion}
                </p>

                {/* Confidence badge */}
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs text-tactical-500 dark:text-tactical-400">Confidence:</span>
                  <span className={cn(
                    'text-xs font-semibold px-1.5 py-0.5 rounded tabular-nums',
                    step.confidence >= 80
                      ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
                      : step.confidence >= 60
                      ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
                      : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                  )}>
                    {step.confidence}%
                  </span>
                  {step.evidence_count > 0 && (
                    <span className="text-xs text-tactical-400 dark:text-tactical-500">
                      ({step.evidence_count} evidence)
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ReasoningStream

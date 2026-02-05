import React, { useState } from 'react'
import { cn } from '../../utils/cn'
import {
  getConfidenceLevel,
  getConfidenceColors,
  normalizeScore,
  toPercentage,
} from '../../utils/confidence'
import {
  ChevronDownIcon,
  ChevronRightIcon,
  ClipboardDocumentIcon,
  CheckIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import type { ReasoningChain, ReasoningChainStep, ImageQuality } from '../../types/investigation2'

interface Investigation2MethodologyProps {
  steps: ReasoningChainStep[]
  reasoningChain?: ReasoningChain
  imageQuality?: ImageQuality
}

export const Investigation2Methodology: React.FC<Investigation2MethodologyProps> = ({
  steps,
  reasoningChain,
  imageQuality,
}) => {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set())
  const [copied, setCopied] = useState(false)

  if (!steps || steps.length === 0) {
    return (
      <div className="text-center py-12">
        <SparklesIcon className="w-16 h-16 mx-auto text-tactical-300 dark:text-tactical-600 mb-4" />
        <h4 className="text-lg font-medium text-tactical-900 dark:text-tactical-100 mb-2">
          No Methodology Data
        </h4>
        <p className="text-tactical-600 dark:text-tactical-400">
          Methodology information is not available for this investigation
        </p>
      </div>
    )
  }

  const toggleStep = (stepNumber: number) => {
    setExpandedSteps(prev => {
      const newSet = new Set(prev)
      if (newSet.has(stepNumber)) {
        newSet.delete(stepNumber)
      } else {
        newSet.add(stepNumber)
      }
      return newSet
    })
  }

  const expandAll = () => {
    setExpandedSteps(new Set(steps.map(s => s.step)))
  }

  const collapseAll = () => {
    setExpandedSteps(new Set())
  }

  const getPhaseColor = (phase: string) => {
    const phaseLower = phase.toLowerCase()
    if (phaseLower.includes('upload') || phaseLower.includes('parse')) return 'border-l-blue-500'
    if (phaseLower.includes('detection') || phaseLower.includes('detect')) return 'border-l-emerald-500'
    if (phaseLower.includes('analysis') || phaseLower.includes('stripe') || phaseLower.includes('reid')) return 'border-l-purple-500'
    if (phaseLower.includes('report') || phaseLower.includes('generation')) return 'border-l-tiger-orange'
    if (phaseLower.includes('search') || phaseLower.includes('web') || phaseLower.includes('intel')) return 'border-l-cyan-500'
    if (phaseLower.includes('verif')) return 'border-l-amber-500'
    return 'border-l-tactical-400'
  }

  const getPhaseBadgeColor = (phase: string) => {
    const phaseLower = phase.toLowerCase()
    if (phaseLower.includes('upload') || phaseLower.includes('parse'))
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300'
    if (phaseLower.includes('detection') || phaseLower.includes('detect'))
      return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300'
    if (phaseLower.includes('analysis') || phaseLower.includes('stripe') || phaseLower.includes('reid'))
      return 'bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300'
    if (phaseLower.includes('report') || phaseLower.includes('generation'))
      return 'bg-orange-100 text-orange-800 dark:bg-orange-900/50 dark:text-orange-300'
    if (phaseLower.includes('search') || phaseLower.includes('web') || phaseLower.includes('intel'))
      return 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/50 dark:text-cyan-300'
    if (phaseLower.includes('verif'))
      return 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300'
    return 'bg-tactical-100 text-tactical-800 dark:bg-tactical-800 dark:text-tactical-300'
  }

  const copyMethodology = async () => {
    const text = steps.map(step =>
      `Step ${step.step}: ${step.phase}\n` +
      `Action: ${step.action}\n` +
      `Reasoning: ${step.reasoning}\n` +
      `Evidence: ${step.evidence.join(', ')}\n` +
      `Conclusion: ${step.conclusion}\n` +
      `Confidence: ${step.confidence}%`
    ).join('\n\n')

    const header = reasoningChain
      ? `Investigation Chain: ${reasoningChain.question}\nStatus: ${reasoningChain.status} | ${steps.length} steps | Final Confidence: ${reasoningChain.overall_confidence || 'N/A'}%\n\n`
      : ''

    await navigator.clipboard.writeText(header + text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const overallConfidence = reasoningChain?.overall_confidence ??
    Math.round(steps.reduce((acc, s) => acc + s.confidence, 0) / steps.length)

  const overallLevel = getConfidenceLevel(overallConfidence / 100)
  const overallColors = getConfidenceColors(overallLevel)

  return (
    <div className="methodology-timeline">
      {/* Chain Summary Header */}
      <div className={cn(
        'mb-6 rounded-xl p-5',
        'bg-gradient-to-r from-blue-50 to-indigo-50',
        'dark:from-blue-900/20 dark:to-indigo-900/20',
        'border border-blue-200 dark:border-blue-800'
      )}>
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex-1">
            <h3 className="text-xl font-bold text-tactical-900 dark:text-tactical-100 mb-1">
              Investigation Chain
            </h3>
            {reasoningChain?.question && (
              <p className="text-tactical-600 dark:text-tactical-400 text-sm mb-3">
                Question: "{reasoningChain.question}"
              </p>
            )}
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <span className={cn(
                'inline-flex items-center px-3 py-1 rounded-full font-medium',
                reasoningChain?.status === 'finalized'
                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300'
                  : reasoningChain?.status === 'active'
                  ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300'
                  : 'bg-tactical-100 text-tactical-800 dark:bg-tactical-800 dark:text-tactical-300'
              )}>
                {reasoningChain?.status || 'Complete'}
              </span>
              <span className="text-tactical-600 dark:text-tactical-400">
                <span className="font-semibold text-tactical-900 dark:text-tactical-100">
                  {steps.length}
                </span> steps
              </span>
              <span className={cn('font-semibold', overallColors.text)}>
                Final Confidence: {overallConfidence}%
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={expandAll}
              className="btn-ghost text-sm"
            >
              Expand All
            </button>
            <button
              onClick={collapseAll}
              className="btn-ghost text-sm"
            >
              Collapse All
            </button>
          </div>
        </div>
      </div>

      {/* Image Quality Badge */}
      {imageQuality && (
        <div className={cn(
          'mb-6 p-4 rounded-xl',
          'bg-white dark:bg-tactical-800',
          'border border-tactical-200 dark:border-tactical-700'
        )}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-tactical-700 dark:text-tactical-300">
                Image Quality:
              </span>
              <div className="flex items-center gap-3">
                <div className="w-32 progress-bar">
                  <div
                    className={cn(
                      'progress-bar-fill',
                      imageQuality.overall_score >= 0.8 ? 'bg-emerald-500' :
                      imageQuality.overall_score >= 0.6 ? 'bg-amber-500' : 'bg-red-500'
                    )}
                    style={{ width: `${imageQuality.overall_score * 100}%` }}
                  />
                </div>
                <span className={cn(
                  'text-sm font-bold tabular-nums',
                  imageQuality.overall_score >= 0.8
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : imageQuality.overall_score >= 0.6
                    ? 'text-amber-600 dark:text-amber-400'
                    : 'text-red-600 dark:text-red-400'
                )}>
                  {Math.round(imageQuality.overall_score * 100)}%
                </span>
              </div>
            </div>
            {imageQuality.issues.length > 0 && (
              <span className="text-sm text-amber-600 dark:text-amber-400">
                {imageQuality.issues.length} issue{imageQuality.issues.length > 1 ? 's' : ''}
              </span>
            )}
          </div>
          {imageQuality.issues.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {imageQuality.issues.map((issue, idx) => (
                <span
                  key={idx}
                  className={cn(
                    'px-2.5 py-1 text-xs font-medium rounded-full',
                    'bg-amber-100 text-amber-800',
                    'dark:bg-amber-900/50 dark:text-amber-300'
                  )}
                >
                  {issue}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Steps Timeline */}
      <div className="space-y-3">
        {steps.map((step, idx) => {
          const isExpanded = expandedSteps.has(step.step)
          const stepConfidence = normalizeScore(step.confidence > 1 ? step.confidence / 100 : step.confidence)
          const stepLevel = getConfidenceLevel(stepConfidence)
          const stepColors = getConfidenceColors(stepLevel)

          return (
            <div key={idx} className="reasoning-step relative">
              {/* Timeline connector */}
              {idx < steps.length - 1 && (
                <div className={cn(
                  'absolute left-6 top-14 h-[calc(100%-2rem)] w-0.5 z-0',
                  'bg-tactical-200 dark:bg-tactical-700'
                )} />
              )}

              {/* Step content */}
              <div className="relative z-10">
                {/* Collapsible header */}
                <button
                  onClick={() => toggleStep(step.step)}
                  className={cn(
                    'w-full flex items-center gap-4 p-4 rounded-xl border transition-all',
                    isExpanded
                      ? 'bg-white dark:bg-tactical-800 border-tactical-300 dark:border-tactical-600 shadow-tactical'
                      : 'bg-tactical-50 dark:bg-tactical-900/50 border-tactical-200 dark:border-tactical-700 hover:border-tactical-300'
                  )}
                >
                  {/* Step number badge */}
                  <div
                    className={cn(
                      'w-10 h-10 rounded-full flex items-center justify-center',
                      'font-bold text-white shadow-sm flex-shrink-0',
                      stepColors.bgSolid
                    )}
                  >
                    {step.step}
                  </div>

                  {/* Step info */}
                  <div className="flex-1 text-left min-w-0">
                    <div className="flex items-center flex-wrap gap-2">
                      <h4 className="font-semibold text-tactical-900 dark:text-tactical-100">
                        {step.phase}
                      </h4>
                      <span className={cn(
                        'px-2 py-0.5 text-xs font-medium rounded-full',
                        getPhaseBadgeColor(step.phase)
                      )}>
                        {step.phase.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                      </span>
                    </div>
                    {!isExpanded && (
                      <p className="text-sm text-tactical-500 dark:text-tactical-400 mt-1 truncate max-w-lg">
                        {step.action}
                      </p>
                    )}
                  </div>

                  {/* Confidence and expand icon */}
                  <div className="flex items-center gap-4">
                    <span className={cn('text-sm font-bold tabular-nums', stepColors.text)}>
                      {toPercentage(stepConfidence)}
                    </span>
                    {isExpanded ? (
                      <ChevronDownIcon className="w-5 h-5 text-tactical-400" />
                    ) : (
                      <ChevronRightIcon className="w-5 h-5 text-tactical-400" />
                    )}
                  </div>
                </button>

                {/* Expanded details */}
                {isExpanded && (
                  <div className={cn(
                    'ml-14 mt-3 p-4 rounded-xl shadow-sm animate-fade-in-up',
                    'bg-white dark:bg-tactical-800',
                    'border-l-4 border border-tactical-200 dark:border-tactical-700',
                    getPhaseColor(step.phase)
                  )}>
                    {/* Action */}
                    <div className="mb-4">
                      <span className="text-xs font-semibold uppercase tracking-wider text-tactical-500 dark:text-tactical-400">
                        Action
                      </span>
                      <p className="text-sm text-tactical-700 dark:text-tactical-300 mt-1">
                        {step.action}
                      </p>
                    </div>

                    {/* Reasoning - highlighted box */}
                    <div className={cn(
                      'mb-4 p-4 rounded-xl',
                      'bg-blue-50 dark:bg-blue-900/20',
                      'border border-blue-200 dark:border-blue-800'
                    )}>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-semibold uppercase tracking-wider text-tactical-500 dark:text-tactical-400">
                          Reasoning
                        </span>
                        <span className={cn(
                          'px-2 py-0.5 text-2xs font-bold rounded',
                          'bg-blue-200 text-blue-800',
                          'dark:bg-blue-800 dark:text-blue-200'
                        )}>
                          Thinking Tokens
                        </span>
                      </div>
                      <p className="text-sm italic text-tactical-700 dark:text-tactical-300 leading-relaxed">
                        {step.reasoning}
                      </p>
                    </div>

                    {/* Evidence */}
                    {step.evidence && step.evidence.length > 0 && (
                      <div className="mb-4">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-semibold uppercase tracking-wider text-tactical-500 dark:text-tactical-400">
                            Evidence
                          </span>
                          <span className="text-xs text-tactical-400">
                            ({step.evidence.length} items)
                          </span>
                        </div>
                        <ul className="space-y-1.5">
                          {step.evidence.map((ev, i) => (
                            <li
                              key={i}
                              className="flex items-start gap-2 text-sm text-tactical-600 dark:text-tactical-400"
                            >
                              <span className="text-tactical-300 mt-1">•</span>
                              <span>{ev}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Conclusion */}
                    <div className={cn(
                      'p-3 rounded-lg',
                      'bg-tactical-50 dark:bg-tactical-900/50',
                      'border border-tactical-200 dark:border-tactical-700'
                    )}>
                      <span className="text-xs font-semibold uppercase tracking-wider text-tactical-500 dark:text-tactical-400">
                        Conclusion
                      </span>
                      <p className="text-sm font-medium text-tactical-800 dark:text-tactical-200 mt-1">
                        {step.conclusion}
                      </p>
                    </div>

                    {/* Timestamp */}
                    {step.timestamp && (
                      <div className="mt-3 text-xs text-tactical-400">
                        Completed: {new Date(step.timestamp).toLocaleString()}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Summary footer with copy button */}
      <div className={cn(
        'mt-8 p-5 rounded-xl',
        'bg-blue-50 dark:bg-blue-900/20',
        'border border-blue-200 dark:border-blue-800'
      )}>
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div>
            <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
              Methodology Summary
            </h4>
            <p className="text-sm text-blue-800 dark:text-blue-200">
              This investigation followed a {steps.length}-step process to analyze the tiger image
              and generate conclusions. Each step builds on previous findings to ensure transparent,
              evidence-based results.
            </p>
          </div>
          <button
            onClick={copyMethodology}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium',
              'bg-white dark:bg-tactical-800',
              'border border-blue-300 dark:border-blue-700',
              'text-blue-700 dark:text-blue-300',
              'hover:bg-blue-50 dark:hover:bg-blue-900/30',
              'transition-colors flex-shrink-0'
            )}
          >
            {copied ? (
              <>
                <CheckIcon className="w-4 h-4 text-emerald-600" />
                <span className="text-emerald-600">Copied!</span>
              </>
            ) : (
              <>
                <ClipboardDocumentIcon className="w-4 h-4" />
                Copy Methodology
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Investigation2Methodology

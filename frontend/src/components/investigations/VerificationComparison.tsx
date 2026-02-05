import { Fragment, useState } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { cn } from '../../utils/cn'
import {
  XMarkIcon,
  ArrowsRightLeftIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  MinusIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  BeakerIcon,
} from '@heroicons/react/24/outline'
import { getConfidenceLevel, getConfidenceColors, normalizeScore } from '../../utils/confidence'
import type { VerifiedCandidate } from '../../types/investigation2'

interface Match {
  tiger_id: string
  tiger_name?: string
  similarity: number
  model?: string
  rank?: number
}

interface VerificationComparisonProps {
  isOpen: boolean
  onClose: () => void
  reidMatches: Match[]
  verifiedCandidates: VerifiedCandidate[]
  className?: string
}

export const VerificationComparison = ({
  isOpen,
  onClose,
  reidMatches,
  verifiedCandidates,
  className,
}: VerificationComparisonProps) => {
  const [selectedTiger, setSelectedTiger] = useState<string | null>(null)

  // Get top 3 from each
  const reidTop3 = reidMatches.slice(0, 3)
  const verifiedTop3 = verifiedCandidates.slice(0, 3)

  // Calculate rank changes
  const getRankChange = (tigerId: string) => {
    const reidRank = reidTop3.findIndex(m => m.tiger_id === tigerId)
    const verifiedRank = verifiedTop3.findIndex(c => c.tiger_id === tigerId)

    if (reidRank === -1 && verifiedRank !== -1) {
      return { type: 'new', change: 0 }
    }
    if (reidRank !== -1 && verifiedRank === -1) {
      return { type: 'dropped', change: 0 }
    }
    if (reidRank === -1 || verifiedRank === -1) {
      return { type: 'none', change: 0 }
    }

    const change = reidRank - verifiedRank
    if (change > 0) return { type: 'up', change }
    if (change < 0) return { type: 'down', change: Math.abs(change) }
    return { type: 'same', change: 0 }
  }

  // Check if top match changed
  const topMatchChanged = reidTop3[0]?.tiger_id !== verifiedTop3[0]?.tiger_id

  const RankChangeIcon = ({ tigerId }: { tigerId: string }) => {
    const { type, change } = getRankChange(tigerId)

    switch (type) {
      case 'up':
        return (
          <div className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
            <ArrowUpIcon className="w-4 h-4" />
            <span className="text-xs font-bold">+{change}</span>
          </div>
        )
      case 'down':
        return (
          <div className="flex items-center gap-1 text-red-600 dark:text-red-400">
            <ArrowDownIcon className="w-4 h-4" />
            <span className="text-xs font-bold">-{change}</span>
          </div>
        )
      case 'new':
        return (
          <span className="px-1.5 py-0.5 text-xs font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-400 rounded">
            NEW
          </span>
        )
      case 'dropped':
        return (
          <span className="px-1.5 py-0.5 text-xs font-bold bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-400 rounded">
            OUT
          </span>
        )
      default:
        return <MinusIcon className="w-4 h-4 text-tactical-400" />
    }
  }

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className={cn('relative z-50', className)} onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className={cn(
                'w-full max-w-4xl transform overflow-hidden rounded-2xl',
                'bg-white dark:bg-tactical-800',
                'shadow-xl transition-all'
              )}>
                {/* Header */}
                <div className={cn(
                  'flex items-center justify-between px-6 py-4',
                  'bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20',
                  'border-b border-amber-200 dark:border-amber-800'
                )}>
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/50">
                      <ArrowsRightLeftIcon className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                    </div>
                    <div>
                      <Dialog.Title className="text-lg font-semibold text-tactical-900 dark:text-tactical-100">
                        Verification Comparison
                      </Dialog.Title>
                      <p className="text-sm text-tactical-600 dark:text-tactical-400">
                        ReID rankings vs. geometric verification results
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={onClose}
                    className={cn(
                      'p-2 rounded-lg',
                      'hover:bg-amber-200/50 dark:hover:bg-amber-800/50',
                      'transition-colors'
                    )}
                  >
                    <XMarkIcon className="w-5 h-5 text-tactical-600 dark:text-tactical-400" />
                  </button>
                </div>

                {/* Alert if top match changed */}
                {topMatchChanged && (
                  <div className={cn(
                    'mx-6 mt-4 flex items-center gap-3 p-4 rounded-lg',
                    'bg-amber-50 dark:bg-amber-900/30',
                    'border border-amber-300 dark:border-amber-700'
                  )}>
                    <ExclamationTriangleIcon className="w-6 h-6 text-amber-600 dark:text-amber-400 flex-shrink-0" />
                    <div>
                      <p className="font-semibold text-amber-800 dark:text-amber-200">
                        Top Match Changed After Verification
                      </p>
                      <p className="text-sm text-amber-700 dark:text-amber-300 mt-0.5">
                        The highest-ranked match differs between ReID and geometric verification.
                        Manual review is strongly recommended.
                      </p>
                    </div>
                  </div>
                )}

                {/* Content */}
                <div className="p-6">
                  {/* Side-by-side comparison */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* ReID Rankings */}
                    <div>
                      <div className="flex items-center gap-2 mb-4">
                        <BeakerIcon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        <h3 className="font-semibold text-tactical-900 dark:text-tactical-100">
                          ReID Rankings
                        </h3>
                        <span className="text-xs text-tactical-500 dark:text-tactical-400">
                          (Before Verification)
                        </span>
                      </div>

                      <div className="space-y-3">
                        {reidTop3.map((match, idx) => {
                          const normalizedScore = normalizeScore(match.similarity)
                          const level = getConfidenceLevel(normalizedScore)
                          const colors = getConfidenceColors(level)
                          const isSelected = selectedTiger === match.tiger_id

                          return (
                            <button
                              key={match.tiger_id}
                              onClick={() => setSelectedTiger(
                                selectedTiger === match.tiger_id ? null : match.tiger_id
                              )}
                              className={cn(
                                'w-full flex items-center gap-3 p-3 rounded-lg text-left',
                                'border transition-all',
                                isSelected
                                  ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700'
                                  : 'bg-tactical-50 dark:bg-tactical-900/50 border-tactical-200 dark:border-tactical-700 hover:border-tactical-300'
                              )}
                            >
                              {/* Rank */}
                              <div className={cn(
                                'w-8 h-8 rounded-full flex items-center justify-center',
                                'text-sm font-bold',
                                idx === 0
                                  ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-400'
                                  : 'bg-tactical-200 text-tactical-600 dark:bg-tactical-700 dark:text-tactical-400'
                              )}>
                                #{idx + 1}
                              </div>

                              {/* Tiger info */}
                              <div className="flex-1 min-w-0">
                                <p className="font-medium text-tactical-900 dark:text-tactical-100 truncate">
                                  {match.tiger_name || `Tiger ${match.tiger_id}`}
                                </p>
                                {match.model && (
                                  <p className="text-xs text-tactical-500 dark:text-tactical-400">
                                    via {match.model}
                                  </p>
                                )}
                              </div>

                              {/* Score */}
                              <div className="text-right">
                                <p className={cn('text-lg font-bold tabular-nums', colors.text)}>
                                  {(normalizedScore * 100).toFixed(1)}%
                                </p>
                              </div>
                            </button>
                          )
                        })}
                      </div>
                    </div>

                    {/* Verified Rankings */}
                    <div>
                      <div className="flex items-center gap-2 mb-4">
                        <ShieldCheckIcon className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                        <h3 className="font-semibold text-tactical-900 dark:text-tactical-100">
                          Verified Rankings
                        </h3>
                        <span className="text-xs text-tactical-500 dark:text-tactical-400">
                          (After Verification)
                        </span>
                      </div>

                      <div className="space-y-3">
                        {verifiedTop3.map((candidate, idx) => {
                          const combinedScore = candidate.combined_score || 0
                          const level = getConfidenceLevel(combinedScore)
                          const colors = getConfidenceColors(level)
                          const isSelected = selectedTiger === candidate.tiger_id

                          return (
                            <button
                              key={candidate.tiger_id}
                              onClick={() => setSelectedTiger(
                                selectedTiger === candidate.tiger_id ? null : candidate.tiger_id
                              )}
                              className={cn(
                                'w-full flex items-center gap-3 p-3 rounded-lg text-left',
                                'border transition-all',
                                isSelected
                                  ? 'bg-purple-50 dark:bg-purple-900/30 border-purple-300 dark:border-purple-700'
                                  : 'bg-tactical-50 dark:bg-tactical-900/50 border-tactical-200 dark:border-tactical-700 hover:border-tactical-300'
                              )}
                            >
                              {/* Rank */}
                              <div className={cn(
                                'w-8 h-8 rounded-full flex items-center justify-center',
                                'text-sm font-bold',
                                idx === 0
                                  ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-400'
                                  : 'bg-tactical-200 text-tactical-600 dark:bg-tactical-700 dark:text-tactical-400'
                              )}>
                                #{idx + 1}
                              </div>

                              {/* Tiger info */}
                              <div className="flex-1 min-w-0">
                                <p className="font-medium text-tactical-900 dark:text-tactical-100 truncate">
                                  {candidate.tiger_name || `Tiger ${candidate.tiger_id}`}
                                </p>
                                <p className="text-xs text-tactical-500 dark:text-tactical-400">
                                  {candidate.num_matches || 0} keypoint matches
                                </p>
                              </div>

                              {/* Rank change indicator */}
                              <RankChangeIcon tigerId={candidate.tiger_id} />

                              {/* Score */}
                              <div className="text-right">
                                <p className={cn('text-lg font-bold tabular-nums', colors.text)}>
                                  {(combinedScore * 100).toFixed(1)}%
                                </p>
                              </div>
                            </button>
                          )
                        })}
                      </div>
                    </div>
                  </div>

                  {/* Selected tiger detail */}
                  {selectedTiger && (
                    <div className={cn(
                      'mt-6 p-4 rounded-lg',
                      'bg-tactical-50 dark:bg-tactical-900/50',
                      'border border-tactical-200 dark:border-tactical-700',
                      'animate-fade-in-up'
                    )}>
                      <h4 className="font-semibold text-tactical-900 dark:text-tactical-100 mb-3">
                        Detailed Comparison: {
                          reidTop3.find(m => m.tiger_id === selectedTiger)?.tiger_name ||
                          verifiedTop3.find(c => c.tiger_id === selectedTiger)?.tiger_name ||
                          `Tiger ${selectedTiger}`
                        }
                      </h4>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {/* ReID Score */}
                        {(() => {
                          const match = reidTop3.find(m => m.tiger_id === selectedTiger)
                          return match && (
                            <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
                              <p className="text-xs text-blue-600 dark:text-blue-400 mb-1">ReID Score</p>
                              <p className="text-xl font-bold text-blue-700 dark:text-blue-300">
                                {(normalizeScore(match.similarity) * 100).toFixed(1)}%
                              </p>
                            </div>
                          )
                        })()}

                        {/* Verified candidate details */}
                        {(() => {
                          const candidate = verifiedTop3.find(c => c.tiger_id === selectedTiger)
                          return candidate && (
                            <>
                              <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/30 rounded-lg">
                                <p className="text-xs text-purple-600 dark:text-purple-400 mb-1">Combined Score</p>
                                <p className="text-xl font-bold text-purple-700 dark:text-purple-300">
                                  {((candidate.combined_score || 0) * 100).toFixed(1)}%
                                </p>
                              </div>

                              <div className="text-center p-3 bg-orange-50 dark:bg-orange-900/30 rounded-lg">
                                <p className="text-xs text-orange-600 dark:text-orange-400 mb-1">Keypoint Matches</p>
                                <p className="text-xl font-bold text-orange-700 dark:text-orange-300">
                                  {candidate.num_matches || 0}
                                </p>
                              </div>

                              <div className="text-center p-3 bg-emerald-50 dark:bg-emerald-900/30 rounded-lg">
                                <p className="text-xs text-emerald-600 dark:text-emerald-400 mb-1">Match Score</p>
                                <p className="text-xl font-bold text-emerald-700 dark:text-emerald-300">
                                  {((candidate.normalized_match_score || 0) * 100).toFixed(1)}%
                                </p>
                              </div>
                            </>
                          )
                        })()}
                      </div>
                    </div>
                  )}

                  {/* Explanation */}
                  <div className={cn(
                    'mt-6 p-4 rounded-lg',
                    'bg-blue-50 dark:bg-blue-900/20',
                    'border border-blue-200 dark:border-blue-800'
                  )}>
                    <h4 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">
                      Why Rankings May Differ
                    </h4>
                    <ul className="space-y-2 text-sm text-blue-700 dark:text-blue-300">
                      <li className="flex items-start gap-2">
                        <span className="text-blue-400 mt-1">•</span>
                        <span>
                          <strong>ReID models</strong> compare high-level visual features and stripe patterns
                          using learned embeddings.
                        </span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-blue-400 mt-1">•</span>
                        <span>
                          <strong>Geometric verification</strong> matches specific keypoints and validates
                          spatial consistency of stripe patterns.
                        </span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-blue-400 mt-1">•</span>
                        <span>
                          Disagreement often occurs when images have different poses, lighting, or partial
                          visibility that affects methods differently.
                        </span>
                      </li>
                    </ul>
                  </div>
                </div>

                {/* Footer */}
                <div className={cn(
                  'flex items-center justify-end gap-3 px-6 py-4',
                  'border-t border-tactical-200 dark:border-tactical-700'
                )}>
                  <button
                    onClick={onClose}
                    className="btn-secondary"
                  >
                    Close
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}

export default VerificationComparison

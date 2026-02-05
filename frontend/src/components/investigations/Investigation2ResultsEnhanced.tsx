import { useState } from 'react'
import Card, { StatCard } from '../common/Card'
import Badge from '../common/Badge'
import { cn } from '../../utils/cn'
import {
  getConfidenceLevel,
  getConfidenceColors,
  normalizeScore,
  toPercentage,
} from '../../utils/confidence'
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  GlobeAltIcon,
  BeakerIcon,
  EyeIcon,
  DocumentTextIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'
import { ShieldCheckIcon, SparklesIcon, UsersIcon, FingerPrintIcon } from '@heroicons/react/24/solid'
import { Investigation2Citations } from './Investigation2Citations'
import { Investigation2Map } from './Investigation2Map'
import { Investigation2MatchCard } from './Investigation2MatchCard'
import { Investigation2Methodology } from './Investigation2Methodology'
import { Investigation2TabNav } from './Investigation2TabNav'
import { ImageQualityPanel, ImageQualityInline } from './ImageQualityPanel'
import { EnsembleVisualization } from './EnsembleVisualization'
import { VerificationComparison } from './VerificationComparison'
import { ReportDownload } from './ReportDownload'
import { MarkdownContent } from '../common/MarkdownContent'
import type {
  ReportAudience,
  ImageQuality,
  ReasoningChain,
  VerifiedCandidate,
  Investigation2Response,
  Investigation2SummaryExtended,
  TopMatch,
  ModelUsedInfo,
  DetectedTiger,
  TavilySearchResult,
  FacilityCrawlResult,
  ReIDMatchForComparison,
  ReverseSearchResults,
  Investigation2ReportData,
} from '../../types/investigation2'

interface Investigation2ResultsEnhancedProps {
  investigation: Investigation2Response & { summary?: Investigation2SummaryExtended }
  fullWidth?: boolean
  onRegenerateReport?: (audience: ReportAudience) => void
}

const AUDIENCE_OPTIONS: { value: ReportAudience; label: string }[] = [
  { value: 'law_enforcement', label: 'Law Enforcement' },
  { value: 'conservation', label: 'Conservation' },
  { value: 'internal', label: 'Internal/Technical' },
  { value: 'public', label: 'Public' }
]

const Investigation2ResultsEnhanced = ({
  investigation,
  fullWidth: _fullWidth = false,
  onRegenerateReport
}: Investigation2ResultsEnhancedProps) => {
  const [activeTab, setActiveTab] = useState('overview')
  const [showComparisonModal, setShowComparisonModal] = useState(false)

  // Suppress unused variable warning - fullWidth reserved for future layout enhancements
  void _fullWidth

  const summary: Investigation2SummaryExtended = investigation.summary || {} as Investigation2SummaryExtended
  const report: Investigation2ReportData = summary.report || (summary as unknown as Investigation2ReportData)
  const topMatches: TopMatch[] = report.top_matches || []
  const modelsUsed: (string | ModelUsedInfo)[] = report.models_used || []
  const detectionCount: number = report.detection_count || 0
  const totalMatches: number = report.total_matches || 0
  const confidence: string = report.confidence || 'medium'

  // Extract phase-specific data
  const reverseSearchResults: ReverseSearchResults = summary.reverse_search_results || {}
  const detectedTigers: DetectedTiger[] = summary.detected_tigers || []

  // Enhanced workflow data
  const imageQuality: ImageQuality | undefined = summary.image_quality
  const reasoningChain: ReasoningChain | undefined = summary.reasoning_chain
  const currentAudience: ReportAudience = summary.report_audience || 'law_enforcement'

  // Verification data
  const verifiedCandidates: VerifiedCandidate[] = summary.verified_candidates || []
  const verificationApplied: boolean = summary.verification_applied || false
  const verificationDisagreement: boolean = summary.verification_disagreement || false

  // Audience selection state
  const [selectedAudience, setSelectedAudience] = useState<ReportAudience>(currentAudience)
  const [isRegenerating, setIsRegenerating] = useState(false)

  const handleRegenerateReport = async () => {
    if (selectedAudience === currentAudience) return

    setIsRegenerating(true)
    try {
      await onRegenerateReport?.(selectedAudience)
    } finally {
      setIsRegenerating(false)
    }
  }

  const getConfidenceBadge = (conf: string) => {
    const level = conf.toLowerCase() as 'high' | 'medium' | 'low'
    const colors = getConfidenceColors(level === 'high' ? 'high' : level === 'medium' ? 'medium' : 'low')

    return (
      <span className={cn(
        'inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold',
        colors.bg,
        colors.text
      )}>
        {conf.charAt(0).toUpperCase() + conf.slice(1)} Confidence
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Sticky Verification Alert Banner */}
      {verificationDisagreement && (
        <div className={cn(
          'sticky top-0 z-20 -mx-6 -mt-6 px-6 py-4',
          'bg-gradient-to-r from-amber-50 via-orange-50 to-amber-50',
          'dark:from-amber-900/30 dark:via-orange-900/30 dark:to-amber-900/30',
          'border-b-2 border-amber-400 dark:border-amber-600',
          'shadow-lg animate-fade-in-down'
        )}>
          <div className="flex items-center justify-between gap-4 max-w-7xl mx-auto">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-amber-200/50 dark:bg-amber-800/50">
                <ExclamationTriangleIcon className="w-6 h-6 text-amber-700 dark:text-amber-300" />
              </div>
              <div>
                <h3 className="font-bold text-amber-900 dark:text-amber-100">
                  Manual Review Required
                </h3>
                <p className="text-sm text-amber-800 dark:text-amber-200 mt-0.5">
                  Geometric verification results disagree with ReID model rankings.
                  The top match may have changed.
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowComparisonModal(true)}
              className={cn(
                'flex-shrink-0 px-4 py-2 rounded-lg font-medium text-sm',
                'bg-amber-200 hover:bg-amber-300 dark:bg-amber-700 dark:hover:bg-amber-600',
                'text-amber-900 dark:text-amber-100',
                'transition-colors shadow-sm'
              )}
            >
              View Comparison
            </button>
          </div>
        </div>
      )}

      {/* Audience Selector Bar */}
      <Card variant="default" padding="md">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <label htmlFor="audience-select" className="text-sm font-medium text-tactical-700 dark:text-tactical-300">
                Report Audience:
              </label>
              <select
                id="audience-select"
                value={selectedAudience}
                onChange={(e) => setSelectedAudience(e.target.value as ReportAudience)}
                className={cn(
                  'rounded-lg px-3 py-1.5 text-sm font-medium',
                  'bg-tactical-50 dark:bg-tactical-800',
                  'border border-tactical-300 dark:border-tactical-600',
                  'text-tactical-900 dark:text-tactical-100',
                  'focus:border-tiger-orange focus:ring-2 focus:ring-tiger-orange/30'
                )}
              >
                {AUDIENCE_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            {selectedAudience !== currentAudience && (
              <button
                onClick={handleRegenerateReport}
                disabled={isRegenerating}
                className="btn-primary flex items-center gap-2 text-sm"
              >
                {isRegenerating ? (
                  <>
                    <ArrowPathIcon className="w-4 h-4 animate-spin" />
                    Regenerating...
                  </>
                ) : (
                  <>
                    <ArrowPathIcon className="w-4 h-4" />
                    Regenerate Report
                  </>
                )}
              </button>
            )}
          </div>

          {/* Image Quality Inline */}
          {imageQuality && (
            <ImageQualityInline score={imageQuality.overall_score} />
          )}

          {/* Download Button */}
          <ReportDownload
            investigationId={investigation.investigation_id}
            audience={selectedAudience}
          />
        </div>
      </Card>

      {/* Image Quality Panel (prominent position) */}
      {imageQuality && (
        <ImageQualityPanel
          quality={imageQuality}
          variant="compact"
          showRecommendations={false}
        />
      )}

      {/* Tab Navigation */}
      <Investigation2TabNav
        activeTab={activeTab}
        onTabChange={setActiveTab}
        counts={{
          detection: detectionCount,
          matches: totalMatches,
          verification: verifiedCandidates.length,
          external: reverseSearchResults.total_results,
          citations: reverseSearchResults.citations?.length,
        }}
        verificationDisagreement={verificationDisagreement}
      />

      {/* Tab Content */}
      <div className="animate-fade-in-up">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                label="Tigers Detected"
                value={detectionCount}
                icon={<EyeIcon className="w-6 h-6" />}
                variant="default"
              />
              <StatCard
                label="Models Used"
                value={modelsUsed.length}
                icon={<BeakerIcon className="w-6 h-6" />}
                variant="default"
              />
              <StatCard
                label="Total Matches"
                value={totalMatches}
                icon={<UsersIcon className="w-6 h-6" />}
                variant="match"
              />
              <Card variant="default" padding="md">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-tactical-600 dark:text-tactical-400 mb-2">
                      Confidence
                    </p>
                    {getConfidenceBadge(confidence)}
                  </div>
                  <div className="p-2 rounded-lg bg-tactical-100 dark:bg-tactical-700/50">
                    <SparklesIcon className="w-6 h-6 text-tactical-600 dark:text-tactical-300" />
                  </div>
                </div>
              </Card>
            </div>

            {/* Top Matches Preview */}
            {topMatches.length > 0 && (
              <Card variant="default" padding="lg">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100">
                    Top 5 Matches
                  </h3>
                  <button
                    onClick={() => setActiveTab('matching')}
                    className="text-sm font-medium text-tiger-orange hover:text-tiger-orange-dark transition-colors"
                  >
                    View All
                  </button>
                </div>
                <div className="space-y-3">
                  {topMatches.slice(0, 5).map((match: TopMatch, index: number) => {
                    const normalizedSim = normalizeScore(match.similarity)
                    const level = getConfidenceLevel(normalizedSim)
                    const colors = getConfidenceColors(level)

                    return (
                      <div
                        key={`${match.tiger_id}-${index}`}
                        className={cn(
                          'border rounded-xl p-4 transition-all',
                          'border-tactical-200 dark:border-tactical-700',
                          'hover:border-tactical-300 dark:hover:border-tactical-600',
                          'hover:shadow-tactical-md'
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-3">
                              <span className={cn(
                                'flex items-center justify-center w-8 h-8 rounded-full',
                                'text-sm font-bold',
                                index === 0
                                  ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-400'
                                  : 'bg-tactical-100 text-tactical-600 dark:bg-tactical-700 dark:text-tactical-400'
                              )}>
                                #{index + 1}
                              </span>
                              <div>
                                <span className="font-semibold text-tactical-900 dark:text-tactical-100">
                                  {match.tiger_name || `Tiger ${match.tiger_id}`}
                                </span>
                                <Badge color="blue" size="sm" className="ml-2">
                                  {match.model}
                                </Badge>
                              </div>
                            </div>
                          </div>
                          <div className="text-right ml-4">
                            <div className={cn('text-2xl font-bold tabular-nums', colors.text)}>
                              {toPercentage(match.similarity)}
                            </div>
                            <div className="text-xs text-tactical-500 dark:text-tactical-400">
                              similarity
                            </div>
                          </div>
                        </div>
                        <div className="mt-3">
                          <div className="progress-bar">
                            <div
                              className={cn(
                                'progress-bar-fill',
                                colors.bgSolid
                              )}
                              style={{ width: `${normalizedSim * 100}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </Card>
            )}

            {/* Ensemble Overview (if models present) */}
            {modelsUsed.length > 0 && (
              <Card variant="default" padding="lg">
                <EnsembleVisualization
                  models={modelsUsed.map((m: string | ModelUsedInfo) => ({
                    model: typeof m === 'string' ? m : m.name || m.model || 'unknown',
                    similarity: typeof m === 'string' ? 0.8 : (m.similarity || m.score || 0.8),
                    matched: true,
                    weight: typeof m === 'string' ? undefined : m.weight,
                  }))}
                  compact={false}
                  showLegend={true}
                />
              </Card>
            )}
          </div>
        )}

        {/* Detection Tab */}
        {activeTab === 'detection' && (
          <div className="space-y-6">
            <Card variant="default" padding="lg">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
                  <EyeIcon className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100">
                    Tiger Detection (MegaDetector GPU)
                  </h3>
                  <p className="text-sm text-tactical-600 dark:text-tactical-400">
                    Automated detection of tigers using MegaDetector v5
                  </p>
                </div>
              </div>

              {detectedTigers.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {detectedTigers.map((tiger: DetectedTiger, index: number) => {
                    const conf = normalizeScore(tiger.confidence)
                    const level = getConfidenceLevel(conf)
                    const colors = getConfidenceColors(level)

                    return (
                      <div
                        key={index}
                        className={cn(
                          'border rounded-xl p-4',
                          'border-tactical-200 dark:border-tactical-700'
                        )}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <h4 className="font-semibold text-tactical-900 dark:text-tactical-100">
                              Detected Tiger #{index + 1}
                            </h4>
                            <p className="text-sm text-tactical-600 dark:text-tactical-400 mt-0.5">
                              Category: {tiger.category || 'animal'}
                            </p>
                          </div>
                          <div className="text-right">
                            <div className={cn('text-2xl font-bold tabular-nums', colors.text)}>
                              {toPercentage(tiger.confidence)}
                            </div>
                            <div className="text-xs text-tactical-500">confidence</div>
                          </div>
                        </div>

                        {tiger.bbox && Array.isArray(tiger.bbox) && (
                          <div className="bg-tactical-50 dark:bg-tactical-800 rounded-lg p-3">
                            <div className="text-xs text-tactical-600 dark:text-tactical-400 mb-2">
                              Bounding Box Coordinates:
                            </div>
                            <div className="grid grid-cols-4 gap-2 text-sm font-mono">
                              <div>
                                <span className="text-tactical-500">X1:</span>{' '}
                                <span className="text-tactical-900 dark:text-tactical-100">
                                  {tiger.bbox[0]?.toFixed(0)}
                                </span>
                              </div>
                              <div>
                                <span className="text-tactical-500">Y1:</span>{' '}
                                <span className="text-tactical-900 dark:text-tactical-100">
                                  {tiger.bbox[1]?.toFixed(0)}
                                </span>
                              </div>
                              <div>
                                <span className="text-tactical-500">X2:</span>{' '}
                                <span className="text-tactical-900 dark:text-tactical-100">
                                  {tiger.bbox[2]?.toFixed(0)}
                                </span>
                              </div>
                              <div>
                                <span className="text-tactical-500">Y2:</span>{' '}
                                <span className="text-tactical-900 dark:text-tactical-100">
                                  {tiger.bbox[3]?.toFixed(0)}
                                </span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-12">
                  <EyeIcon className="w-16 h-16 mx-auto text-tactical-300 dark:text-tactical-600 mb-4" />
                  <h4 className="text-lg font-medium text-tactical-900 dark:text-tactical-100 mb-2">
                    No Tigers Detected
                  </h4>
                  <p className="text-tactical-600 dark:text-tactical-400">
                    No tiger subjects were detected in this image
                  </p>
                </div>
              )}
            </Card>
          </div>
        )}

        {/* Matching Tab */}
        {activeTab === 'matching' && (
          <div className="space-y-6">
            {topMatches.length > 0 ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100">
                    Top Matches ({topMatches.length})
                  </h3>
                </div>
                {topMatches.map((match: TopMatch, index: number) => (
                  <Investigation2MatchCard
                    key={`${match.tiger_id}-${index}`}
                    match={{
                      tiger_id: match.tiger_id,
                      tiger_name: match.tiger_name || `Tiger ${match.tiger_id}`,
                      similarity: match.similarity * 100,
                      model: match.model,
                      database_image: match.image_path || '/placeholder-tiger.png',
                      facility: {
                        name: match.facility_name || 'Unknown Facility',
                        location: match.facility_location || 'Unknown Location',
                        coordinates: match.facility_coordinates
                      }
                    }}
                  />
                ))}
              </div>
            ) : (
              <Card variant="default" padding="lg">
                <div className="text-center py-12">
                  <FingerPrintIcon className="w-16 h-16 mx-auto text-tactical-300 dark:text-tactical-600 mb-4" />
                  <h4 className="text-lg font-medium text-tactical-900 dark:text-tactical-100 mb-2">
                    No Matches Found
                  </h4>
                  <p className="text-tactical-600 dark:text-tactical-400">
                    No matching tigers were found in the reference database
                  </p>
                </div>
              </Card>
            )}
          </div>
        )}

        {/* Verification Tab */}
        {activeTab === 'verification' && (
          <div className="space-y-6">
            {/* Verification Alert */}
            {verificationDisagreement && (
              <div className="alert-banner alert-banner-warning">
                <ExclamationTriangleIcon className="w-6 h-6 text-amber-600 dark:text-amber-400 flex-shrink-0" />
                <div className="flex-1">
                  <h4 className="font-semibold text-amber-800 dark:text-amber-200">
                    Verification Disagreement
                  </h4>
                  <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                    The geometric verification results disagree with the ReID model rankings.
                    Manual review is recommended.
                  </p>
                </div>
                <button
                  onClick={() => setShowComparisonModal(true)}
                  className="btn-secondary text-sm"
                >
                  Compare Rankings
                </button>
              </div>
            )}

            {/* Verification Method Card */}
            <Card variant="match" padding="lg">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 rounded-xl bg-blue-100 dark:bg-blue-900/30">
                  <ShieldCheckIcon className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100">
                    MatchAnything Geometric Verification
                  </h3>
                  <p className="text-sm text-tactical-600 dark:text-tactical-400">
                    Keypoint-based verification using ELOFTR for robust stripe pattern matching
                  </p>
                </div>
              </div>

              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 mb-4">
                <h4 className="font-medium text-blue-800 dark:text-blue-200 mb-2">How It Works</h4>
                <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1.5">
                  <li className="flex items-start gap-2">
                    <span className="text-blue-400 mt-1">1.</span>
                    <span>Extracts keypoints from query and gallery images</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-400 mt-1">2.</span>
                    <span>Matches keypoints geometrically (not just by embedding similarity)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-400 mt-1">3.</span>
                    <span>Counts reliable matches to verify stripe pattern alignment</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-400 mt-1">4.</span>
                    <span>Combines with ReID scores using adaptive weighting</span>
                  </li>
                </ul>
              </div>

              <Badge variant={verificationApplied ? 'success' : 'default'}>
                {verificationApplied ? 'Verification Applied' : 'Verification Not Applied'}
              </Badge>
            </Card>

            {/* Verified Candidates */}
            {verifiedCandidates.length > 0 ? (
              <Card variant="default" padding="lg">
                <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-4">
                  Verified Candidates
                </h3>
                <div className="space-y-4">
                  {verifiedCandidates.map((candidate, index) => {
                    const combinedScore = candidate.combined_score || 0
                    const level = getConfidenceLevel(combinedScore)
                    const colors = getConfidenceColors(level)

                    return (
                      <div
                        key={`${candidate.tiger_id}-${index}`}
                        className={cn(
                          'border rounded-xl p-4',
                          candidate.verification_status === 'high_confidence'
                            ? 'border-emerald-300 bg-emerald-50/50 dark:border-emerald-700 dark:bg-emerald-900/20'
                            : candidate.verification_status === 'verified'
                            ? 'border-blue-200 bg-blue-50/50 dark:border-blue-700 dark:bg-blue-900/20'
                            : candidate.verification_status === 'low_confidence'
                            ? 'border-amber-200 bg-amber-50/50 dark:border-amber-700 dark:bg-amber-900/20'
                            : 'border-tactical-200 dark:border-tactical-700'
                        )}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-3">
                              <span className={cn(
                                'flex items-center justify-center w-8 h-8 rounded-full',
                                'text-sm font-bold',
                                'bg-tactical-200 text-tactical-600 dark:bg-tactical-700 dark:text-tactical-400'
                              )}>
                                #{index + 1}
                              </span>
                              <span className="font-semibold text-tactical-900 dark:text-tactical-100">
                                {candidate.tiger_name || `Tiger ${candidate.tiger_id}`}
                              </span>
                              <Badge
                                variant={
                                  candidate.verification_status === 'high_confidence' ? 'success' :
                                  candidate.verification_status === 'verified' ? 'info' :
                                  candidate.verification_status === 'low_confidence' ? 'warning' :
                                  candidate.verification_status === 'error' ? 'danger' : 'default'
                                }
                                size="sm"
                              >
                                {candidate.verification_status?.replace('_', ' ') || 'unknown'}
                              </Badge>
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/30 rounded-lg">
                                <span className="text-xs text-purple-600 dark:text-purple-400 block mb-1">
                                  Combined Score
                                </span>
                                <span className="text-xl font-bold text-purple-700 dark:text-purple-300">
                                  {toPercentage(candidate.combined_score || 0)}
                                </span>
                              </div>
                              <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
                                <span className="text-xs text-blue-600 dark:text-blue-400 block mb-1">
                                  ReID Score
                                </span>
                                <span className="text-xl font-bold text-blue-700 dark:text-blue-300">
                                  {toPercentage(candidate.weighted_score || candidate.similarity || 0)}
                                </span>
                              </div>
                              <div className="text-center p-3 bg-emerald-50 dark:bg-emerald-900/30 rounded-lg">
                                <span className="text-xs text-emerald-600 dark:text-emerald-400 block mb-1">
                                  Keypoint Matches
                                </span>
                                <span className="text-xl font-bold text-emerald-700 dark:text-emerald-300">
                                  {candidate.num_matches || 0}
                                </span>
                              </div>
                              <div className="text-center p-3 bg-orange-50 dark:bg-orange-900/30 rounded-lg">
                                <span className="text-xs text-orange-600 dark:text-orange-400 block mb-1">
                                  Match Score
                                </span>
                                <span className="text-xl font-bold text-orange-700 dark:text-orange-300">
                                  {toPercentage(candidate.normalized_match_score || 0)}
                                </span>
                              </div>
                            </div>

                            {/* Weight breakdown bar */}
                            <div className="mt-4">
                              <div className="flex items-center gap-2 text-xs text-tactical-500 mb-1">
                                <span>Score Breakdown</span>
                              </div>
                              <div className="h-2.5 bg-tactical-200 dark:bg-tactical-700 rounded-full overflow-hidden flex">
                                <div
                                  className="bg-blue-500 h-full"
                                  style={{ width: `${(candidate.reid_weight_used || 0.6) * 100}%` }}
                                  title="ReID contribution"
                                />
                                <div
                                  className="bg-orange-500 h-full"
                                  style={{ width: `${(candidate.match_weight_used || 0.4) * 100}%` }}
                                  title="Match contribution"
                                />
                              </div>
                              <div className="flex justify-between text-xs text-tactical-500 mt-1">
                                <span className="text-blue-600 dark:text-blue-400">
                                  ReID ({((candidate.reid_weight_used || 0.6) * 100).toFixed(0)}%)
                                </span>
                                <span className="text-orange-600 dark:text-orange-400">
                                  Geometric ({((candidate.match_weight_used || 0.4) * 100).toFixed(0)}%)
                                </span>
                              </div>
                            </div>

                            {candidate.verification_error && (
                              <div className="mt-3 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30 rounded-lg p-2">
                                Error: {candidate.verification_error}
                              </div>
                            )}
                          </div>

                          <div className="text-right ml-6">
                            <div className={cn('text-3xl font-bold tabular-nums', colors.text)}>
                              {toPercentage(candidate.combined_score || 0, 0)}
                            </div>
                            <div className="text-xs text-tactical-500">combined</div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </Card>
            ) : (
              <Card variant="default" padding="lg">
                <div className="text-center py-12">
                  <ShieldCheckIcon className="w-16 h-16 mx-auto text-tactical-300 dark:text-tactical-600 mb-4" />
                  <h4 className="text-lg font-medium text-tactical-900 dark:text-tactical-100 mb-2">
                    No Verification Data
                  </h4>
                  <p className="text-tactical-600 dark:text-tactical-400">
                    {verificationApplied
                      ? 'Verification was attempted but no candidates were verified.'
                      : 'Geometric verification was not applied to this investigation.'}
                  </p>
                </div>
              </Card>
            )}
          </div>
        )}

        {/* Methodology Tab */}
        {activeTab === 'methodology' && (
          <Card variant="default" padding="lg">
            <Investigation2Methodology
              steps={report.methodology_steps || reasoningChain?.steps || []}
              reasoningChain={reasoningChain}
              imageQuality={imageQuality}
            />
          </Card>
        )}

        {/* Location Tab */}
        {activeTab === 'location' && (
          <Card variant="default" padding="lg">
            <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-4">
              Tiger Location Analysis
            </h3>
            <Investigation2Map locations={[]} />
          </Card>
        )}

        {/* Citations Tab */}
        {activeTab === 'citations' && (
          <Card variant="default" padding="lg">
            <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-4">
              Web Search Citations
            </h3>
            <Investigation2Citations citations={reverseSearchResults.citations || []} />
          </Card>
        )}

        {/* External Intel Tab */}
        {activeTab === 'external' && (
          <div className="space-y-6">
            {reverseSearchResults.providers && (
              <>
                {/* Tavily Results */}
                {reverseSearchResults.providers.tavily && (
                  <Card variant="default" padding="lg">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
                          <GlobeAltIcon className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
                        </div>
                        <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100">
                          Tavily Search Results
                        </h3>
                      </div>
                      <Badge variant="success">
                        {reverseSearchResults.providers.tavily.count || 0} results
                      </Badge>
                    </div>

                    {reverseSearchResults.providers.tavily.results &&
                    reverseSearchResults.providers.tavily.results.length > 0 ? (
                      <div className="space-y-3">
                        {reverseSearchResults.providers.tavily.results.map((result: TavilySearchResult, idx: number) => (
                          <a
                            key={idx}
                            href={result.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={cn(
                              'block border rounded-xl p-4 transition-all',
                              'border-tactical-200 dark:border-tactical-700',
                              'hover:border-blue-300 dark:hover:border-blue-600',
                              'hover:shadow-match'
                            )}
                          >
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1 min-w-0">
                                <h4 className="font-medium text-blue-600 dark:text-blue-400 hover:underline">
                                  {result.title}
                                </h4>
                                <p className="text-sm text-tactical-600 dark:text-tactical-400 mt-1 line-clamp-2">
                                  {result.content}
                                </p>
                                <p className="text-xs text-tactical-400 mt-2 truncate">
                                  {result.url}
                                </p>
                              </div>
                              {result.score && (
                                <Badge variant="info" size="sm">
                                  {(result.score * 100).toFixed(0)}% relevance
                                </Badge>
                              )}
                            </div>
                          </a>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-tactical-500">
                        No Tavily results available
                      </div>
                    )}

                    {/* Tavily Images */}
                    {reverseSearchResults.providers.tavily.images &&
                    reverseSearchResults.providers.tavily.images.length > 0 && (
                      <div className="mt-6 pt-6 border-t border-tactical-200 dark:border-tactical-700">
                        <h4 className="font-medium text-tactical-900 dark:text-tactical-100 mb-3">
                          Related Images
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                          {reverseSearchResults.providers.tavily.images.map((imgUrl: string, idx: number) => (
                            <a
                              key={idx}
                              href={imgUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={cn(
                                'block aspect-square rounded-xl overflow-hidden',
                                'border border-tactical-200 dark:border-tactical-700',
                                'hover:ring-2 hover:ring-blue-400 transition-all'
                              )}
                            >
                              <img
                                src={imgUrl}
                                alt={`Related tiger ${idx + 1}`}
                                className="w-full h-full object-cover"
                              />
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </Card>
                )}

                {/* Facility Crawl Results */}
                {reverseSearchResults.providers.facilities && (
                  <Card variant="default" padding="lg">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100">
                        Facility Website Crawls
                      </h3>
                      <Badge variant="primary">
                        {reverseSearchResults.providers.facilities.crawled || 0} crawled
                      </Badge>
                    </div>

                    {reverseSearchResults.providers.facilities.results &&
                    reverseSearchResults.providers.facilities.results.length > 0 ? (
                      <div className="space-y-3">
                        {reverseSearchResults.providers.facilities.results.map((facility: FacilityCrawlResult, idx: number) => (
                          <div
                            key={idx}
                            className={cn(
                              'border rounded-xl p-4',
                              facility.success
                                ? 'border-tactical-200 dark:border-tactical-700'
                                : 'border-red-200 bg-red-50/50 dark:border-red-800 dark:bg-red-900/20'
                            )}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <h4 className="font-medium text-tactical-900 dark:text-tactical-100">
                                    {facility.facility}
                                  </h4>
                                  {facility.has_tiger_content && (
                                    <Badge variant="success" size="sm">Tiger Content Found</Badge>
                                  )}
                                  {facility.success ? (
                                    <CheckCircleIcon className="w-5 h-5 text-emerald-500" />
                                  ) : (
                                    <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
                                  )}
                                </div>
                                <a
                                  href={facility.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-sm text-blue-600 dark:text-blue-400 hover:underline mt-1 block"
                                >
                                  {facility.url}
                                </a>
                                {facility.content_preview && (
                                  <p className="text-sm text-tactical-600 dark:text-tactical-400 mt-2">
                                    {facility.content_preview}
                                  </p>
                                )}
                                {facility.links_found !== undefined && facility.links_found > 0 && (
                                  <p className="text-xs text-tactical-500 mt-2">
                                    Found {facility.links_found} links
                                  </p>
                                )}
                                {facility.error && (
                                  <p className="text-xs text-red-600 dark:text-red-400 mt-2">
                                    Error: {facility.error}
                                  </p>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-tactical-500">
                        No facilities crawled
                      </div>
                    )}
                  </Card>
                )}

                {/* Google/SerpApi Results */}
                {reverseSearchResults.providers.google && (
                  <Card variant="default" padding="lg">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100">
                        Google Lens / SerpApi
                      </h3>
                      <Badge variant="info">
                        {reverseSearchResults.providers.google.count || 0} results
                      </Badge>
                    </div>

                    {reverseSearchResults.providers.google.error ? (
                      <div className="alert-banner alert-banner-warning">
                        <ExclamationTriangleIcon className="w-5 h-5 text-amber-600 flex-shrink-0" />
                        <div>
                          <p className="font-medium text-amber-900 dark:text-amber-100">
                            Service Unavailable
                          </p>
                          <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                            {reverseSearchResults.providers.google.note ||
                            reverseSearchResults.providers.google.error}
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-tactical-500">
                        No Google Lens results
                      </div>
                    )}
                  </Card>
                )}
              </>
            )}
          </div>
        )}

        {/* Report Tab */}
        {activeTab === 'report' && (
          <Card variant="elevated" padding="lg">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-tactical-900 dark:text-tactical-100">
                Investigation Report
              </h3>
              <div className="flex gap-2">
                <Badge variant="primary">Claude AI Generated</Badge>
                {getConfidenceBadge(confidence)}
              </div>
            </div>

            {report.summary ? (
              <div className="prose prose-tactical dark:prose-invert max-w-none">
                <MarkdownContent content={report.summary} />
              </div>
            ) : (
              <div className="text-center py-12">
                <DocumentTextIcon className="w-16 h-16 mx-auto text-tactical-300 dark:text-tactical-600 mb-4" />
                <h4 className="text-lg font-medium text-tactical-900 dark:text-tactical-100 mb-2">
                  Report Not Yet Generated
                </h4>
                <p className="text-tactical-600 dark:text-tactical-400">
                  The investigation report has not been generated yet
                </p>
              </div>
            )}
          </Card>
        )}
      </div>

      {/* No Results Message */}
      {topMatches.length === 0 && totalMatches === 0 && activeTab === 'overview' && (
        <Card variant="default" padding="lg">
          <div className="text-center py-8">
            <InformationCircleIcon className="w-16 h-16 mx-auto text-tactical-400 dark:text-tactical-500 mb-4" />
            <h3 className="text-lg font-medium text-tactical-900 dark:text-tactical-100 mb-2">
              No Matches Found
            </h3>
            <p className="text-tactical-600 dark:text-tactical-400 max-w-md mx-auto">
              No matching tigers were found in the reference database. This could indicate:
            </p>
            <ul className="text-sm text-tactical-600 dark:text-tactical-400 mt-4 space-y-1 max-w-md mx-auto text-left">
              <li className="flex items-start gap-2">
                <span className="text-tactical-400">•</span>
                <span>This is a new/unrecorded individual</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-tactical-400">•</span>
                <span>The reference database needs expansion</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-tactical-400">•</span>
                <span>Image quality or angle affects matching</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-tactical-400">•</span>
                <span>Stripe patterns are not clearly visible</span>
              </li>
            </ul>
          </div>
        </Card>
      )}

      {/* Verification Comparison Modal */}
      <VerificationComparison
        isOpen={showComparisonModal}
        onClose={() => setShowComparisonModal(false)}
        reidMatches={topMatches.map((m: TopMatch, idx: number): ReIDMatchForComparison => ({
          tiger_id: m.tiger_id,
          tiger_name: m.tiger_name,
          similarity: m.similarity,
          model: m.model,
          rank: idx + 1,
        }))}
        verifiedCandidates={verifiedCandidates}
      />
    </div>
  )
}

export default Investigation2ResultsEnhanced

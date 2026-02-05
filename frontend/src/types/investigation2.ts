/**
 * TypeScript types for Investigation 2.0 workflow.
 *
 * These types provide proper typing for the Investigation 2.0 feature,
 * replacing `any` types throughout the codebase.
 */

// ==================== Enums ====================

export type Investigation2Phase =
  | 'upload_and_parse'
  | 'reverse_image_search'
  | 'tiger_detection'
  | 'stripe_analysis'
  | 'report_generation'
  | 'complete'

export type Investigation2Status =
  | 'pending'
  | 'running'
  | 'completed'
  | 'error'
  | 'cancelled'

export type StepStatus = 'pending' | 'running' | 'completed' | 'error'

/**
 * Verification status from MatchAnything geometric verification.
 */
export type VerificationStatus =
  | 'skipped'
  | 'insufficient_matches'
  | 'low_confidence'
  | 'verified'
  | 'high_confidence'
  | 'error'

/**
 * Report audience options for Investigation 2.0.
 */
export type ReportAudience = 'law_enforcement' | 'conservation' | 'internal' | 'public'

/**
 * Image quality assessment from Image Analysis MCP.
 */
export interface ImageQuality {
  overall_score: number  // 0-1
  resolution_score: number
  blur_score: number
  stripe_visibility: number
  issues: string[]
  recommendations: string[]
}

/**
 * Enhanced reasoning step from Sequential Thinking MCP.
 */
export interface ReasoningChainStep {
  step: number
  phase: string
  action: string
  evidence: string[]
  reasoning: string
  conclusion: string
  confidence: number
  timestamp: string
}

/**
 * Full reasoning chain from Sequential Thinking MCP.
 */
export interface ReasoningChain {
  chain_id: string
  question: string
  reasoning_type: string
  steps: ReasoningChainStep[]
  status: 'active' | 'finalized' | 'abandoned'
  final_conclusion?: string
  overall_confidence?: number
}

/**
 * Deep research session data.
 */
export interface DeepResearchData {
  session_id: string
  sources_analyzed: number
  entities_found: string[]
}

// ==================== Core Types ====================

/**
 * A single step in the Investigation 2.0 workflow.
 */
export interface Investigation2Step {
  step_id: string
  step_type: Investigation2Phase
  status: StepStatus
  timestamp?: string
  result?: Investigation2StepResult
  error_message?: string
  duration_ms?: number
}

/**
 * Result data for a completed step.
 */
export interface Investigation2StepResult {
  phase: Investigation2Phase
  success: boolean
  data?: Record<string, unknown>
  message?: string
  methodology?: MethodologyEntry
}

/**
 * Entry in the methodology tracking chain.
 */
export interface MethodologyEntry {
  step: string
  action: string
  reasoning?: string
  timestamp: string
  outcome?: string
  confidence?: number
}

/**
 * Tiger match found during the investigation.
 */
export interface TigerMatch {
  tiger_id: string
  tiger_name: string
  similarity: number
  confidence: number
  model: string
  image_url?: string
  facility_name?: string
  facility_id?: string
  last_seen_location?: string
  last_seen_date?: string
}

/**
 * Verified candidate with geometric verification from MatchAnything.
 */
export interface VerifiedCandidate extends TigerMatch {
  /** Number of keypoint matches from MatchAnything */
  num_matches: number
  /** Raw match score from MatchAnything */
  match_score: number
  /** Normalized match score (0-1 via sigmoid) */
  normalized_match_score: number
  /** Combined ReID + verification score */
  combined_score: number
  /** Verification status based on thresholds */
  verification_status: VerificationStatus
  /** ReID weight used for this candidate */
  reid_weight_used?: number
  /** Match weight used for this candidate */
  match_weight_used?: number
  /** Number of gallery images tested */
  gallery_images_tested?: number
  /** Error message if verification failed */
  verification_error?: string
  /** Weighted score from ReID ensemble */
  weighted_score?: number
  /** Number of models that matched this candidate */
  models_matched?: number
}

/**
 * Evidence found during reverse image search.
 */
export interface ImageSearchEvidence {
  url: string
  title?: string
  snippet?: string
  source?: string
  relevance_score?: number
  matched_at: string
}

/**
 * Citation for display in the UI.
 * Maps to the Investigation2Citations component props.
 */
export interface Citation {
  title: string
  uri: string
  snippet: string
  relevance_score?: number
  location_mentions?: string[]
}

/**
 * Detection result from the tiger detection phase.
 */
export interface DetectionResult {
  detected: boolean
  confidence: number
  bbox?: [number, number, number, number]
  crop_path?: string
}

/**
 * Analysis result from visual analysis tools.
 */
export interface VisualAnalysisResult {
  description: string
  characteristics?: string[]
  stripe_pattern_notes?: string
  age_estimate?: string
  health_notes?: string
  behavior_notes?: string
  environment_description?: string
}

// ==================== Investigation Data ====================

/**
 * Summary of the investigation findings.
 */
export interface Investigation2Summary {
  identified: boolean
  confidence: number
  best_match?: TigerMatch
  all_matches: TigerMatch[]
  evidence_count: number
  key_findings: string[]
  recommendations: string[]
  methodology_summary?: string
  // New fields for enhanced workflow
  image_quality?: ImageQuality
  reasoning_chain?: ReasoningChain
  report_audience?: ReportAudience
  deep_research?: DeepResearchData
  // Verification fields
  verified_candidates?: VerifiedCandidate[]
  verification_applied?: boolean
  verification_disagreement?: boolean
}

/**
 * Report generated at the end of the investigation.
 */
export interface Investigation2Report {
  investigation_id: string
  title: string
  generated_at: string
  summary: Investigation2Summary
  evidence: ImageSearchEvidence[]
  matches: TigerMatch[]
  visual_analysis?: VisualAnalysisResult
  methodology: MethodologyEntry[]
  conclusions: string[]
}

/**
 * Full Investigation 2.0 response from the API.
 */
export interface Investigation2Response {
  investigation_id: string
  status: Investigation2Status
  started_at: string
  completed_at?: string
  steps: Investigation2Step[]
  summary?: Investigation2Summary
  report?: Investigation2Report
  error?: string
}

// ==================== Request/Response Types ====================

/**
 * Context provided when launching an investigation.
 */
export interface Investigation2Context {
  location?: string
  date?: string
  notes?: string
}

/**
 * Response from launching a new investigation.
 */
export interface LaunchInvestigation2Response {
  success: boolean
  investigation_id: string
  message?: string
}

/**
 * WebSocket message received during investigation.
 */
export interface Investigation2WebSocketMessage {
  event: 'phase_started' | 'phase_completed' | 'investigation_completed' | 'error'
  data: {
    phase?: Investigation2Phase
    status?: StepStatus
    result?: Investigation2StepResult
    error?: string
    timestamp: string
  }
}

// ==================== Component Props Types ====================

/**
 * Progress step data that can be returned from various phases.
 */
export interface ProgressStepData {
  tigers_detected?: number
  models_run?: number
  results_count?: number
  [key: string]: unknown
}

/**
 * Progress step for display in the UI.
 */
export interface ProgressStep {
  phase: Investigation2Phase | string
  status: StepStatus
  timestamp?: string
  data?: ProgressStepData | Investigation2StepResult
}

/**
 * Props for the Investigation2Upload component.
 */
export interface Investigation2UploadProps {
  image: File | null
  imagePreview: string | null
  context: Investigation2Context
  onImageUpload: (file: File) => void
  onContextChange: (field: keyof Investigation2Context, value: string) => void
  disabled?: boolean
}

/**
 * Props for the Investigation2Progress component.
 */
export interface Investigation2ProgressProps {
  steps: ProgressStep[]
  investigationId: string | null
}

/**
 * Props for the Investigation2Results component.
 */
export interface Investigation2ResultsProps {
  investigation: Investigation2Response
  fullWidth?: boolean
}

/**
 * Facility info for match cards.
 */
export interface MatchFacilityInfo {
  name: string
  location: string
  coordinates?: { lat: number; lon: number }
}

/**
 * Confidence breakdown for detailed match analysis.
 */
export interface MatchConfidenceBreakdown {
  stripe_similarity: number
  visual_features: number
  historical_context: number
}

/**
 * Model score entry for ensemble visualization.
 */
export interface ModelScoreEntry {
  model: string
  score: number
  matched: boolean
}

/**
 * Extended match type for match card component with UI-specific fields.
 */
export interface MatchCardData {
  tiger_id: string
  tiger_name: string
  similarity: number
  model: string
  uploaded_image_crop?: string
  database_image: string
  facility: MatchFacilityInfo
  confidence_breakdown?: MatchConfidenceBreakdown
  // Verification fields
  verification_status?: VerificationStatus
  num_matches?: number
  normalized_match_score?: number
  combined_score?: number
  reid_weight_used?: number
  match_weight_used?: number
  gallery_images_tested?: number
  verification_error?: string
  // Ensemble fields
  models_matched?: number
  total_models?: number
  model_scores?: ModelScoreEntry[]
}

/**
 * Props for the Investigation2MatchCard component.
 */
export interface Investigation2MatchCardProps {
  match: MatchCardData
  rank?: number
  showEnsemble?: boolean
  onClick?: () => void
}

// ==================== UI Data Types ====================

/**
 * Tavily search result item.
 */
export interface TavilySearchResult {
  url: string
  title: string
  content: string
  score?: number
}

/**
 * Tavily search provider data.
 */
export interface TavilySearchProvider {
  count: number
  results?: TavilySearchResult[]
  images?: string[]
}

/**
 * Facility crawl result.
 */
export interface FacilityCrawlResult {
  facility: string
  url: string
  success: boolean
  has_tiger_content?: boolean
  content_preview?: string
  links_found?: number
  error?: string
}

/**
 * Facilities search provider data.
 */
export interface FacilitiesSearchProvider {
  crawled: number
  results?: FacilityCrawlResult[]
}

/**
 * Google/SerpApi search provider data.
 */
export interface GoogleSearchProvider {
  count: number
  results?: unknown[]
  error?: string
  note?: string
}

/**
 * Reverse search providers collection.
 */
export interface ReverseSearchProviders {
  tavily?: TavilySearchProvider
  facilities?: FacilitiesSearchProvider
  google?: GoogleSearchProvider
}

/**
 * Reverse image search results.
 */
export interface ReverseSearchResults {
  total_results?: number
  citations?: Citation[]
  providers?: ReverseSearchProviders
}

/**
 * Detected tiger from MegaDetector.
 */
export interface DetectedTiger {
  confidence: number
  category?: string
  bbox?: [number, number, number, number]
}

/**
 * Top match from stripe analysis.
 */
export interface TopMatch {
  tiger_id: string
  tiger_name?: string
  similarity: number
  model: string
  image_path?: string
  facility_name?: string
  facility_location?: string
  facility_coordinates?: { lat: number; lon: number }
}

/**
 * Model info used in analysis.
 */
export interface ModelUsedInfo {
  name?: string
  model?: string
  similarity?: number
  score?: number
  weight?: number
}

/**
 * Report data structure.
 */
export interface Investigation2ReportData {
  top_matches?: TopMatch[]
  models_used?: (string | ModelUsedInfo)[]
  detection_count?: number
  total_matches?: number
  confidence?: string
  methodology_steps?: ReasoningChainStep[]
  summary?: string
}

/**
 * Extended summary data for UI rendering.
 */
export interface Investigation2SummaryExtended extends Investigation2Summary {
  report?: Investigation2ReportData
  reverse_search_results?: ReverseSearchResults
  detected_tigers?: DetectedTiger[]
}

/**
 * ReID match for comparison modal.
 */
export interface ReIDMatchForComparison {
  tiger_id: string
  tiger_name?: string
  similarity: number
  model: string
  rank: number
}

// ==================== Utility Types ====================

/**
 * Type guard to check if a step is completed.
 */
export function isStepCompleted(step: Investigation2Step): boolean {
  return step.status === 'completed'
}

/**
 * Type guard to check if investigation is complete.
 */
export function isInvestigationComplete(
  response: Investigation2Response
): boolean {
  return (
    response.status === 'completed' ||
    response.steps.some(
      (s) => s.step_type === 'complete' && s.status === 'completed'
    )
  )
}

/**
 * Get display name for a phase.
 */
export function getPhaseDisplayName(phase: Investigation2Phase): string {
  const names: Record<Investigation2Phase, string> = {
    upload_and_parse: 'Upload & Parse',
    reverse_image_search: 'Reverse Image Search',
    tiger_detection: 'Tiger Detection',
    stripe_analysis: 'Stripe Analysis',
    report_generation: 'Report Generation',
    complete: 'Complete',
  }
  return names[phase] || phase
}

/**
 * Get status color class for a step status.
 */
export function getStatusColor(status: StepStatus): string {
  const colors: Record<StepStatus, string> = {
    pending: 'text-gray-400',
    running: 'text-blue-500',
    completed: 'text-green-500',
    error: 'text-red-500',
  }
  return colors[status] || 'text-gray-400'
}

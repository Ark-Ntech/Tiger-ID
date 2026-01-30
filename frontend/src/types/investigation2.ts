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
  | 'omnivinci_comparison'
  | 'report_generation'
  | 'complete'

export type Investigation2Status =
  | 'pending'
  | 'running'
  | 'completed'
  | 'error'
  | 'cancelled'

export type StepStatus = 'pending' | 'running' | 'completed' | 'error'

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
 * Detection result from the tiger detection phase.
 */
export interface DetectionResult {
  detected: boolean
  confidence: number
  bbox?: [number, number, number, number]
  crop_path?: string
}

/**
 * Analysis result from OmniVinci or similar visual analysis.
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
 * Progress step for display in the UI.
 */
export interface ProgressStep {
  phase: Investigation2Phase
  status: StepStatus
  timestamp?: string
  data?: Investigation2StepResult
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
 * Props for the Investigation2MatchCard component.
 */
export interface Investigation2MatchCardProps {
  match: TigerMatch
  rank: number
  onClick?: () => void
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
    omnivinci_comparison: 'Visual Comparison',
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

/**
 * Shared activity event types for Investigation 2.0 real-time feeds.
 *
 * This is the canonical source of truth for all activity event types.
 * Used by Investigation2Context, LiveActivityFeed, and progress components.
 */

/**
 * All possible activity event types.
 */
export type ActivityEventType =
  | 'phase_started'
  | 'phase_completed'
  | 'model_started'
  | 'model_completed'
  | 'subagent_spawned'
  | 'subagent_completed'
  | 'match_found'
  | 'error'
  | 'info'
  | 'reasoning_step'
  | 'match_preview'
  | 'image_quality'

/**
 * Activity event for the investigation timeline.
 */
export interface ActivityEvent {
  id: string
  timestamp: string
  type: ActivityEventType
  message: string
  phase?: string
  model?: string
  metadata?: Record<string, any>
}

/**
 * Reasoning step received via WebSocket during investigation.
 */
export interface ReasoningStepEvent {
  step: number
  phase: string
  conclusion: string
  confidence: number
  evidence_count: number
  timestamp: string
}

/**
 * Match preview received via WebSocket during stripe analysis.
 */
export interface MatchPreviewEvent {
  model: string
  tiger_id: string
  tiger_name: string
  similarity: number
  image_path?: string
  facility_name?: string
  timestamp: string
}

/**
 * Image quality assessment received via WebSocket.
 */
export interface ImageQualityEvent {
  overall_score: number
  issues: string[]
  timestamp: string
}

/**
 * Types for Verification Queue API
 *
 * These types match the backend schemas in verification_routes.py
 */

// Entity type for verification items
export type VerificationEntityType = 'tiger' | 'facility'

// Verification status options
export type VerificationQueueStatus = 'pending' | 'approved' | 'rejected' | 'in_review'

// Priority levels
export type VerificationPriority = 'critical' | 'high' | 'medium' | 'low'

// Source of verification item
export type VerificationSource = 'auto_discovery' | 'user_upload'

/**
 * Entity details for tiger in verification queue
 */
export interface TigerEntityDetails {
  name?: string
  alias?: string
  status?: string
  last_seen_location?: string
  last_seen_date?: string
}

/**
 * Entity details for facility in verification queue
 */
export interface FacilityEntityDetails {
  exhibitor_name?: string
  usda_license?: string
  city?: string
  state?: string
  tiger_count?: number
  website?: string
}

/**
 * Response schema for a verification queue item (list view)
 */
export interface VerificationQueueItem {
  queue_id: string
  entity_type: VerificationEntityType
  entity_id: string
  priority: VerificationPriority
  status: VerificationQueueStatus
  requires_human_review: boolean
  source?: VerificationSource
  investigation_id?: string
  assigned_to?: string
  reviewed_by?: string
  review_notes?: string
  created_at?: string
  reviewed_at?: string
  entity_name?: string
  entity_details?: TigerEntityDetails | FacilityEntityDetails
}

/**
 * Full tiger entity details for single item view
 */
export interface TigerEntityFull {
  type: 'tiger'
  tiger_id: string
  name?: string
  alias?: string
  status?: string
  last_seen_location?: string
  last_seen_date?: string
  notes?: string
  tags?: string[]
  is_reference?: boolean
  discovery_confidence?: number
  created_at?: string
  facility?: {
    facility_id: string
    exhibitor_name?: string
    city?: string
    state?: string
  }
}

/**
 * Full facility entity details for single item view
 */
export interface FacilityEntityFull {
  type: 'facility'
  facility_id: string
  exhibitor_name?: string
  usda_license?: string
  city?: string
  state?: string
  address?: string
  tiger_count?: number
  tiger_capacity?: number
  website?: string
  accreditation_status?: string
  last_inspection_date?: string
  last_crawled_at?: string
  is_reference_facility?: boolean
  data_source?: string
  created_at?: string
}

/**
 * Investigation context for verification item
 */
export interface VerificationInvestigationContext {
  investigation_id: string
  title?: string
  description?: string
  status?: string
  priority?: string
  created_at?: string
  completed_at?: string
}

/**
 * Full verification queue item response (single item view)
 */
export interface VerificationQueueItemFull {
  queue_id: string
  entity_type: VerificationEntityType
  entity_id: string
  priority: VerificationPriority
  status: VerificationQueueStatus
  requires_human_review: boolean
  source?: VerificationSource
  investigation_id?: string
  assigned_to?: string
  reviewed_by?: string
  review_notes?: string
  created_at?: string
  reviewed_at?: string
  entity?: TigerEntityFull | FacilityEntityFull
  investigation?: VerificationInvestigationContext
}

/**
 * Request parameters for getting verification queue
 */
export interface GetVerificationQueueParams {
  entity_type?: VerificationEntityType
  source?: VerificationSource
  priority?: VerificationPriority
  status?: VerificationQueueStatus
  limit?: number
  offset?: number
}

/**
 * Request schema for updating verification status
 */
export interface VerificationStatusUpdate {
  status: 'approved' | 'rejected' | 'in_review'
  review_notes?: string
}

/**
 * Response after updating verification status
 */
export interface VerificationStatusUpdateResponse {
  queue_id: string
  status: VerificationQueueStatus
  reviewed_by: string
  reviewed_at: string
  review_notes?: string
}

/**
 * Hourly activity breakdown
 */
export interface HourlyActivity {
  hour: string
  approved: number
  rejected: number
}

/**
 * Response schema for verification statistics
 */
export interface VerificationStatsResponse {
  by_status: Record<VerificationQueueStatus, number>
  by_source: Record<string, number>
  by_priority: Record<VerificationPriority, number>
  by_entity_type: Record<VerificationEntityType, number>
  recent_activity: {
    approved_24h: number
    rejected_24h: number
    hourly_breakdown: HourlyActivity[]
  }
  total_pending: number
  total_approved_24h: number
  total_rejected_24h: number
  total_items: number
  timestamp: string
}

/**
 * Paginated response for verification queue
 */
export interface VerificationQueuePaginatedResponse {
  data: VerificationQueueItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

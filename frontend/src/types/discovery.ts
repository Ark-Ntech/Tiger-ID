/**
 * Types for Discovery API
 *
 * These types match the backend schemas in discovery_routes.py
 */

// Time range filter options
export type TimeRange = '24h' | '7d' | '30d'

// Auto-investigation status filter options
export type AutoInvestigationStatusFilter = 'all' | 'completed' | 'failed' | 'pending' | 'active'

/**
 * Discovery scheduler status response
 */
export interface DiscoveryStatusResponse {
  status: 'running' | 'stopped'
  enabled: boolean
  total_crawls: number
  last_crawl_time?: string
  facilities_crawled?: number
  images_processed?: number
}

/**
 * Response after starting/stopping scheduler
 */
export interface SchedulerActionResponse {
  status: 'started' | 'stopped' | 'already_running' | 'not_running'
  message: string
  tools_used?: string[]
}

/**
 * Single facility in crawl queue
 */
export interface CrawlQueueFacility {
  facility_id: string
  exhibitor_name?: string
  state?: string
  city?: string
  tiger_count?: number
  website?: string
  has_social_media: boolean
  last_crawled_at?: string
}

/**
 * Crawl queue response
 */
export interface CrawlQueueResponse {
  count: number
  days_since_crawl: number
  facilities: CrawlQueueFacility[]
}

/**
 * Single crawl history record
 */
export interface CrawlHistoryRecord {
  crawl_id: string
  facility_id?: string
  source_url?: string
  status: string
  images_found?: number
  tigers_identified?: number
  crawled_at?: string
  completed_at?: string
  duration_ms?: number
  error?: string
}

/**
 * Crawl history response
 */
export interface CrawlHistoryResponse {
  count: number
  crawls: CrawlHistoryRecord[]
}

/**
 * Discovery stats - facilities section
 */
export interface DiscoveryFacilityStats {
  total: number
  reference: number
  crawled: number
  with_website: number
  with_social_media: number
  pending_crawl: number
}

/**
 * Discovery stats - tigers section
 */
export interface DiscoveryTigerStats {
  total: number
  discovered: number
  reference: number
  real: number
}

/**
 * Discovery stats - images section
 */
export interface DiscoveryImageStats {
  total: number
  discovered: number
  verified: number
}

/**
 * Discovery stats - crawls section
 */
export interface DiscoveryCrawlStats {
  total: number
  successful: number
  recent_7_days: number
}

/**
 * Discovery stats - scheduler section
 */
export interface DiscoverySchedulerStats {
  running: boolean
  enabled: boolean
  total_crawls: number
  last_crawl?: string
}

/**
 * Full discovery statistics response
 */
export interface DiscoveryStatsResponse {
  facilities: DiscoveryFacilityStats
  tigers: DiscoveryTigerStats
  images: DiscoveryImageStats
  crawls: DiscoveryCrawlStats
  scheduler: DiscoverySchedulerStats
  tools_used: string[]
}

/**
 * Request params for auto-investigation stats
 */
export interface AutoInvestigationStatsParams {
  time_range?: TimeRange
}

/**
 * Auto-investigation statistics response
 */
export interface AutoInvestigationStatsResponse {
  time_range: TimeRange
  total_triggered: number
  completed: number
  failed: number
  pending: number
  avg_duration_ms: number
  cutoff_time: string
}

/**
 * Request params for recent auto-investigations
 */
export interface RecentAutoInvestigationsParams {
  limit?: number
  status?: AutoInvestigationStatusFilter
}

/**
 * Single auto-investigation record
 */
export interface AutoInvestigationRecord {
  investigation_id: string
  title?: string
  status: string
  priority?: string
  facility_name?: string
  tiger_name?: string
  created_at?: string
  started_at?: string
  completed_at?: string
}

/**
 * Recent auto-investigations response
 */
export interface RecentAutoInvestigationsResponse {
  count: number
  limit: number
  status_filter: string
  investigations: AutoInvestigationRecord[]
}

/**
 * Runtime stats from ImagePipelineService
 */
export interface PipelineRuntimeStats {
  images_processed: number
  duplicates_skipped: number
  quality_rejected: number
  no_tiger_detected: number
  embedding_failures: number
  new_tigers: number
  existing_tigers: number
  auto_investigations_triggered: number
}

/**
 * Database stats for pipeline
 */
export interface PipelineDatabaseStats {
  total_discovered_images: number
  images_with_content_hash: number
  duplicates_detected: number
  auto_investigations_triggered: number
  verified_discovered_images: number
}

/**
 * Pipeline statistics response
 */
export interface PipelineStatsResponse {
  runtime_stats: PipelineRuntimeStats
  database_stats: PipelineDatabaseStats
  tools_used: string[]
}

/**
 * Deep research response
 */
export interface DeepResearchResponse {
  facility_id: string
  facility_name: string
  research_session_id: string
  queries_executed: number
  results_found: number
  synthesis?: string
  tool_used: string
}

/**
 * Crawl trigger response
 */
export interface CrawlTriggerResponse {
  status: 'crawl_started' | 'completed' | 'failed'
  message: string
  method?: string
  tools_used?: string[]
  images_found?: number
  tigers_identified?: number
}

/**
 * Request params for crawl queue
 */
export interface CrawlQueueParams {
  limit?: number
  days_old?: number
}

/**
 * Request params for crawl history
 */
export interface CrawlHistoryParams {
  limit?: number
  facility_id?: string
  status?: string
}

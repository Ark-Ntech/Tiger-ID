// API Response types
export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// User types
export interface User {
  id: string
  username: string
  email: string
  full_name?: string
  role: 'admin' | 'investigator' | 'analyst' | 'viewer'
  created_at: string
  updated_at: string
}

export interface LoginCredentials {
  username: string
  password: string
  remember_me?: boolean
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
  expires_in: number
}

// Investigation types
export interface Investigation {
  id: string
  title: string
  description: string
  status: 'draft' | 'in_progress' | 'completed' | 'archived'
  priority: 'low' | 'medium' | 'high' | 'critical'
  created_by: string
  assigned_to?: string[]
  created_at: string
  updated_at: string
  completed_at?: string
  tags?: string[]
  metadata?: Record<string, any>
  related_tigers?: string[]
}

export interface InvestigationInput {
  title: string
  description: string
  priority?: 'low' | 'medium' | 'high' | 'critical'
  tags?: string[]
  files?: File[]
  notes?: string
}

// Tiger types
export interface Tiger {
  id: string
  name?: string
  estimated_age?: number
  sex?: 'male' | 'female' | 'unknown'
  first_seen: string
  last_seen: string
  confidence_score: number
  stripe_signature?: string
  images: TigerImage[]
  locations: Location[]
  metadata?: Record<string, any>
}

export interface TigerImage {
  id: string
  url: string
  thumbnail_url?: string
  uploaded_at: string
  source?: string
  metadata?: Record<string, any>
}

export interface TigerIdentificationRequest {
  image: File | string
  confidence_threshold?: number
}

export interface TigerIdentificationResult {
  identified: boolean
  tiger_id?: string
  tiger_name?: string
  similarity?: number
  confidence: number
  message?: string
  requires_verification?: boolean
  model?: string
  matches?: TigerMatch[]
  // For multi-model results
  models?: Record<string, any>
  best_match?: {
    tiger_id: string
    tiger_name: string
    confidence: number
    model: string
  }
  all_matches?: Array<{
    tiger_id: string
    tiger_name: string
    confidence: number
    model: string
  }>
  is_new?: boolean
}

export interface TigerMatch {
  tiger_id: string
  confidence: number
  tiger: Tiger
}

// Facility types
export interface Facility {
  id: string
  name: string
  exhibitor_name?: string
  license_number?: string
  usda_license?: string
  facility_type: string
  address: string
  city: string
  state: string
  country: string
  latitude?: number
  longitude?: number
  status: 'active' | 'inactive' | 'suspended'
  verified: boolean
  tiger_count?: number
  tiger_capacity?: number
  accreditation_status?: string
  ir_date?: string
  last_inspection_date?: string
  website?: string
  social_media_links?: Record<string, string>
  social_media?: SocialMediaAccount[]
  last_inspection?: string
  is_reference_facility?: boolean
  data_source?: string
  reference_metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface SocialMediaAccount {
  platform: 'facebook' | 'instagram' | 'twitter' | 'youtube' | 'tiktok'
  username: string
  url: string
  followers?: number
  last_crawled?: string
}

// Evidence types
export interface Evidence {
  id: string
  investigation_id: string
  type: 'image' | 'document' | 'video' | 'audio' | 'text' | 'url'
  title: string
  description?: string
  file_url?: string
  content?: string
  source?: string
  collected_at: string
  created_by: string
  verified: boolean
  tags?: string[]
  metadata?: Record<string, any>
}

// Event types
export interface Event {
  id: string
  event_type: string
  investigation_id?: string
  user_id?: string
  timestamp: string
  data: Record<string, any>
  metadata?: Record<string, any>
}

// Agent types
export interface AgentMessage {
  id: string
  agent_type: 'research' | 'analysis' | 'validation' | 'reporting'
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  metadata?: Record<string, any>
}

export interface AgentActivity {
  agent_type: string
  status: 'idle' | 'working' | 'completed' | 'error'
  current_task?: string
  progress?: number
  last_update: string
}

// Template types
export interface Template {
  id: string
  name: string
  description?: string
  category: string
  content: Record<string, any>
  created_by: string
  is_public: boolean
  created_at: string
  updated_at: string
}

// Saved Search types
export interface SavedSearch {
  id: string
  name: string
  description?: string
  query: Record<string, any>
  filters?: Record<string, any>
  created_by: string
  created_at: string
  updated_at: string
}

// Notification types
export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  read: boolean
  action_url?: string
  created_at: string
}

// Location types
export interface Location {
  latitude: number
  longitude: number
  address?: string
  timestamp?: string
}

// Export types
export interface ExportRequest {
  format: 'pdf' | 'docx' | 'xlsx' | 'json'
  investigation_id?: string
  filters?: Record<string, any>
  options?: Record<string, any>
}

// Verification types
export interface VerificationTask {
  id: string
  type: 'image' | 'facility' | 'tiger' | 'social_media'
  entity_id: string
  status: 'pending' | 'in_progress' | 'verified' | 'rejected'
  assigned_to?: string
  notes?: string
  created_at: string
  updated_at: string
  verified_at?: string
  verified_by?: string
}

// Analytics types
export interface DashboardStats {
  total_investigations: number
  active_investigations: number
  completed_investigations: number
  total_tigers: number
  total_facilities: number
  pending_verifications: number
  recent_activity: Event[]
}

// WebSocket types
export interface WebSocketMessage {
  type: 'event' | 'notification' | 'agent_update' | 'investigation_update'
  data: any
  timestamp: string
}

// Investigation Tools types
export interface WebSearchRequest {
  query: string
  limit?: number
  provider?: 'firecrawl' | 'serper' | 'tavily' | 'perplexity'
  location?: string
  gl?: string
  hl?: string
}

export interface WebSearchResult {
  title: string
  url: string
  snippet?: string
  position?: number
  score?: number
}

export interface WebSearchResponse {
  results: WebSearchResult[]
  count: number
  query: string
  provider: string
  answer_box?: any
  knowledge_graph?: any
  people_also_ask?: any[]
  related_questions?: any[]
  total_results?: string
}

export interface ReverseImageSearchRequest {
  image_url: string
  provider?: 'google' | 'tineye' | 'yandex'
}

export interface ReverseImageSearchResult {
  url: string
  title?: string
  snippet?: string
  score?: number
}

export interface ReverseImageSearchResponse {
  results: ReverseImageSearchResult[]
  count: number
  provider: string
  image_url: string
}

export interface NewsSearchRequest {
  query?: string
  days?: number
  limit?: number
}

export interface NewsArticle {
  title: string
  url: string
  source?: string
  snippet?: string
  date?: string
  facility_name?: string
}

export interface NewsSearchResponse {
  articles: NewsArticle[]
  count: number
  query?: string
  days: number
}

export interface LeadGenerationRequest {
  location?: string
  include_listings?: boolean
  include_social_media?: boolean
}

export interface LeadListing {
  title: string
  url: string
  snippet?: string
  suspicious_score: number
  matched_facilities?: string[]
}

export interface SocialMediaPost {
  platform: string
  url: string
  snippet?: string
  suspicious_score: number
}

export interface LeadGenerationResponse {
  leads: {
    listings: LeadListing[]
    social_media_posts: SocialMediaPost[]
    summary: {
      total_leads: number
      high_priority_leads: number
    }
    total_leads: number
  }
  summary: Record<string, any>
  total_leads: number
}

export interface RelationshipAnalysisRequest {
  facility_id: string
}

export interface RelationshipConnection {
  type: string
  connection_strength: number
  facility_name?: string
  facility_id?: string
}

export interface RelationshipAnalysisResponse {
  relationships: {
    connections: RelationshipConnection[]
    tigers: Array<{
      name: string
      status: string
    }>
  }
  facility_id: string
}

export interface EvidenceCompilationRequest {
  investigation_id: string
  source_urls: string[]
}

export interface EvidenceCompilationResponse {
  compilation: {
    compiled: Array<{
      evidence_id: string
      score: number
    }>
    compiled_count: number
    errors?: string[]
    error_count?: number
  }
  investigation_id: string
}

export interface EvidenceGroupsResponse {
  groups: {
    by_facility?: Record<string, any[]>
    high_relevance?: Array<{
      score: number
      source_type: string
    }>
  }
  investigation_id: string
}

export interface CrawlScheduleRequest {
  facility_id: string
  priority?: 'high' | 'medium' | 'low'
}

export interface CrawlScheduleResponse {
  scheduling: {
    task_id: string
  }
  facility_id: string
}

export interface CrawlStatisticsResponse {
  statistics: {
    total_crawls: number
    successful_crawls: number
    failed_crawls: number
    average_duration_ms: number
    total_images_found: number
    total_tigers_identified: number
  }
  facility_id?: string
}

// Analytics types
export interface InvestigationAnalytics {
  total_investigations: number
  by_status: Record<string, number>
  by_priority: Record<string, number>
  trends: Array<{
    date: string
    count: number
  }>
  completion_rate: number
  average_duration_days: number
  in_progress: number
  status_distribution: Record<string, number>
  priority_distribution: Record<string, number>
  timeline_data: Record<string, number>
}

export interface EvidenceAnalytics {
  total_evidence: number
  by_type: Record<string, number>
  by_status: Record<string, number>
  trends: Array<{
    date: string
    count: number
  }>
}

export interface VerificationAnalytics {
  total_tasks: number
  by_status: Record<string, number>
  by_type: Record<string, number>
  average_completion_time: number
  trends: Array<{
    date: string
    count: number
  }>
}

export interface GeographicAnalytics {
  facilities_by_state: Record<string, number>
  investigations_by_location: Array<{
    location: string
    count: number
    latitude?: number
    longitude?: number
  }>
}

export interface FacilityAnalytics {
  total_facilities: number
  by_type: Record<string, number>
  by_status: Record<string, number>
  reference_facilities: number
}

export interface TigerAnalytics {
  total_tigers: number
  by_status: Record<string, number>
  identification_rate: number
  trends: Array<{
    date: string
    count: number
  }>
}

export interface AgentAnalytics {
  agent_performance: Array<{
    agent_type: string
    tasks_completed: number
    success_rate: number
    average_duration: number
  }>
  workflow_metrics: Record<string, any>
}

// Annotation types
export interface Annotation {
  annotation_id: string
  investigation_id: string
  evidence_id?: string
  user_id: string
  annotation_type: 'highlight' | 'comment' | 'marker' | 'note'
  notes?: string
  coordinates?: Record<string, any>
  created_at: string
}

export interface AnnotationCreate {
  investigation_id: string
  annotation_type: string
  notes?: string
  evidence_id?: string
  coordinates?: Record<string, any>
}

export interface AnnotationUpdate {
  notes?: string
  coordinates?: Record<string, any>
}

// Global Search types
export interface GlobalSearchRequest {
  q: string
  entity_types?: string[]
  limit?: number
}

export interface GlobalSearchResponse {
  query: string
  results: {
    investigations: Investigation[]
    tigers: Tiger[]
    facilities: Facility[]
    evidence: Evidence[]
  }
  counts: {
    investigations: number
    tigers: number
    facilities: number
    evidence: number
  }
}

// Integration types
export interface SyncFacilityRequest {
  license_number: string
  investigation_id?: string
}

export interface SyncFacilityResponse {
  status: 'success' | 'queued'
  facility_id?: string
  facility?: {
    exhibitor_name: string
    usda_license: string
    state: string
    city: string
  }
  task_id?: string
  message?: string
}

export interface SyncInspectionsRequest {
  facility_id: string
  investigation_id?: string
}

export interface SyncInspectionsResponse {
  status: 'success' | 'queued'
  count: number
  inspections?: any[]
  task_id?: string
  message?: string
}

export interface SyncCITESRequest {
  investigation_id: string
  country_origin?: string
  country_destination?: string
  year?: number
  limit?: number
}

export interface SyncCITESResponse {
  status: 'success' | 'queued'
  count: number
  records?: any[]
  task_id?: string
  message?: string
}

export interface SyncUSFWSRequest {
  investigation_id: string
  permit_number?: string
  applicant_name?: string
  limit?: number
}

export interface SyncUSFWSResponse {
  status: 'success' | 'queued'
  count: number
  permits?: any[]
  task_id?: string
  message?: string
}

// Investigation Step types
export interface InvestigationStep {
  step_id: string
  investigation_id: string
  step_type: string
  agent_name?: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  result?: Record<string, any>
  parent_step_id?: string
  timestamp: string
  created_at: string
}

// Event types (expanded)
export interface InvestigationEvent {
  event_id?: string
  investigation_id: string
  event_type: string
  user_id?: string
  timestamp: string
  data: Record<string, any>
  metadata?: Record<string, any>
}

export interface InvestigationEventsResponse {
  investigation_id: string
  events: InvestigationEvent[]
  count: number
}

// Model Testing types
export interface ModelTestResult {
  model_name: string
  inference_time_ms: number
  embedding_length: number
  embedding_sample: number[]
  message: string
  error?: string
}

export interface ModelEvaluationResult {
  model_name: string
  metrics: {
    rank1_accuracy: number
    map: number
    cmc_curve: number[]
  }
  dataset_name: string
  total_queries: number
  total_gallery: number
}

export interface ModelComparisonResult {
  comparison_results: {
    models: Record<string, {
      rank1_accuracy: number
      map: number
      avg_inference_time_ms: number
    }>
    best_model: string
    best_metric: string
  }
  dataset_name: string
}

export interface ModelBenchmarkResult {
  model_name: string
  benchmark_results: {
    avg_inference_time_ms: number
    min_inference_time_ms: number
    max_inference_time_ms: number
    memory_usage_mb: number
  }
  num_runs: number
}

export interface AvailableModelsResponse {
  models: Record<string, any> | string[]
  default: string
}


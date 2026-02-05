/**
 * Discovery API endpoints.
 *
 * Handles all discovery-related endpoints including:
 * - Auto-investigation statistics
 * - Discovery scheduler control
 * - Crawl queue and history
 * - Pipeline statistics
 * - Deep research
 */
import { baseApi } from './baseApi'
import type {
  ApiResponse,
  AutoInvestigationStatsParams,
  AutoInvestigationStatsResponse,
  RecentAutoInvestigationsParams,
  RecentAutoInvestigationsResponse,
  PipelineStatsResponse,
  DiscoveryStatusResponse,
  DiscoveryStatsResponse,
  CrawlQueueResponse,
  CrawlQueueParams,
  CrawlHistoryResponse,
  CrawlHistoryParams,
  SchedulerActionResponse,
  CrawlTriggerResponse,
  DeepResearchResponse,
} from '../../types'

export const discoveryApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // =========================================================================
    // Auto-Investigation Statistics
    // =========================================================================

    /**
     * Get auto-investigation statistics with time range filter
     */
    getAutoInvestigationStats: builder.query<
      ApiResponse<AutoInvestigationStatsResponse>,
      AutoInvestigationStatsParams
    >({
      query: (params) => ({
        url: '/api/v1/discovery/auto-investigation/stats',
        params: {
          time_range: params.time_range,
        },
      }),
      providesTags: ['Discovery', 'Investigation'],
    }),

    /**
     * Get recent auto-triggered investigations
     */
    getRecentAutoInvestigations: builder.query<
      ApiResponse<RecentAutoInvestigationsResponse>,
      RecentAutoInvestigationsParams
    >({
      query: (params) => ({
        url: '/api/v1/discovery/auto-investigation/recent',
        params: {
          limit: params.limit,
          status: params.status,
        },
      }),
      providesTags: ['Discovery', 'Investigation'],
    }),

    // =========================================================================
    // Pipeline Statistics
    // =========================================================================

    /**
     * Get image pipeline processing statistics
     */
    getPipelineStats: builder.query<ApiResponse<PipelineStatsResponse>, void>({
      query: () => '/api/v1/discovery/pipeline/stats',
      providesTags: ['Discovery'],
    }),

    // =========================================================================
    // Discovery Scheduler
    // =========================================================================

    /**
     * Get discovery scheduler status
     */
    getDiscoveryStatus: builder.query<ApiResponse<DiscoveryStatusResponse>, void>({
      query: () => '/api/v1/discovery/status',
      providesTags: ['Discovery'],
    }),

    /**
     * Get comprehensive discovery statistics
     */
    getDiscoveryStats: builder.query<ApiResponse<DiscoveryStatsResponse>, void>({
      query: () => '/api/v1/discovery/stats',
      providesTags: ['Discovery', 'Facility', 'Tiger'],
    }),

    /**
     * Start the discovery scheduler
     */
    startDiscovery: builder.mutation<ApiResponse<SchedulerActionResponse>, void>({
      query: () => ({
        url: '/api/v1/discovery/start',
        method: 'POST',
      }),
      invalidatesTags: ['Discovery'],
    }),

    /**
     * Stop the discovery scheduler
     */
    stopDiscovery: builder.mutation<ApiResponse<SchedulerActionResponse>, void>({
      query: () => ({
        url: '/api/v1/discovery/stop',
        method: 'POST',
      }),
      invalidatesTags: ['Discovery'],
    }),

    // =========================================================================
    // Crawl Queue & History
    // =========================================================================

    /**
     * Get facilities pending crawl
     */
    getCrawlQueue: builder.query<ApiResponse<CrawlQueueResponse>, CrawlQueueParams>({
      query: (params) => ({
        url: '/api/v1/discovery/queue',
        params,
      }),
      providesTags: ['Discovery', 'Facility'],
    }),

    /**
     * Get crawl history records
     */
    getCrawlHistory: builder.query<ApiResponse<CrawlHistoryResponse>, CrawlHistoryParams>({
      query: (params) => ({
        url: '/api/v1/discovery/history',
        params,
      }),
      providesTags: ['Discovery'],
    }),

    // =========================================================================
    // Crawl Operations
    // =========================================================================

    /**
     * Trigger a full crawl of all facilities
     */
    triggerFullCrawl: builder.mutation<ApiResponse<CrawlTriggerResponse>, void>({
      query: () => ({
        url: '/api/v1/discovery/crawl/all',
        method: 'POST',
      }),
      invalidatesTags: ['Discovery', 'Facility'],
    }),

    /**
     * Crawl a single facility
     */
    crawlFacility: builder.mutation<ApiResponse<CrawlTriggerResponse>, string>({
      query: (facility_id) => ({
        url: `/api/v1/discovery/crawl/facility/${facility_id}`,
        method: 'POST',
      }),
      invalidatesTags: ['Discovery', 'Facility'],
    }),

    /**
     * Run deep research on a facility
     */
    runDeepResearch: builder.mutation<ApiResponse<DeepResearchResponse>, string>({
      query: (facility_id) => ({
        url: `/api/v1/discovery/research/${facility_id}`,
        method: 'POST',
      }),
      invalidatesTags: ['Discovery', 'Facility'],
    }),
  }),
  overrideExisting: false,
})

export const {
  // Auto-Investigation
  useGetAutoInvestigationStatsQuery,
  useGetRecentAutoInvestigationsQuery,
  // Pipeline
  useGetPipelineStatsQuery,
  // Discovery Scheduler
  useGetDiscoveryStatusQuery,
  useGetDiscoveryStatsQuery,
  useStartDiscoveryMutation,
  useStopDiscoveryMutation,
  // Crawl Queue & History
  useGetCrawlQueueQuery,
  useGetCrawlHistoryQuery,
  // Crawl Operations
  useTriggerFullCrawlMutation,
  useCrawlFacilityMutation,
  useRunDeepResearchMutation,
} = discoveryApi

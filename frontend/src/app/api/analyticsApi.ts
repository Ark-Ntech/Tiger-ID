/**
 * Analytics API endpoints.
 *
 * Handles all analytics-related endpoints including:
 * - Investigation analytics
 * - Evidence analytics
 * - Verification analytics
 * - Geographic analytics
 * - Facility analytics
 * - Tiger analytics
 * - Agent analytics
 * - Annotations
 * - Network graph
 * - Global search
 * - Integrations
 */
import { baseApi } from './baseApi'
import type {
  ApiResponse,
  InvestigationAnalytics,
  EvidenceAnalytics,
  VerificationAnalytics,
  GeographicAnalytics,
  FacilityAnalytics,
  TigerAnalytics,
  AgentAnalytics,
  Annotation,
  AnnotationCreate,
  AnnotationUpdate,
  GlobalSearchRequest,
  GlobalSearchResponse,
  NetworkGraphResponse,
  SyncFacilityRequest,
  SyncFacilityResponse,
  SyncInspectionsRequest,
  SyncInspectionsResponse,
  SyncCITESRequest,
  SyncCITESResponse,
  SyncUSFWSRequest,
  SyncUSFWSResponse,
} from '../../types'

export const analyticsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // =========================================================================
    // Analytics Endpoints
    // =========================================================================

    getInvestigationAnalytics: builder.query<
      ApiResponse<InvestigationAnalytics>,
      { start_date?: string; end_date?: string }
    >({
      query: (params) => ({
        url: '/api/v1/analytics/investigations',
        params,
      }),
      providesTags: ['Analytics'],
    }),

    getEvidenceAnalytics: builder.query<
      ApiResponse<EvidenceAnalytics>,
      { investigation_id?: string; start_date?: string; end_date?: string }
    >({
      query: (params) => ({
        url: '/api/v1/analytics/evidence',
        params,
      }),
      providesTags: ['Analytics'],
    }),

    getVerificationAnalytics: builder.query<
      ApiResponse<VerificationAnalytics>,
      { start_date?: string; end_date?: string }
    >({
      query: (params) => ({
        url: '/api/v1/analytics/verification',
        params,
      }),
      providesTags: ['Analytics'],
    }),

    getGeographicAnalytics: builder.query<
      ApiResponse<GeographicAnalytics>,
      { investigation_id?: string }
    >({
      query: (params) => ({
        url: '/api/v1/analytics/geographic',
        params,
      }),
      providesTags: ['Analytics'],
    }),

    getFacilityAnalytics: builder.query<
      ApiResponse<FacilityAnalytics>,
      { start_date?: string; end_date?: string }
    >({
      query: (params) => ({
        url: '/api/v1/analytics/facilities',
        params,
      }),
      providesTags: ['Analytics'],
    }),

    getTigerAnalytics: builder.query<
      ApiResponse<TigerAnalytics>,
      { investigation_id?: string; facility_id?: string }
    >({
      query: (params) => ({
        url: '/api/v1/analytics/tigers',
        params,
      }),
      providesTags: ['Analytics'],
    }),

    getAgentAnalytics: builder.query<
      ApiResponse<AgentAnalytics>,
      { investigation_id?: string; start_date?: string; end_date?: string }
    >({
      query: (params) => ({
        url: '/api/v1/analytics/agents',
        params,
      }),
      providesTags: ['Analytics'],
    }),

    // =========================================================================
    // Annotation Endpoints
    // =========================================================================

    getAnnotations: builder.query<
      ApiResponse<{ annotations: Annotation[]; count: number }>,
      {
        investigation_id?: string
        evidence_id?: string
        user_id?: string
        annotation_type?: string
        target_entity_type?: string
        target_entity_id?: string
        limit?: number
        offset?: number
      }
    >({
      query: (params) => ({
        url: '/api/v1/annotations',
        params,
      }),
      providesTags: ['Annotation'],
    }),

    getAnnotation: builder.query<ApiResponse<Annotation>, string>({
      query: (annotation_id) => ({
        url: `/api/v1/annotations/${annotation_id}`,
      }),
      providesTags: (_result, _error, id) => [{ type: 'Annotation', id }],
    }),

    createAnnotation: builder.mutation<ApiResponse<Annotation>, AnnotationCreate>({
      query: (data) => ({
        url: '/api/v1/annotations',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Annotation'],
    }),

    updateAnnotation: builder.mutation<
      ApiResponse<Annotation>,
      { annotation_id: string; data: AnnotationUpdate }
    >({
      query: ({ annotation_id, data }) => ({
        url: `/api/v1/annotations/${annotation_id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: (_result, _error, { annotation_id }) => [
        { type: 'Annotation', id: annotation_id },
      ],
    }),

    deleteAnnotation: builder.mutation<ApiResponse<{ message: string }>, string>({
      query: (annotation_id) => ({
        url: `/api/v1/annotations/${annotation_id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Annotation'],
    }),

    // =========================================================================
    // Network Graph Endpoint
    // =========================================================================

    getNetworkGraph: builder.query<ApiResponse<NetworkGraphResponse>, string>({
      query: (id) => ({
        url: `/api/v1/network/graph/${id}`,
      }),
      providesTags: ['Investigation', 'Facility', 'Tiger'],
    }),

    // =========================================================================
    // Global Search Endpoint
    // =========================================================================

    globalSearch: builder.query<ApiResponse<GlobalSearchResponse>, GlobalSearchRequest>({
      query: (params) => ({
        url: '/api/v1/search/global',
        params: {
          q: params.q,
          entity_types: params.entity_types?.join(','),
          limit: params.limit,
        },
      }),
      providesTags: ['Investigation', 'Tiger', 'Facility', 'Evidence'],
    }),

    // =========================================================================
    // Integration Endpoints
    // =========================================================================

    syncFacilityUSDA: builder.mutation<
      ApiResponse<SyncFacilityResponse>,
      { data: SyncFacilityRequest; background?: boolean }
    >({
      query: ({ data, background }) => ({
        url: '/api/integrations/usda/sync-facility',
        method: 'POST',
        body: data,
        params: { background },
      }),
      invalidatesTags: ['Facility', 'Integration'],
    }),

    syncInspections: builder.mutation<
      ApiResponse<SyncInspectionsResponse>,
      { data: SyncInspectionsRequest; background?: boolean }
    >({
      query: ({ data, background }) => ({
        url: '/api/integrations/usda/sync-inspections',
        method: 'POST',
        body: data,
        params: { background },
      }),
      invalidatesTags: ['Facility', 'Integration'],
    }),

    syncCITESRecords: builder.mutation<
      ApiResponse<SyncCITESResponse>,
      { data: SyncCITESRequest; background?: boolean }
    >({
      query: ({ data, background }) => ({
        url: '/api/integrations/cites/sync-trade-records',
        method: 'POST',
        body: data,
        params: { background },
      }),
      invalidatesTags: ['Investigation', 'Integration'],
    }),

    syncUSFWSPermits: builder.mutation<
      ApiResponse<SyncUSFWSResponse>,
      { data: SyncUSFWSRequest; background?: boolean }
    >({
      query: ({ data, background }) => ({
        url: '/api/integrations/usfws/sync-permits',
        method: 'POST',
        body: data,
        params: { background },
      }),
      invalidatesTags: ['Investigation', 'Integration'],
    }),
  }),
  overrideExisting: false,
})

export const {
  // Analytics
  useGetInvestigationAnalyticsQuery,
  useGetEvidenceAnalyticsQuery,
  useGetVerificationAnalyticsQuery,
  useGetGeographicAnalyticsQuery,
  useGetFacilityAnalyticsQuery,
  useGetTigerAnalyticsQuery,
  useGetAgentAnalyticsQuery,
  // Annotations
  useGetAnnotationsQuery,
  useGetAnnotationQuery,
  useCreateAnnotationMutation,
  useUpdateAnnotationMutation,
  useDeleteAnnotationMutation,
  // Network Graph
  useGetNetworkGraphQuery,
  // Global Search
  useGlobalSearchQuery,
  // Integrations
  useSyncFacilityUSDAMutation,
  useSyncInspectionsMutation,
  useSyncCITESRecordsMutation,
  useSyncUSFWSPermitsMutation,
} = analyticsApi

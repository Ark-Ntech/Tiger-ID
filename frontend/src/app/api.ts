import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import type { RootState } from './store'
import type {
  User,
  Investigation,
  Tiger,
  Facility,
  Template,
  SavedSearch,
  VerificationTask,
  DashboardStats,
  Evidence,
  ApiResponse,
  PaginatedResponse,
  WebSearchRequest,
  WebSearchResponse,
  ReverseImageSearchRequest,
  ReverseImageSearchResponse,
  NewsSearchRequest,
  NewsSearchResponse,
  LeadGenerationRequest,
  LeadGenerationResponse,
  RelationshipAnalysisRequest,
  RelationshipAnalysisResponse,
  EvidenceCompilationRequest,
  EvidenceCompilationResponse,
  EvidenceGroupsResponse,
  CrawlScheduleRequest,
  CrawlScheduleResponse,
  CrawlStatisticsResponse,
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
  SyncFacilityRequest,
  SyncFacilityResponse,
  SyncInspectionsRequest,
  SyncInspectionsResponse,
  SyncCITESRequest,
  SyncCITESResponse,
  SyncUSFWSRequest,
  SyncUSFWSResponse,
  InvestigationStep,
  InvestigationEventsResponse,
} from '../types'

// In development, use Vite proxy (empty baseUrl uses relative paths which go through proxy)
// In production, use VITE_API_URL environment variable
const baseUrl = import.meta.env.PROD 
  ? (import.meta.env.VITE_API_URL || 'http://localhost:8000')
  : '' // Empty string in dev mode uses Vite proxy

export const api = createApi({
  reducerPath: 'api',
  baseQuery: async (args, api, extraOptions) => {
    const baseQuery = fetchBaseQuery({
      baseUrl,
      prepareHeaders: (headers, { getState }) => {
        const token = (getState() as RootState).auth.token
        if (token) {
          headers.set('authorization', `Bearer ${token}`)
        }
        return headers
      },
    })
    
    const result = await baseQuery(args, api, extraOptions)
    
    // Handle 401 errors - redirect to login
    if (result.error && 'status' in result.error && result.error.status === 401) {
      // Clear token
      localStorage.removeItem('token')
      // Dispatch logout action
      api.dispatch({ type: 'auth/logout' })
      // Redirect to login
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
    }
    
    return result
  },
  tagTypes: [
    'User',
    'Investigation',
    'Tiger',
    'Facility',
    'Template',
    'SavedSearch',
    'Verification',
    'Evidence',
    'Dashboard',
    'Analytics',
    'Annotation',
    'Export',
    'Integration',
  ],
  endpoints: (builder) => ({
    // Auth endpoints
    getCurrentUser: builder.query<ApiResponse<User>, void>({
      query: () => '/api/auth/me',
      providesTags: ['User'],
    }),

    // Dashboard endpoints
    getDashboardStats: builder.query<ApiResponse<DashboardStats>, void>({
      query: () => '/api/v1/dashboard/stats',
      providesTags: ['Dashboard'],
    }),

    // Investigation endpoints
    getInvestigations: builder.query<
      ApiResponse<PaginatedResponse<Investigation>>,
      { page?: number; page_size?: number; status?: string }
    >({
      query: (params) => ({
        url: '/api/v1/investigations',
        params,
      }),
      providesTags: ['Investigation'],
    }),

    getInvestigation: builder.query<ApiResponse<Investigation>, string>({
      query: (id) => `/api/v1/investigations/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'Investigation', id }],
    }),

    createInvestigation: builder.mutation<ApiResponse<Investigation>, FormData>({
      query: (data) => ({
        url: '/api/v1/investigations',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Investigation', 'Dashboard'],
    }),

    updateInvestigation: builder.mutation<
      ApiResponse<Investigation>,
      { id: string; data: Partial<Investigation> }
    >({
      query: ({ id, data }) => ({
        url: `/api/v1/investigations/${id}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'Investigation', id },
        'Dashboard',
      ],
    }),

    launchInvestigation: builder.mutation<ApiResponse<Investigation>, { investigation_id: string; user_input?: string; files?: File[]; selected_tools?: string[] }>({
      query: ({ investigation_id, user_input, files, selected_tools }) => {
        const formData = new FormData()
        if (user_input) formData.append('user_input', user_input)
        if (selected_tools) {
          selected_tools.forEach(tool => formData.append('selected_tools', tool))
        }
        if (files) {
          files.forEach(file => formData.append('files', file))
        }
        return {
          url: `/api/v1/investigations/${investigation_id}/launch`,
          method: 'POST',
          body: formData,
        }
      },
      invalidatesTags: (_result, _error, { investigation_id }) => [{ type: 'Investigation', id: investigation_id }],
    }),

    getMCPTools: builder.query<ApiResponse<{ servers: Record<string, any>; total_tools: number }>, void>({
      query: () => ({
        url: '/api/v1/investigations/mcp-tools',
      }),
      providesTags: ['Investigation'],
    }),

    // Tiger endpoints
    getTigers: builder.query<
      ApiResponse<PaginatedResponse<Tiger>>,
      { page?: number; page_size?: number }
    >({
      query: (params) => ({
        url: '/api/v1/tigers',
        params,
      }),
      providesTags: ['Tiger'],
    }),

    getTiger: builder.query<ApiResponse<Tiger>, string>({
      query: (id) => `/api/v1/tigers/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'Tiger', id }],
    }),

    identifyTiger: builder.mutation<ApiResponse<any>, FormData>({
      query: (data) => ({
        url: '/api/v1/tigers/identify',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Tiger'],
    }),

    identifyTigersBatch: builder.mutation<ApiResponse<any>, FormData>({
      query: (data) => ({
        url: '/api/v1/tigers/identify/batch',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Tiger'],
    }),

    getAvailableModels: builder.query<ApiResponse<{ models: string[]; default: string }>, void>({
      query: () => '/api/v1/tigers/models',
      providesTags: ['Tiger'],
    }),

    // Model testing endpoints
    testModel: builder.mutation<ApiResponse<any>, FormData>({
      query: (data) => ({
        url: '/api/v1/models/test',
        method: 'POST',
        body: data,
      }),
    }),

    evaluateModel: builder.mutation<ApiResponse<any>, FormData>({
      query: (data) => ({
        url: '/api/v1/models/evaluate',
        method: 'POST',
        body: data,
      }),
    }),

    compareModels: builder.mutation<ApiResponse<any>, FormData>({
      query: (data) => ({
        url: '/api/v1/models/compare',
        method: 'POST',
        body: data,
      }),
    }),

    benchmarkModel: builder.mutation<ApiResponse<any>, FormData>({
      query: (data) => ({
        url: '/api/v1/models/benchmark',
        method: 'POST',
        body: data,
      }),
    }),

    getModelsAvailable: builder.query<ApiResponse<{ models: Record<string, any>; default: string }>, void>({
      query: () => '/api/v1/models/available',
    }),

    // Facility endpoints
    getFacilities: builder.query<
      ApiResponse<PaginatedResponse<Facility>>,
      { page?: number; page_size?: number }
    >({
      query: (params) => ({
        url: '/api/v1/facilities',
        params,
      }),
      providesTags: ['Facility'],
    }),

    getFacility: builder.query<ApiResponse<Facility>, string>({
      query: (id) => `/api/v1/facilities/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'Facility', id }],
    }),

    importFacilitiesExcel: builder.mutation<
      ApiResponse<{ message: string; stats: { created: number; updated: number; skipped: number; errors: any[] } }>,
      { file: File; update_existing?: boolean }
    >({
      query: ({ file, update_existing = true }) => {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('update_existing', update_existing.toString())
        return {
          url: '/api/v1/facilities/import-excel',
          method: 'POST',
          body: formData,
        }
      },
      invalidatesTags: ['Facility'],
    }),

    // Template endpoints
    getTemplates: builder.query<ApiResponse<Template[]>, void>({
      query: () => '/api/v1/templates',
      providesTags: ['Template'],
    }),

    createTemplate: builder.mutation<ApiResponse<Template>, Partial<Template>>({
      query: (data) => ({
        url: '/api/v1/templates',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Template'],
    }),

    // Saved Search endpoints
    getSavedSearches: builder.query<ApiResponse<SavedSearch[]>, void>({
      query: () => '/api/v1/saved-searches',
      providesTags: ['SavedSearch'],
    }),

    createSavedSearch: builder.mutation<ApiResponse<SavedSearch>, Partial<SavedSearch>>({
      query: (data) => ({
        url: '/api/v1/saved-searches',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['SavedSearch'],
    }),

    // Verification endpoints
    getVerificationTasks: builder.query<
      ApiResponse<PaginatedResponse<VerificationTask>>,
      { page?: number; page_size?: number; status?: string }
    >({
      query: (params) => ({
        url: '/api/v1/verification/tasks',
        params,
      }),
      providesTags: ['Verification'],
    }),

    updateVerificationTask: builder.mutation<
      ApiResponse<VerificationTask>,
      { id: string; data: Partial<VerificationTask> }
    >({
      query: ({ id, data }) => ({
        url: `/api/v1/verification/tasks/${id}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: ['Verification', 'Dashboard'],
    }),

    // Evidence endpoints
    getEvidence: builder.query<
      ApiResponse<Evidence[]>,
      { investigation_id: string }
    >({
      query: ({ investigation_id }) => ({
        url: `/api/v1/investigations/${investigation_id}/evidence`,
      }),
      providesTags: ['Evidence'],
    }),

    addEvidence: builder.mutation<
      ApiResponse<Evidence>,
      { investigation_id: string; data: FormData }
    >({
      query: ({ investigation_id, data }) => ({
        url: `/api/v1/investigations/${investigation_id}/evidence`,
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Evidence'],
    }),

    // Investigation Tools endpoints
    webSearch: builder.mutation<ApiResponse<WebSearchResponse>, WebSearchRequest>({
      query: (data) => ({
        url: '/api/v1/investigations/web-search',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Investigation'],
    }),

    reverseImageSearch: builder.mutation<
      ApiResponse<ReverseImageSearchResponse>,
      ReverseImageSearchRequest
    >({
      query: (data) => ({
        url: '/api/v1/investigations/reverse-image-search',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Investigation'],
    }),

    newsSearch: builder.mutation<ApiResponse<NewsSearchResponse>, NewsSearchRequest>({
      query: (data) => ({
        url: '/api/v1/investigations/news-search',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Investigation'],
    }),

    generateLeads: builder.mutation<
      ApiResponse<LeadGenerationResponse>,
      LeadGenerationRequest
    >({
      query: (data) => ({
        url: '/api/v1/investigations/generate-leads',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Investigation'],
    }),

    relationshipAnalysis: builder.mutation<
      ApiResponse<RelationshipAnalysisResponse>,
      RelationshipAnalysisRequest
    >({
      query: (data) => ({
        url: '/api/v1/investigations/relationship-analysis',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Investigation'],
    }),

    compileEvidence: builder.mutation<
      ApiResponse<EvidenceCompilationResponse>,
      EvidenceCompilationRequest
    >({
      query: (data) => ({
        url: '/api/v1/investigations/compile-evidence',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Evidence', 'Investigation'],
    }),

    getEvidenceGroups: builder.query<ApiResponse<EvidenceGroupsResponse>, string>({
      query: (investigation_id) => ({
        url: `/api/v1/investigations/evidence-groups/${investigation_id}`,
      }),
      providesTags: ['Evidence'],
    }),

    scheduleCrawl: builder.mutation<
      ApiResponse<CrawlScheduleResponse>,
      CrawlScheduleRequest
    >({
      query: (data) => ({
        url: '/api/v1/investigations/schedule-crawl',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Facility'],
    }),

    getCrawlStatistics: builder.query<
      ApiResponse<CrawlStatisticsResponse>,
      { facility_id?: string; days?: number }
    >({
      query: (params) => ({
        url: '/api/v1/investigations/crawl-statistics',
        params,
      }),
      providesTags: ['Facility'],
    }),

    // Analytics endpoints
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

    // Export endpoints
    exportInvestigationJSON: builder.query<
      Blob,
      { investigation_id: string; include_evidence?: boolean; include_steps?: boolean; include_metadata?: boolean }
    >({
      query: ({ investigation_id, include_evidence, include_steps, include_metadata }) => ({
        url: `/api/v1/investigations/${investigation_id}/export/json`,
        params: { include_evidence, include_steps, include_metadata },
        responseHandler: (response) => response.blob(),
      }),
    }),

    exportInvestigationMarkdown: builder.query<
      Blob,
      { investigation_id: string; include_evidence?: boolean; include_steps?: boolean }
    >({
      query: ({ investigation_id, include_evidence, include_steps }) => ({
        url: `/api/v1/investigations/${investigation_id}/export/markdown`,
        params: { include_evidence, include_steps },
        responseHandler: (response) => response.blob(),
      }),
    }),

    exportInvestigationPDF: builder.query<
      Blob,
      { investigation_id: string; include_evidence?: boolean; include_steps?: boolean }
    >({
      query: ({ investigation_id, include_evidence, include_steps }) => ({
        url: `/api/v1/investigations/${investigation_id}/export/pdf`,
        params: { include_evidence, include_steps },
        responseHandler: (response) => response.blob(),
      }),
    }),

    exportInvestigationCSV: builder.query<
      Blob,
      { investigation_id: string; data_type?: 'evidence' | 'steps' | 'summary' }
    >({
      query: ({ investigation_id, data_type }) => ({
        url: `/api/v1/investigations/${investigation_id}/export/csv`,
        params: { data_type },
        responseHandler: (response) => response.blob(),
      }),
    }),

    // Annotation endpoints
    getAnnotations: builder.query<
      ApiResponse<{ annotations: Annotation[]; count: number }>,
      {
        investigation_id?: string
        evidence_id?: string
        user_id?: string
        annotation_type?: string
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

    // Global Search endpoint
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

    // Integration endpoints
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

    // Investigation Steps & Events
    getInvestigationSteps: builder.query<
      ApiResponse<InvestigationStep[]>,
      string
    >({
      query: (investigation_id) => ({
        url: `/api/v1/investigations/${investigation_id}/steps`,
      }),
      providesTags: ['Investigation'],
    }),

    getInvestigationEvents: builder.query<
      ApiResponse<InvestigationEventsResponse>,
      { investigation_id: string; event_type?: string; limit?: number }
    >({
      query: ({ investigation_id, event_type, limit }) => ({
        url: `/api/v1/events/investigation/${investigation_id}`,
        params: { event_type, limit },
      }),
      providesTags: ['Investigation'],
    }),
  }),
})

export const {
  useGetCurrentUserQuery,
  useGetDashboardStatsQuery,
  useGetInvestigationsQuery,
  useGetInvestigationQuery,
  useCreateInvestigationMutation,
  useUpdateInvestigationMutation,
  useLaunchInvestigationMutation,
  useGetTigersQuery,
  useGetTigerQuery,
  useIdentifyTigerMutation,
  useIdentifyTigersBatchMutation,
  useGetAvailableModelsQuery,
  useTestModelMutation,
  useEvaluateModelMutation,
  useCompareModelsMutation,
  useBenchmarkModelMutation,
  useGetModelsAvailableQuery,
  useGetFacilitiesQuery,
  useGetFacilityQuery,
  useImportFacilitiesExcelMutation,
  useGetTemplatesQuery,
  useCreateTemplateMutation,
  useApplyTemplateMutation,
  useGetSavedSearchesQuery,
  useCreateSavedSearchMutation,
  useGetVerificationTasksQuery,
  useUpdateVerificationTaskMutation,
  useGetEvidenceQuery,
  useAddEvidenceMutation,
  // Investigation Tools
  useWebSearchMutation,
  useReverseImageSearchMutation,
  useNewsSearchMutation,
  useGenerateLeadsMutation,
  useRelationshipAnalysisMutation,
  useCompileEvidenceMutation,
  useGetEvidenceGroupsQuery,
  useScheduleCrawlMutation,
  useGetCrawlStatisticsQuery,
  // Analytics
  useGetInvestigationAnalyticsQuery,
  useGetEvidenceAnalyticsQuery,
  useGetVerificationAnalyticsQuery,
  useGetGeographicAnalyticsQuery,
  useGetFacilityAnalyticsQuery,
  useGetTigerAnalyticsQuery,
  useGetAgentAnalyticsQuery,
  // Export
  useExportInvestigationJSONQuery,
  useExportInvestigationMarkdownQuery,
  useExportInvestigationPDFQuery,
  useExportInvestigationCSVQuery,
  // Annotations
  useGetAnnotationsQuery,
  useGetAnnotationQuery,
  useCreateAnnotationMutation,
  useUpdateAnnotationMutation,
  useDeleteAnnotationMutation,
  // Global Search
  useGlobalSearchQuery,
  // Integrations
  useSyncFacilityUSDAMutation,
  useSyncInspectionsMutation,
  useSyncCITESRecordsMutation,
  useSyncUSFWSPermitsMutation,
  // Investigation Steps & Events
  useGetInvestigationStepsQuery,
  useGetInvestigationEventsQuery,
  // MCP Tools
  useGetMCPToolsQuery,
} = api


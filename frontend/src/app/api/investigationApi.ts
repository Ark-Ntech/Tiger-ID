/**
 * Investigation API endpoints.
 *
 * Handles all investigation-related endpoints including:
 * - Investigation CRUD operations
 * - Investigation 2.0 workflow
 * - Investigation tools (web search, evidence, etc.)
 * - Export endpoints
 */
import { baseApi } from './baseApi'
import type {
  Investigation,
  ApiResponse,
  PaginatedResponse,
  Evidence,
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
  InvestigationStep,
  InvestigationEventsResponse,
} from '../../types'
import type {
  LaunchInvestigation2Response,
  ReportAudience,
  Investigation2Report,
  Investigation2Response,
  TigerMatch as Investigation2Match,
} from '../../types/investigation2'

export const investigationApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // =========================================================================
    // Core Investigation CRUD
    // =========================================================================

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

    createInvestigation: builder.mutation<
      ApiResponse<Investigation>,
      { title: string; description?: string; priority?: string; tags?: string[] }
    >({
      query: (data) => {
        console.log('Creating investigation with data:', data)
        return {
          url: '/api/v1/investigations',
          method: 'POST',
          body: data,
        }
      },
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

    launchInvestigation: builder.mutation<
      ApiResponse<Investigation>,
      {
        investigation_id: string
        user_input?: string
        files?: File[]
        selected_tools?: string[]
        tiger_id?: string
      }
    >({
      query: ({ investigation_id, user_input, files, selected_tools, tiger_id }) => {
        const formData = new FormData()

        // Always append user_input, even if empty
        formData.append('user_input', user_input || '')

        // Append selected_tools if provided
        if (selected_tools && selected_tools.length > 0) {
          selected_tools.forEach((tool) => formData.append('selected_tools', tool))
        }

        // Append files if provided
        if (files && files.length > 0) {
          files.forEach((file) => formData.append('files', file))
        }

        if (tiger_id) {
          formData.append('tiger_id', tiger_id)
        }

        console.log('Sending launchInvestigation request:', {
          investigation_id,
          user_input: user_input || '',
          selected_tools,
          files_count: files?.length || 0,
          tiger_id,
        })

        return {
          url: `/api/v1/investigations/${investigation_id}/launch`,
          method: 'POST',
          body: formData,
        }
      },
      invalidatesTags: (_result, _error, { investigation_id }) => [
        { type: 'Investigation', id: investigation_id },
      ],
    }),

    getMCPTools: builder.query<
      ApiResponse<{ servers: Record<string, unknown>; total_tools: number }>,
      void
    >({
      query: () => ({
        url: '/api/v1/investigations/mcp-tools',
      }),
      providesTags: ['Investigation'],
    }),

    getInvestigationExtended: builder.query<ApiResponse<unknown>, string>({
      query: (id) => `/api/v1/investigations/${id}/extended`,
      providesTags: (_result, _error, id) => [{ type: 'Investigation', id }],
    }),

    resumeInvestigation: builder.mutation<ApiResponse<Investigation>, string>({
      query: (id) => ({
        url: `/api/v1/investigations/${id}/resume`,
        method: 'POST',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'Investigation', id }, 'Dashboard'],
    }),

    pauseInvestigation: builder.mutation<ApiResponse<Investigation>, string>({
      query: (id) => ({
        url: `/api/v1/investigations/${id}/pause`,
        method: 'POST',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'Investigation', id }, 'Dashboard'],
    }),

    bulkPauseInvestigations: builder.mutation<
      ApiResponse<{ paused: number; failed: number }>,
      string[]
    >({
      query: (ids) => ({
        url: '/api/v1/investigations/bulk/pause',
        method: 'POST',
        body: ids,
      }),
      invalidatesTags: ['Investigation', 'Dashboard'],
    }),

    bulkArchiveInvestigations: builder.mutation<
      ApiResponse<{ archived: number; failed: number }>,
      string[]
    >({
      query: (ids) => ({
        url: '/api/v1/investigations/bulk/archive',
        method: 'POST',
        body: ids,
      }),
      invalidatesTags: ['Investigation', 'Dashboard'],
    }),

    // =========================================================================
    // Investigation 2.0 Workflow
    // =========================================================================

    launchInvestigation2: builder.mutation<LaunchInvestigation2Response, FormData>({
      query: (formData) => ({
        url: '/api/v1/investigations2/launch',
        method: 'POST',
        body: formData,
      }),
      invalidatesTags: ['Investigation', 'Dashboard'],
    }),

    getInvestigation2: builder.query<ApiResponse<Investigation2Response>, string>({
      query: (id) => `/api/v1/investigations2/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'Investigation', id }],
    }),

    getInvestigation2Report: builder.query<ApiResponse<Investigation2Report>, string>({
      query: (id) => `/api/v1/investigations2/${id}/report`,
      providesTags: (_result, _error, id) => [{ type: 'Investigation', id }],
    }),

    getInvestigation2Matches: builder.query<
      ApiResponse<{ matches: Investigation2Match[] }>,
      string
    >({
      query: (id) => `/api/v1/investigations2/${id}/matches`,
      providesTags: (_result, _error, id) => [{ type: 'Investigation', id }],
    }),

    regenerateInvestigation2Report: builder.mutation<
      ApiResponse<Investigation2Report>,
      { investigation_id: string; audience: ReportAudience }
    >({
      query: ({ investigation_id, audience }) => ({
        url: `/api/v1/investigations2/${investigation_id}/regenerate-report`,
        method: 'POST',
        body: { audience },
      }),
      invalidatesTags: (_result, _error, { investigation_id }) => [
        { type: 'Investigation', id: investigation_id },
      ],
    }),

    // =========================================================================
    // Evidence Management
    // =========================================================================

    getEvidence: builder.query<ApiResponse<Evidence[]>, { investigation_id: string }>({
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

    uploadEvidence: builder.mutation<
      ApiResponse<unknown>,
      { investigation_id: string; file: File; title?: string; description?: string }
    >({
      query: ({ investigation_id, file, title, description }) => {
        const formData = new FormData()
        formData.append('file', file)
        if (title) formData.append('title', title)
        if (description) formData.append('description', description)
        return {
          url: `/api/v1/investigations/${investigation_id}/evidence/upload`,
          method: 'POST',
          body: formData,
        }
      },
      invalidatesTags: ['Evidence'],
    }),

    linkTigerEvidence: builder.mutation<
      ApiResponse<unknown>,
      { investigation_id: string; tiger_id: string; image_url?: string; notes?: string }
    >({
      query: ({ investigation_id, tiger_id, image_url, notes }) => ({
        url: `/api/v1/investigations/${investigation_id}/evidence/link-tiger`,
        method: 'POST',
        body: { tiger_id, image_url, notes },
      }),
      invalidatesTags: ['Evidence', 'Investigation'],
    }),

    // =========================================================================
    // Investigation Tools
    // =========================================================================

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

    generateLeads: builder.mutation<ApiResponse<LeadGenerationResponse>, LeadGenerationRequest>({
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

    scheduleCrawl: builder.mutation<ApiResponse<CrawlScheduleResponse>, CrawlScheduleRequest>({
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

    // =========================================================================
    // Investigation Steps & Events
    // =========================================================================

    getInvestigationSteps: builder.query<ApiResponse<InvestigationStep[]>, string>({
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

    // =========================================================================
    // Export Endpoints
    // =========================================================================

    exportInvestigationJSON: builder.query<
      Blob,
      {
        investigation_id: string
        include_evidence?: boolean
        include_steps?: boolean
        include_metadata?: boolean
        audience?: ReportAudience
      }
    >({
      query: ({ investigation_id, include_evidence, include_steps, include_metadata, audience }) => ({
        url: `/api/v1/investigations/${investigation_id}/export/json`,
        params: { include_evidence, include_steps, include_metadata, audience },
        responseHandler: (response: Response) => response.blob(),
      }),
    }),

    exportInvestigationMarkdown: builder.query<
      Blob,
      {
        investigation_id: string
        include_evidence?: boolean
        include_steps?: boolean
        audience?: ReportAudience
      }
    >({
      query: ({ investigation_id, include_evidence, include_steps, audience }) => ({
        url: `/api/v1/investigations/${investigation_id}/export/markdown`,
        params: { include_evidence, include_steps, audience },
        responseHandler: (response: Response) => response.blob(),
      }),
    }),

    exportInvestigationPDF: builder.query<
      Blob,
      {
        investigation_id: string
        include_evidence?: boolean
        include_steps?: boolean
        audience?: ReportAudience
      }
    >({
      query: ({ investigation_id, include_evidence, include_steps, audience }) => ({
        url: `/api/v1/investigations/${investigation_id}/export/pdf`,
        params: { include_evidence, include_steps, audience },
        responseHandler: (response: Response) => response.blob(),
      }),
    }),

    exportInvestigationCSV: builder.query<
      Blob,
      {
        investigation_id: string
        data_type?: 'evidence' | 'steps' | 'summary'
        audience?: ReportAudience
      }
    >({
      query: ({ investigation_id, data_type, audience }) => ({
        url: `/api/v1/investigations/${investigation_id}/export/csv`,
        params: { data_type, audience },
        responseHandler: (response: Response) => response.blob(),
      }),
    }),
  }),
  overrideExisting: false,
})

export const {
  // Core Investigation CRUD
  useGetInvestigationsQuery,
  useGetInvestigationQuery,
  useCreateInvestigationMutation,
  useUpdateInvestigationMutation,
  useLaunchInvestigationMutation,
  useGetMCPToolsQuery,
  useGetInvestigationExtendedQuery,
  useResumeInvestigationMutation,
  usePauseInvestigationMutation,
  useBulkPauseInvestigationsMutation,
  useBulkArchiveInvestigationsMutation,
  // Investigation 2.0
  useLaunchInvestigation2Mutation,
  useGetInvestigation2Query,
  useGetInvestigation2ReportQuery,
  useGetInvestigation2MatchesQuery,
  useRegenerateInvestigation2ReportMutation,
  // Evidence
  useGetEvidenceQuery,
  useAddEvidenceMutation,
  useUploadEvidenceMutation,
  useLinkTigerEvidenceMutation,
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
  // Steps & Events
  useGetInvestigationStepsQuery,
  useGetInvestigationEventsQuery,
  // Export
  useExportInvestigationJSONQuery,
  useExportInvestigationMarkdownQuery,
  useExportInvestigationPDFQuery,
  useExportInvestigationCSVQuery,
} = investigationApi

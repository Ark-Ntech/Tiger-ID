/**
 * API Module Index
 *
 * This file re-exports all API modules and hooks for backward compatibility.
 * Import from this file to access any API functionality.
 *
 * Example usage:
 *   import { useGetTigersQuery, useGetInvestigationsQuery } from '@/app/api'
 *   import { api } from '@/app/api'
 */

// Export base API (for store configuration)
export { baseApi, TAG_TYPES } from './baseApi'
export type { TagType } from './baseApi'

// Export the api as an alias for baseApi (backward compatibility)
export { baseApi as api } from './baseApi'

// =========================================================================
// Auth API
// =========================================================================
export { authApi } from './authApi'
export {
  useGetCurrentUserQuery,
  useGetDashboardStatsQuery,
} from './authApi'

// =========================================================================
// Investigation API
// =========================================================================
export { investigationApi } from './investigationApi'
export {
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
} from './investigationApi'

// =========================================================================
// Tiger API
// =========================================================================
export { tigerApi } from './tigerApi'
export {
  // Tiger CRUD
  useGetTigersQuery,
  useGetTigerQuery,
  useCreateTigerMutation,
  // Tiger Identification
  useIdentifyTigerMutation,
  useIdentifyTigersBatchMutation,
  useIdentifyTigerImageMutation,
  useGetAvailableModelsQuery,
  // Tiger Registration
  useRegisterTigerMutation,
  useLaunchInvestigationFromTigerMutation,
  // Model Testing
  useTestModelMutation,
  useEvaluateModelMutation,
  useCompareModelsMutation,
  useBenchmarkModelMutation,
  useGetModelsAvailableQuery,
} from './tigerApi'

// =========================================================================
// Facility API
// =========================================================================
export { facilityApi } from './facilityApi'
export {
  // Facility CRUD
  useGetFacilitiesQuery,
  useGetFacilityQuery,
  useImportFacilitiesExcelMutation,
  // Templates
  useGetTemplatesQuery,
  useCreateTemplateMutation,
  useApplyTemplateMutation,
  // Saved Searches
  useGetSavedSearchesQuery,
  useCreateSavedSearchMutation,
} from './facilityApi'

// =========================================================================
// Verification API
// =========================================================================
export { verificationApi } from './verificationApi'
export {
  // Verification Tasks (Legacy)
  useGetVerificationTasksQuery,
  useUpdateVerificationTaskMutation,
  // Verification Queue
  useGetVerificationQueueQuery,
  useGetVerificationItemQuery,
  useUpdateVerificationStatusMutation,
  useGetVerificationStatsQuery,
} from './verificationApi'

// =========================================================================
// Discovery API
// =========================================================================
export { discoveryApi } from './discoveryApi'
export {
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
} from './discoveryApi'

// =========================================================================
// Analytics API
// =========================================================================
export { analyticsApi } from './analyticsApi'
export {
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
} from './analyticsApi'

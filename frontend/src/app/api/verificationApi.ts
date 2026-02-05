/**
 * Verification API endpoints.
 *
 * Handles all verification-related endpoints including:
 * - Verification tasks
 * - Verification queue management
 * - Verification statistics
 */
import { baseApi } from './baseApi'
import type {
  VerificationTask,
  ApiResponse,
  PaginatedResponse,
  GetVerificationQueueParams,
  VerificationQueuePaginatedResponse,
  VerificationQueueItemFull,
  VerificationStatusUpdate,
  VerificationStatusUpdateResponse,
  VerificationStatsResponse,
} from '../../types'

export const verificationApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // =========================================================================
    // Verification Tasks (Legacy)
    // =========================================================================

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

    // =========================================================================
    // Verification Queue
    // =========================================================================

    /**
     * Get paginated verification queue with filtering
     */
    getVerificationQueue: builder.query<
      ApiResponse<VerificationQueuePaginatedResponse>,
      GetVerificationQueueParams
    >({
      query: (params) => ({
        url: '/api/v1/verification/queue',
        params: {
          entity_type: params.entity_type,
          source: params.source,
          priority: params.priority,
          status: params.status,
          limit: params.limit,
          offset: params.offset,
        },
      }),
      providesTags: ['VerificationQueue'],
    }),

    /**
     * Get a single verification queue item with full details
     */
    getVerificationItem: builder.query<ApiResponse<VerificationQueueItemFull>, string>({
      query: (queueId) => `/api/v1/verification/queue/${queueId}`,
      providesTags: (_result, _error, queueId) => [{ type: 'VerificationQueue', id: queueId }],
    }),

    /**
     * Update verification status (approve/reject/in_review)
     */
    updateVerificationStatus: builder.mutation<
      ApiResponse<VerificationStatusUpdateResponse>,
      { queueId: string; data: VerificationStatusUpdate }
    >({
      query: ({ queueId, data }) => ({
        url: `/api/v1/verification/queue/${queueId}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (_result, _error, { queueId }) => [
        { type: 'VerificationQueue', id: queueId },
        'VerificationQueue',
        'Dashboard',
      ],
    }),

    /**
     * Get verification queue statistics
     */
    getVerificationStats: builder.query<ApiResponse<VerificationStatsResponse>, void>({
      query: () => '/api/v1/verification/stats',
      providesTags: ['VerificationQueue', 'Dashboard'],
    }),
  }),
  overrideExisting: false,
})

export const {
  // Verification Tasks (Legacy)
  useGetVerificationTasksQuery,
  useUpdateVerificationTaskMutation,
  // Verification Queue
  useGetVerificationQueueQuery,
  useGetVerificationItemQuery,
  useUpdateVerificationStatusMutation,
  useGetVerificationStatsQuery,
} = verificationApi

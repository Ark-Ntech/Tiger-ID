/**
 * Tiger API endpoints.
 *
 * Handles all tiger-related endpoints including:
 * - Tiger CRUD operations
 * - Tiger identification and registration
 * - Model testing and comparison
 */
import { baseApi } from './baseApi'
import type {
  Tiger,
  ApiResponse,
  PaginatedResponse,
  TigerIdentificationResult,
} from '../../types'

export const tigerApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // =========================================================================
    // Tiger CRUD
    // =========================================================================

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

    createTiger: builder.mutation<ApiResponse<unknown>, FormData>({
      query: (data) => ({
        url: '/api/v1/tigers',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Tiger'],
    }),

    // =========================================================================
    // Tiger Identification
    // =========================================================================

    identifyTiger: builder.mutation<ApiResponse<TigerIdentificationResult>, FormData>({
      query: (data) => ({
        url: '/api/v1/tigers/identify',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Tiger'],
    }),

    identifyTigersBatch: builder.mutation<
      ApiResponse<{ results: TigerIdentificationResult[] }>,
      FormData
    >({
      query: (data) => ({
        url: '/api/v1/tigers/identify/batch',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Tiger'],
    }),

    identifyTigerImage: builder.mutation<
      ApiResponse<TigerIdentificationResult>,
      {
        image: File
        model_name?: string
        similarity_threshold?: number
        use_all_models?: boolean
        ensemble_mode?: string
      }
    >({
      query: ({ image, model_name, similarity_threshold, use_all_models, ensemble_mode }) => {
        const formData = new FormData()
        formData.append('image', image)

        if (typeof similarity_threshold === 'number') {
          formData.append('similarity_threshold', similarity_threshold.toString())
        }
        if (model_name) {
          formData.append('model_name', model_name)
        }
        if (use_all_models) {
          formData.append('use_all_models', 'true')
        }
        if (ensemble_mode) {
          formData.append('ensemble_mode', ensemble_mode)
        }

        return {
          url: '/api/v1/tigers/identify',
          method: 'POST',
          body: formData,
        }
      },
      invalidatesTags: ['Tiger'],
    }),

    getAvailableModels: builder.query<ApiResponse<{ models: string[]; default: string }>, void>({
      query: () => '/api/v1/tigers/models',
      providesTags: ['Tiger'],
    }),

    // =========================================================================
    // Tiger Registration
    // =========================================================================

    registerTiger: builder.mutation<
      ApiResponse<unknown>,
      { name: string; images: File[]; alias?: string; notes?: string; model_name?: string }
    >({
      query: ({ name, images, alias, notes, model_name }) => {
        const formData = new FormData()
        formData.append('name', name)
        if (alias) {
          formData.append('alias', alias)
        }
        if (notes) {
          formData.append('notes', notes)
        }
        if (model_name) {
          formData.append('model_name', model_name)
        }
        images.forEach((image) => formData.append('images', image))

        return {
          url: '/api/v1/tigers',
          method: 'POST',
          body: formData,
        }
      },
      invalidatesTags: ['Tiger'],
    }),

    launchInvestigationFromTiger: builder.mutation<
      ApiResponse<unknown>,
      { tiger_id: string; tiger_name?: string }
    >({
      query: ({ tiger_id }) => ({
        url: `/api/v1/tigers/${tiger_id}/launch-investigation`,
        method: 'POST',
      }),
      invalidatesTags: ['Investigation', 'Tiger'],
    }),

    // =========================================================================
    // Model Testing Endpoints
    // =========================================================================

    testModel: builder.mutation<
      ApiResponse<{
        model: string
        total_images: number
        results: Array<{
          filename: string
          success: boolean
          embedding_shape?: number[]
          error?: string
        }>
      }>,
      FormData
    >({
      query: (data) => ({
        url: '/api/v1/models/test',
        method: 'POST',
        body: data,
      }),
    }),

    evaluateModel: builder.mutation<
      ApiResponse<{
        model: string
        query_count: number
        gallery_count: number
        embedding_dim: number
        results: Array<{
          query_image: string
          top_matches: Array<{ gallery_image: string; similarity: number }>
        }>
      }>,
      FormData
    >({
      query: (data) => ({
        url: '/api/v1/models/evaluate',
        method: 'POST',
        body: data,
      }),
    }),

    compareModels: builder.mutation<
      ApiResponse<{
        models_compared: string[]
        results: Record<
          string,
          {
            success: boolean
            query_processed?: number
            gallery_processed?: number
            processing_time_seconds?: number
            error?: string
          }
        >
        best_model?: string
      }>,
      FormData
    >({
      query: (data) => ({
        url: '/api/v1/models/compare',
        method: 'POST',
        body: data,
      }),
    }),

    benchmarkModel: builder.mutation<
      ApiResponse<{
        model: string
        num_runs: number
        avg_time_ms: number
        min_time_ms: number
        max_time_ms: number
        throughput_images_per_sec: number
      }>,
      FormData
    >({
      query: (data) => ({
        url: '/api/v1/models/benchmark',
        method: 'POST',
        body: data,
      }),
    }),

    getModelsAvailable: builder.query<
      ApiResponse<{ models: Record<string, unknown>; default: string }>,
      void
    >({
      query: () => '/api/v1/models/available',
    }),
  }),
  overrideExisting: false,
})

export const {
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
} = tigerApi

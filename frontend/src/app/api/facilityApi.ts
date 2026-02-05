/**
 * Facility API endpoints.
 *
 * Handles all facility-related endpoints including:
 * - Facility CRUD operations
 * - Facility import
 * - Template and saved search management
 */
import { baseApi } from './baseApi'
import type {
  Facility,
  Template,
  SavedSearch,
  ApiResponse,
  PaginatedResponse,
} from '../../types'

export const facilityApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // =========================================================================
    // Facility CRUD
    // =========================================================================

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
      ApiResponse<{
        message: string
        stats: { created: number; updated: number; skipped: number; errors: unknown[] }
      }>,
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

    // =========================================================================
    // Template Management
    // =========================================================================

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

    applyTemplate: builder.mutation<
      ApiResponse<unknown>,
      { template_id: string; investigation_id: string }
    >({
      query: ({ template_id, investigation_id }) => ({
        url: `/api/v1/templates/${template_id}/apply`,
        method: 'POST',
        params: { investigation_id },
      }),
      invalidatesTags: ['Template', 'Investigation'],
    }),

    // =========================================================================
    // Saved Search Management
    // =========================================================================

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
  }),
  overrideExisting: false,
})

export const {
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
} = facilityApi

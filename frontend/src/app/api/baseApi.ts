/**
 * Base RTK Query API configuration.
 *
 * This file sets up the base API with authentication, error handling,
 * and tag types. Domain-specific endpoints are injected via injectEndpoints.
 */
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import type { RootState } from '../store'

// In development, use Vite proxy (empty baseUrl uses relative paths which go through proxy)
// In production, use VITE_API_URL environment variable
const baseUrl = import.meta.env.PROD
  ? (import.meta.env.VITE_API_URL || 'http://localhost:8000')
  : '' // Empty string in dev mode uses Vite proxy

/**
 * Tag types for RTK Query cache invalidation.
 * Each domain module can use these tags to manage cache behavior.
 */
export const TAG_TYPES = [
  'User',
  'Investigation',
  'Tiger',
  'Facility',
  'Template',
  'SavedSearch',
  'Verification',
  'VerificationQueue',
  'Evidence',
  'Dashboard',
  'Analytics',
  'Annotation',
  'Export',
  'Integration',
  'Discovery',
] as const

export type TagType = (typeof TAG_TYPES)[number]

/**
 * Base API with authentication and error handling.
 * Domain-specific endpoints are injected from separate modules.
 */
export const baseApi = createApi({
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
  tagTypes: TAG_TYPES,
  endpoints: () => ({}),
})

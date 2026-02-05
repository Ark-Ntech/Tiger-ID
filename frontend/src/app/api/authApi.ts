/**
 * Auth API endpoints.
 *
 * Handles authentication and user-related endpoints using RTK Query.
 * Replaces axios-based createAsyncThunk implementations in authSlice.
 */
import { baseApi } from './baseApi'
import type {
  User,
  AuthResponse,
  LoginCredentials,
  ApiResponse,
  DashboardStats,
} from '../../types'

/**
 * Registration request data
 */
export interface RegisterData {
  username: string
  email: string
  password: string
  full_name?: string
}

/**
 * Password reset request data
 */
export interface PasswordResetRequest {
  email: string
}

/**
 * Password reset confirmation data
 */
export interface PasswordResetConfirm {
  token: string
  new_password: string
}

/**
 * Token refresh response
 */
export interface RefreshTokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export const authApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    /**
     * Login with username and password
     */
    login: builder.mutation<AuthResponse, LoginCredentials>({
      query: (credentials) => ({
        url: '/api/auth/login',
        method: 'POST',
        body: credentials,
      }),
      invalidatesTags: ['User', 'Dashboard'],
    }),

    /**
     * Logout the current user
     */
    logout: builder.mutation<void, void>({
      query: () => ({
        url: '/api/auth/logout',
        method: 'POST',
      }),
      // Invalidate all user-related caches on logout
      invalidatesTags: ['User', 'Dashboard', 'Investigation', 'Tiger', 'Facility'],
    }),

    /**
     * Register a new user account
     */
    register: builder.mutation<AuthResponse, RegisterData>({
      query: (data) => ({
        url: '/api/auth/register',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['User'],
    }),

    /**
     * Get current authenticated user
     */
    getCurrentUser: builder.query<ApiResponse<User>, void>({
      query: () => '/api/auth/me',
      providesTags: ['User'],
    }),

    /**
     * Refresh the authentication token
     */
    refreshToken: builder.mutation<RefreshTokenResponse, void>({
      query: () => ({
        url: '/api/auth/refresh',
        method: 'POST',
      }),
    }),

    /**
     * Request a password reset email
     */
    requestPasswordReset: builder.mutation<{ message: string }, PasswordResetRequest>({
      query: (data) => ({
        url: '/api/auth/password-reset/request',
        method: 'POST',
        body: data,
      }),
    }),

    /**
     * Confirm password reset with token
     */
    confirmPasswordReset: builder.mutation<{ message: string }, PasswordResetConfirm>({
      query: (data) => ({
        url: '/api/auth/password-reset/confirm',
        method: 'POST',
        body: data,
      }),
    }),

    /**
     * Dashboard statistics
     */
    getDashboardStats: builder.query<ApiResponse<DashboardStats>, void>({
      query: () => '/api/v1/dashboard/stats',
      providesTags: ['Dashboard'],
    }),
  }),
  overrideExisting: true,
})

export const {
  useLoginMutation,
  useLogoutMutation,
  useRegisterMutation,
  useGetCurrentUserQuery,
  useRefreshTokenMutation,
  useRequestPasswordResetMutation,
  useConfirmPasswordResetMutation,
  useGetDashboardStatsQuery,
} = authApi

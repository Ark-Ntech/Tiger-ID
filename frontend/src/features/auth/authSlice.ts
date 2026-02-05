/**
 * Auth slice for Redux state management.
 *
 * Manages authentication state (user, token, isAuthenticated).
 * Listens to RTK Query auth endpoints for state updates.
 */
import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { User } from '../../types'
import { authApi } from '../../app/api/authApi'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  loading: boolean
  error: string | null
}

const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  loading: false,
  error: null,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    /**
     * Clear any auth error
     */
    clearError: (state) => {
      state.error = null
    },

    /**
     * Manually set the user (e.g., from getCurrentUser query)
     */
    setUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload
    },

    /**
     * Manually trigger logout (used by baseApi on 401)
     */
    logout: (state) => {
      state.user = null
      state.token = null
      state.isAuthenticated = false
      state.error = null
      localStorage.removeItem('token')
    },
  },
  extraReducers: (builder) => {
    // =========================================================================
    // Login mutation
    // =========================================================================
    builder
      .addMatcher(authApi.endpoints.login.matchPending, (state) => {
        state.loading = true
        state.error = null
      })
      .addMatcher(authApi.endpoints.login.matchFulfilled, (state, action) => {
        state.loading = false
        state.isAuthenticated = true
        state.user = action.payload.user
        state.token = action.payload.access_token
        localStorage.setItem('token', action.payload.access_token)
      })
      .addMatcher(authApi.endpoints.login.matchRejected, (state, action) => {
        state.loading = false
        state.error = (action.payload as any)?.data?.message ||
                      (action.payload as any)?.data?.detail ||
                      action.error?.message ||
                      'Login failed'
      })

    // =========================================================================
    // Logout mutation
    // =========================================================================
    builder
      .addMatcher(authApi.endpoints.logout.matchPending, (state) => {
        state.loading = true
      })
      .addMatcher(authApi.endpoints.logout.matchFulfilled, (state) => {
        state.loading = false
        state.user = null
        state.token = null
        state.isAuthenticated = false
        localStorage.removeItem('token')
      })
      .addMatcher(authApi.endpoints.logout.matchRejected, (state) => {
        // Clear auth state even if API call fails
        state.loading = false
        state.user = null
        state.token = null
        state.isAuthenticated = false
        localStorage.removeItem('token')
      })

    // =========================================================================
    // Register mutation
    // =========================================================================
    builder
      .addMatcher(authApi.endpoints.register.matchPending, (state) => {
        state.loading = true
        state.error = null
      })
      .addMatcher(authApi.endpoints.register.matchFulfilled, (state, action) => {
        state.loading = false
        state.isAuthenticated = true
        state.user = action.payload.user
        state.token = action.payload.access_token
        localStorage.setItem('token', action.payload.access_token)
      })
      .addMatcher(authApi.endpoints.register.matchRejected, (state, action) => {
        state.loading = false
        state.error = (action.payload as any)?.data?.message ||
                      (action.payload as any)?.data?.detail ||
                      action.error?.message ||
                      'Registration failed'
      })

    // =========================================================================
    // Request password reset mutation
    // =========================================================================
    builder
      .addMatcher(authApi.endpoints.requestPasswordReset.matchPending, (state) => {
        state.loading = true
        state.error = null
      })
      .addMatcher(authApi.endpoints.requestPasswordReset.matchFulfilled, (state) => {
        state.loading = false
      })
      .addMatcher(authApi.endpoints.requestPasswordReset.matchRejected, (state, action) => {
        state.loading = false
        state.error = (action.payload as any)?.data?.message ||
                      (action.payload as any)?.data?.detail ||
                      action.error?.message ||
                      'Password reset request failed'
      })

    // =========================================================================
    // Confirm password reset mutation
    // =========================================================================
    builder
      .addMatcher(authApi.endpoints.confirmPasswordReset.matchPending, (state) => {
        state.loading = true
        state.error = null
      })
      .addMatcher(authApi.endpoints.confirmPasswordReset.matchFulfilled, (state) => {
        state.loading = false
      })
      .addMatcher(authApi.endpoints.confirmPasswordReset.matchRejected, (state, action) => {
        state.loading = false
        state.error = (action.payload as any)?.data?.message ||
                      (action.payload as any)?.data?.detail ||
                      action.error?.message ||
                      'Password reset failed'
      })

    // =========================================================================
    // Refresh token mutation
    // =========================================================================
    builder
      .addMatcher(authApi.endpoints.refreshToken.matchFulfilled, (state, action) => {
        state.token = action.payload.access_token
        localStorage.setItem('token', action.payload.access_token)
      })
      .addMatcher(authApi.endpoints.refreshToken.matchRejected, (state) => {
        // If refresh fails, clear auth state
        state.user = null
        state.token = null
        state.isAuthenticated = false
        localStorage.removeItem('token')
      })

    // =========================================================================
    // Get current user query
    // =========================================================================
    builder
      .addMatcher(authApi.endpoints.getCurrentUser.matchFulfilled, (state, action) => {
        if (action.payload.data) {
          state.user = action.payload.data
          state.isAuthenticated = true
        }
      })
      .addMatcher(authApi.endpoints.getCurrentUser.matchRejected, (state) => {
        // If we can't get the user, clear auth state
        state.user = null
        state.token = null
        state.isAuthenticated = false
        localStorage.removeItem('token')
      })
  },
})

export const { clearError, setUser, logout } = authSlice.actions
export default authSlice.reducer

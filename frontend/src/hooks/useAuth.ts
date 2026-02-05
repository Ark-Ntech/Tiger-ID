/**
 * Authentication hook using RTK Query.
 *
 * Provides a consistent interface for authentication operations
 * while using RTK Query mutations under the hood.
 */
import { useCallback } from 'react'
import { useAppSelector } from '../app/hooks'
import {
  useLoginMutation,
  useLogoutMutation,
  useRegisterMutation,
  useRequestPasswordResetMutation,
  useConfirmPasswordResetMutation,
  useRefreshTokenMutation,
  useGetCurrentUserQuery,
  type RegisterData,
} from '../app/api/authApi'
import type { LoginCredentials } from '../types'

export const useAuth = () => {
  // Get auth state from Redux store
  const { user, isAuthenticated, loading, error, token } = useAppSelector(
    (state) => state.auth
  )

  // RTK Query mutations
  const [loginMutation, { isLoading: isLoginLoading }] = useLoginMutation()
  const [logoutMutation, { isLoading: isLogoutLoading }] = useLogoutMutation()
  const [registerMutation, { isLoading: isRegisterLoading }] = useRegisterMutation()
  const [requestPasswordResetMutation, { isLoading: isRequestingReset }] =
    useRequestPasswordResetMutation()
  const [confirmPasswordResetMutation, { isLoading: isConfirmingReset }] =
    useConfirmPasswordResetMutation()
  const [refreshTokenMutation] = useRefreshTokenMutation()

  // Fetch current user if we have a token but no user data
  const { refetch: refetchUser } = useGetCurrentUserQuery(undefined, {
    skip: !token || !!user,
  })

  /**
   * Login with username and password
   */
  const login = useCallback(
    async (credentials: LoginCredentials) => {
      const result = await loginMutation(credentials).unwrap()
      return result
    },
    [loginMutation]
  )

  /**
   * Logout the current user
   */
  const logout = useCallback(async () => {
    try {
      await logoutMutation().unwrap()
    } catch {
      // Logout locally even if API call fails
      // The authSlice handles clearing state on rejection
    }
  }, [logoutMutation])

  /**
   * Register a new user account
   */
  const register = useCallback(
    async (data: RegisterData) => {
      const result = await registerMutation(data).unwrap()
      return result
    },
    [registerMutation]
  )

  /**
   * Request a password reset email
   */
  const requestPasswordReset = useCallback(
    async (email: string) => {
      const result = await requestPasswordResetMutation({ email }).unwrap()
      return result
    },
    [requestPasswordResetMutation]
  )

  /**
   * Confirm password reset with token and new password
   */
  const confirmPasswordReset = useCallback(
    async (token: string, newPassword: string) => {
      const result = await confirmPasswordResetMutation({
        token,
        new_password: newPassword,
      }).unwrap()
      return result
    },
    [confirmPasswordResetMutation]
  )

  /**
   * Refresh the authentication token
   */
  const refreshToken = useCallback(async () => {
    const result = await refreshTokenMutation().unwrap()
    return result
  }, [refreshTokenMutation])

  /**
   * Refetch the current user data
   */
  const fetchCurrentUser = useCallback(() => {
    return refetchUser()
  }, [refetchUser])

  return {
    // State
    user,
    isAuthenticated,
    loading: loading || isLoginLoading || isLogoutLoading || isRegisterLoading,
    error,
    token,

    // Loading states for individual operations
    isLoginLoading,
    isLogoutLoading,
    isRegisterLoading,
    isRequestingReset,
    isConfirmingReset,

    // Actions
    login,
    logout,
    register,
    requestPasswordReset,
    confirmPasswordReset,
    refreshToken,
    fetchCurrentUser,
  }
}

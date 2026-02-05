import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import type { ReactNode } from 'react'
import { useAuth } from './useAuth'
import authReducer from '../features/auth/authSlice'
import { baseApi } from '../app/api/baseApi'
import type { User } from '../types'

// Mock fetch for RTK Query
const mockFetch = vi.fn()
global.fetch = mockFetch

interface TestAuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  loading: boolean
  error: string | null
}

const createTestStore = (initialState?: Partial<TestAuthState>) => {
  const defaultState: TestAuthState = {
    user: null,
    token: null,
    isAuthenticated: false,
    loading: false,
    error: null,
    ...initialState,
  }

  return configureStore({
    reducer: {
      [baseApi.reducerPath]: baseApi.reducer,
      auth: authReducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(baseApi.middleware),
    preloadedState: {
      auth: defaultState as any, // Cast to avoid strict type checking in tests
    },
  })
}

const wrapper = (store: ReturnType<typeof createTestStore>) => {
  return function TestWrapper({ children }: { children: ReactNode }) {
    return <Provider store={store}>{children}</Provider>
  }
}

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
  })

  describe('initial state', () => {
    it('should return initial auth state', () => {
      const store = createTestStore()
      const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      expect(result.current.user).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.loading).toBe(false)
      expect(result.current.error).toBeNull()
    })

    it('should return user when authenticated', () => {
      const mockUser = {
        id: '123',
        username: 'testuser',
        email: 'test@example.com',
        role: 'investigator' as const,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }
      const store = createTestStore({
        user: mockUser,
        isAuthenticated: true,
        token: 'test-token',
      })

      const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
    })

    it('should return loading state', () => {
      const store = createTestStore({ loading: true })
      const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      expect(result.current.loading).toBe(true)
    })

    it('should return error state', () => {
      const store = createTestStore({ error: 'Login failed' })
      const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      expect(result.current.error).toBe('Login failed')
    })
  })

  describe('login function', () => {
    it('should return login function', () => {
      const store = createTestStore()
      const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      expect(typeof result.current.login).toBe('function')
    })

    it('should call login mutation with credentials', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: 'new-token',
          token_type: 'bearer',
          user: {
            id: '123',
            username: 'testuser',
            email: 'test@example.com',
            role: 'investigator',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
          expires_in: 3600,
        }),
      })

      const store = createTestStore()
      const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      const credentials = { username: 'testuser', password: 'password123' }

      await act(async () => {
        await result.current.login(credentials)
      })

      // Verify fetch was called with correct endpoint
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/login'),
        expect.objectContaining({
          method: 'POST',
        })
      )
    })
  })

  describe('logout function', () => {
    it('should return logout function', () => {
      const store = createTestStore()
      const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      expect(typeof result.current.logout).toBe('function')
    })

    it('should call logout mutation', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      const store = createTestStore({
        user: {
          id: '123',
          username: 'test',
          email: 'test@test.com',
          role: 'investigator' as const,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        isAuthenticated: true,
        token: 'test-token',
      })
      const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      await act(async () => {
        await result.current.logout()
      })

      // Verify fetch was called with correct endpoint
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/logout'),
        expect.objectContaining({
          method: 'POST',
        })
      )
    })
  })

  describe('register function', () => {
    it('should return register function', () => {
      const store = createTestStore()
      const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      expect(typeof result.current.register).toBe('function')
    })

    it('should call register mutation with data', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: 'new-token',
          token_type: 'bearer',
          user: {
            id: '123',
            username: 'newuser',
            email: 'new@example.com',
            role: 'investigator',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
          expires_in: 3600,
        }),
      })

      const store = createTestStore()
      const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      const registerData = {
        username: 'newuser',
        email: 'new@example.com',
        password: 'password123',
        full_name: 'New User',
      }

      await act(async () => {
        await result.current.register(registerData)
      })

      // Verify fetch was called with correct endpoint
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/register'),
        expect.objectContaining({
          method: 'POST',
        })
      )
    })

    it('should call register without optional full_name', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: 'new-token',
          token_type: 'bearer',
          user: {
            id: '123',
            username: 'newuser',
            email: 'new@example.com',
            role: 'investigator',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
          expires_in: 3600,
        }),
      })

      const store = createTestStore()
      const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      const registerData = {
        username: 'newuser',
        email: 'new@example.com',
        password: 'password123',
      }

      await act(async () => {
        await result.current.register(registerData)
      })

      // Verify fetch was called
      expect(mockFetch).toHaveBeenCalled()
    })
  })

  describe('password reset functions', () => {
    it('should return requestPasswordReset function', () => {
      const store = createTestStore()
      const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      expect(typeof result.current.requestPasswordReset).toBe('function')
    })

    it('should return confirmPasswordReset function', () => {
      const store = createTestStore()
      const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      expect(typeof result.current.confirmPasswordReset).toBe('function')
    })

    it('should call requestPasswordReset mutation', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Password reset email sent' }),
      })

      const store = createTestStore()
      const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      await act(async () => {
        await result.current.requestPasswordReset('test@example.com')
      })

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/password-reset/request'),
        expect.objectContaining({
          method: 'POST',
        })
      )
    })

    it('should call confirmPasswordReset mutation', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Password reset successful' }),
      })

      const store = createTestStore()
      const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      await act(async () => {
        await result.current.confirmPasswordReset('reset-token', 'newpassword123')
      })

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/password-reset/confirm'),
        expect.objectContaining({
          method: 'POST',
        })
      )
    })
  })

  describe('return value structure', () => {
    it('should return all expected properties', () => {
      const store = createTestStore()
      const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      // State
      expect(result.current).toHaveProperty('user')
      expect(result.current).toHaveProperty('isAuthenticated')
      expect(result.current).toHaveProperty('loading')
      expect(result.current).toHaveProperty('error')
      expect(result.current).toHaveProperty('token')

      // Loading states
      expect(result.current).toHaveProperty('isLoginLoading')
      expect(result.current).toHaveProperty('isLogoutLoading')
      expect(result.current).toHaveProperty('isRegisterLoading')
      expect(result.current).toHaveProperty('isRequestingReset')
      expect(result.current).toHaveProperty('isConfirmingReset')

      // Functions
      expect(result.current).toHaveProperty('login')
      expect(result.current).toHaveProperty('logout')
      expect(result.current).toHaveProperty('register')
      expect(result.current).toHaveProperty('requestPasswordReset')
      expect(result.current).toHaveProperty('confirmPasswordReset')
      expect(result.current).toHaveProperty('refreshToken')
      expect(result.current).toHaveProperty('fetchCurrentUser')
    })

    it('should return stable function references', () => {
      const store = createTestStore()
      const { result, rerender } = renderHook(() => useAuth(), { wrapper: wrapper(store) })

      const firstLogin = result.current.login
      const firstLogout = result.current.logout
      const firstRegister = result.current.register

      rerender()

      // Functions should be stable (same reference) due to useCallback
      expect(result.current.login).toBe(firstLogin)
      expect(result.current.logout).toBe(firstLogout)
      expect(result.current.register).toBe(firstRegister)
    })
  })
})

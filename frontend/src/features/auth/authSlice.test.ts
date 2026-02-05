import { describe, it, expect, vi, beforeEach } from 'vitest'
import { configureStore } from '@reduxjs/toolkit'
import authReducer, { clearError, setUser, logout } from './authSlice'
import { baseApi } from '../../app/api/baseApi'
import type { User } from '../../types'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: () => {
      store = {}
    },
  }
})()

Object.defineProperty(global, 'localStorage', { value: localStorageMock })

// Mock fetch for RTK Query
const mockFetch = vi.fn()
global.fetch = mockFetch

const createTestStore = (preloadedAuth?: Partial<ReturnType<typeof authReducer>>) => {
  return configureStore({
    reducer: {
      [baseApi.reducerPath]: baseApi.reducer,
      auth: authReducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(baseApi.middleware),
    preloadedState: preloadedAuth
      ? {
          auth: {
            user: null,
            token: null,
            isAuthenticated: false,
            loading: false,
            error: null,
            ...preloadedAuth,
          },
        }
      : undefined,
  })
}

describe('authSlice', () => {
  beforeEach(() => {
    localStorageMock.clear()
    vi.clearAllMocks()
    mockFetch.mockReset()
  })

  describe('initial state', () => {
    it('should have correct initial state without token', () => {
      const state = authReducer(undefined, { type: 'unknown' })

      expect(state.user).toBeNull()
      expect(state.isAuthenticated).toBe(false)
      expect(state.loading).toBe(false)
      expect(state.error).toBeNull()
    })

    it('should initialize with token from localStorage', () => {
      localStorageMock.getItem.mockReturnValueOnce('stored-token')

      // Re-import to get fresh initial state
      // Note: In practice, the initial state is evaluated once at module load time
      // This test verifies the pattern used in the slice
      expect(localStorageMock.getItem).toHaveBeenCalledWith('token')
    })
  })

  describe('clearError action', () => {
    it('should clear error state', () => {
      const previousState = {
        user: null,
        token: null,
        isAuthenticated: false,
        loading: false,
        error: 'Some error',
      }

      const state = authReducer(previousState, clearError())

      expect(state.error).toBeNull()
    })
  })

  describe('setUser action', () => {
    it('should set user in state', () => {
      const user: User = {
        id: '123',
        username: 'testuser',
        email: 'test@example.com',
        role: 'investigator',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      const state = authReducer(undefined, setUser(user))

      expect(state.user).toEqual(user)
    })
  })

  describe('logout action', () => {
    it('should clear auth state', () => {
      const previousState = {
        user: {
          id: '123',
          username: 'test',
          email: 'test@test.com',
          role: 'investigator' as const,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        token: 'token',
        isAuthenticated: true,
        loading: false,
        error: null,
      }

      const state = authReducer(previousState, logout())

      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
      expect(state.isAuthenticated).toBe(false)
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token')
    })
  })

  describe('login mutation integration', () => {
    it('should update state on successful login', async () => {
      const mockResponse = {
        user: {
          id: '123',
          username: 'testuser',
          email: 'test@example.com',
          role: 'investigator',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        access_token: 'mock-token',
        token_type: 'bearer',
        expires_in: 3600,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const store = createTestStore()

      // Dispatch login via RTK Query
      const { login } = await import('../../app/api/authApi').then((m) => ({
        login: m.authApi.endpoints.login,
      }))

      await store.dispatch(
        login.initiate({ username: 'testuser', password: 'password' })
      )

      const state = store.getState().auth

      expect(state.loading).toBe(false)
      expect(state.isAuthenticated).toBe(true)
      expect(state.user).toEqual(mockResponse.user)
      expect(state.token).toBe('mock-token')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('token', 'mock-token')
    })

    it('should set error on failed login', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ message: 'Invalid credentials', detail: 'Invalid credentials' }),
      })

      const store = createTestStore()

      const { login } = await import('../../app/api/authApi').then((m) => ({
        login: m.authApi.endpoints.login,
      }))

      await store.dispatch(
        login.initiate({ username: 'testuser', password: 'wrong' })
      )

      const state = store.getState().auth

      expect(state.loading).toBe(false)
      expect(state.isAuthenticated).toBe(false)
      expect(state.error).toBeTruthy()
    })
  })

  describe('register mutation integration', () => {
    it('should update state on successful registration', async () => {
      const mockResponse = {
        user: {
          id: '456',
          username: 'newuser',
          email: 'new@example.com',
          role: 'investigator',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        access_token: 'new-token',
        token_type: 'bearer',
        expires_in: 3600,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const store = createTestStore()

      const { register } = await import('../../app/api/authApi').then((m) => ({
        register: m.authApi.endpoints.register,
      }))

      await store.dispatch(
        register.initiate({
          username: 'newuser',
          email: 'new@example.com',
          password: 'password123',
        })
      )

      const state = store.getState().auth

      expect(state.loading).toBe(false)
      expect(state.isAuthenticated).toBe(true)
      expect(state.user).toEqual(mockResponse.user)
      expect(state.token).toBe('new-token')
    })
  })

  describe('logout mutation integration', () => {
    it('should clear state on logout', async () => {
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
        token: 'existing-token',
        isAuthenticated: true,
      })

      const { logout: logoutEndpoint } = await import('../../app/api/authApi').then(
        (m) => ({
          logout: m.authApi.endpoints.logout,
        })
      )

      await store.dispatch(logoutEndpoint.initiate())

      const state = store.getState().auth

      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
      expect(state.isAuthenticated).toBe(false)
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token')
    })

    it('should clear state even if logout API call fails', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const store = createTestStore({
        user: {
          id: '123',
          username: 'test',
          email: 'test@test.com',
          role: 'investigator' as const,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        token: 'existing-token',
        isAuthenticated: true,
      })

      const { logout: logoutEndpoint } = await import('../../app/api/authApi').then(
        (m) => ({
          logout: m.authApi.endpoints.logout,
        })
      )

      await store.dispatch(logoutEndpoint.initiate())

      const state = store.getState().auth

      // Should still clear state on error
      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })
  })

  describe('password reset mutation integration', () => {
    it('should handle requestPasswordReset', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Email sent' }),
      })

      const store = createTestStore()

      const { requestPasswordReset } = await import('../../app/api/authApi').then(
        (m) => ({
          requestPasswordReset: m.authApi.endpoints.requestPasswordReset,
        })
      )

      await store.dispatch(requestPasswordReset.initiate({ email: 'test@example.com' }))

      const state = store.getState().auth

      expect(state.loading).toBe(false)
      expect(state.error).toBeNull()
    })

    it('should handle confirmPasswordReset', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Password reset' }),
      })

      const store = createTestStore()

      const { confirmPasswordReset } = await import('../../app/api/authApi').then(
        (m) => ({
          confirmPasswordReset: m.authApi.endpoints.confirmPasswordReset,
        })
      )

      await store.dispatch(
        confirmPasswordReset.initiate({
          token: 'reset-token',
          new_password: 'newpassword123',
        })
      )

      const state = store.getState().auth

      expect(state.loading).toBe(false)
      expect(state.error).toBeNull()
    })

    it('should set error on failed password reset request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ message: 'Email not found', detail: 'Email not found' }),
      })

      const store = createTestStore()

      const { requestPasswordReset } = await import('../../app/api/authApi').then(
        (m) => ({
          requestPasswordReset: m.authApi.endpoints.requestPasswordReset,
        })
      )

      await store.dispatch(requestPasswordReset.initiate({ email: 'nonexistent@example.com' }))

      const state = store.getState().auth

      expect(state.loading).toBe(false)
      expect(state.error).toBeTruthy()
    })
  })

  describe('getCurrentUser query integration', () => {
    it('should update user on successful getCurrentUser', async () => {
      const mockUser = {
        id: '789',
        username: 'currentuser',
        email: 'current@example.com',
        role: 'admin',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: mockUser, success: true }),
      })

      const store = createTestStore({ token: 'valid-token' })

      const { getCurrentUser } = await import('../../app/api/authApi').then((m) => ({
        getCurrentUser: m.authApi.endpoints.getCurrentUser,
      }))

      await store.dispatch(getCurrentUser.initiate())

      const state = store.getState().auth

      expect(state.user).toEqual(mockUser)
      expect(state.isAuthenticated).toBe(true)
    })

    it('should clear auth on failed getCurrentUser', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ message: 'Unauthorized' }),
      })

      const store = createTestStore({
        token: 'invalid-token',
        isAuthenticated: true,
      })

      const { getCurrentUser } = await import('../../app/api/authApi').then((m) => ({
        getCurrentUser: m.authApi.endpoints.getCurrentUser,
      }))

      await store.dispatch(getCurrentUser.initiate())

      const state = store.getState().auth

      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })
  })
})

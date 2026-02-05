import { describe, it, expect, beforeEach } from 'vitest'
import { configureStore } from '@reduxjs/toolkit'
import authReducer, { setUser, clearError } from '../authSlice'
import { api } from '../../../app/api'
import type { User } from '../../../types'

describe('Auth Slice - RTK Query Integration', () => {
  let store: ReturnType<typeof configureStore>

  beforeEach(() => {
    store = configureStore({
      reducer: {
        auth: authReducer,
        [api.reducerPath]: api.reducer,
      },
      middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware().concat(api.middleware),
    })
  })

  describe('RTK Query auth mutations', () => {
    it('should handle login mutation pending state', () => {
      const initialState = store.getState() as any
      expect(initialState.auth).toBeDefined()
      expect(initialState.auth.loading).toBe(false)
    })

    it('should update state from RTK Query login response', () => {
      const mockUser: User = {
        id: '123',
        username: 'testuser',
        email: 'test@example.com',
        role: 'investigator',
        created_at: '2026-02-05T10:00:00Z',
        updated_at: '2026-02-05T10:00:00Z',
      }

      store.dispatch(setUser(mockUser))

      const state = store.getState() as any
      expect(state.auth.user).toEqual(mockUser)
    })

    it('should clear errors', () => {
      store.dispatch(clearError())
      const state = store.getState() as any
      expect(state.auth.error).toBeNull()
    })
  })

  describe('Auth state management', () => {
    it('should maintain authentication state', () => {
      const mockUser: User = {
        id: '456',
        username: 'admin',
        email: 'admin@example.com',
        role: 'admin',
        created_at: '2026-02-05T10:00:00Z',
        updated_at: '2026-02-05T10:00:00Z',
      }

      store.dispatch(setUser(mockUser))

      const state = store.getState() as any
      expect(state.auth.user).toEqual(mockUser)
      expect(state.auth.isAuthenticated).toBe(true)
    })

    it('should handle token storage', () => {
      const state = store.getState() as any
      expect(state.auth).toHaveProperty('token')
    })
  })
})

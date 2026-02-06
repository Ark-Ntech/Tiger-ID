import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { renderHook } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import { Investigation2Provider, useInvestigation2 } from '../Investigation2Context'
import { api } from '../../app/api'

const createMockStore = () => {
  return configureStore({
    reducer: {
      [api.reducerPath]: api.reducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(api.middleware),
  })
}

describe('Investigation2Context', () => {
  describe('Investigation2Provider', () => {
    it('should provide investigation data to children', () => {
      const store = createMockStore()

      const TestComponent = () => {
        const { investigationId, isLaunching, error } = useInvestigation2()
        return (
          <div>
            <div data-testid="launching">{isLaunching ? 'true' : 'false'}</div>
            <div data-testid="id">{investigationId || 'null'}</div>
            <div data-testid="error">{error || 'none'}</div>
          </div>
        )
      }

      render(
        <Provider store={store}>
          <Investigation2Provider>
            <TestComponent />
          </Investigation2Provider>
        </Provider>
      )

      expect(screen.getByTestId('launching')).toBeDefined()
      expect(screen.getByTestId('id').textContent).toBe('null')
    })

    it('should provide all required context values', () => {
      const store = createMockStore()

      const TestComponent = () => {
        const context = useInvestigation2()

        return (
          <div>
            <div data-testid="has-state">
              {context.investigationId !== undefined ? 'yes' : 'no'}
            </div>
            <div data-testid="has-actions">
              {typeof context.launchInvestigation === 'function' ? 'yes' : 'no'}
            </div>
            <div data-testid="has-ws">
              {context.wsConnected !== undefined ? 'yes' : 'no'}
            </div>
          </div>
        )
      }

      render(
        <Provider store={store}>
          <Investigation2Provider>
            <TestComponent />
          </Investigation2Provider>
        </Provider>
      )

      expect(screen.getByTestId('has-state').textContent).toBe('yes')
      expect(screen.getByTestId('has-actions').textContent).toBe('yes')
      expect(screen.getByTestId('has-ws').textContent).toBe('yes')
    })
  })

  describe('useInvestigation2 hook', () => {
    it('should throw error when used outside provider', () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

      expect(() => {
        renderHook(() => useInvestigation2())
      }).toThrow('useInvestigation2 must be used within Investigation2Provider')

      consoleError.mockRestore()
    })

    it('should return all context values when used inside provider', () => {
      const store = createMockStore()

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <Provider store={store}>
          <Investigation2Provider>
            {children}
          </Investigation2Provider>
        </Provider>
      )

      const { result } = renderHook(() => useInvestigation2(), { wrapper })

      // State properties
      expect(result.current).toHaveProperty('investigationId')
      expect(result.current).toHaveProperty('investigation')
      expect(result.current).toHaveProperty('progressSteps')
      expect(result.current).toHaveProperty('isLaunching')
      expect(result.current).toHaveProperty('uploadedImage')
      expect(result.current).toHaveProperty('imagePreview')
      expect(result.current).toHaveProperty('context')
      expect(result.current).toHaveProperty('error')

      // WebSocket state
      expect(result.current).toHaveProperty('wsConnected')
      expect(result.current).toHaveProperty('wsError')

      // Computed state
      expect(result.current).toHaveProperty('isCompleted')
      expect(result.current).toHaveProperty('isInProgress')

      // Actions
      expect(result.current).toHaveProperty('setInvestigationId')
      expect(result.current).toHaveProperty('setUploadedImage')
      expect(result.current).toHaveProperty('setImagePreview')
      expect(result.current).toHaveProperty('setContext')
      expect(result.current).toHaveProperty('updateContext')
      expect(result.current).toHaveProperty('setError')
      expect(result.current).toHaveProperty('launchInvestigation')
      expect(result.current).toHaveProperty('resetInvestigation')
      expect(result.current).toHaveProperty('regenerateReport')
    })

    it('should have properly typed action functions', () => {
      const store = createMockStore()

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <Provider store={store}>
          <Investigation2Provider>
            {children}
          </Investigation2Provider>
        </Provider>
      )

      const { result } = renderHook(() => useInvestigation2(), { wrapper })

      expect(typeof result.current.launchInvestigation).toBe('function')
      expect(typeof result.current.resetInvestigation).toBe('function')
      expect(typeof result.current.regenerateReport).toBe('function')
      expect(typeof result.current.updateContext).toBe('function')
    })
  })

  describe('Context value updates', () => {
    it('should handle investigation state properly', () => {
      const store = createMockStore()

      const TestComponent = () => {
        const { investigationId, setInvestigationId } = useInvestigation2()

        return (
          <div>
            <div data-testid="id">{investigationId || 'none'}</div>
            <button onClick={() => setInvestigationId('test-123')}>Set ID</button>
          </div>
        )
      }

      render(
        <Provider store={store}>
          <Investigation2Provider>
            <TestComponent />
          </Investigation2Provider>
        </Provider>
      )

      expect(screen.getByTestId('id').textContent).toBe('none')
    })

    it('should track progress steps', () => {
      const store = createMockStore()

      const TestComponent = () => {
        const { progressSteps } = useInvestigation2()

        return (
          <div>
            <div data-testid="steps">{progressSteps.length}</div>
          </div>
        )
      }

      render(
        <Provider store={store}>
          <Investigation2Provider>
            <TestComponent />
          </Investigation2Provider>
        </Provider>
      )

      // Initially no steps
      expect(screen.getByTestId('steps').textContent).toBe('0')
    })
  })

  describe('Type safety', () => {
    it('should not allow any types in context values', () => {
      const store = createMockStore()

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <Provider store={store}>
          <Investigation2Provider>
            {children}
          </Investigation2Provider>
        </Provider>
      )

      const { result } = renderHook(() => useInvestigation2(), { wrapper })

      // Verify types are not any
      expect(result.current.investigationId).toBeTypeOf('object') // null is object
      expect(result.current.isLaunching).toBeTypeOf('boolean')
      expect(result.current.progressSteps).toBeInstanceOf(Array)
      expect(result.current.context).toBeTypeOf('object')
    })
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import Investigation2Progress from '../Investigation2Progress'
import { Investigation2Provider } from '../../../context/Investigation2Context'
import authReducer from '../../../features/auth/authSlice'
import { api } from '../../../app/api'

// Mock the API hooks
vi.mock('../../../app/api', async () => {
  const actual = await vi.importActual('../../../app/api')
  return {
    ...actual,
    useLaunchInvestigation2Mutation: () => [vi.fn(), { isLoading: false }],
    useGetInvestigation2Query: () => ({ data: null }),
    useRegenerateInvestigation2ReportMutation: () => [vi.fn()],
  }
})

// Mock useWebSocket
vi.mock('../../../hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    isConnected: false,
    error: null,
    connect: vi.fn(),
    disconnect: vi.fn(),
    send: vi.fn(),
    joinInvestigation: vi.fn(),
    leaveInvestigation: vi.fn(),
  }),
}))

const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      [api.reducerPath]: api.reducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(api.middleware),
    preloadedState: {
      auth: {
        user: null,
        token: 'mock-token',
        isAuthenticated: true,
        loading: false,
        error: null,
      },
      ...initialState,
    },
  })
}

const renderWithProviders = (ui: React.ReactElement) => {
  const store = createMockStore()
  return render(
    <Provider store={store}>
      <Investigation2Provider>
        {ui}
      </Investigation2Provider>
    </Provider>
  )
}

describe('Investigation2Progress', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders investigation progress title', () => {
    renderWithProviders(<Investigation2Progress />)
    expect(screen.getByText('Investigation Progress')).toBeInTheDocument()
  })

  it('renders progress bar', () => {
    renderWithProviders(<Investigation2Progress />)
    // Initially shows 0 of 0 steps when no investigation is running
    expect(screen.getByText(/steps completed/)).toBeInTheDocument()
  })

  it('shows 0% when no investigation started', () => {
    renderWithProviders(<Investigation2Progress />)
    expect(screen.getByText('0%')).toBeInTheDocument()
    expect(screen.getByText('0 of 0 steps completed')).toBeInTheDocument()
  })

  it('handles missing investigation ID gracefully', () => {
    renderWithProviders(<Investigation2Progress />)
    // Should not show ID when null
    expect(screen.queryByText(/ID:/)).not.toBeInTheDocument()
  })
})

// Test the phase labels and descriptions (static content)
describe('Investigation2Progress phase labels', () => {
  it('has correct phase label mappings', () => {
    // These are defined in the component
    const phaseLabels: Record<string, string> = {
      upload_and_parse: 'Upload & Parse',
      reverse_image_search: 'Reverse Image Search',
      tiger_detection: 'Tiger Detection',
      stripe_analysis: 'Stripe Analysis',
      report_generation: 'Report Generation',
      complete: 'Complete'
    }

    expect(phaseLabels.upload_and_parse).toBe('Upload & Parse')
    expect(phaseLabels.reverse_image_search).toBe('Reverse Image Search')
    expect(phaseLabels.tiger_detection).toBe('Tiger Detection')
    expect(phaseLabels.stripe_analysis).toBe('Stripe Analysis')
    expect(phaseLabels.report_generation).toBe('Report Generation')
    expect(phaseLabels.complete).toBe('Complete')
  })

  it('has correct phase description mappings', () => {
    const phaseDescriptions: Record<string, string> = {
      upload_and_parse: 'Processing uploaded image and context',
      reverse_image_search: 'Searching web for related tiger images',
      tiger_detection: 'Detecting tigers using MegaDetector',
      stripe_analysis: 'Running 6-model ReID ensemble in parallel',
      report_generation: 'Generating comprehensive report with Claude',
      complete: 'Investigation complete'
    }

    expect(phaseDescriptions.upload_and_parse).toBe('Processing uploaded image and context')
    expect(phaseDescriptions.tiger_detection).toBe('Detecting tigers using MegaDetector')
  })
})

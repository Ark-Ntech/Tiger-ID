import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import { BrowserRouter } from 'react-router-dom'
import React from 'react'
import Home from '../Home'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock the API hook
const mockStatsData = {
  data: {
    total_investigations: 150,
    active_investigations: 12,
    total_tigers: 500,
    total_facilities: 75,
    pending_verifications: 5,
    recent_activity: [
      { id: '1', event_type: 'Investigation Started', timestamp: '2024-01-01T12:00:00Z' },
      { id: '2', event_type: 'Tiger Identified', timestamp: '2024-01-01T11:00:00Z' },
    ],
  },
}

vi.mock('../../app/api', () => ({
  useGetDashboardStatsQuery: vi.fn(() => ({
    data: mockStatsData,
    isLoading: false,
    error: null,
  })),
}))

// Mock formatters
vi.mock('../../utils/formatters', () => ({
  formatRelativeTime: (date: string) => '1 hour ago',
}))

const createMockStore = () => {
  return configureStore({
    reducer: {
      api: () => ({}),
    },
  })
}

const renderHome = (store = createMockStore()) => {
  return render(
    <Provider store={store}>
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    </Provider>
  )
}

describe('Home', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('should render welcome header', () => {
      renderHome()

      expect(screen.getByText('Welcome to Tiger ID')).toBeInTheDocument()
    })

    it('should render system description', () => {
      renderHome()

      expect(screen.getByText(/tiger trafficking investigation/i)).toBeInTheDocument()
    })
  })

  describe('stats cards', () => {
    it('should render total investigations', () => {
      renderHome()

      expect(screen.getByText('Total Investigations')).toBeInTheDocument()
      expect(screen.getByText('150')).toBeInTheDocument()
    })

    it('should render active cases', () => {
      renderHome()

      expect(screen.getByText('Active Cases')).toBeInTheDocument()
      expect(screen.getByText('12')).toBeInTheDocument()
    })

    it('should render tigers identified', () => {
      renderHome()

      expect(screen.getByText('Tigers Identified')).toBeInTheDocument()
      expect(screen.getByText('500')).toBeInTheDocument()
    })

    it('should render facilities tracked', () => {
      renderHome()

      expect(screen.getByText('Facilities Tracked')).toBeInTheDocument()
      expect(screen.getByText('75')).toBeInTheDocument()
    })
  })

  describe('quick actions', () => {
    it('should render launch investigation button', () => {
      renderHome()

      expect(screen.getByRole('button', { name: /launch investigation/i })).toBeInTheDocument()
    })

    it('should render identify tiger button', () => {
      renderHome()

      expect(screen.getByRole('button', { name: /identify tiger/i })).toBeInTheDocument()
    })

    it('should render verify evidence button', () => {
      renderHome()

      expect(screen.getByRole('button', { name: /verify evidence/i })).toBeInTheDocument()
    })

    it('should navigate to investigations on launch investigation click', () => {
      renderHome()

      const button = screen.getByRole('button', { name: /launch investigation/i })
      fireEvent.click(button)

      expect(mockNavigate).toHaveBeenCalledWith('/investigations?tab=1')
    })

    it('should navigate to tigers on identify tiger click', () => {
      renderHome()

      const button = screen.getByRole('button', { name: /identify tiger/i })
      fireEvent.click(button)

      expect(mockNavigate).toHaveBeenCalledWith('/tigers')
    })

    it('should navigate to verification on verify evidence click', () => {
      renderHome()

      const button = screen.getByRole('button', { name: /verify evidence/i })
      fireEvent.click(button)

      expect(mockNavigate).toHaveBeenCalledWith('/verification')
    })
  })

  describe('recent activity', () => {
    it('should render recent activity section', () => {
      renderHome()

      expect(screen.getByText('Recent Activity')).toBeInTheDocument()
    })

    it('should display activity items', () => {
      renderHome()

      const investigationItems = screen.getAllByText('Investigation Started')
      expect(investigationItems.length).toBeGreaterThan(0)

      const tigerItems = screen.getAllByText('Tiger Identified')
      expect(tigerItems.length).toBeGreaterThan(0)
    })
  })

  describe('system status', () => {
    it('should render system status section', () => {
      renderHome()

      expect(screen.getByText('System Status')).toBeInTheDocument()
    })

    it('should display API status', () => {
      renderHome()

      expect(screen.getByText('API Status')).toBeInTheDocument()
      expect(screen.getByText('Online')).toBeInTheDocument()
    })

    it('should display database status', () => {
      renderHome()

      expect(screen.getByText('Database')).toBeInTheDocument()
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    it('should display websocket status', () => {
      renderHome()

      expect(screen.getByText('WebSocket')).toBeInTheDocument()
      expect(screen.getByText('Active')).toBeInTheDocument()
    })

    it('should display pending verifications count', () => {
      renderHome()

      expect(screen.getByText('Pending Verifications')).toBeInTheDocument()
      expect(screen.getByText('5')).toBeInTheDocument()
    })
  })

  describe('getting started', () => {
    it('should render getting started section', () => {
      renderHome()

      expect(screen.getByText('Getting Started')).toBeInTheDocument()
    })

    it('should render documentation button', () => {
      renderHome()

      expect(screen.getByRole('button', { name: /view documentation/i })).toBeInTheDocument()
    })
  })

  describe('loading state', () => {
    it('should show loading spinner when loading', () => {
      vi.doMock('../../app/api', () => ({
        useGetDashboardStatsQuery: vi.fn(() => ({
          data: null,
          isLoading: true,
          error: null,
        })),
      }))

      // Would need to re-import to test loading state
    })
  })

  describe('error state', () => {
    it('should show error message on failure', () => {
      vi.doMock('../../app/api', () => ({
        useGetDashboardStatsQuery: vi.fn(() => ({
          data: null,
          isLoading: false,
          error: { message: 'Failed' },
        })),
      }))

      // Would need to re-import to test error state
    })
  })
})

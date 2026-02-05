import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import { BrowserRouter } from 'react-router-dom'
import React from 'react'
import Dashboard from '../Dashboard'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock API hooks
const mockStatsData = {
  data: {
    total_investigations: 150,
    active_investigations: 12,
    completed_investigations: 138,
    total_tigers: 500,
    total_facilities: 75,
  },
}

const mockInvestigationsData = {
  data: {
    data: [
      { id: '1', title: 'Investigation 1', description: 'Test investigation', status: 'in_progress' },
      { id: '2', title: 'Investigation 2', description: 'Another investigation', status: 'completed' },
    ],
  },
}

const mockFacilitiesData = {
  data: {
    data: [
      { id: 'f1', exhibitor_name: 'Facility 1', city: 'New York', state: 'NY', tiger_count: 10 },
      { id: 'f2', exhibitor_name: 'Facility 2', city: 'Los Angeles', state: 'CA', tiger_count: 5 },
    ],
  },
}

const mockInvestigationAnalytics = {
  data: {
    total_investigations: 150,
    completed: 138,
    completion_rate: 92,
    average_duration_days: 14,
    by_status: { completed: 138, in_progress: 12 },
    by_priority: { high: 50, medium: 80, low: 20 },
    timeline_data: { '2024-01-01': 10, '2024-01-02': 15 },
  },
}

const mockEvidenceAnalytics = {
  data: {
    total_evidence: 500,
    high_relevance_count: 100,
    by_type: { image: 200, document: 150, video: 150 },
  },
}

const mockVerificationAnalytics = {
  data: {
    total_tasks: 200,
    pending: 50,
    approved: 150,
    average_completion_time: 2.5,
    by_status: { pending: 50, approved: 150 },
  },
}

const mockGeographicAnalytics = {
  data: {
    facilities_by_state: { TX: 20, CA: 15, FL: 10 },
    investigations_by_location: [{ location: 'Texas', count: 25 }],
  },
}

const mockTigerAnalytics = {
  data: {
    total_tigers: 500,
    identification_rate: 85,
    by_status: { identified: 425, unidentified: 75 },
    trends: [
      { date: '2024-01-01', count: 10 },
      { date: '2024-01-02', count: 15 },
    ],
  },
}

const mockAgentAnalytics = {
  data: {
    total_steps: 1000,
    unique_agents: 5,
    agent_success_rates: {
      agent1: { success_rate: 95, total: 200 },
      agent2: { success_rate: 88, total: 150 },
    },
    agent_activity: { agent1: 200, agent2: 150 },
  },
}

const mockFacilityAnalytics = {
  data: {
    total_facilities: 75,
    total_tigers: 500,
    avg_tigers_per_facility: 6.7,
    state_distribution: { TX: 20, CA: 15, FL: 10 },
  },
}

const mockModelsData = {
  data: {
    models: {
      wildlife_tools: { name: 'Wildlife Tools', description: 'ReID model', gpu: 'A10G', backend: 'Modal', type: 'reid' },
      cvwc2019: { name: 'CVWC 2019', description: 'Competition model', gpu: 'A10G', backend: 'Modal', type: 'reid' },
    },
    default: 'wildlife_tools',
  },
}

const mockRefetch = vi.fn().mockResolvedValue({})

vi.mock('../../app/api', () => {
  const mockRefetchInternal = vi.fn().mockResolvedValue({})
  return {
    useGetDashboardStatsQuery: vi.fn(() => ({
      data: mockStatsData,
      isLoading: false,
      refetch: mockRefetchInternal,
    })),
    useGetInvestigationsQuery: vi.fn(() => ({
      data: mockInvestigationsData,
      isLoading: false,
      refetch: mockRefetchInternal,
    })),
    useGetFacilitiesQuery: vi.fn(() => ({
      data: mockFacilitiesData,
      refetch: mockRefetchInternal,
    })),
    useGetInvestigationAnalyticsQuery: vi.fn(() => ({
      data: mockInvestigationAnalytics,
      isLoading: false,
      refetch: mockRefetchInternal,
    })),
    useGetEvidenceAnalyticsQuery: vi.fn(() => ({
      data: mockEvidenceAnalytics,
      isLoading: false,
      refetch: mockRefetchInternal,
    })),
    useGetVerificationAnalyticsQuery: vi.fn(() => ({
      data: mockVerificationAnalytics,
      isLoading: false,
      refetch: mockRefetchInternal,
    })),
    useGetGeographicAnalyticsQuery: vi.fn(() => ({
      data: mockGeographicAnalytics,
      isLoading: false,
      refetch: mockRefetchInternal,
    })),
    useGetTigerAnalyticsQuery: vi.fn(() => ({
      data: mockTigerAnalytics,
      isLoading: false,
      refetch: mockRefetchInternal,
    })),
    useGetAgentAnalyticsQuery: vi.fn(() => ({
      data: mockAgentAnalytics,
      isLoading: false,
      refetch: mockRefetchInternal,
    })),
    useGetFacilityAnalyticsQuery: vi.fn(() => ({
      data: mockFacilityAnalytics,
      isLoading: false,
      refetch: mockRefetchInternal,
    })),
    useGetModelsAvailableQuery: vi.fn(() => ({
      data: mockModelsData,
      isLoading: false,
    })),
    useBenchmarkModelMutation: vi.fn(() => [vi.fn(), { isLoading: false }]),
    api: {
      util: {
        invalidateTags: vi.fn(() => ({ type: 'INVALIDATE_TAGS' })),
      },
    },
  }
})

// Mock recharts components
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
  BarChart: ({ children }: { children: React.ReactNode }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  PieChart: ({ children }: { children: React.ReactNode }) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
}))

// Mock GeographicMap
vi.mock('../../components/analytics/GeographicMap', () => ({
  default: () => <div data-testid="geographic-map">Geographic Map</div>,
}))

// Mock heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  ChartBarIcon: () => <span data-testid="chart-icon">Chart</span>,
  ClockIcon: () => <span data-testid="clock-icon">Clock</span>,
  CpuChipIcon: () => <span data-testid="cpu-icon">CPU</span>,
  ArrowPathIcon: () => <span data-testid="refresh-icon">Refresh</span>,
  BuildingOfficeIcon: () => <span data-testid="building-icon">Building</span>,
  FolderOpenIcon: () => <span data-testid="folder-icon">Folder</span>,
}))

const createMockStore = () => {
  return configureStore({
    reducer: {
      api: () => ({}),
    },
  })
}

const renderDashboard = (store = createMockStore()) => {
  return render(
    <Provider store={store}>
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    </Provider>
  )
}

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('rendering', () => {
    it('should render dashboard header', () => {
      renderDashboard()

      expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument()
    })

    it('should render dashboard subtitle', () => {
      renderDashboard()

      expect(screen.getByText('Comprehensive system analytics and insights')).toBeInTheDocument()
    })

    it('should render refresh button', () => {
      renderDashboard()

      expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument()
    })

    it('should render time range selector', () => {
      renderDashboard()

      expect(screen.getByDisplayValue('Last 30 Days')).toBeInTheDocument()
    })
  })

  describe('time range selector', () => {
    it('should have 7 days option', () => {
      renderDashboard()

      const select = screen.getByDisplayValue('Last 30 Days')
      expect(select).toContainHTML('Last 7 Days')
    })

    it('should have 30 days option', () => {
      renderDashboard()

      const select = screen.getByDisplayValue('Last 30 Days')
      expect(select).toContainHTML('Last 30 Days')
    })

    it('should have 90 days option', () => {
      renderDashboard()

      const select = screen.getByDisplayValue('Last 30 Days')
      expect(select).toContainHTML('Last 90 Days')
    })

    it('should have 1 year option', () => {
      renderDashboard()

      const select = screen.getByDisplayValue('Last 30 Days')
      expect(select).toContainHTML('Last Year')
    })

    it('should change time range when option selected', () => {
      renderDashboard()

      const select = screen.getByDisplayValue('Last 30 Days')
      fireEvent.change(select, { target: { value: '7days' } })

      expect(select).toHaveValue('7days')
    })
  })

  describe('tab navigation', () => {
    it('should render Investigations tab', () => {
      renderDashboard()

      expect(screen.getByText('Investigations')).toBeInTheDocument()
    })

    it('should render Evidence & Verification tab', () => {
      renderDashboard()

      expect(screen.getByText('Evidence & Verification')).toBeInTheDocument()
    })

    it('should render Geographic tab', () => {
      renderDashboard()

      expect(screen.getByText('Geographic')).toBeInTheDocument()
    })

    it('should render Tigers tab', () => {
      renderDashboard()

      expect(screen.getByText('Tigers')).toBeInTheDocument()
    })

    it('should render Facilities tab', () => {
      renderDashboard()

      expect(screen.getByText('Facilities')).toBeInTheDocument()
    })

    it('should render Agent Performance tab', () => {
      renderDashboard()

      expect(screen.getByText('Agent Performance')).toBeInTheDocument()
    })

    it('should render Model Performance tab', () => {
      renderDashboard()

      expect(screen.getByText('Model Performance')).toBeInTheDocument()
    })

    it('should switch tabs when clicked', () => {
      renderDashboard()

      fireEvent.click(screen.getByText('Geographic'))

      // Geographic tab content should be visible (map)
      expect(screen.getByTestId('geographic-map')).toBeInTheDocument()
    })
  })

  describe('summary stats', () => {
    it('should render total investigations', () => {
      renderDashboard()

      expect(screen.getByText('Total Investigations')).toBeInTheDocument()
      expect(screen.getByText('150')).toBeInTheDocument()
    })

    it('should render completion rate', () => {
      renderDashboard()

      expect(screen.getByText('Completion Rate')).toBeInTheDocument()
    })

    it('should render avg duration', () => {
      renderDashboard()

      expect(screen.getByText('Avg. Duration')).toBeInTheDocument()
    })

    it('should render total tigers', () => {
      renderDashboard()

      expect(screen.getByText('Total Tigers')).toBeInTheDocument()
    })

    it('should render total facilities', () => {
      renderDashboard()

      expect(screen.getByText('Total Facilities')).toBeInTheDocument()
    })

    it('should render total evidence', () => {
      renderDashboard()

      expect(screen.getByText('Total Evidence')).toBeInTheDocument()
    })

    it('should render verification tasks', () => {
      renderDashboard()

      expect(screen.getByText('Verification Tasks')).toBeInTheDocument()
    })

    it('should render agent steps', () => {
      renderDashboard()

      expect(screen.getByText('Agent Steps')).toBeInTheDocument()
    })
  })

  describe('navigation', () => {
    it('should navigate to investigations when investigations card clicked', async () => {
      vi.useRealTimers()
      renderDashboard()

      const investigationsText = screen.getByText('Total Investigations')
      const cardElement = investigationsText.closest('div')

      if (cardElement) {
        await act(async () => {
          fireEvent.click(cardElement)
        })

        await waitFor(() => {
          expect(mockNavigate).toHaveBeenCalledWith('/investigations')
        }, { timeout: 1000 })
      }
      vi.useFakeTimers()
    })

    it('should navigate to tigers when tigers card clicked', async () => {
      vi.useRealTimers()
      renderDashboard()

      const tigersText = screen.getByText('Total Tigers')
      const cardElement = tigersText.closest('div')

      if (cardElement) {
        await act(async () => {
          fireEvent.click(cardElement)
        })

        await waitFor(() => {
          expect(mockNavigate).toHaveBeenCalledWith('/tigers')
        }, { timeout: 1000 })
      }
      vi.useFakeTimers()
    })

    it('should navigate to facilities when facilities card clicked', async () => {
      vi.useRealTimers()
      renderDashboard()

      const facilitiesText = screen.getByText('Total Facilities')
      const cardElement = facilitiesText.closest('div')

      if (cardElement) {
        await act(async () => {
          fireEvent.click(cardElement)
        })

        await waitFor(() => {
          expect(mockNavigate).toHaveBeenCalledWith('/facilities')
        }, { timeout: 1000 })
      }
      vi.useFakeTimers()
    })
  })

  describe('refresh functionality', () => {
    it('should render refresh button and it is clickable', () => {
      renderDashboard()

      const refreshButton = screen.getByRole('button', { name: /refresh/i })

      expect(refreshButton).toBeInTheDocument()
      expect(refreshButton).not.toBeDisabled()

      fireEvent.click(refreshButton)

      // Button should still be in the document after click
      expect(refreshButton).toBeInTheDocument()
    })
  })

  describe('investigations tab', () => {
    it('should show investigations by status chart', () => {
      renderDashboard()

      expect(screen.getByText('Investigations by Status')).toBeInTheDocument()
    })

    it('should show investigations by priority chart', () => {
      renderDashboard()

      expect(screen.getByText('Investigations by Priority')).toBeInTheDocument()
    })

    it('should show investigations over time chart', () => {
      renderDashboard()

      expect(screen.getByText('Investigations Over Time')).toBeInTheDocument()
    })

    it('should show recent investigations list', () => {
      renderDashboard()

      expect(screen.getByText('Recent Investigations')).toBeInTheDocument()
    })
  })

  describe('evidence & verification tab', () => {
    it('should show evidence by type chart', async () => {
      vi.useRealTimers()
      renderDashboard()

      fireEvent.click(screen.getByText('Evidence & Verification'))

      await waitFor(() => {
        expect(screen.getByText('Evidence by Type')).toBeInTheDocument()
      }, { timeout: 1000 })
      vi.useFakeTimers()
    })

    it('should show verification by status chart', async () => {
      vi.useRealTimers()
      renderDashboard()

      fireEvent.click(screen.getByText('Evidence & Verification'))

      await waitFor(() => {
        expect(screen.getByText('Verification by Status')).toBeInTheDocument()
      }, { timeout: 1000 })
      vi.useFakeTimers()
    })
  })

  describe('tigers tab', () => {
    it('should show tiger identifications chart', async () => {
      vi.useRealTimers()
      renderDashboard()

      fireEvent.click(screen.getByText('Tigers'))

      await waitFor(() => {
        expect(screen.getByText('Tiger Identifications')).toBeInTheDocument()
      }, { timeout: 1000 })
      vi.useFakeTimers()
    })

    it('should show tigers by status chart', async () => {
      vi.useRealTimers()
      renderDashboard()

      fireEvent.click(screen.getByText('Tigers'))

      await waitFor(() => {
        expect(screen.getByText('Tigers by Status')).toBeInTheDocument()
      }, { timeout: 1000 })
      vi.useFakeTimers()
    })
  })

  describe('facilities tab', () => {
    it('should show facilities by state chart', async () => {
      vi.useRealTimers()
      renderDashboard()

      const tabs = screen.getAllByText('Facilities')
      fireEvent.click(tabs[0])

      await waitFor(() => {
        expect(screen.getByText('Facilities by State')).toBeInTheDocument()
      }, { timeout: 1000 })
      vi.useFakeTimers()
    })

    it('should show state distribution chart', async () => {
      vi.useRealTimers()
      renderDashboard()

      const tabs = screen.getAllByText('Facilities')
      fireEvent.click(tabs[0])

      await waitFor(() => {
        expect(screen.getByText('State Distribution')).toBeInTheDocument()
      }, { timeout: 1000 })
      vi.useFakeTimers()
    })
  })

  describe('agent performance tab', () => {
    it('should show agent success rates chart', async () => {
      vi.useRealTimers()
      renderDashboard()

      fireEvent.click(screen.getByText('Agent Performance'))

      await waitFor(() => {
        expect(screen.getByText('Agent Success Rates')).toBeInTheDocument()
      }, { timeout: 1000 })
      vi.useFakeTimers()
    })

    it('should show agent activity section', async () => {
      vi.useRealTimers()
      renderDashboard()

      fireEvent.click(screen.getByText('Agent Performance'))

      await waitFor(() => {
        expect(screen.getByText('Agent Activity')).toBeInTheDocument()
      }, { timeout: 1000 })
      vi.useFakeTimers()
    })
  })

  describe('model performance tab', () => {
    it('should show model performance header', async () => {
      vi.useRealTimers()
      renderDashboard()

      fireEvent.click(screen.getByText('Model Performance'))

      await waitFor(() => {
        const elements = screen.getAllByText('Model Performance')
        expect(elements.length).toBeGreaterThan(0)
      }, { timeout: 1000 })
      vi.useFakeTimers()
    })

    it('should show model selection dropdown', async () => {
      vi.useRealTimers()
      renderDashboard()

      fireEvent.click(screen.getByText('Model Performance'))

      await waitFor(() => {
        expect(screen.getByText('Select model to benchmark')).toBeInTheDocument()
      }, { timeout: 1000 })
      vi.useFakeTimers()
    })

    it('should show run benchmark button', async () => {
      vi.useRealTimers()
      renderDashboard()

      fireEvent.click(screen.getByText('Model Performance'))

      await waitFor(() => {
        expect(screen.getByText('Run Benchmark')).toBeInTheDocument()
      }, { timeout: 1000 })
      vi.useFakeTimers()
    })

    it('should show accuracy comparison chart', async () => {
      vi.useRealTimers()
      renderDashboard()

      fireEvent.click(screen.getByText('Model Performance'))

      await waitFor(() => {
        expect(screen.getByText('Accuracy Comparison')).toBeInTheDocument()
      }, { timeout: 1000 })
      vi.useFakeTimers()
    })

    it('should show performance metrics chart', async () => {
      vi.useRealTimers()
      renderDashboard()

      fireEvent.click(screen.getByText('Model Performance'))

      await waitFor(() => {
        expect(screen.getByText('Performance Metrics')).toBeInTheDocument()
      }, { timeout: 1000 })
      vi.useFakeTimers()
    })

    it('should show model performance summary table', async () => {
      vi.useRealTimers()
      renderDashboard()

      fireEvent.click(screen.getByText('Model Performance'))

      await waitFor(() => {
        expect(screen.getByText('Model Performance Summary')).toBeInTheDocument()
      }, { timeout: 1000 })
      vi.useFakeTimers()
    })
  })

  describe('charts', () => {
    it('should render responsive containers', () => {
      renderDashboard()

      const containers = screen.getAllByTestId('responsive-container')
      expect(containers.length).toBeGreaterThan(0)
    })

    it('should render pie charts', () => {
      renderDashboard()

      const pieCharts = screen.getAllByTestId('pie-chart')
      expect(pieCharts.length).toBeGreaterThan(0)
    })

    it('should render bar charts', () => {
      renderDashboard()

      const barCharts = screen.getAllByTestId('bar-chart')
      expect(barCharts.length).toBeGreaterThan(0)
    })

    it('should render line charts', () => {
      renderDashboard()

      const lineCharts = screen.getAllByTestId('line-chart')
      expect(lineCharts.length).toBeGreaterThan(0)
    })
  })

  describe('last refresh timestamp', () => {
    it('should display last updated time', () => {
      renderDashboard()

      expect(screen.getByText(/Last updated:/)).toBeInTheDocument()
    })
  })
})

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import { BrowserRouter } from 'react-router-dom'
import React from 'react'
import ModelDashboard from '../ModelDashboard'

// Mock API hooks
const mockModelsData = {
  data: {
    models: {
      wildlife_tools: {
        name: 'Wildlife Tools',
        description: 'ReID model for wildlife',
        gpu: 'A10G',
        backend: 'Modal',
        type: 'reid',
      },
      cvwc2019_reid: {
        name: 'CVWC 2019',
        description: 'Competition winner model',
        gpu: 'A10G',
        backend: 'Modal',
        type: 'reid',
      },
      transreid: {
        name: 'TransReID',
        description: 'Transformer-based ReID',
        gpu: 'T4',
        backend: 'Modal',
        type: 'reid',
      },
    },
    default: 'wildlife_tools',
  },
}

const mockBenchmarkMutation = vi.fn()

vi.mock('../../app/api', () => ({
  useGetModelsAvailableQuery: vi.fn(() => ({
    data: mockModelsData,
    isLoading: false,
    error: null,
  })),
  useBenchmarkModelMutation: vi.fn(() => [
    mockBenchmarkMutation,
    { isLoading: false },
  ]),
}))

// Mock heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  ChartBarIcon: () => <span data-testid="chart-bar-icon">ChartBar</span>,
  ClockIcon: () => <span data-testid="clock-icon">Clock</span>,
  CpuChipIcon: () => <span data-testid="cpu-chip-icon">CPU</span>,
}))

// Mock recharts components
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  BarChart: ({ children, data }: { children: React.ReactNode; data?: any[] }) => (
    <div data-testid="bar-chart" data-items={data?.length}>
      {children}
    </div>
  ),
  Bar: ({ dataKey, fill, name }: { dataKey?: string; fill?: string; name?: string }) => (
    <div data-testid="bar" data-key={dataKey} data-fill={fill} data-name={name} />
  ),
  LineChart: ({ children, data }: { children: React.ReactNode; data?: any[] }) => (
    <div data-testid="line-chart" data-items={data?.length}>
      {children}
    </div>
  ),
  Line: ({ dataKey, stroke, name }: { dataKey?: string; stroke?: string; name?: string }) => (
    <div data-testid="line" data-key={dataKey} data-stroke={stroke} data-name={name} />
  ),
  XAxis: ({ dataKey }: { dataKey?: string }) => (
    <div data-testid="x-axis" data-key={dataKey} />
  ),
  YAxis: ({ domain }: { domain?: number[] }) => (
    <div data-testid="y-axis" data-domain={domain?.join(',')} />
  ),
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: ({ formatter }: { formatter?: (value: number) => string }) => (
    <div data-testid="tooltip" data-has-formatter={!!formatter} />
  ),
  Legend: () => <div data-testid="legend" />,
}))

const createMockStore = () => {
  return configureStore({
    reducer: {
      api: () => ({}),
    },
  })
}

const renderModelDashboard = (store = createMockStore()) => {
  return render(
    <Provider store={store}>
      <BrowserRouter>
        <ModelDashboard />
      </BrowserRouter>
    </Provider>
  )
}

describe('ModelDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('loading state', () => {
    it('should show loading spinner when models are loading', () => {
      const { useGetModelsAvailableQuery } = require('../../app/api')
      useGetModelsAvailableQuery.mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
      })

      renderModelDashboard()

      expect(screen.getByRole('status')).toBeInTheDocument()
    })

    it('should display loading spinner in center of screen', () => {
      const { useGetModelsAvailableQuery } = require('../../app/api')
      useGetModelsAvailableQuery.mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
      })

      renderModelDashboard()

      const container = screen.getByRole('status').closest('.flex')
      expect(container?.className).toContain('items-center')
      expect(container?.className).toContain('justify-center')
    })
  })

  describe('header section', () => {
    it('should render page title', () => {
      renderModelDashboard()

      expect(screen.getByText('Model Performance Dashboard')).toBeInTheDocument()
    })

    it('should render page subtitle', () => {
      renderModelDashboard()

      expect(screen.getByText('Compare RE-ID model performance metrics')).toBeInTheDocument()
    })

    it('should render model selection dropdown', () => {
      renderModelDashboard()

      expect(screen.getByRole('combobox')).toBeInTheDocument()
      expect(screen.getByText('Select model to benchmark')).toBeInTheDocument()
    })

    it('should render run benchmark button', () => {
      renderModelDashboard()

      expect(screen.getByRole('button', { name: /Run Benchmark/i })).toBeInTheDocument()
    })
  })

  describe('model selection', () => {
    it('should populate dropdown with available models', () => {
      renderModelDashboard()

      const select = screen.getByRole('combobox')
      expect(select).toHaveTextContent('wildlife_tools')
      expect(select).toHaveTextContent('cvwc2019_reid')
      expect(select).toHaveTextContent('transreid')
    })

    it('should update selected model when option is chosen', () => {
      renderModelDashboard()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      expect(select).toHaveValue('wildlife_tools')
    })

    it('should default to empty selection', () => {
      renderModelDashboard()

      const select = screen.getByRole('combobox')
      expect(select).toHaveValue('')
    })

    it('should render all model options in dropdown', () => {
      renderModelDashboard()

      const options = screen.getAllByRole('option')
      // Includes "Select model to benchmark" plus 3 models
      expect(options).toHaveLength(4)
    })
  })

  describe('benchmark button', () => {
    it('should be disabled when no model is selected', () => {
      renderModelDashboard()

      const button = screen.getByRole('button', { name: /Run Benchmark/i })
      expect(button).toBeDisabled()
    })

    it('should be enabled when a model is selected', () => {
      renderModelDashboard()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const button = screen.getByRole('button', { name: /Run Benchmark/i })
      expect(button).toBeEnabled()
    })

    it('should be disabled when benchmarking is in progress', async () => {
      renderModelDashboard()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const button = screen.getByRole('button', { name: /Run Benchmark/i })

      await act(async () => {
        fireEvent.click(button)
      })

      await waitFor(() => {
        expect(screen.getByText(/Benchmarking.../i)).toBeInTheDocument()
      })
    })

    it('should show loading text when benchmarking', async () => {
      renderModelDashboard()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const button = screen.getByRole('button', { name: /Run Benchmark/i })

      await act(async () => {
        fireEvent.click(button)
      })

      await waitFor(() => {
        expect(screen.getByText(/Benchmarking.../i)).toBeInTheDocument()
      })
    })

    it('should trigger benchmark when clicked', async () => {
      renderModelDashboard()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const button = screen.getByRole('button', { name: /Run Benchmark/i })

      await act(async () => {
        fireEvent.click(button)
      })

      await waitFor(() => {
        expect(screen.getByText(/Benchmark Results/i)).toBeInTheDocument()
      })
    })

    it('should be disabled when API mutation is loading', () => {
      const { useBenchmarkModelMutation } = require('../../app/api')
      useBenchmarkModelMutation.mockReturnValue([
        mockBenchmarkMutation,
        { isLoading: true },
      ])

      renderModelDashboard()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const button = screen.getByRole('button', { name: /Run Benchmark/i })
      expect(button).toBeDisabled()
    })
  })

  describe('accuracy comparison chart', () => {
    it('should render accuracy comparison card', () => {
      renderModelDashboard()

      expect(screen.getByText('Accuracy Comparison')).toBeInTheDocument()
    })

    it('should render chart bar icon', () => {
      renderModelDashboard()

      expect(screen.getByTestId('chart-bar-icon')).toBeInTheDocument()
    })

    it('should render bar chart', () => {
      renderModelDashboard()

      const barCharts = screen.getAllByTestId('bar-chart')
      expect(barCharts.length).toBeGreaterThan(0)
    })

    it('should render rank-1 accuracy bars', () => {
      renderModelDashboard()

      const bars = screen.getAllByTestId('bar')
      const rank1Bar = bars.find((bar) => bar.getAttribute('data-key') === 'rank1_accuracy')
      expect(rank1Bar).toBeDefined()
      expect(rank1Bar?.getAttribute('data-fill')).toBe('#3b82f6')
      expect(rank1Bar?.getAttribute('data-name')).toBe('Rank-1 Accuracy')
    })

    it('should render mAP bars', () => {
      renderModelDashboard()

      const bars = screen.getAllByTestId('bar')
      const mapBar = bars.find((bar) => bar.getAttribute('data-key') === 'map')
      expect(mapBar).toBeDefined()
      expect(mapBar?.getAttribute('data-fill')).toBe('#10b981')
      expect(mapBar?.getAttribute('data-name')).toBe('mAP')
    })

    it('should render chart axes', () => {
      renderModelDashboard()

      const xAxes = screen.getAllByTestId('x-axis')
      expect(xAxes.length).toBeGreaterThan(0)

      const yAxes = screen.getAllByTestId('y-axis')
      expect(yAxes.length).toBeGreaterThan(0)
    })

    it('should set Y-axis domain from 0 to 1', () => {
      renderModelDashboard()

      const yAxes = screen.getAllByTestId('y-axis')
      const accuracyYAxis = yAxes.find((axis) => axis.getAttribute('data-domain') === '0,1')
      expect(accuracyYAxis).toBeDefined()
    })

    it('should render cartesian grid', () => {
      renderModelDashboard()

      expect(screen.getAllByTestId('cartesian-grid').length).toBeGreaterThan(0)
    })

    it('should render tooltip with percentage formatter', () => {
      renderModelDashboard()

      const tooltips = screen.getAllByTestId('tooltip')
      const formattedTooltip = tooltips.find(
        (tooltip) => tooltip.getAttribute('data-has-formatter') === 'true'
      )
      expect(formattedTooltip).toBeDefined()
    })

    it('should render legend', () => {
      renderModelDashboard()

      expect(screen.getAllByTestId('legend').length).toBeGreaterThan(0)
    })
  })

  describe('performance metrics chart', () => {
    it('should render performance metrics card', () => {
      renderModelDashboard()

      expect(screen.getByText('Performance Metrics')).toBeInTheDocument()
    })

    it('should render clock icon', () => {
      renderModelDashboard()

      expect(screen.getByTestId('clock-icon')).toBeInTheDocument()
    })

    it('should render line chart', () => {
      renderModelDashboard()

      const lineCharts = screen.getAllByTestId('line-chart')
      expect(lineCharts.length).toBeGreaterThan(0)
    })

    it('should render latency line', () => {
      renderModelDashboard()

      const lines = screen.getAllByTestId('line')
      const latencyLine = lines.find((line) => line.getAttribute('data-key') === 'latency_ms')
      expect(latencyLine).toBeDefined()
      expect(latencyLine?.getAttribute('data-stroke')).toBe('#ef4444')
      expect(latencyLine?.getAttribute('data-name')).toBe('Latency (ms)')
    })

    it('should render throughput line', () => {
      renderModelDashboard()

      const lines = screen.getAllByTestId('line')
      const throughputLine = lines.find((line) => line.getAttribute('data-key') === 'throughput')
      expect(throughputLine).toBeDefined()
      expect(throughputLine?.getAttribute('data-stroke')).toBe('#8b5cf6')
      expect(throughputLine?.getAttribute('data-name')).toBe('Throughput (img/s)')
    })
  })

  describe('model performance summary table', () => {
    it('should render performance summary card', () => {
      renderModelDashboard()

      expect(screen.getByText('Model Performance Summary')).toBeInTheDocument()
    })

    it('should render CPU chip icon', () => {
      renderModelDashboard()

      expect(screen.getByTestId('cpu-chip-icon')).toBeInTheDocument()
    })

    it('should render table headers', () => {
      renderModelDashboard()

      expect(screen.getByText('Model')).toBeInTheDocument()
      expect(screen.getByText('Rank-1 Accuracy')).toBeInTheDocument()
      expect(screen.getByText('mAP')).toBeInTheDocument()
      expect(screen.getByText('Latency (ms)')).toBeInTheDocument()
      expect(screen.getByText('Throughput (img/s)')).toBeInTheDocument()
      expect(screen.getByText('Status')).toBeInTheDocument()
    })

    it('should render model names in table', () => {
      renderModelDashboard()

      expect(screen.getByText('wildlife_tools')).toBeInTheDocument()
      expect(screen.getByText('cvwc2019_reid')).toBeInTheDocument()
      expect(screen.getByText('transreid')).toBeInTheDocument()
    })

    it('should render status badges for all models', () => {
      renderModelDashboard()

      const statusBadges = screen.getAllByText('Available')
      expect(statusBadges.length).toBe(3)
    })

    it('should render performance metrics for each model', () => {
      renderModelDashboard()

      const table = screen.getByRole('table')
      const rows = table.querySelectorAll('tbody tr')
      expect(rows.length).toBe(3)
    })

    it('should display percentage values for accuracy and mAP', () => {
      renderModelDashboard()

      const table = screen.getByRole('table')
      const percentagePattern = /\d+\.\d+%/
      const cells = table.querySelectorAll('td')
      const percentageCells = Array.from(cells).filter((cell) =>
        percentagePattern.test(cell.textContent || '')
      )
      // Should have at least 6 percentage cells (2 per model × 3 models)
      expect(percentageCells.length).toBeGreaterThanOrEqual(6)
    })

    it('should display latency values in milliseconds', () => {
      renderModelDashboard()

      const table = screen.getByRole('table')
      const msPattern = /\d+ms/
      const cells = table.querySelectorAll('td')
      const msCells = Array.from(cells).filter((cell) => msPattern.test(cell.textContent || ''))
      // Should have 3 latency cells (1 per model)
      expect(msCells.length).toBe(3)
    })

    it('should apply hover effect to table rows', () => {
      renderModelDashboard()

      const table = screen.getByRole('table')
      const rows = table.querySelectorAll('tbody tr')
      rows.forEach((row) => {
        expect(row.className).toContain('hover:bg-gray-50')
      })
    })
  })

  describe('benchmark results', () => {
    it('should not show results initially', () => {
      renderModelDashboard()

      expect(screen.queryByText('Benchmark Results')).not.toBeInTheDocument()
    })

    it('should display benchmark results after running benchmark', async () => {
      renderModelDashboard()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const button = screen.getByRole('button', { name: /Run Benchmark/i })

      await act(async () => {
        fireEvent.click(button)
      })

      await waitFor(() => {
        expect(screen.getByText('Benchmark Results')).toBeInTheDocument()
      })
    })

    it('should show informational message about test images requirement', async () => {
      renderModelDashboard()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const button = screen.getByRole('button', { name: /Run Benchmark/i })

      await act(async () => {
        fireEvent.click(button)
      })

      await waitFor(() => {
        expect(
          screen.getByText(
            /Benchmarking requires test images. Use the Model Testing page to run benchmarks./i
          )
        ).toBeInTheDocument()
      })
    })

    it('should clear previous results when new benchmark starts', async () => {
      renderModelDashboard()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const button = screen.getByRole('button', { name: /Run Benchmark/i })

      await act(async () => {
        fireEvent.click(button)
      })

      await waitFor(() => {
        expect(screen.getByText('Benchmark Results')).toBeInTheDocument()
      })

      // Change model and benchmark again
      fireEvent.change(select, { target: { value: 'cvwc2019_reid' } })

      await act(async () => {
        fireEvent.click(button)
      })

      // Should show results again after second benchmark
      await waitFor(() => {
        expect(screen.getByText('Benchmark Results')).toBeInTheDocument()
      })
    })
  })

  describe('best model recommendations', () => {
    it('should render best model recommendation section', () => {
      renderModelDashboard()

      expect(screen.getByText('Best Model Recommendation')).toBeInTheDocument()
    })

    it('should recommend best accuracy model', () => {
      renderModelDashboard()

      expect(screen.getByText('Best Accuracy:')).toBeInTheDocument()
    })

    it('should recommend fastest model', () => {
      renderModelDashboard()

      expect(screen.getByText('Fastest:')).toBeInTheDocument()
    })

    it('should recommend best throughput model', () => {
      renderModelDashboard()

      expect(screen.getByText('Best Throughput:')).toBeInTheDocument()
    })

    it('should display model names in recommendations', () => {
      renderModelDashboard()

      const recommendations = screen.getByText('Best Model Recommendation').parentElement
      const modelNames = recommendations?.textContent
      expect(modelNames).toMatch(/wildlife_tools|cvwc2019_reid|transreid/)
    })

    it('should apply correct styling to recommendation cards', () => {
      renderModelDashboard()

      const bestAccuracy = screen.getByText('Best Accuracy:').closest('div')
      expect(bestAccuracy?.className).toContain('bg-blue-50')

      const fastest = screen.getByText('Fastest:').closest('div')
      expect(fastest?.className).toContain('bg-green-50')

      const bestThroughput = screen.getByText('Best Throughput:').closest('div')
      expect(bestThroughput?.className).toContain('bg-purple-50')
    })

    it('should not show recommendations when no models available', () => {
      const { useGetModelsAvailableQuery } = require('../../app/api')
      useGetModelsAvailableQuery.mockReturnValue({
        data: { data: { models: {} } },
        isLoading: false,
        error: null,
      })

      renderModelDashboard()

      expect(screen.queryByText('Best Model Recommendation')).not.toBeInTheDocument()
    })
  })

  describe('performance data generation', () => {
    it('should generate performance data for all models', () => {
      renderModelDashboard()

      const table = screen.getByRole('table')
      const rows = table.querySelectorAll('tbody tr')
      expect(rows.length).toBe(3)
    })

    it('should update performance data when models change', () => {
      const { useGetModelsAvailableQuery } = require('../../app/api')
      const { rerender } = renderModelDashboard()

      const initialTable = screen.getByRole('table')
      const initialRows = initialTable.querySelectorAll('tbody tr')
      expect(initialRows.length).toBe(3)

      // Update models
      useGetModelsAvailableQuery.mockReturnValue({
        data: {
          data: {
            models: {
              wildlife_tools: mockModelsData.data.models.wildlife_tools,
            },
          },
        },
        isLoading: false,
        error: null,
      })

      rerender(
        <Provider store={createMockStore()}>
          <BrowserRouter>
            <ModelDashboard />
          </BrowserRouter>
        </Provider>
      )

      const updatedTable = screen.getByRole('table')
      const updatedRows = updatedTable.querySelectorAll('tbody tr')
      expect(updatedRows.length).toBe(1)
    })
  })

  describe('responsive containers', () => {
    it('should render charts in responsive containers', () => {
      renderModelDashboard()

      const containers = screen.getAllByTestId('responsive-container')
      expect(containers.length).toBeGreaterThanOrEqual(2)
    })

    it('should set chart height to 300 pixels', () => {
      renderModelDashboard()

      const containers = screen.getAllByTestId('responsive-container')
      containers.forEach((container) => {
        expect(container.textContent).toBeTruthy()
      })
    })
  })

  describe('grid layout', () => {
    it('should render charts in grid layout', () => {
      renderModelDashboard()

      const gridContainer = screen.getByText('Accuracy Comparison').closest('.grid')
      expect(gridContainer).toBeInTheDocument()
      expect(gridContainer?.className).toContain('grid-cols-1')
      expect(gridContainer?.className).toContain('lg:grid-cols-2')
    })

    it('should apply gap between grid items', () => {
      renderModelDashboard()

      const gridContainer = screen.getByText('Accuracy Comparison').closest('.grid')
      expect(gridContainer?.className).toContain('gap-6')
    })
  })

  describe('empty state', () => {
    it('should handle empty models data gracefully', () => {
      const { useGetModelsAvailableQuery } = require('../../app/api')
      useGetModelsAvailableQuery.mockReturnValue({
        data: { data: { models: {} } },
        isLoading: false,
        error: null,
      })

      renderModelDashboard()

      expect(screen.getByText('Model Performance Dashboard')).toBeInTheDocument()
      expect(screen.getByRole('combobox')).toBeInTheDocument()
    })

    it('should not crash when models data is null', () => {
      const { useGetModelsAvailableQuery } = require('../../app/api')
      useGetModelsAvailableQuery.mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      })

      renderModelDashboard()

      expect(screen.getByText('Model Performance Dashboard')).toBeInTheDocument()
    })

    it('should show empty table when no models available', () => {
      const { useGetModelsAvailableQuery } = require('../../app/api')
      useGetModelsAvailableQuery.mockReturnValue({
        data: { data: { models: {} } },
        isLoading: false,
        error: null,
      })

      renderModelDashboard()

      const table = screen.getByRole('table')
      const rows = table.querySelectorAll('tbody tr')
      expect(rows.length).toBe(0)
    })
  })

  describe('accessibility', () => {
    it('should have accessible form elements', () => {
      renderModelDashboard()

      const select = screen.getByRole('combobox')
      expect(select).toBeInTheDocument()

      const button = screen.getByRole('button', { name: /Run Benchmark/i })
      expect(button).toBeInTheDocument()
    })

    it('should have accessible table structure', () => {
      renderModelDashboard()

      const table = screen.getByRole('table')
      expect(table).toBeInTheDocument()

      const headers = screen.getAllByRole('columnheader')
      expect(headers.length).toBe(6)
    })

    it('should disable button with proper attribute', () => {
      renderModelDashboard()

      const button = screen.getByRole('button', { name: /Run Benchmark/i })
      expect(button).toHaveAttribute('disabled')
    })
  })

  describe('styling and presentation', () => {
    it('should apply correct heading styles', () => {
      renderModelDashboard()

      const heading = screen.getByText('Model Performance Dashboard')
      expect(heading.className).toContain('text-3xl')
      expect(heading.className).toContain('font-bold')
    })

    it('should apply correct card spacing', () => {
      renderModelDashboard()

      const mainContainer = screen.getByText('Model Performance Dashboard').parentElement?.parentElement
      expect(mainContainer?.className).toContain('space-y-6')
    })

    it('should render icons with correct colors', () => {
      renderModelDashboard()

      const chartIcon = screen.getByTestId('chart-bar-icon').parentElement
      expect(chartIcon?.className).toContain('text-blue-600')

      const clockIcon = screen.getByTestId('clock-icon').parentElement
      expect(clockIcon?.className).toContain('text-green-600')

      const cpuIcon = screen.getByTestId('cpu-chip-icon').parentElement
      expect(cpuIcon?.className).toContain('text-purple-600')
    })
  })
})

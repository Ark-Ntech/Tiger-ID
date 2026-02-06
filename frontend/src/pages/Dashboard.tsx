import { useState, useMemo, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  useGetDashboardStatsQuery,
  useGetInvestigationsQuery,
  useGetFacilitiesQuery,
  useGetInvestigationAnalyticsQuery,
  useGetEvidenceAnalyticsQuery,
  useGetVerificationAnalyticsQuery,
  useGetGeographicAnalyticsQuery,
  useGetTigerAnalyticsQuery,
  useGetAgentAnalyticsQuery,
  useGetFacilityAnalyticsQuery,
  useGetModelsAvailableQuery,
  useBenchmarkModelMutation,
  api,
} from '../app/api'
import { useAppDispatch } from '../app/hooks'
import Card from '../components/common/Card'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import Button from '../components/common/Button'
import Alert from '../components/common/Alert'
import QuickStatsGrid, { StatItem } from '../components/dashboard/QuickStatsGrid'
import SubagentActivityPanel, {
  SubagentTask,
  PoolStats,
} from '../components/dashboard/SubagentActivityPanel'
import RecentInvestigationsTable, {
  Investigation as TableInvestigation,
} from '../components/dashboard/RecentInvestigationsTable'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts'
import GeographicMap from '../components/analytics/GeographicMap'
import {
  ChartBarIcon,
  ClockIcon,
  CpuChipIcon,
  ArrowPathIcon,
  BuildingOfficeIcon,
  FolderOpenIcon,
  ShieldCheckIcon,
  IdentificationIcon,
} from '@heroicons/react/24/outline'

const COLORS = ['#ff6b35', '#f97316', '#ea580c', '#c2410c', '#10b981', '#3b82f6']

const Dashboard = () => {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const [timeRange, setTimeRange] = useState('30days')
  const [activeTab, setActiveTab] = useState(0)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  // Calculate date range
  const dateRange = useMemo(() => {
    const endDate = new Date()
    let startDate: Date | undefined
    switch (timeRange) {
      case '7days':
        startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000)
        break
      case '30days':
        startDate = new Date(endDate.getTime() - 30 * 24 * 60 * 60 * 1000)
        break
      case '90days':
        startDate = new Date(endDate.getTime() - 90 * 24 * 60 * 60 * 1000)
        break
      case '1year':
        startDate = new Date(endDate.getTime() - 365 * 24 * 60 * 60 * 1000)
        break
      default:
        startDate = undefined
    }
    return {
      start_date: startDate?.toISOString(),
      end_date: endDate.toISOString(),
    }
  }, [timeRange])

  const { data: statsData, isLoading: statsLoading, refetch: refetchStats } = useGetDashboardStatsQuery()
  const { data: investigationsData, isLoading: investigationsLoading, refetch: refetchInvestigations } =
    useGetInvestigationsQuery({ page: 1, page_size: 10 })
  const { data: facilitiesData, refetch: refetchFacilities } = useGetFacilitiesQuery({ page: 1, page_size: 1000 })

  const facilities = facilitiesData?.data?.data || []

  // Transform facilities for GeographicMap (requires 'name' property)
  const mapFacilities = useMemo(
    () =>
      facilities.map(
        (f: { id: string; exhibitor_name?: string; name?: string; state?: string; city?: string; tiger_count?: number }) => ({
          id: f.id,
          name: f.exhibitor_name || f.name || 'Unknown',
          state: f.state,
          city: f.city,
          tiger_count: f.tiger_count,
        })
      ),
    [facilities]
  )

  // Analytics queries
  const {
    data: investigationAnalyticsData,
    isLoading: investigationAnalyticsLoading,
    refetch: refetchInvestigationAnalytics,
  } = useGetInvestigationAnalyticsQuery(dateRange)
  const {
    data: evidenceAnalyticsData,
    isLoading: evidenceAnalyticsLoading,
    refetch: refetchEvidenceAnalytics,
  } = useGetEvidenceAnalyticsQuery(dateRange)
  const {
    data: verificationAnalyticsData,
    isLoading: verificationAnalyticsLoading,
    refetch: refetchVerificationAnalytics,
  } = useGetVerificationAnalyticsQuery(dateRange)
  const {
    data: geographicAnalyticsData,
    isLoading: geographicAnalyticsLoading,
    refetch: refetchGeographicAnalytics,
  } = useGetGeographicAnalyticsQuery({})
  const {
    data: tigerAnalyticsData,
    isLoading: tigerAnalyticsLoading,
    refetch: refetchTigerAnalytics,
  } = useGetTigerAnalyticsQuery({})
  const {
    data: agentAnalyticsData,
    isLoading: agentAnalyticsLoading,
    refetch: refetchAgentAnalytics,
  } = useGetAgentAnalyticsQuery(dateRange)
  const {
    data: facilityAnalyticsData,
    isLoading: facilityAnalyticsLoading,
    refetch: refetchFacilityAnalytics,
  } = useGetFacilityAnalyticsQuery(dateRange)

  const stats = statsData?.data
  const invAnalytics = investigationAnalyticsData?.data
  const evAnalytics = evidenceAnalyticsData?.data
  const verAnalytics = verificationAnalyticsData?.data
  const geoAnalytics = geographicAnalyticsData?.data
  const tigAnalytics = tigerAnalyticsData?.data
  const agAnalytics = agentAnalyticsData?.data
  const facAnalytics = facilityAnalyticsData?.data

  const isLoading =
    statsLoading ||
    investigationsLoading ||
    investigationAnalyticsLoading ||
    evidenceAnalyticsLoading ||
    verificationAnalyticsLoading ||
    geographicAnalyticsLoading ||
    tigerAnalyticsLoading ||
    agentAnalyticsLoading ||
    facilityAnalyticsLoading

  // Refresh all data
  const handleRefresh = useCallback(async () => {
    await Promise.all([
      refetchStats(),
      refetchInvestigations(),
      refetchFacilities(),
      refetchInvestigationAnalytics(),
      refetchEvidenceAnalytics(),
      refetchVerificationAnalytics(),
      refetchGeographicAnalytics(),
      refetchTigerAnalytics(),
      refetchAgentAnalytics(),
      refetchFacilityAnalytics(),
    ])
    setLastRefresh(new Date())
    // Invalidate all analytics cache
    dispatch(api.util.invalidateTags(['Analytics', 'Dashboard']))
  }, [
    refetchStats,
    refetchInvestigations,
    refetchFacilities,
    refetchInvestigationAnalytics,
    refetchEvidenceAnalytics,
    refetchVerificationAnalytics,
    refetchGeographicAnalytics,
    refetchTigerAnalytics,
    refetchAgentAnalytics,
    refetchFacilityAnalytics,
    dispatch,
  ])

  // Auto-refresh every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      handleRefresh()
    }, 5 * 60 * 1000) // 5 minutes

    return () => clearInterval(interval)
  }, [handleRefresh])

  // Transform analytics data for charts
  const investigationsByStatus = useMemo(() => {
    if (!invAnalytics?.by_status) return []
    return Object.entries(invAnalytics.by_status).map(([name, value]) => ({
      name,
      value: Number(value),
    }))
  }, [invAnalytics])

  const investigationsByPriority = useMemo(() => {
    if (!invAnalytics?.by_priority) return []
    return Object.entries(invAnalytics.by_priority).map(([name, value]) => ({
      name,
      value: Number(value),
    }))
  }, [invAnalytics])

  const investigationsTimeline = useMemo(() => {
    if (!invAnalytics?.timeline_data) return []
    return Object.entries(invAnalytics.timeline_data)
      .map(([date, count]) => ({
        date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        count: Number(count),
      }))
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
  }, [invAnalytics])

  const tigerIdentifications = useMemo(() => {
    if (!tigAnalytics?.trends) return []
    return tigAnalytics.trends
      .map((trend: { date: string; count: number }) => ({
        date: new Date(trend.date).toLocaleDateString('en-US', { month: '2-digit', day: '2-digit' }),
        count: trend.count,
      }))
      .slice(-6) // Last 6 data points
  }, [tigAnalytics])

  // Model performance data - use Modal model metadata instead of mock data
  const { data: modelsData, isLoading: modelsLoading } = useGetModelsAvailableQuery()
  const [_benchmarkModel, { isLoading: benchmarkLoading }] = useBenchmarkModelMutation()
  void _benchmarkModel // Reserved for benchmark feature
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [benchmarkResults, setBenchmarkResults] = useState<{ message: string; model: string } | null>(null)
  const [isBenchmarking, setIsBenchmarking] = useState(false)

  // Define model info type
  type ModelInfo = {
    name?: string
    description?: string
    gpu?: string
    backend?: string
    type?: string
  }

  const availableModels = useMemo(
    () => (modelsData?.data?.models || {}) as Record<string, ModelInfo>,
    [modelsData?.data?.models]
  )
  const modelNames = useMemo(() => Object.keys(availableModels), [availableModels])

  // Use Modal model metadata instead of mock data
  const performanceData = useMemo(() => {
    return modelNames.map((modelName) => {
      const modelInfo: ModelInfo = availableModels[modelName] || {}
      return {
        model: modelName,
        name: modelInfo.name || modelName,
        description: modelInfo.description || '',
        gpu: modelInfo.gpu || 'Unknown',
        backend: modelInfo.backend || 'Modal',
        type: modelInfo.type || 'unknown',
        // Performance metrics would come from actual benchmarks
        // For now, show model metadata
        rank1_accuracy: null,
        map: null,
        latency_ms: null,
        throughput: null,
      }
    })
  }, [modelNames, availableModels])

  const handleBenchmark = async () => {
    if (!selectedModel) return
    setIsBenchmarking(true)
    setBenchmarkResults(null)
    try {
      setBenchmarkResults({
        message: 'Benchmarking requires test images. Use the Model Testing page to run benchmarks.',
        model: selectedModel,
      })
    } catch (error: unknown) {
      console.error('Error benchmarking model:', error)
    } finally {
      setIsBenchmarking(false)
    }
  }

  // Build QuickStatsGrid data
  const quickStats: StatItem[] = useMemo(() => {
    const tigerChange = tigAnalytics?.trends?.length
      ? tigAnalytics.trends[tigAnalytics.trends.length - 1]?.count -
        (tigAnalytics.trends[tigAnalytics.trends.length - 2]?.count || 0)
      : 0

    return [
      {
        label: 'Total Tigers',
        value: stats?.total_tigers || tigAnalytics?.total_tigers || 0,
        icon: <IdentificationIcon className="w-5 h-5" />,
        color: 'info' as const,
        href: '/tigers',
        change:
          tigerChange !== 0
            ? {
                value: Math.abs(tigerChange),
                type: tigerChange > 0 ? ('increase' as const) : ('decrease' as const),
                period: 'vs last period',
              }
            : undefined,
      },
      {
        label: 'Facilities',
        value: stats?.total_facilities || facAnalytics?.total_facilities || 0,
        icon: <BuildingOfficeIcon className="w-5 h-5" />,
        color: 'success' as const,
        href: '/facilities',
        change:
          (facAnalytics as unknown as { active_facilities?: number } | undefined)?.active_facilities &&
          (facAnalytics as unknown as { active_facilities: number }).active_facilities > 0
            ? {
                value: (facAnalytics as unknown as { active_facilities: number }).active_facilities,
                type: 'neutral' as const,
                period: 'active',
              }
            : undefined,
      },
      {
        label: 'ID Rate',
        value: `${tigAnalytics?.identification_rate?.toFixed(0) || 0}%`,
        icon: <ShieldCheckIcon className="w-5 h-5" />,
        color: (tigAnalytics?.identification_rate || 0) >= 80 ? ('success' as const) : ('warning' as const),
      },
      {
        label: 'Pending Verifications',
        value: verAnalytics?.pending || 0,
        icon: <ClockIcon className="w-5 h-5" />,
        color: (verAnalytics?.pending || 0) > 10 ? ('warning' as const) : ('default' as const),
        href: '/verification',
      },
    ]
  }, [stats, tigAnalytics, facAnalytics, verAnalytics])

  // Transform investigations for RecentInvestigationsTable
  const tableInvestigations: TableInvestigation[] = useMemo(() => {
    const rawInvestigations = investigationsData?.data?.data || []
    return rawInvestigations.map((inv: {
      id: string
      created_at?: string
      status: string
      query_image_url?: string
      match_count?: number
      top_match_confidence?: number
      top_match_tiger_name?: string
      phase?: string
    }) => ({
      id: inv.id,
      createdAt: inv.created_at || new Date().toISOString(),
      status: inv.status as 'pending' | 'in_progress' | 'completed' | 'failed',
      queryImageUrl: inv.query_image_url,
      matchCount: inv.match_count || 0,
      topMatchConfidence: inv.top_match_confidence,
      topMatchTigerName: inv.top_match_tiger_name,
      phase: inv.phase,
    }))
  }, [investigationsData])

  // Mock subagent tasks - in production this would come from an API
  const subagentTasks: SubagentTask[] = useMemo(() => {
    const tasks: SubagentTask[] = []

    // Create tasks based on current investigation status
    const activeInvestigations = tableInvestigations.filter(
      (inv) => inv.status === 'in_progress' || inv.status === 'pending'
    )

    activeInvestigations.forEach((inv, index) => {
      if (inv.status === 'in_progress') {
        tasks.push({
          id: `ml-${inv.id}`,
          type: 'ml_inference',
          status: 'running',
          investigation_id: inv.id,
          started_at: new Date(Date.now() - index * 60000).toISOString(),
          progress: Math.min(95, 30 + index * 20),
          model: 'wildlife_tools',
        })
      } else if (inv.status === 'pending') {
        tasks.push({
          id: `queue-${inv.id}`,
          type: 'ml_inference',
          status: 'queued',
          investigation_id: inv.id,
        })
      }
    })

    // Add some completed tasks
    if (tableInvestigations.length > 0) {
      const completedInv = tableInvestigations.find((inv) => inv.status === 'completed')
      if (completedInv) {
        tasks.push({
          id: `report-${completedInv.id}`,
          type: 'report_generation',
          status: 'completed',
          investigation_id: completedInv.id,
          started_at: new Date(Date.now() - 300000).toISOString(),
        })
      }
    }

    return tasks
  }, [tableInvestigations])

  // Mock pool stats - in production this would come from an API
  const poolStats: PoolStats = useMemo(() => {
    const runningMl = subagentTasks.filter((t) => t.type === 'ml_inference' && t.status === 'running').length
    const runningResearch = subagentTasks.filter((t) => t.type === 'research' && t.status === 'running').length
    const runningReport = subagentTasks.filter(
      (t) => t.type === 'report_generation' && t.status === 'running'
    ).length

    return {
      ml_inference: { active: runningMl, max: 4 },
      research: { active: runningResearch, max: 2 },
      report_generation: { active: runningReport, max: 2 },
    }
  }, [subagentTasks])

  const handleViewInvestigation = (id: string) => {
    navigate(`/investigation2/${id}`)
  }

  const handleTaskClick = (taskId: string) => {
    const task = subagentTasks.find((t) => t.id === taskId)
    if (task?.investigation_id) {
      navigate(`/investigation2/${task.investigation_id}`)
    }
  }

  const tabs = [
    'Investigations',
    'Evidence & Verification',
    'Geographic',
    'Tigers',
    'Facilities',
    'Agent Performance',
    'Model Performance',
  ]

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      {/* Header */}
      <div className="flex items-center justify-between" data-testid="dashboard-header">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-2">Wildlife identification system overview</p>
          {lastRefresh && (
            <p className="text-xs text-gray-500 mt-1">Last updated: {lastRefresh.toLocaleTimeString()}</p>
          )}
        </div>
        <div className="flex items-center space-x-2" data-testid="dashboard-controls">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setTimeRange('7days')}
            className={timeRange === '7days' ? 'ring-2 ring-primary-500' : ''}
          >
            7d
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setTimeRange('30days')}
            className={timeRange === '30days' ? 'ring-2 ring-primary-500' : ''}
          >
            30d
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setTimeRange('90days')}
            className={timeRange === '90days' ? 'ring-2 ring-primary-500' : ''}
          >
            90d
          </Button>
          <Button
            variant="secondary"
            onClick={handleRefresh}
            disabled={isLoading}
            className="flex items-center space-x-2"
            data-testid="refresh-button"
          >
            <ArrowPathIcon className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* Quick Stats Grid */}
      <QuickStatsGrid stats={quickStats} columns={4} loading={statsLoading} />

      {/* Main Content Grid: Charts + Subagent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6" data-testid="dashboard-main-content">
        {/* Investigation Activity Chart */}
        <div className="lg:col-span-2">
          <Card data-testid="investigation-activity-chart">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Investigation Activity</h3>
            {investigationAnalyticsLoading ? (
              <div className="flex items-center justify-center h-[300px]">
                <LoadingSpinner size="lg" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={investigationsTimeline}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="#ff6b35" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </Card>
        </div>

        {/* Subagent Activity Panel */}
        <div className="lg:col-span-1">
          <SubagentActivityPanel
            tasks={subagentTasks}
            poolStats={poolStats}
            onTaskClick={handleTaskClick}
          />
        </div>
      </div>

      {/* Second Row: Recent Investigations + Geographic Map */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" data-testid="dashboard-secondary-content">
        {/* Recent Investigations Table */}
        <Card padding="md" data-testid="recent-investigations-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Recent Investigations</h3>
            <Button variant="ghost" size="sm" onClick={() => navigate('/investigation2')}>
              View All
            </Button>
          </div>
          <RecentInvestigationsTable
            investigations={tableInvestigations}
            maxRows={5}
            onViewInvestigation={handleViewInvestigation}
            isLoading={investigationsLoading}
          />
        </Card>

        {/* Geographic Map */}
        <Card padding="md" data-testid="geographic-map-card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Geographic Distribution</h3>
          {geographicAnalyticsLoading ? (
            <div className="flex items-center justify-center h-[300px]">
              <LoadingSpinner size="lg" />
            </div>
          ) : mapFacilities && mapFacilities.length > 0 ? (
            <GeographicMap facilities={mapFacilities} isLoading={false} />
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-500">
              No facility data available
            </div>
          )}
        </Card>
      </div>

      {/* Analytics Tabs */}
      <Card padding="none" data-testid="analytics-tabs">
        <div className="border-b border-gray-200">
          <nav className="flex overflow-x-auto -mb-px" aria-label="Tabs">
            {tabs.map((tab, index) => (
              <button
                key={index}
                onClick={() => setActiveTab(index)}
                className={`
                  whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm transition-colors
                  ${
                    activeTab === index
                      ? 'border-tiger-orange text-tiger-orange'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
                data-testid={`tab-${tab.toLowerCase().replace(/\s+/g, '-')}`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <LoadingSpinner size="xl" />
              <p className="text-sm text-gray-500 mt-4">Loading analytics data...</p>
            </div>
          ) : (
            <>
              {activeTab === 0 && (
                <InvestigationAnalyticsTab
                  analytics={invAnalytics}
                  investigationsByStatus={investigationsByStatus}
                  investigationsByPriority={investigationsByPriority}
                  investigationsTimeline={investigationsTimeline}
                  investigations={investigationsData?.data?.data || []}
                  navigate={navigate}
                />
              )}
              {activeTab === 1 && (
                <EvidenceVerificationAnalyticsTab
                  evidenceAnalytics={evAnalytics}
                  verificationAnalytics={verAnalytics}
                />
              )}
              {activeTab === 2 && (
                <GeographicAnalyticsTab analytics={geoAnalytics} facilities={facilities} navigate={navigate} />
              )}
              {activeTab === 3 && (
                <TigerAnalyticsTab
                  analytics={tigAnalytics}
                  tigerIdentifications={tigerIdentifications}
                  navigate={navigate}
                />
              )}
              {activeTab === 4 && (
                <FacilityAnalyticsTab analytics={facAnalytics} facilities={facilities} navigate={navigate} />
              )}
              {activeTab === 5 && <AgentAnalyticsTab analytics={agAnalytics} />}
              {activeTab === 6 && (
                <ModelPerformanceTab
                  modelsData={modelsData}
                  modelsLoading={modelsLoading}
                  performanceData={performanceData}
                  selectedModel={selectedModel}
                  setSelectedModel={setSelectedModel}
                  benchmarkResults={benchmarkResults}
                  isBenchmarking={isBenchmarking}
                  benchmarkLoading={benchmarkLoading}
                  handleBenchmark={handleBenchmark}
                />
              )}
            </>
          )}
        </div>
      </Card>
    </div>
  )
}

// Investigation Analytics Tab Component
const InvestigationAnalyticsTab = ({
  analytics: _analytics,
  investigationsByStatus,
  investigationsByPriority,
  investigationsTimeline,
  investigations,
  navigate,
}: {
  analytics: unknown
  investigationsByStatus: Array<{ name: string; value: number }>
  investigationsByPriority: Array<{ name: string; value: number }>
  investigationsTimeline: Array<{ date: string; count: number }>
  investigations: Array<{
    id: string
    title?: string
    description?: string
    status: string
  }>
  navigate: (path: string) => void
}) => {
  void _analytics // Reserved for future analytics features
  return (
    <div className="space-y-6" data-testid="investigation-analytics-tab">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Investigations by Status</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={investigationsByStatus}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {investigationsByStatus.map((_entry, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Investigations by Priority</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={investigationsByPriority}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#ff6b35" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Investigations Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={investigationsTimeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#ff6b35" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Investigations</h3>
          <div className="space-y-3 max-h-[300px] overflow-y-auto">
            {investigations.map((investigation) => (
              <div
                key={investigation.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                onClick={() => navigate && navigate(`/investigations/${investigation.id}`)}
                data-testid={`investigation-item-${investigation.id}`}
              >
                <div className="flex items-center space-x-3 flex-1">
                  <FolderOpenIcon className="h-5 w-5 text-tiger-orange" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{investigation.title}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {investigation.description?.substring(0, 50)}...
                    </p>
                  </div>
                </div>
                <Badge
                  variant={
                    investigation.status === 'in_progress'
                      ? 'info'
                      : investigation.status === 'completed'
                        ? 'success'
                        : 'default'
                  }
                >
                  {investigation.status}
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}

// Evidence & Verification Analytics Tab Component
const EvidenceVerificationAnalyticsTab = ({
  evidenceAnalytics,
  verificationAnalytics,
}: {
  evidenceAnalytics?: {
    by_type?: Record<string, number>
    total_evidence?: number
  }
  verificationAnalytics?: {
    by_status?: Record<string, number>
    total_tasks?: number
    average_completion_time?: number
  }
}) => {
  const evidenceByType = evidenceAnalytics?.by_type
    ? Object.entries(evidenceAnalytics.by_type).map(([name, value]) => ({
        name,
        value: Number(value),
      }))
    : []

  const verificationByStatus = verificationAnalytics?.by_status
    ? Object.entries(verificationAnalytics.by_status).map(([name, value]) => ({
        name,
        value: Number(value),
      }))
    : []

  return (
    <div className="space-y-6" data-testid="evidence-verification-tab">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Evidence by Type</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={evidenceByType}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {evidenceByType.map((_entry, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Verification by Status</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={verificationByStatus}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <p className="text-sm text-gray-600">Total Evidence</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{evidenceAnalytics?.total_evidence || 0}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-600">Total Verification Tasks</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{verificationAnalytics?.total_tasks || 0}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-600">Avg Completion Time</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            {verificationAnalytics?.average_completion_time?.toFixed(1) || 0}h
          </p>
        </Card>
      </div>
    </div>
  )
}

// Geographic Analytics Tab Component
const GeographicAnalyticsTab = ({
  analytics,
  facilities,
  navigate,
}: {
  analytics?: {
    facilities_by_state?: Record<string, number>
    investigations_by_location?: Array<{ location: string; count: number }>
  }
  facilities: Array<{
    id: string
    exhibitor_name?: string
    name?: string
    city?: string
    state?: string
    tiger_count?: number
  }>
  navigate: (path: string) => void
}) => {
  const facilitiesByState = analytics?.facilities_by_state
    ? Object.entries(analytics.facilities_by_state)
        .map(([state, count]) => ({
          state,
          count: Number(count),
        }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10)
    : []

  // Transform facilities for GeographicMap (requires 'name' property)
  const mapFacilities = facilities.map((f) => ({
    id: f.id,
    name: f.exhibitor_name || f.name || 'Unknown',
    state: f.state,
    city: f.city,
    tiger_count: f.tiger_count,
  }))

  return (
    <div className="space-y-6" data-testid="geographic-tab">
      {/* Map Visualization */}
      {mapFacilities && mapFacilities.length > 0 && (
        <GeographicMap facilities={mapFacilities} isLoading={false} />
      )}

      {/* Chart Visualization */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Facilities by State</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={facilitiesByState} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="state" type="category" width={80} />
            <Tooltip />
            <Bar dataKey="count" fill="#10b981" />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {analytics?.investigations_by_location && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Investigations by Location</h3>
          <div className="space-y-2">
            {analytics.investigations_by_location.slice(0, 10).map((loc, idx: number) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span className="text-sm text-gray-700">{loc.location}</span>
                <Badge variant="info">{loc.count}</Badge>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Top Facilities List */}
      {facilities && facilities.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Facilities</h3>
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {[...facilities]
              .sort((a, b) => (b.tiger_count || 0) - (a.tiger_count || 0))
              .slice(0, 10)
              .map((facility) => (
                <div
                  key={facility.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                  onClick={() => navigate && navigate(`/facilities/${facility.id}`)}
                  data-testid={`facility-item-${facility.id}`}
                >
                  <div className="flex items-center space-x-3 flex-1">
                    <BuildingOfficeIcon className="h-5 w-5 text-green-600" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {facility.exhibitor_name || facility.name}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {facility.city && facility.state
                          ? `${facility.city}, ${facility.state}`
                          : facility.state || facility.city || 'Location unknown'}
                      </p>
                    </div>
                  </div>
                  <Badge variant="info">{facility.tiger_count || 0} tigers</Badge>
                </div>
              ))}
          </div>
        </Card>
      )}
    </div>
  )
}

// Tiger Analytics Tab Component
const TigerAnalyticsTab = ({
  analytics,
  tigerIdentifications,
  navigate,
}: {
  analytics?: {
    by_status?: Record<string, number>
    total_tigers?: number
    identification_rate?: number
  }
  tigerIdentifications: Array<{ date: string; count: number }>
  navigate: (path: string) => void
}) => {
  const tigersByStatus = analytics?.by_status
    ? Object.entries(analytics.by_status).map(([name, value]) => ({
        name,
        value: Number(value),
      }))
    : []

  return (
    <div className="space-y-6" data-testid="tiger-analytics-tab">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Tiger Identifications</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={tigerIdentifications}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#ff6b35" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Tigers by Status</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={tigersByStatus}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {tigersByStatus.map((_entry, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <p className="text-sm text-gray-600">Total Tigers</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{analytics?.total_tigers || 0}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-600">Identification Rate</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            {analytics?.identification_rate?.toFixed(0) || 0}%
          </p>
        </Card>
        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => navigate && navigate('/tigers')}
        >
          <p className="text-sm text-gray-600">View All Tigers</p>
          <p className="text-lg font-semibold text-tiger-orange mt-2">Browse Tigers</p>
        </Card>
      </div>
    </div>
  )
}

// Facility Analytics Tab Component
const FacilityAnalyticsTab = ({
  analytics,
  facilities,
  navigate,
}: {
  analytics?: {
    total_facilities?: number
    total_tigers?: number
    avg_tigers_per_facility?: number
    state_distribution?: Record<string, number>
  }
  facilities: Array<{
    id: string
    exhibitor_name?: string
    name?: string
    city?: string
    state?: string
    tiger_count?: number
  }>
  navigate: (path: string) => void
}) => {
  const facilitiesByState = analytics?.state_distribution
    ? Object.entries(analytics.state_distribution)
        .map(([state, count]) => ({
          state,
          count: Number(count),
        }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10)
    : []

  return (
    <div className="space-y-6" data-testid="facility-analytics-tab">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600">Total Facilities</p>
            <p className="text-4xl font-bold text-tiger-orange mt-2">{analytics?.total_facilities || 0}</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600">Total Tigers</p>
            <p className="text-4xl font-bold text-green-600 mt-2">{analytics?.total_tigers || 0}</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600">Avg Tigers/Facility</p>
            <p className="text-4xl font-bold text-blue-600 mt-2">
              {analytics?.avg_tigers_per_facility?.toFixed(1) || 0}
            </p>
          </div>
        </Card>
        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => navigate && navigate('/facilities')}
        >
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600">View All Facilities</p>
            <p className="text-lg font-semibold text-tiger-orange mt-2">Browse</p>
          </div>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Facilities by State</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={facilitiesByState} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="state" type="category" width={80} />
              <Tooltip />
              <Bar dataKey="count" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">State Distribution</h3>
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={facilitiesByState.slice(0, 8)}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ state, percent }) => `${state}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="count"
              >
                {facilitiesByState.slice(0, 8).map((_entry, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Top Facilities List */}
      {facilities && facilities.length > 0 && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Top Facilities by Tiger Count</h3>
            <Button variant="secondary" size="sm" onClick={() => navigate && navigate('/facilities')}>
              View All
            </Button>
          </div>
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {[...facilities]
              .sort((a, b) => (b.tiger_count || 0) - (a.tiger_count || 0))
              .slice(0, 15)
              .map((facility) => (
                <div
                  key={facility.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                  onClick={() => navigate && navigate(`/facilities/${facility.id}`)}
                  data-testid={`top-facility-item-${facility.id}`}
                >
                  <div className="flex items-center space-x-3 flex-1">
                    <BuildingOfficeIcon className="h-5 w-5 text-green-600" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {facility.exhibitor_name || facility.name}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {facility.city && facility.state
                          ? `${facility.city}, ${facility.state}`
                          : facility.state || facility.city || 'Location unknown'}
                      </p>
                    </div>
                  </div>
                  <Badge variant="info">{facility.tiger_count || 0} tigers</Badge>
                </div>
              ))}
          </div>
        </Card>
      )}
    </div>
  )
}

// Agent Analytics Tab Component
const AgentAnalyticsTab = ({
  analytics,
}: {
  analytics?: {
    agent_performance?: unknown[]
    agent_success_rates?: Record<string, { success_rate: number; total: number }>
    agent_activity?: Record<string, number>
    total_steps?: number
    unique_agents?: number
  }
}) => {
  const _agentPerformance = analytics?.agent_performance || []
  void _agentPerformance // Reserved for agent performance chart
  const agentSuccessRates = analytics?.agent_success_rates
    ? Object.entries(analytics.agent_success_rates).map(([agent, data]) => ({
        agent,
        success_rate: data.success_rate || 0,
        total: data.total || 0,
      }))
    : []

  return (
    <div className="space-y-6" data-testid="agent-analytics-tab">
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Success Rates</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={agentSuccessRates}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="agent" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="success_rate" fill="#3b82f6" name="Success Rate (%)" />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Activity</h3>
          <div className="space-y-2">
            {analytics?.agent_activity &&
              Object.entries(analytics.agent_activity).map(([agent, count]) => (
                <div key={agent} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="text-sm text-gray-700">{agent}</span>
                  <Badge variant="info">{count}</Badge>
                </div>
              ))}
          </div>
        </Card>

        <Card>
          <p className="text-sm text-gray-600 mb-4">Total Steps</p>
          <p className="text-3xl font-bold text-gray-900">{analytics?.total_steps || 0}</p>
          <p className="text-sm text-gray-600 mt-4 mb-2">Unique Agents</p>
          <p className="text-2xl font-bold text-gray-900">{analytics?.unique_agents || 0}</p>
        </Card>
      </div>
    </div>
  )
}

// Model Performance Tab Component
const ModelPerformanceTab = ({
  modelsData,
  modelsLoading,
  performanceData,
  selectedModel,
  setSelectedModel,
  benchmarkResults,
  isBenchmarking,
  benchmarkLoading,
  handleBenchmark,
}: {
  modelsData?: { data?: { models?: Record<string, unknown> } }
  modelsLoading: boolean
  performanceData: Array<{
    model: string
    name: string
    description: string
    gpu: string
    backend: string
    type: string
    rank1_accuracy: number | null
    map: number | null
    latency_ms: number | null
    throughput: number | null
  }>
  selectedModel: string
  setSelectedModel: (model: string) => void
  benchmarkResults: { message: string; model: string } | null
  isBenchmarking: boolean
  benchmarkLoading: boolean
  handleBenchmark: () => void
}) => {
  const availableModels = modelsData?.data?.models || {}
  const modelNames = Object.keys(availableModels)

  if (modelsLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  return (
    <div className="space-y-6" data-testid="model-performance-tab">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Model Performance</h2>
          <p className="text-gray-600 mt-2">Compare RE-ID model performance metrics</p>
        </div>
        <div className="flex gap-2">
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            data-testid="model-select"
          >
            <option value="">Select model to benchmark</option>
            {modelNames.map((modelName) => (
              <option key={modelName} value={modelName}>
                {modelName}
              </option>
            ))}
          </select>
          <Button
            variant="primary"
            onClick={handleBenchmark}
            disabled={!selectedModel || isBenchmarking || benchmarkLoading}
            data-testid="benchmark-button"
          >
            {isBenchmarking || benchmarkLoading ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                Benchmarking...
              </>
            ) : (
              'Run Benchmark'
            )}
          </Button>
        </div>
      </div>

      {/* Model Comparison Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Accuracy Comparison */}
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <ChartBarIcon className="h-6 w-6 text-blue-600" />
            <h3 className="text-xl font-semibold">Accuracy Comparison</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={performanceData.filter((d) => d.rank1_accuracy !== null)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 1]} />
              <Tooltip
                formatter={(value: number) => (value !== null ? `${(value * 100).toFixed(1)}%` : 'N/A')}
              />
              <Legend />
              <Bar dataKey="rank1_accuracy" fill="#3b82f6" name="Rank-1 Accuracy" />
              <Bar dataKey="map" fill="#10b981" name="mAP" />
            </BarChart>
          </ResponsiveContainer>
          {performanceData.filter((d) => d.rank1_accuracy === null).length > 0 && (
            <p className="text-sm text-gray-500 mt-2">
              Performance metrics require benchmarks. Use the Model Testing page to run benchmarks.
            </p>
          )}
        </Card>

        {/* Performance Metrics */}
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <ClockIcon className="h-6 w-6 text-green-600" />
            <h3 className="text-xl font-semibold">Performance Metrics</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="model" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="latency_ms" stroke="#ef4444" name="Latency (ms)" />
              <Line type="monotone" dataKey="throughput" stroke="#8b5cf6" name="Throughput (img/s)" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Model Performance Table */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <CpuChipIcon className="h-6 w-6 text-purple-600" />
          <h3 className="text-xl font-semibold">Model Performance Summary</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200" data-testid="model-performance-table">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Model
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rank-1 Accuracy
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  mAP
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Latency (ms)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Throughput (img/s)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {performanceData.map((model, index: number) => (
                <tr key={index} className="hover:bg-gray-50" data-testid={`model-row-${model.model}`}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    <div>
                      <div className="font-medium">{model.name || model.model}</div>
                      <div className="text-xs text-gray-500">{model.description || model.type}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {model.rank1_accuracy !== null ? `${(model.rank1_accuracy * 100).toFixed(1)}%` : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {model.map !== null ? `${(model.map * 100).toFixed(1)}%` : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {model.latency_ms !== null ? `${model.latency_ms.toFixed(0)}ms` : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {model.throughput !== null ? `${model.throughput.toFixed(1)}` : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge variant="success">Available</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Benchmark Results */}
      {benchmarkResults && (
        <Card data-testid="benchmark-results">
          <h3 className="text-xl font-semibold mb-4">Benchmark Results</h3>
          <Alert type="info">{benchmarkResults.message}</Alert>
        </Card>
      )}

      {/* Model Information */}
      {performanceData.length > 0 && (
        <Card>
          <h3 className="text-xl font-semibold mb-4">Model Information</h3>
          <div className="space-y-2">
            {performanceData.map((model) => (
              <div
                key={model.model}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                data-testid={`model-info-${model.model}`}
              >
                <div>
                  <span className="font-medium text-gray-900">{model.name || model.model}</span>
                  <span className="text-sm text-gray-500 ml-2">({model.gpu})</span>
                </div>
                <Badge variant="info">{model.type}</Badge>
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-500 mt-4">
            Performance metrics require benchmarks. Use the Model Testing page to run benchmarks and compare
            models.
          </p>
        </Card>
      )}
    </div>
  )
}

export default Dashboard

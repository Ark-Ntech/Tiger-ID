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
      .map((trend) => ({
        date: new Date(trend.date).toLocaleDateString('en-US', { month: '2-digit', day: '2-digit' }),
        count: trend.count,
      }))
      .slice(-6) // Last 6 data points
  }, [tigAnalytics])

  // Model performance data - use Modal model metadata instead of mock data
  const { data: modelsData, isLoading: modelsLoading } = useGetModelsAvailableQuery()
  const [benchmarkModel, { isLoading: benchmarkLoading }] = useBenchmarkModelMutation()
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [benchmarkResults, setBenchmarkResults] = useState<any>(null)
  const [isBenchmarking, setIsBenchmarking] = useState(false)

  const availableModels = modelsData?.data?.models || {}
  const modelNames = Object.keys(availableModels)
  
  // Use Modal model metadata instead of mock data
  const performanceData = useMemo(() => {
    return modelNames.map((modelName) => {
      const modelInfo = availableModels[modelName] || {}
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
        model: selectedModel
      })
    } catch (error: any) {
      console.error('Error benchmarking model:', error)
    } finally {
      setIsBenchmarking(false)
    }
  }

  const tabs = [
    'Investigations', 
    'Evidence & Verification', 
    'Geographic', 
    'Tigers', 
    'Facilities',
    'Agent Performance', 
    'Model Performance'
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-2">Comprehensive system analytics and insights</p>
          {lastRefresh && (
            <p className="text-xs text-gray-500 mt-1">
              Last updated: {lastRefresh.toLocaleTimeString()}
            </p>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="secondary"
            onClick={handleRefresh}
            disabled={isLoading}
            className="flex items-center space-x-2"
          >
            <ArrowPathIcon className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </Button>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="7days">Last 7 Days</option>
            <option value="30days">Last 30 Days</option>
            <option value="90days">Last 90 Days</option>
            <option value="1year">Last Year</option>
          </select>
        </div>
      </div>

      {/* Tab Navigation */}
      <Card padding="none">
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
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
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
                <FacilityAnalyticsTab
                  analytics={facAnalytics}
                  facilities={facilities}
                  navigate={navigate}
                />
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

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => navigate('/investigations')}>
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-2">
              <FolderOpenIcon className="h-5 w-5 text-primary-600" />
              <p className="text-sm font-medium text-gray-600">Total Investigations</p>
            </div>
            <p className="text-4xl font-bold text-primary-600 mt-2">{stats?.total_investigations || 0}</p>
            <p className="text-xs text-gray-500 mt-1">
              {stats?.active_investigations || 0} active • {stats?.completed_investigations || 0} completed
            </p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600">Completion Rate</p>
            <p className="text-4xl font-bold text-green-600 mt-2">
              {invAnalytics?.completion_rate?.toFixed(0) || 0}%
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {invAnalytics?.completed || 0} of {invAnalytics?.total_investigations || 0} resolved
            </p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600">Avg. Duration</p>
            <p className="text-4xl font-bold text-blue-600 mt-2">
              {invAnalytics?.average_duration_days?.toFixed(0) || 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">Days to completion</p>
          </div>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => navigate('/tigers')}>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600">Total Tigers</p>
            <p className="text-4xl font-bold text-purple-600 mt-2">
              {stats?.total_tigers || tigAnalytics?.total_tigers || 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {tigAnalytics?.identification_rate?.toFixed(0) || 0}% identification rate
            </p>
          </div>
        </Card>
      </div>

      {/* Additional Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => navigate('/facilities')}>
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-2">
              <BuildingOfficeIcon className="h-5 w-5 text-green-600" />
              <p className="text-sm font-medium text-gray-600">Total Facilities</p>
            </div>
            <p className="text-4xl font-bold text-green-600 mt-2">{stats?.total_facilities || facAnalytics?.total_facilities || 0}</p>
            <p className="text-xs text-gray-500 mt-1">
              {facAnalytics?.avg_tigers_per_facility?.toFixed(1) || 0} avg tigers/facility
            </p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600">Total Evidence</p>
            <p className="text-4xl font-bold text-orange-600 mt-2">
              {evAnalytics?.total_evidence || 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {evAnalytics?.high_relevance_count || 0} high relevance
            </p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600">Verification Tasks</p>
            <p className="text-4xl font-bold text-indigo-600 mt-2">
              {verAnalytics?.total_tasks || 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {verAnalytics?.pending || 0} pending • {verAnalytics?.approved || 0} approved
            </p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600">Agent Steps</p>
            <p className="text-4xl font-bold text-teal-600 mt-2">
              {agAnalytics?.total_steps || 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {agAnalytics?.unique_agents || 0} unique agents
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
}

// Investigation Analytics Tab Component
const InvestigationAnalyticsTab = ({
  analytics,
  investigationsByStatus,
  investigationsByPriority,
  investigationsTimeline,
  investigations,
  navigate,
}: any) => {
  return (
    <div className="space-y-6">
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
                {investigationsByStatus.map((entry: any, index: number) => (
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
            {investigations.map((investigation: any) => (
              <div
                key={investigation.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                onClick={() => navigate && navigate(`/investigations/${investigation.id}`)}
              >
                <div className="flex items-center space-x-3 flex-1">
                  <FolderOpenIcon className="h-5 w-5 text-primary-600" />
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
const EvidenceVerificationAnalyticsTab = ({ evidenceAnalytics, verificationAnalytics }: any) => {
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
    <div className="space-y-6">
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
                {evidenceByType.map((entry: any, index: number) => (
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
          <p className="text-3xl font-bold text-gray-900 mt-2">
            {evidenceAnalytics?.total_evidence || 0}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-gray-600">Total Verification Tasks</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            {verificationAnalytics?.total_tasks || 0}
          </p>
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
const GeographicAnalyticsTab = ({ analytics, facilities, navigate }: any) => {
  const facilitiesByState = analytics?.facilities_by_state
    ? Object.entries(analytics.facilities_by_state)
        .map(([state, count]) => ({
          state,
          count: Number(count),
        }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10)
    : []

  return (
    <div className="space-y-6">
      {/* Map Visualization */}
      {facilities && facilities.length > 0 && (
        <GeographicMap
          facilities={facilities}
          isLoading={false}
        />
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
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Investigations by Location
          </h3>
          <div className="space-y-2">
            {analytics.investigations_by_location.slice(0, 10).map((loc: any, idx: number) => (
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
              .sort((a: any, b: any) => (b.tiger_count || 0) - (a.tiger_count || 0))
              .slice(0, 10)
              .map((facility: any) => (
                <div
                  key={facility.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                  onClick={() => navigate && navigate(`/facilities/${facility.id}`)}
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
const TigerAnalyticsTab = ({ analytics, tigerIdentifications, navigate }: any) => {
  const tigersByStatus = analytics?.by_status
    ? Object.entries(analytics.by_status).map(([name, value]) => ({
        name,
        value: Number(value),
      }))
    : []

  return (
    <div className="space-y-6">
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
                {tigersByStatus.map((entry: any, index: number) => (
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
        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => navigate && navigate('/tigers')}>
          <p className="text-sm text-gray-600">View All Tigers</p>
          <p className="text-lg font-semibold text-primary-600 mt-2">→ Browse Tigers</p>
        </Card>
      </div>
    </div>
  )
}

// Facility Analytics Tab Component
const FacilityAnalyticsTab = ({ analytics, facilities, navigate }: any) => {
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
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600">Total Facilities</p>
            <p className="text-4xl font-bold text-primary-600 mt-2">
              {analytics?.total_facilities || 0}
            </p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600">Total Tigers</p>
            <p className="text-4xl font-bold text-green-600 mt-2">
              {analytics?.total_tigers || 0}
            </p>
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
        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => navigate && navigate('/facilities')}>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600">View All Facilities</p>
            <p className="text-lg font-semibold text-primary-600 mt-2">→ Browse</p>
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
                {facilitiesByState.slice(0, 8).map((entry: any, index: number) => (
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
            <Button
              variant="secondary"
              size="sm"
              onClick={() => navigate && navigate('/facilities')}
            >
              View All
            </Button>
          </div>
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {[...facilities]
              .sort((a: any, b: any) => (b.tiger_count || 0) - (a.tiger_count || 0))
              .slice(0, 15)
              .map((facility: any) => (
                <div
                  key={facility.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                  onClick={() => navigate && navigate(`/facilities/${facility.id}`)}
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
const AgentAnalyticsTab = ({ analytics }: any) => {
  const agentPerformance = analytics?.agent_performance || []
  const agentSuccessRates = analytics?.agent_success_rates
    ? Object.entries(analytics.agent_success_rates).map(([agent, data]: [string, any]) => ({
        agent,
        success_rate: data.success_rate || 0,
        total: data.total || 0,
      }))
    : []

  return (
    <div className="space-y-6">
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
              Object.entries(analytics.agent_activity).map(([agent, count]: [string, any]) => (
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
}: any) => {
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
    <div className="space-y-6">
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
            <BarChart data={performanceData.filter(d => d.rank1_accuracy !== null)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 1]} />
              <Tooltip formatter={(value: number) => value !== null ? `${(value * 100).toFixed(1)}%` : 'N/A'} />
              <Legend />
              <Bar dataKey="rank1_accuracy" fill="#3b82f6" name="Rank-1 Accuracy" />
              <Bar dataKey="map" fill="#10b981" name="mAP" />
            </BarChart>
          </ResponsiveContainer>
          {performanceData.filter(d => d.rank1_accuracy === null).length > 0 && (
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
          <table className="min-w-full divide-y divide-gray-200">
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
              {performanceData.map((model: any, index: number) => (
                <tr key={index} className="hover:bg-gray-50">
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
        <Card>
          <h3 className="text-xl font-semibold mb-4">Benchmark Results</h3>
          <Alert type="info">{benchmarkResults.message}</Alert>
        </Card>
      )}

      {/* Model Information */}
      {performanceData.length > 0 && (
        <Card>
          <h3 className="text-xl font-semibold mb-4">Model Information</h3>
          <div className="space-y-2">
            {performanceData.map((model: any) => (
              <div key={model.model} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <span className="font-medium text-gray-900">{model.name || model.model}</span>
                  <span className="text-sm text-gray-500 ml-2">({model.gpu})</span>
                </div>
                <Badge variant="info">{model.type}</Badge>
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-500 mt-4">
            Performance metrics require benchmarks. Use the Model Testing page to run benchmarks and compare models.
          </p>
        </Card>
      )}
    </div>
  )
}

export default Dashboard

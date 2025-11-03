import { useState, useMemo } from 'react'
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
} from '../app/api'
import Card from '../components/common/Card'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
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

const COLORS = ['#ff6b35', '#f97316', '#ea580c', '#c2410c', '#10b981', '#3b82f6']

const Dashboard = () => {
  const [timeRange, setTimeRange] = useState('30days')
  const [activeTab, setActiveTab] = useState(0)

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

  const { data: statsData, isLoading: statsLoading } = useGetDashboardStatsQuery()
  const { data: investigationsData, isLoading: investigationsLoading } =
    useGetInvestigationsQuery({ page: 1, page_size: 10 })
  const { data: facilitiesData } = useGetFacilitiesQuery({ page: 1, page_size: 1000 })
  
  const facilities = facilitiesData?.data?.data || []

  // Analytics queries
  const {
    data: investigationAnalyticsData,
    isLoading: investigationAnalyticsLoading,
  } = useGetInvestigationAnalyticsQuery(dateRange)
  const {
    data: evidenceAnalyticsData,
    isLoading: evidenceAnalyticsLoading,
  } = useGetEvidenceAnalyticsQuery(dateRange)
  const {
    data: verificationAnalyticsData,
    isLoading: verificationAnalyticsLoading,
  } = useGetVerificationAnalyticsQuery(dateRange)
  const { data: geographicAnalyticsData, isLoading: geographicAnalyticsLoading } =
    useGetGeographicAnalyticsQuery({})
  const { data: tigerAnalyticsData, isLoading: tigerAnalyticsLoading } =
    useGetTigerAnalyticsQuery({})
  const { data: agentAnalyticsData, isLoading: agentAnalyticsLoading } =
    useGetAgentAnalyticsQuery(dateRange)

  const stats = statsData?.data
  const invAnalytics = investigationAnalyticsData?.data
  const evAnalytics = evidenceAnalyticsData?.data
  const verAnalytics = verificationAnalyticsData?.data
  const geoAnalytics = geographicAnalyticsData?.data
  const tigAnalytics = tigerAnalyticsData?.data
  const agAnalytics = agentAnalyticsData?.data

  const isLoading =
    statsLoading ||
    investigationsLoading ||
    investigationAnalyticsLoading ||
    evidenceAnalyticsLoading ||
    verificationAnalyticsLoading ||
    geographicAnalyticsLoading ||
    tigerAnalyticsLoading ||
    agentAnalyticsLoading

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

  const tabs = ['Investigations', 'Evidence & Verification', 'Geographic', 'Tigers', 'Agent Performance']

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-2">Comprehensive system analytics and insights</p>
        </div>
        <div className="flex items-center space-x-2">
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
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner size="xl" />
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
                />
              )}
              {activeTab === 1 && (
                <EvidenceVerificationAnalyticsTab
                  evidenceAnalytics={evAnalytics}
                  verificationAnalytics={verAnalytics}
                />
              )}
              {activeTab === 2 && (
                <GeographicAnalyticsTab analytics={geoAnalytics} facilities={facilities} />
              )}
              {activeTab === 3 && (
                <TigerAnalyticsTab
                  analytics={tigAnalytics}
                  tigerIdentifications={tigerIdentifications}
                />
              )}
              {activeTab === 4 && <AgentAnalyticsTab analytics={agAnalytics} />}
            </>
          )}
        </div>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600">Total Investigations</p>
            <p className="text-4xl font-bold text-primary-600 mt-2">{stats?.total_investigations || 0}</p>
            <p className="text-xs text-gray-500 mt-1">
              {stats?.active_investigations || 0} active
            </p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600">Completion Rate</p>
            <p className="text-4xl font-bold text-green-600 mt-2">
              {invAnalytics?.completion_rate?.toFixed(0) || 0}%
            </p>
            <p className="text-xs text-gray-500 mt-1">Cases resolved</p>
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

        <Card>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600">Tiger Identifications</p>
            <p className="text-4xl font-bold text-purple-600 mt-2">
              {tigAnalytics?.identification_rate?.toFixed(0) || 0}%
            </p>
            <p className="text-xs text-gray-500 mt-1">AI accuracy</p>
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
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{investigation.title}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {investigation.description?.substring(0, 50)}...
                  </p>
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
const GeographicAnalyticsTab = ({ analytics, facilities }: any) => {
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
    </div>
  )
}

// Tiger Analytics Tab Component
const TigerAnalyticsTab = ({ analytics, tigerIdentifications }: any) => {
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
      </div>
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

export default Dashboard

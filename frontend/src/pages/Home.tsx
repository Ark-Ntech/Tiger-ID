import { useNavigate } from 'react-router-dom'
import { useGetDashboardStatsQuery } from '../app/api'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import {
  FolderIcon,
  ShieldCheckIcon,
  BuildingOfficeIcon,
  ClockIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline'
import { formatRelativeTime } from '../utils/formatters'

const Home = () => {
  const navigate = useNavigate()
  const { data, isLoading, error } = useGetDashboardStatsQuery()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-red-600">Failed to load dashboard statistics</p>
      </div>
    )
  }

  const stats = data?.data

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Welcome to Tiger ID</h1>
        <p className="text-gray-600 mt-2">
          Your comprehensive tiger trafficking investigation system
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Investigations</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {stats?.total_investigations || 0}
              </p>
            </div>
            <div className="p-3 bg-primary-100 rounded-lg">
              <FolderIcon className="h-8 w-8 text-primary-600" />
            </div>
          </div>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Cases</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {stats?.active_investigations || 0}
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <ClockIcon className="h-8 w-8 text-blue-600" />
            </div>
          </div>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Tigers Identified</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {stats?.total_tigers || 0}
              </p>
            </div>
            <div className="p-3 bg-orange-100 rounded-lg">
              <ShieldCheckIcon className="h-8 w-8 text-orange-600" />
            </div>
          </div>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Facilities Tracked</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {stats?.total_facilities || 0}
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <BuildingOfficeIcon className="h-8 w-8 text-green-600" />
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button
            variant="primary"
            className="w-full"
            onClick={() => navigate('/investigations/launch')}
          >
            <FolderIcon className="h-5 w-5 mr-2" />
            Launch Investigation
          </Button>
          <Button
            variant="outline"
            className="w-full"
            onClick={() => navigate('/tigers')}
          >
            <ShieldCheckIcon className="h-5 w-5 mr-2" />
            Identify Tiger
          </Button>
          <Button
            variant="outline"
            className="w-full"
            onClick={() => navigate('/verification')}
          >
            <CheckCircleIcon className="h-5 w-5 mr-2" />
            Verify Evidence
          </Button>
        </div>
      </Card>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
          <div className="space-y-4">
            {stats?.recent_activity && stats.recent_activity.length > 0 ? (
              stats.recent_activity.slice(0, 5).map((event: any) => (
                <div key={event.id} className="flex items-start space-x-3 pb-3 border-b last:border-b-0">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{event.event_type}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatRelativeTime(event.timestamp)}
                    </p>
                  </div>
                  <Badge variant="info">{event.event_type}</Badge>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500">No recent activity</p>
            )}
          </div>
        </Card>

        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">System Status</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">API Status</span>
              <Badge variant="success">Online</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Database</span>
              <Badge variant="success">Connected</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">WebSocket</span>
              <Badge variant="success">Active</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Pending Verifications</span>
              <Badge variant="warning">{stats?.pending_verifications || 0}</Badge>
            </div>
          </div>
        </Card>
      </div>

      {/* Getting Started */}
      <Card className="bg-gradient-to-br from-primary-50 to-primary-100 border border-primary-200">
        <div className="flex items-start space-x-4">
          <div className="text-4xl">🐅</div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">Getting Started</h3>
            <p className="text-sm text-gray-700 mt-2">
              This system helps investigators determine if a tiger is being trafficked or moved
              illicitly by analyzing user-provided data and external information using multi-agent AI.
            </p>
            <div className="mt-4">
              <Button variant="primary" size="sm">
                View Documentation
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default Home


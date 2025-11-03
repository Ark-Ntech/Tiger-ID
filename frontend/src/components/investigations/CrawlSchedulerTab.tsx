import { useState } from 'react'
import {
  useScheduleCrawlMutation,
  useGetCrawlStatisticsQuery,
  useGetFacilitiesQuery,
} from '../../app/api'
import Card from '../common/Card'
import Button from '../common/Button'
import Input from '../common/Input'
import LoadingSpinner from '../common/LoadingSpinner'
import Badge from '../common/Badge'
import { ServerIcon } from '@heroicons/react/24/outline'

const CrawlSchedulerTab = () => {
  const [selectedFacilityId, setSelectedFacilityId] = useState('')
  const [priority, setPriority] = useState<'high' | 'medium' | 'low'>('medium')
  const [statsDays, setStatsDays] = useState(30)
  const [showStats, setShowStats] = useState(false)
  const { data: facilitiesData, isLoading: facilitiesLoading } = useGetFacilitiesQuery({
    page: 1,
    page_size: 100,
  })
  const [scheduleCrawl, { isLoading: scheduling, data: scheduleData, error: scheduleError }] =
    useScheduleCrawlMutation()
  const {
    data: statsData,
    isLoading: statsLoading,
    refetch: refetchStats,
  } = useGetCrawlStatisticsQuery(
    { facility_id: selectedFacilityId || undefined, days: statsDays },
    { skip: !showStats }
  )

  const facilities = facilitiesData?.data?.data || []

  const handleSchedule = async () => {
    if (!selectedFacilityId) return
    try {
      await scheduleCrawl({
        facility_id: selectedFacilityId,
        priority,
      })
    } catch (err) {
      console.error('Crawl scheduling error:', err)
    }
  }

  const handleViewStats = () => {
    setShowStats(true)
    refetchStats()
  }

  const stats = statsData?.data?.statistics

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <ServerIcon className="h-6 w-6 text-primary-600" />
          Crawl Scheduler
        </h2>
        <p className="text-gray-600 mt-2">Schedule and manage facility web crawls</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Schedule Crawl</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Facility to Crawl
              </label>
              {facilitiesLoading ? (
                <LoadingSpinner size="sm" />
              ) : (
                <select
                  value={selectedFacilityId}
                  onChange={(e) => setSelectedFacilityId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">Select a facility...</option>
                  {facilities.map((facility) => (
                    <option key={facility.id} value={facility.id}>
                      {facility.name} ({facility.state || 'Unknown'})
                    </option>
                  ))}
                </select>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Crawl Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <Button
              onClick={handleSchedule}
              disabled={!selectedFacilityId || scheduling}
              className="w-full"
            >
              {scheduling ? 'Scheduling...' : '🕷️ Schedule Crawl'}
            </Button>
            {scheduleError && (
              <div className="text-red-600 text-sm">
                Crawl scheduling failed: {'data' in scheduleError ? JSON.stringify(scheduleError.data) : 'Unknown error'}
              </div>
            )}
            {scheduleData?.data && (
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-sm text-green-700">
                  ✅ Crawl scheduled! Task ID: {scheduleData.data.scheduling?.task_id || 'Unknown'}
                </p>
              </div>
            )}
          </div>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Statistics</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Statistics Days
              </label>
              <Input
                type="number"
                min={1}
                max={365}
                value={statsDays}
                onChange={(e) => setStatsDays(parseInt(e.target.value) || 30)}
              />
            </div>
            <Button onClick={handleViewStats} disabled={statsLoading} className="w-full">
              {statsLoading ? 'Loading...' : '📊 View Statistics'}
            </Button>
            {stats && (
              <div className="space-y-3 mt-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-600">Total Crawls</p>
                    <p className="text-xl font-bold text-gray-900">{stats.total_crawls}</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-600">Successful</p>
                    <p className="text-xl font-bold text-green-600">{stats.successful_crawls}</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-600">Failed</p>
                    <p className="text-xl font-bold text-red-600">{stats.failed_crawls}</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-600">Avg Duration</p>
                    <p className="text-xl font-bold text-gray-900">
                      {(stats.average_duration_ms / 1000).toFixed(1)}s
                    </p>
                  </div>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-xs text-blue-600">Images Found</p>
                  <p className="text-xl font-bold text-blue-900">{stats.total_images_found}</p>
                </div>
                <div className="p-3 bg-purple-50 rounded-lg">
                  <p className="text-xs text-purple-600">Tigers Identified</p>
                  <p className="text-xl font-bold text-purple-900">
                    {stats.total_tigers_identified}
                  </p>
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}

export default CrawlSchedulerTab


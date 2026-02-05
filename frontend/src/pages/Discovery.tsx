import { useState, useCallback, useMemo, useEffect } from 'react'
import {
  useGetDiscoveryStatusQuery,
  useGetDiscoveryStatsQuery,
  useGetCrawlQueueQuery,
  useGetCrawlHistoryQuery,
  useStartDiscoveryMutation,
  useStopDiscoveryMutation,
  useTriggerFullCrawlMutation,
} from '../app/api'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import { cn } from '../utils/cn'
import {
  PlayIcon,
  StopIcon,
  ArrowPathIcon,
  SignalIcon,
  BuildingOfficeIcon,
  PhotoIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  MapIcon,
} from '@heroicons/react/24/outline'
import { useWebSocket } from '../hooks/useWebSocket'

// Import new discovery components
import { FacilityCrawlGrid, type FacilityCrawlStatus, type CrawlStatus as FacilityCrawlStatusType } from '../components/discovery/FacilityCrawlGrid'
import { DiscoveryActivityFeed, type DiscoveryEvent, type DiscoveryEventType } from '../components/discovery/DiscoveryActivityFeed'
import { DiscoveryFacilitiesMap, type FacilityMapMarker, type FacilityStatus } from '../components/discovery/DiscoveryFacilitiesMap'
import { CrawlProgressCard } from '../components/discovery/CrawlProgressCard'

// Tab type definition
type TabId = 'overview' | 'queue' | 'history' | 'map'

// Interface for WebSocket discovery events
interface DiscoveryWebSocketMessage {
  type: 'discovery_event' | 'crawl_update' | 'notification'
  event_type?: DiscoveryEventType
  facility_id?: string
  facility_name?: string
  message?: string
  data?: Record<string, unknown>
  status?: FacilityCrawlStatusType
  progress?: number
  images_found?: number
  wait_seconds?: number
  error_message?: string
}

const Discovery = () => {
  const [activeTab, setActiveTab] = useState<TabId>('overview')
  const [selectedFacilityId, setSelectedFacilityId] = useState<string | undefined>()

  // Real-time state for WebSocket updates
  const [liveEvents, setLiveEvents] = useState<DiscoveryEvent[]>([])
  const [liveCrawlStatuses, setLiveCrawlStatuses] = useState<Map<string, FacilityCrawlStatus>>(new Map())

  // Fetch data
  const { data: statusData, isLoading: statusLoading, refetch: refetchStatus } = useGetDiscoveryStatusQuery()
  const { data: statsData, isLoading: statsLoading, refetch: refetchStats } = useGetDiscoveryStatsQuery()
  const { data: queueData, isLoading: queueLoading } = useGetCrawlQueueQuery({ limit: 50, days_old: 7 })
  const { data: historyData, isLoading: historyLoading } = useGetCrawlHistoryQuery({ limit: 50 })

  // Mutations
  const [startDiscovery, { isLoading: isStarting }] = useStartDiscoveryMutation()
  const [stopDiscovery, { isLoading: isStopping }] = useStopDiscoveryMutation()
  const [triggerFullCrawl, { isLoading: isCrawling }] = useTriggerFullCrawlMutation()

  const status = statusData?.data
  const stats = statsData?.data
  const queue = queueData?.data
  const history = historyData?.data

  // WebSocket handler for real-time updates
  const handleWebSocketMessage = useCallback((message: DiscoveryWebSocketMessage) => {
    if (message.type === 'discovery_event' && message.event_type) {
      const newEvent: DiscoveryEvent = {
        id: `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
        timestamp: new Date().toISOString(),
        type: message.event_type,
        facilityId: message.facility_id,
        facilityName: message.facility_name,
        message: message.message || '',
        metadata: message.data,
      }
      setLiveEvents((prev) => [newEvent, ...prev].slice(0, 100))
    }

    if (message.type === 'crawl_update' && message.facility_id) {
      setLiveCrawlStatuses((prev) => {
        const updated = new Map(prev)
        updated.set(message.facility_id!, {
          facility_id: message.facility_id!,
          facility_name: message.facility_name || 'Unknown Facility',
          status: message.status || 'waiting',
          progress: message.progress || 0,
          images_found: message.images_found || 0,
          last_update: new Date().toISOString(),
          wait_seconds: message.wait_seconds,
          error_message: message.error_message,
        })
        return updated
      })

      // Refetch stats when crawl updates occur
      refetchStats()
    }
  }, [refetchStats])

  // Initialize WebSocket connection
  const { isConnected } = useWebSocket({
    onMessage: handleWebSocketMessage,
    onConnect: () => {
      console.log('Discovery WebSocket connected')
    },
    autoConnect: true,
  })

  // Clear completed crawls after 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setLiveCrawlStatuses((prev) => {
        const updated = new Map(prev)
        const now = Date.now()
        for (const [id, crawl] of updated.entries()) {
          const lastUpdate = new Date(crawl.last_update).getTime()
          if (crawl.status === 'completed' && now - lastUpdate > 30000) {
            updated.delete(id)
          }
        }
        return updated
      })
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const handleStartStop = async () => {
    if (status?.status === 'running') {
      await stopDiscovery()
    } else {
      await startDiscovery()
    }
    refetchStatus()
    refetchStats()
  }

  const handleFullCrawl = async () => {
    await triggerFullCrawl()
    refetchStats()
  }

  const handleFacilityClick = useCallback((facilityId: string) => {
    setSelectedFacilityId(facilityId)
    // Could navigate to facility details or show a modal
    console.log('Facility clicked:', facilityId)
  }, [])

  const handleEventClick = useCallback((event: DiscoveryEvent) => {
    if (event.facilityId) {
      setSelectedFacilityId(event.facilityId)
    }
    console.log('Event clicked:', event)
  }, [])

  // Transform queue data to FacilityCrawlStatus format for the grid
  const facilityCrawlStatuses = useMemo((): FacilityCrawlStatus[] => {
    // Start with live crawl statuses
    const statusMap = new Map<string, FacilityCrawlStatus>(liveCrawlStatuses)

    // Add queue facilities that aren't already being tracked
    if (queue?.facilities) {
      for (const facility of queue.facilities) {
        if (!statusMap.has(facility.facility_id)) {
          statusMap.set(facility.facility_id, {
            facility_id: facility.facility_id,
            facility_name: facility.exhibitor_name || 'Unknown Facility',
            status: 'waiting',
            progress: 0,
            images_found: 0,
            last_update: facility.last_crawled_at || new Date().toISOString(),
          })
        }
      }
    }

    return Array.from(statusMap.values())
  }, [queue?.facilities, liveCrawlStatuses])

  // Transform queue data to map markers
  const facilityMapMarkers = useMemo((): FacilityMapMarker[] => {
    if (!queue?.facilities) return []

    // Note: Real implementation would need lat/lng from facility data
    // This creates placeholder markers for demonstration
    return queue.facilities
      .filter((f: any) => f.latitude && f.longitude)
      .map((facility: any): FacilityMapMarker => {
        const crawlStatus = liveCrawlStatuses.get(facility.facility_id)
        let mapStatus: FacilityStatus = 'idle'

        if (crawlStatus) {
          switch (crawlStatus.status) {
            case 'crawling':
              mapStatus = 'active'
              break
            case 'rate_limited':
              mapStatus = 'rate_limited'
              break
            case 'error':
              mapStatus = 'error'
              break
            default:
              mapStatus = 'idle'
          }
        }

        return {
          id: facility.facility_id,
          name: facility.exhibitor_name || 'Unknown Facility',
          latitude: facility.latitude || 0,
          longitude: facility.longitude || 0,
          status: mapStatus,
          lastCrawl: facility.last_crawled_at,
          imageCount: crawlStatus?.images_found || 0,
          tigerCount: facility.tiger_count || 0,
        }
      })
  }, [queue?.facilities, liveCrawlStatuses])

  // Tab configuration
  const tabs: { id: TabId; label: string; icon?: React.ReactNode }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'queue', label: 'Queue' },
    { id: 'history', label: 'History' },
    { id: 'map', label: 'Facilities Map', icon: <MapIcon className="h-4 w-4" /> },
  ]

  if (statusLoading || statsLoading) {
    return (
      <div data-testid="discovery-loading" className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  return (
    <div data-testid="discovery-page" className="space-y-6">
      {/* Header */}
      <div data-testid="discovery-header" className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Discovery Monitor</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Continuous tiger discovery from facility websites
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {/* WebSocket Connection Status */}
          <Badge
            data-testid="websocket-status"
            variant={isConnected ? 'success' : 'default'}
            className="px-2 py-0.5 text-xs"
          >
            {isConnected ? 'Live' : 'Offline'}
          </Badge>

          <Badge
            data-testid="scheduler-status"
            variant={status?.status === 'running' ? 'success' : 'default'}
            className="px-3 py-1"
          >
            <SignalIcon className="h-4 w-4 mr-1 inline" />
            {status?.status === 'running' ? 'Running' : 'Stopped'}
          </Badge>
          <Button
            data-testid="start-stop-button"
            variant={status?.status === 'running' ? 'danger' : 'primary'}
            onClick={handleStartStop}
            disabled={isStarting || isStopping}
          >
            {isStarting || isStopping ? (
              <LoadingSpinner size="sm" />
            ) : status?.status === 'running' ? (
              <>
                <StopIcon className="h-4 w-4 mr-2" />
                Stop
              </>
            ) : (
              <>
                <PlayIcon className="h-4 w-4 mr-2" />
                Start
              </>
            )}
          </Button>
          <Button
            data-testid="full-crawl-button"
            variant="outline"
            onClick={handleFullCrawl}
            disabled={isCrawling}
          >
            {isCrawling ? (
              <LoadingSpinner size="sm" />
            ) : (
              <>
                <ArrowPathIcon className="h-4 w-4 mr-2" />
                Full Crawl
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Stats Overview Cards */}
      <div data-testid="discovery-stats" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card data-testid="stat-facilities" className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Facilities</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {stats?.facilities?.total || 0}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {stats?.facilities?.crawled || 0} crawled
              </p>
            </div>
            <BuildingOfficeIcon className="h-10 w-10 text-blue-500" />
          </div>
        </Card>

        <Card data-testid="stat-tigers" className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Tigers Discovered</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {stats?.tigers?.discovered || 0}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {stats?.tigers?.total || 0} total in database
              </p>
            </div>
            <span className="text-4xl" aria-hidden="true">&#128005;</span>
          </div>
        </Card>

        <Card data-testid="stat-images" className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Images</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {stats?.images?.total || 0}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {stats?.images?.verified || 0} verified
              </p>
            </div>
            <PhotoIcon className="h-10 w-10 text-green-500" />
          </div>
        </Card>

        <Card data-testid="stat-crawls" className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Crawls (7 days)</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {stats?.crawls?.recent_7_days || 0}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {stats?.crawls?.successful || 0} successful
              </p>
            </div>
            <ClockIcon className="h-10 w-10 text-purple-500" />
          </div>
        </Card>
      </div>

      {/* Tools Used */}
      <Card data-testid="tools-used" className="p-4">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Tools Used (All Free)</h3>
        <div className="flex flex-wrap gap-2">
          {(stats?.tools_used || ['duckduckgo', 'playwright', 'opencv', 'modal_gpu']).map((tool: string) => (
            <Badge key={tool} variant="default" className="text-xs">
              {tool}
            </Badge>
          ))}
        </div>
      </Card>

      {/* Tabs */}
      <div data-testid="discovery-tabs" className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              data-testid={`tab-${tab.id}`}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'py-4 px-1 border-b-2 font-medium text-sm transition-colors flex items-center gap-2',
                activeTab === tab.id
                  ? 'border-tiger-orange text-tiger-orange'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              )}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div data-testid="tab-content-overview" className="space-y-6">
          {/* Facility Crawl Grid */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Active Crawls
            </h3>
            <FacilityCrawlGrid
              facilities={facilityCrawlStatuses}
              onFacilityClick={handleFacilityClick}
            />
          </div>

          {/* Two-column layout: Scheduler Status + Activity Feed */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column: Scheduler Status + Facility Breakdown */}
            <div className="space-y-6">
              {/* Scheduler Status */}
              <Card data-testid="scheduler-status-card">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  Scheduler Status
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Status</span>
                    <Badge variant={status?.status === 'running' ? 'success' : 'default'}>
                      {status?.status || 'unknown'}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Enabled</span>
                    <span className="text-gray-900 dark:text-gray-100">
                      {status?.enabled ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Total Crawls</span>
                    <span className="text-gray-900 dark:text-gray-100">
                      {stats?.scheduler?.total_crawls || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Last Crawl</span>
                    <span className="text-gray-900 dark:text-gray-100">
                      {stats?.scheduler?.last_crawl
                        ? new Date(stats.scheduler.last_crawl).toLocaleString()
                        : 'Never'}
                    </span>
                  </div>
                </div>
              </Card>

              {/* Facility Breakdown */}
              <Card data-testid="facility-breakdown-card">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  Facility Breakdown
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Reference Facilities</span>
                    <span className="text-gray-900 dark:text-gray-100">
                      {stats?.facilities?.reference || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">With Website</span>
                    <span className="text-gray-900 dark:text-gray-100">
                      {stats?.facilities?.with_website || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">With Social Media</span>
                    <span className="text-gray-900 dark:text-gray-100">
                      {stats?.facilities?.with_social_media || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Pending Crawl</span>
                    <span className="text-tiger-orange font-medium">
                      {stats?.facilities?.pending_crawl || 0}
                    </span>
                  </div>
                </div>
              </Card>
            </div>

            {/* Right Column: Activity Feed */}
            <div>
              <DiscoveryActivityFeed
                events={liveEvents}
                maxEvents={50}
                autoScroll={true}
                onEventClick={handleEventClick}
                className="h-full"
              />
            </div>
          </div>
        </div>
      )}

      {activeTab === 'queue' && (
        <Card data-testid="tab-content-queue">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Crawl Queue ({queue?.count || 0} facilities pending)
          </h3>
          {queueLoading ? (
            <LoadingSpinner />
          ) : queue?.facilities?.length ? (
            <div className="overflow-x-auto">
              <table data-testid="queue-table" className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead>
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Facility
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Location
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Tigers
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Last Crawled
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {queue.facilities.map((facility: any) => (
                    <tr
                      key={facility.facility_id}
                      data-testid={`queue-row-${facility.facility_id}`}
                      className="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                      onClick={() => handleFacilityClick(facility.facility_id)}
                    >
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {facility.exhibitor_name}
                        </div>
                        {facility.website && (
                          <a
                            href={facility.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-500 hover:underline"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {facility.website}
                          </a>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                        {facility.city}, {facility.state}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {facility.tiger_count || 0}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                        {facility.last_crawled_at
                          ? new Date(facility.last_crawled_at).toLocaleDateString()
                          : 'Never'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p data-testid="queue-empty" className="text-gray-500 dark:text-gray-400 text-center py-8">
              No facilities pending crawl
            </p>
          )}
        </Card>
      )}

      {activeTab === 'history' && (
        <Card data-testid="tab-content-history">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Recent Crawl History
          </h3>
          {historyLoading ? (
            <LoadingSpinner />
          ) : history?.crawls?.length ? (
            <div className="space-y-3">
              {history.crawls.map((crawl: any) => (
                <div
                  key={crawl.crawl_id}
                  data-testid={`history-item-${crawl.crawl_id}`}
                  className={cn(
                    'p-4 rounded-lg border cursor-pointer transition-colors',
                    crawl.status === 'completed'
                      ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/30'
                      : crawl.status === 'failed'
                      ? 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30'
                      : 'border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700'
                  )}
                  onClick={() => crawl.facility_id && handleFacilityClick(crawl.facility_id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                      {crawl.status === 'completed' ? (
                        <CheckCircleIcon className="h-5 w-5 text-green-500" />
                      ) : crawl.status === 'failed' ? (
                        <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                      ) : (
                        <ClockIcon className="h-5 w-5 text-gray-500" />
                      )}
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {crawl.source_url || 'Unknown source'}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {crawl.crawled_at
                            ? new Date(crawl.crawled_at).toLocaleString()
                            : 'Unknown time'}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge
                        variant={
                          crawl.status === 'completed'
                            ? 'success'
                            : crawl.status === 'failed'
                            ? 'danger'
                            : 'default'
                        }
                      >
                        {crawl.status}
                      </Badge>
                      {crawl.images_found > 0 && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {crawl.images_found} images, {crawl.tigers_identified} tigers
                        </p>
                      )}
                    </div>
                  </div>
                  {crawl.error && (
                    <p className="mt-2 text-xs text-red-600 dark:text-red-400">
                      {crawl.error}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p data-testid="history-empty" className="text-gray-500 dark:text-gray-400 text-center py-8">
              No crawl history available
            </p>
          )}
        </Card>
      )}

      {activeTab === 'map' && (
        <div data-testid="tab-content-map" className="space-y-4">
          <DiscoveryFacilitiesMap
            facilities={facilityMapMarkers}
            selectedFacilityId={selectedFacilityId}
            onFacilitySelect={handleFacilityClick}
            height="600px"
          />

          {/* Optional: Show selected facility details */}
          {selectedFacilityId && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {facilityCrawlStatuses
                .filter((f) => f.facility_id === selectedFacilityId)
                .map((facility) => (
                  <CrawlProgressCard
                    key={facility.facility_id}
                    facilityId={facility.facility_id}
                    facilityName={facility.facility_name}
                    status={facility.status === 'crawling' ? 'crawling'
                      : facility.status === 'completed' ? 'completed'
                      : facility.status === 'error' ? 'error'
                      : facility.status === 'rate_limited' ? 'rate_limited'
                      : 'idle'}
                    progress={facility.progress}
                    imagesFound={facility.images_found}
                    rateLimitWait={facility.wait_seconds}
                    errorMessage={facility.error_message}
                    onClick={() => handleFacilityClick(facility.facility_id)}
                  />
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Discovery

import { useState, useMemo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGetFacilitiesQuery, useGetCrawlHistoryQuery } from '../app/api'
import Card from '../components/common/Card'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import Alert from '../components/common/Alert'
import FacilityMapView, { Facility as MapFacility } from '../components/facilities/FacilityMapView'
import FacilityFilters, { FacilityFiltersProps } from '../components/facilities/FacilityFilters'
import CrawlHistoryTimeline, { CrawlEvent } from '../components/facilities/CrawlHistoryTimeline'
import FacilityTigerGallery, { TigerImage } from '../components/facilities/FacilityTigerGallery'
import {
  BuildingOfficeIcon,
  GlobeAltIcon,
  LinkIcon,
  MapIcon,
  ListBulletIcon,
  PlusIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'
import { Facility } from '../types'

// View mode type
type ViewMode = 'list' | 'map'

/**
 * Transform API facility to map view facility format
 */
function toMapFacility(facility: Facility): MapFacility {
  // Map facility_type to the expected type enum
  const typeMap: Record<string, MapFacility['type']> = {
    'zoo': 'zoo',
    'sanctuary': 'sanctuary',
    'rescue': 'rescue',
    'breeding': 'breeding',
  }

  return {
    id: facility.id,
    name: facility.exhibitor_name || facility.name,
    type: typeMap[facility.facility_type?.toLowerCase()] || 'other',
    latitude: facility.latitude,
    longitude: facility.longitude,
    country: facility.country,
    region: facility.state,
    tigerCount: facility.tiger_count,
    lastDiscovery: facility.updated_at,
    discoveryStatus: facility.status === 'active' ? 'active' : facility.status === 'inactive' ? 'inactive' : 'pending',
  }
}

/**
 * Transform crawl history records to CrawlEvent format
 */
function toCrawlEvents(crawls: Array<{
  crawl_id: string
  status: string
  images_found?: number
  tigers_identified?: number
  crawled_at?: string
  completed_at?: string
  duration_ms?: number
  error?: string
}>): CrawlEvent[] {
  const events: CrawlEvent[] = []

  crawls.forEach(crawl => {
    // Add crawl started event
    if (crawl.crawled_at) {
      events.push({
        id: `${crawl.crawl_id}-start`,
        timestamp: crawl.crawled_at,
        type: 'crawl_started',
        details: {},
      })
    }

    // Add images found event if applicable
    if (crawl.images_found && crawl.images_found > 0 && crawl.crawled_at) {
      events.push({
        id: `${crawl.crawl_id}-images`,
        timestamp: crawl.crawled_at,
        type: 'images_found',
        details: { imageCount: crawl.images_found },
      })
    }

    // Add tigers detected event if applicable
    if (crawl.tigers_identified && crawl.tigers_identified > 0 && crawl.crawled_at) {
      events.push({
        id: `${crawl.crawl_id}-tigers`,
        timestamp: crawl.crawled_at,
        type: 'tigers_detected',
        details: { tigerCount: crawl.tigers_identified },
      })
    }

    // Add completion or error event
    if (crawl.status === 'completed' && crawl.completed_at) {
      events.push({
        id: `${crawl.crawl_id}-complete`,
        timestamp: crawl.completed_at,
        type: 'crawl_completed',
        details: {
          duration: crawl.duration_ms,
          imageCount: crawl.images_found,
          tigerCount: crawl.tigers_identified,
        },
      })
    } else if (crawl.status === 'failed' && crawl.crawled_at) {
      events.push({
        id: `${crawl.crawl_id}-error`,
        timestamp: crawl.completed_at || crawl.crawled_at,
        type: 'error',
        details: { errorMessage: crawl.error },
      })
    } else if (crawl.status === 'rate_limited' && crawl.crawled_at) {
      events.push({
        id: `${crawl.crawl_id}-ratelimit`,
        timestamp: crawl.crawled_at,
        type: 'rate_limited',
        details: { waitTime: crawl.duration_ms },
      })
    }
  })

  return events
}

const Facilities = () => {
  const [page, _setPage] = useState(1)
  void _setPage // Reserved for pagination feature
  const navigate = useNavigate()

  // View state
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [selectedFacility, setSelectedFacility] = useState<Facility | null>(null)

  // Filter state
  const [filters, setFilters] = useState<FacilityFiltersProps['filters']>({})

  // API queries
  const { data, isLoading, error } = useGetFacilitiesQuery({ page, page_size: 50 })

  // Get crawl history for selected facility
  const { data: crawlHistoryData, isLoading: isCrawlHistoryLoading } = useGetCrawlHistoryQuery(
    { facility_id: selectedFacility?.id, limit: 20 },
    { skip: !selectedFacility }
  )

  // Extract facilities from response
  const facilities = useMemo(() => data?.data?.data || [], [data])

  // Extract unique facility types and countries for filters
  const facilityTypes = useMemo(() => {
    const types = new Set<string>()
    facilities.forEach(f => {
      if (f.facility_type) types.add(f.facility_type.toLowerCase())
    })
    return Array.from(types)
  }, [facilities])

  const countries = useMemo(() => {
    const countrySet = new Set<string>()
    facilities.forEach(f => {
      if (f.country) countrySet.add(f.country)
    })
    return Array.from(countrySet).sort()
  }, [facilities])

  // Apply filters to facilities
  const filteredFacilities = useMemo(() => {
    return facilities.filter(facility => {
      // Search filter
      if (filters.search) {
        const search = filters.search.toLowerCase()
        const name = (facility.exhibitor_name || facility.name || '').toLowerCase()
        const city = (facility.city || '').toLowerCase()
        const state = (facility.state || '').toLowerCase()
        if (!name.includes(search) && !city.includes(search) && !state.includes(search)) {
          return false
        }
      }

      // Type filter
      if (filters.type && filters.type.length > 0) {
        const facilityType = (facility.facility_type || '').toLowerCase()
        if (!filters.type.some(t => facilityType.includes(t))) {
          return false
        }
      }

      // Country filter
      if (filters.country && filters.country.length > 0) {
        if (!filters.country.includes(facility.country || '')) {
          return false
        }
      }

      // Discovery status filter
      if (filters.discoveryStatus && filters.discoveryStatus.length > 0) {
        if (!filters.discoveryStatus.includes(facility.status)) {
          return false
        }
      }

      // Has tigers filter
      if (filters.hasTigers === true) {
        if (!facility.tiger_count || facility.tiger_count === 0) {
          return false
        }
      }

      return true
    })
  }, [facilities, filters])

  // Convert facilities for map view
  const mapFacilities = useMemo(() => {
    return filteredFacilities.map(toMapFacility)
  }, [filteredFacilities])

  // Convert crawl history to events
  const crawlEvents = useMemo(() => {
    if (!crawlHistoryData?.data?.crawls) return []
    return toCrawlEvents(crawlHistoryData.data.crawls)
  }, [crawlHistoryData])

  // Mock tiger images for the selected facility (in real app, would come from API)
  const facilityTigerImages: TigerImage[] = useMemo(() => {
    // This would be replaced with actual API data
    // For now, return empty array
    return []
  }, [])

  // Handlers
  const handleFiltersChange = useCallback((newFilters: FacilityFiltersProps['filters']) => {
    setFilters(newFilters)
  }, [])

  const handleFacilitySelect = useCallback((facility: Facility) => {
    setSelectedFacility(facility)
  }, [])

  const handleMapFacilitySelect = useCallback((mapFacility: MapFacility) => {
    const facility = facilities.find(f => f.id === mapFacility.id)
    if (facility) {
      setSelectedFacility(facility)
    }
  }, [facilities])

  const handleCloseDetail = useCallback(() => {
    setSelectedFacility(null)
  }, [])

  const handleTigerClick = useCallback((tigerId: string) => {
    navigate(`/tigers/${tigerId}`)
  }, [navigate])

  const formatDate = (dateStr: string | undefined) => {
    if (!dateStr) return null
    try {
      return new Date(dateStr).toLocaleDateString()
    } catch {
      return dateStr
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full" data-testid="facilities-loading">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full" data-testid="facilities-error">
        <Alert type="error">Error loading facilities. Please try again.</Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6" data-testid="facilities-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100" data-testid="facilities-title">
            Facilities
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Track and monitor tiger facilities from TPC dataset
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Add Facility Button */}
          <button
            type="button"
            data-testid="add-facility-button"
            className="inline-flex items-center gap-2 px-4 py-2 bg-tiger-orange hover:bg-tiger-orange-dark text-white font-medium rounded-lg transition-colors"
            onClick={() => navigate('/facilities/new')}
          >
            <PlusIcon className="h-5 w-5" />
            Add Facility
          </button>

          {/* View Toggle */}
          <div
            className="flex items-center bg-gray-100 dark:bg-tactical-800 rounded-lg p-1"
            data-testid="view-mode-toggle"
          >
            <button
              type="button"
              onClick={() => setViewMode('list')}
              data-testid="view-mode-list"
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'list'
                  ? 'bg-white dark:bg-tactical-600 text-gray-900 dark:text-gray-100 shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
              aria-label="List view"
              aria-pressed={viewMode === 'list'}
            >
              <ListBulletIcon className="h-5 w-5" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode('map')}
              data-testid="view-mode-map"
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'map'
                  ? 'bg-white dark:bg-tactical-600 text-gray-900 dark:text-gray-100 shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
              aria-label="Map view"
              aria-pressed={viewMode === 'map'}
            >
              <MapIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <FacilityFilters
        filters={filters}
        onFiltersChange={handleFiltersChange}
        facilityTypes={facilityTypes}
        countries={countries}
        data-testid="facility-filters"
      />

      {/* Main Content Area */}
      <div className="flex gap-6">
        {/* Facilities List/Map */}
        <div className={`flex-1 ${selectedFacility ? 'lg:w-2/3' : 'w-full'}`}>
          {viewMode === 'list' ? (
            // List View
            filteredFacilities.length > 0 ? (
              <div className="space-y-4" data-testid="facilities-list">
                {filteredFacilities.map((facility: Facility) => (
                  <Card
                    key={facility.id}
                    data-testid={`facility-card-${facility.id}`}
                    className={`hover:shadow-lg transition-shadow cursor-pointer ${
                      selectedFacility?.id === facility.id
                        ? 'ring-2 ring-tiger-orange'
                        : ''
                    }`}
                    onClick={() => handleFacilitySelect(facility)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-start space-x-4">
                          <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                            <BuildingOfficeIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-start justify-between">
                              <div>
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                  {facility.exhibitor_name || facility.name}
                                </h3>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                  {facility.city && facility.state ? (
                                    `${facility.city}, ${facility.state}`
                                  ) : facility.state || facility.city || 'Location unknown'}
                                </p>
                                {facility.address && (
                                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">{facility.address}</p>
                                )}
                              </div>
                              <div className="flex flex-col items-end space-y-2">
                                {facility.is_reference_facility && (
                                  <Badge variant="success">Reference Facility</Badge>
                                )}
                                {facility.accreditation_status && (
                                  <Badge variant={facility.accreditation_status === 'Non-Accredited' ? 'warning' : 'info'}>
                                    {facility.accreditation_status}
                                  </Badge>
                                )}
                              </div>
                            </div>

                            <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                              {facility.tiger_count !== undefined && (
                                <div>
                                  <span className="text-gray-500 dark:text-gray-400">Tiger Count:</span>
                                  <p className="font-medium text-gray-900 dark:text-gray-100">{facility.tiger_count}</p>
                                </div>
                              )}
                              {facility.ir_date && (
                                <div>
                                  <span className="text-gray-500 dark:text-gray-400">IR Date:</span>
                                  <p className="font-medium text-gray-900 dark:text-gray-100">{formatDate(facility.ir_date)}</p>
                                </div>
                              )}
                              {facility.last_inspection_date && (
                                <div>
                                  <span className="text-gray-500 dark:text-gray-400">Last Inspection:</span>
                                  <p className="font-medium text-gray-900 dark:text-gray-100">{formatDate(facility.last_inspection_date)}</p>
                                </div>
                              )}
                            </div>

                            {(facility.website || (facility.social_media_links && Object.keys(facility.social_media_links).length > 0)) && (
                              <div className="mt-4 flex items-center space-x-4">
                                {facility.website && (
                                  <a
                                    href={facility.website.startsWith('http') ? facility.website : `https://${facility.website}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    <GlobeAltIcon className="h-4 w-4" />
                                    <span>Website</span>
                                  </a>
                                )}
                                {facility.social_media_links && Object.keys(facility.social_media_links).length > 0 && (
                                  <div className="flex items-center space-x-2">
                                    {Object.entries(facility.social_media_links).map(([platform, url]) => (
                                      <a
                                        key={platform}
                                        href={url.startsWith('http') ? url : `https://${url}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                                        title={platform}
                                        onClick={(e) => e.stopPropagation()}
                                      >
                                        <LinkIcon className="h-4 w-4" />
                                        <span className="capitalize">{platform}</span>
                                      </a>
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <Card className="text-center py-12" data-testid="facilities-empty">
                <BuildingOfficeIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 dark:text-gray-400">
                  {filters.search || filters.type?.length || filters.country?.length
                    ? 'No facilities match your filters'
                    : 'No facilities found'}
                </p>
              </Card>
            )
          ) : (
            // Map View
            <div data-testid="facilities-map-container">
              <FacilityMapView
                facilities={mapFacilities}
                selectedFacilityId={selectedFacility?.id}
                onFacilitySelect={handleMapFacilitySelect}
                className="h-[600px]"
              />
            </div>
          )}
        </div>

        {/* Selected Facility Detail Panel */}
        {selectedFacility && (
          <div
            className="hidden lg:block lg:w-1/3 space-y-6"
            data-testid="facility-detail-panel"
          >
            {/* Facility Header */}
            <Card>
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start space-x-3">
                  <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                    <BuildingOfficeIcon className="h-5 w-5 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {selectedFacility.exhibitor_name || selectedFacility.name}
                    </h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {selectedFacility.city && selectedFacility.state
                        ? `${selectedFacility.city}, ${selectedFacility.state}`
                        : selectedFacility.state || selectedFacility.city || 'Location unknown'}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleCloseDetail}
                  data-testid="close-detail-panel"
                  className="p-1 rounded-full text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-tactical-700 transition-colors"
                  aria-label="Close detail panel"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                {selectedFacility.tiger_count !== undefined && (
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Tigers</span>
                    <p className="font-semibold text-tiger-orange">{selectedFacility.tiger_count}</p>
                  </div>
                )}
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Status</span>
                  <p className="font-medium text-gray-900 dark:text-gray-100 capitalize">{selectedFacility.status}</p>
                </div>
                {selectedFacility.facility_type && (
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Type</span>
                    <p className="font-medium text-gray-900 dark:text-gray-100">{selectedFacility.facility_type}</p>
                  </div>
                )}
                {selectedFacility.country && (
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Country</span>
                    <p className="font-medium text-gray-900 dark:text-gray-100">{selectedFacility.country}</p>
                  </div>
                )}
              </div>

              <button
                type="button"
                onClick={() => navigate(`/facilities/${selectedFacility.id}`)}
                data-testid="view-facility-details"
                className="mt-4 w-full py-2 px-4 bg-gray-100 dark:bg-tactical-700 hover:bg-gray-200 dark:hover:bg-tactical-600 text-gray-900 dark:text-gray-100 font-medium rounded-lg transition-colors text-sm"
              >
                View Full Details
              </button>
            </Card>

            {/* Crawl History Timeline */}
            <CrawlHistoryTimeline
              events={crawlEvents}
              facilityId={selectedFacility.id}
              maxEvents={5}
              isLoading={isCrawlHistoryLoading}
              data-testid="crawl-history-timeline"
            />

            {/* Tiger Gallery */}
            <Card>
              <FacilityTigerGallery
                facilityId={selectedFacility.id}
                facilityName={selectedFacility.exhibitor_name || selectedFacility.name}
                images={facilityTigerImages}
                onTigerClick={handleTigerClick}
                viewMode="grid"
                data-testid="facility-tiger-gallery"
              />
            </Card>
          </div>
        )}
      </div>

      {/* Mobile Detail Panel (slides up from bottom) */}
      {selectedFacility && (
        <div
          className="lg:hidden fixed inset-x-0 bottom-0 z-50 bg-white dark:bg-tactical-900 border-t border-gray-200 dark:border-tactical-700 shadow-lg max-h-[70vh] overflow-y-auto rounded-t-2xl"
          data-testid="facility-detail-panel-mobile"
        >
          <div className="p-4">
            {/* Handle bar */}
            <div className="w-12 h-1 bg-gray-300 dark:bg-tactical-600 rounded-full mx-auto mb-4" />

            {/* Facility Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-start space-x-3">
                <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <BuildingOfficeIcon className="h-5 w-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {selectedFacility.exhibitor_name || selectedFacility.name}
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {selectedFacility.city && selectedFacility.state
                      ? `${selectedFacility.city}, ${selectedFacility.state}`
                      : selectedFacility.state || selectedFacility.city || 'Location unknown'}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={handleCloseDetail}
                data-testid="close-detail-panel-mobile"
                className="p-1 rounded-full text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-tactical-700 transition-colors"
                aria-label="Close detail panel"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm mb-4">
              {selectedFacility.tiger_count !== undefined && (
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Tigers</span>
                  <p className="font-semibold text-tiger-orange">{selectedFacility.tiger_count}</p>
                </div>
              )}
              <div>
                <span className="text-gray-500 dark:text-gray-400">Status</span>
                <p className="font-medium text-gray-900 dark:text-gray-100 capitalize">{selectedFacility.status}</p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => navigate(`/facilities/${selectedFacility.id}`)}
              data-testid="view-facility-details-mobile"
              className="w-full py-2 px-4 bg-tiger-orange hover:bg-tiger-orange-dark text-white font-medium rounded-lg transition-colors text-sm"
            >
              View Full Details
            </button>

            {/* Crawl History (collapsed) */}
            <div className="mt-6">
              <CrawlHistoryTimeline
                events={crawlEvents}
                facilityId={selectedFacility.id}
                maxEvents={3}
                isLoading={isCrawlHistoryLoading}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Facilities

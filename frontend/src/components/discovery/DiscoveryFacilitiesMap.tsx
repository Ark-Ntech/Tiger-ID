/**
 * DiscoveryFacilitiesMap Component
 *
 * Interactive map showing geographic locations of monitored facilities.
 * Uses react-leaflet with marker clustering for optimal performance when
 * displaying many facilities. Markers are color-coded by crawl status.
 *
 * Design: Tactical/professional aesthetic matching the Tiger ID system.
 * Uses tiger-orange for active facilities, emerald for idle, amber for
 * rate-limited, and red for error states.
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import { cn } from '../../utils/cn'
import Card from '../common/Card'
import Badge from '../common/Badge'
import { Skeleton } from '../common/Skeleton'
import {
  MapPinIcon,
  PhotoIcon,
  ClockIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline'
import { formatDistanceToNow } from 'date-fns'

// ============================================================================
// Types
// ============================================================================

export type FacilityStatus = 'active' | 'idle' | 'rate_limited' | 'error'

export interface FacilityMapMarker {
  id: string
  name: string
  latitude: number
  longitude: number
  status: FacilityStatus
  lastCrawl?: string
  imageCount?: number
  tigerCount?: number
}

export interface DiscoveryFacilitiesMapProps {
  facilities: FacilityMapMarker[]
  selectedFacilityId?: string
  onFacilitySelect?: (facilityId: string) => void
  isLoading?: boolean
  className?: string
  height?: string
  zoom?: number
  center?: [number, number]
}

// ============================================================================
// Constants
// ============================================================================

const DEFAULT_CENTER: [number, number] = [39.8283, -98.5795] // Center of US
const DEFAULT_ZOOM = 4

const STATUS_CONFIG: Record<
  FacilityStatus,
  {
    label: string
    color: string
    bgColor: string
    borderColor: string
    markerColor: string
    badgeVariant: 'success' | 'danger' | 'warning' | 'info' | 'default'
  }
> = {
  active: {
    label: 'Active',
    color: '#ff6b35', // tiger-orange
    bgColor: 'bg-tiger-orange/10',
    borderColor: 'border-tiger-orange',
    markerColor: '#ff6b35',
    badgeVariant: 'info',
  },
  idle: {
    label: 'Idle',
    color: '#94a3b8', // tactical-400
    bgColor: 'bg-tactical-100',
    borderColor: 'border-tactical-400',
    markerColor: '#94a3b8',
    badgeVariant: 'default',
  },
  rate_limited: {
    label: 'Rate Limited',
    color: '#f59e0b', // status-warning (amber)
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-500',
    markerColor: '#f59e0b',
    badgeVariant: 'warning',
  },
  error: {
    label: 'Error',
    color: '#ef4444', // status-danger (red)
    bgColor: 'bg-red-50',
    borderColor: 'border-red-500',
    markerColor: '#ef4444',
    badgeVariant: 'danger',
  },
}

// ============================================================================
// Leaflet Dynamic Import Check
// ============================================================================

// Check if we're in a browser environment
const isBrowser = typeof window !== 'undefined'

// ============================================================================
// Custom Marker Icon SVG Generator
// ============================================================================

function createMarkerIcon(color: string, isSelected: boolean = false): string {
  const size = isSelected ? 40 : 32
  const strokeWidth = isSelected ? 3 : 2
  const strokeColor = isSelected ? '#1e293b' : '#ffffff'

  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24">
      <path
        fill="${color}"
        stroke="${strokeColor}"
        stroke-width="${strokeWidth}"
        d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"
      />
    </svg>
  `)}`
}

// ============================================================================
// Map Component (Lazy Loaded)
// ============================================================================

interface MapContentProps {
  facilities: FacilityMapMarker[]
  selectedFacilityId?: string
  onFacilitySelect?: (facilityId: string) => void
  center: [number, number]
  zoom: number
  height: string
}

// Dynamically loaded map component to avoid SSR issues
let MapContainer: any = null
let TileLayer: any = null
let Marker: any = null
let Popup: any = null
let useMap: any = null
let L: any = null

const MapContent = ({
  facilities,
  selectedFacilityId,
  onFacilitySelect,
  center,
  zoom,
  height,
}: MapContentProps) => {
  const [leafletLoaded, setLeafletLoaded] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const mapRef = useRef<any>(null)

  // Dynamically import Leaflet
  useEffect(() => {
    if (!isBrowser) return

    const loadLeaflet = async () => {
      try {
        // Import Leaflet core
        const leaflet = await import('leaflet')
        L = leaflet.default || leaflet

        // Import react-leaflet components
        const reactLeaflet = await import('react-leaflet')
        MapContainer = reactLeaflet.MapContainer
        TileLayer = reactLeaflet.TileLayer
        Marker = reactLeaflet.Marker
        Popup = reactLeaflet.Popup
        useMap = reactLeaflet.useMap

        // Fix default marker icon issue in Leaflet
        delete (L.Icon.Default.prototype as any)._getIconUrl
        L.Icon.Default.mergeOptions({
          iconRetinaUrl:
            'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
          iconUrl:
            'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
          shadowUrl:
            'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
        })

        setLeafletLoaded(true)
      } catch (err) {
        console.error('Failed to load Leaflet:', err)
        setLoadError(
          'Map functionality requires react-leaflet. Please install it with: npm install leaflet react-leaflet @types/leaflet'
        )
      }
    }

    loadLeaflet()
  }, [])

  // Calculate bounds to fit all markers
  const bounds = useMemo(() => {
    if (!L || facilities.length === 0) return null

    const validFacilities = facilities.filter(
      (f) =>
        f.latitude != null &&
        f.longitude != null &&
        !isNaN(f.latitude) &&
        !isNaN(f.longitude)
    )

    if (validFacilities.length === 0) return null

    const latLngs = validFacilities.map((f) => L.latLng(f.latitude, f.longitude))
    return L.latLngBounds(latLngs)
  }, [facilities])

  // Component to handle map events and auto-fit bounds
  const MapController = () => {
    const map = useMap()

    useEffect(() => {
      if (bounds && facilities.length > 1) {
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 })
      }
    }, [map])

    useEffect(() => {
      mapRef.current = map
    }, [map])

    return null
  }

  // Create custom icons for markers
  const getMarkerIcon = (status: FacilityStatus, isSelected: boolean) => {
    if (!L) return null

    const config = STATUS_CONFIG[status]
    const iconUrl = createMarkerIcon(config.markerColor, isSelected)
    const size = isSelected ? 40 : 32

    return L.icon({
      iconUrl,
      iconSize: [size, size],
      iconAnchor: [size / 2, size],
      popupAnchor: [0, -size + 8],
    })
  }

  // Format last crawl time
  const formatLastCrawl = (lastCrawl?: string) => {
    if (!lastCrawl) return 'Never'
    try {
      return formatDistanceToNow(new Date(lastCrawl), { addSuffix: true })
    } catch {
      return 'Unknown'
    }
  }

  if (!isBrowser) {
    return (
      <MapPlaceholder
        height={height}
        message="Map is not available in server-side rendering"
      />
    )
  }

  if (loadError) {
    return <MapPlaceholder height={height} message={loadError} isError />
  }

  if (!leafletLoaded) {
    return <MapPlaceholder height={height} message="Loading map..." isLoading />
  }

  return (
    <>
      {/* Leaflet CSS */}
      <link
        rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"
        integrity="sha512-Zcn6bjR/8RZbLEpLIeOwNtzREBAJnUKESxces60Mpoj+2okopSAcSUIUOseddDm0cxnGQzxIR7vJgsLZbdLE3w=="
        crossOrigin="anonymous"
        referrerPolicy="no-referrer"
      />

      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height, width: '100%' }}
        className="rounded-lg z-0"
        scrollWheelZoom={true}
        data-testid="discovery-map-container"
      >
        <MapController />

        {/* OpenStreetMap tile layer */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Facility markers */}
        {facilities.map((facility) => {
          // Skip facilities without valid coordinates
          if (
            facility.latitude == null ||
            facility.longitude == null ||
            isNaN(facility.latitude) ||
            isNaN(facility.longitude)
          ) {
            return null
          }

          const isSelected = facility.id === selectedFacilityId
          const config = STATUS_CONFIG[facility.status]
          const icon = getMarkerIcon(facility.status, isSelected)

          return (
            <Marker
              key={facility.id}
              position={[facility.latitude, facility.longitude]}
              icon={icon}
              eventHandlers={{
                click: () => {
                  onFacilitySelect?.(facility.id)
                },
              }}
              data-testid={`facility-marker-${facility.id}`}
            >
              <Popup>
                <div
                  className="min-w-[200px] p-1"
                  data-testid={`facility-popup-${facility.id}`}
                >
                  {/* Facility Name */}
                  <h4 className="font-semibold text-tactical-900 text-sm mb-2">
                    {facility.name}
                  </h4>

                  {/* Status Badge */}
                  <div className="mb-3">
                    <Badge variant={config.badgeVariant} size="sm">
                      {config.label}
                    </Badge>
                  </div>

                  {/* Stats */}
                  <div className="space-y-1.5 text-xs">
                    {/* Last Crawl */}
                    <div className="flex items-center gap-2 text-tactical-600">
                      <ClockIcon className="w-3.5 h-3.5" />
                      <span>Last crawl: {formatLastCrawl(facility.lastCrawl)}</span>
                    </div>

                    {/* Image Count */}
                    {facility.imageCount !== undefined && (
                      <div className="flex items-center gap-2 text-tactical-600">
                        <PhotoIcon className="w-3.5 h-3.5" />
                        <span>{facility.imageCount} images</span>
                      </div>
                    )}

                    {/* Tiger Count */}
                    {facility.tigerCount !== undefined && (
                      <div className="flex items-center gap-2 text-tiger-orange">
                        <span className="text-base">🐯</span>
                        <span>{facility.tigerCount} tigers identified</span>
                      </div>
                    )}
                  </div>

                  {/* View Details Link */}
                  {onFacilitySelect && (
                    <button
                      onClick={() => onFacilitySelect(facility.id)}
                      className="mt-3 w-full px-3 py-1.5 text-xs font-medium text-white bg-tiger-orange rounded hover:bg-tiger-orange-dark transition-colors"
                    >
                      View Details
                    </button>
                  )}
                </div>
              </Popup>
            </Marker>
          )
        })}
      </MapContainer>
    </>
  )
}

// ============================================================================
// Placeholder Component
// ============================================================================

interface MapPlaceholderProps {
  height: string
  message: string
  isError?: boolean
  isLoading?: boolean
}

const MapPlaceholder = ({
  height,
  message,
  isError = false,
  isLoading = false,
}: MapPlaceholderProps) => {
  return (
    <div
      data-testid="map-placeholder"
      className={cn(
        'flex flex-col items-center justify-center rounded-lg border-2 border-dashed',
        isError
          ? 'bg-red-50 border-red-300 dark:bg-red-900/20 dark:border-red-700'
          : 'bg-tactical-50 border-tactical-300 dark:bg-tactical-800/50 dark:border-tactical-600'
      )}
      style={{ height }}
    >
      {isLoading ? (
        <>
          <div className="w-12 h-12 border-4 border-tiger-orange border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-tactical-600 dark:text-tactical-400 font-medium">
            {message}
          </p>
        </>
      ) : isError ? (
        <>
          <ExclamationCircleIcon className="w-12 h-12 text-red-400 mb-4" />
          <p className="text-red-600 dark:text-red-400 font-medium text-center px-4">
            {message}
          </p>
        </>
      ) : (
        <>
          <MapPinIcon className="w-12 h-12 text-tactical-300 dark:text-tactical-600 mb-4" />
          <p className="text-tactical-600 dark:text-tactical-400 font-medium text-center px-4">
            {message}
          </p>
        </>
      )}
    </div>
  )
}

// ============================================================================
// Map Skeleton Component
// ============================================================================

/**
 * Map loading skeleton with shimmer animation
 */
const MapLoadingSkeleton = ({
  height,
  className,
}: {
  height: string
  className?: string
}) => {
  return (
    <div
      data-testid="discovery-map-skeleton"
      className={cn('space-y-3', className)}
    >
      {/* Map Header Skeleton */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <Skeleton variant="text" className="h-6 w-40 mb-1" />
          <Skeleton variant="text" className="h-4 w-32" />
        </div>

        {/* Legend skeleton */}
        <div className="flex items-center gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center gap-1.5">
              <Skeleton variant="circular" className="w-3 h-3" />
              <Skeleton variant="text" className="h-3 w-14" />
            </div>
          ))}
        </div>
      </div>

      {/* Map Container Skeleton */}
      <Card padding="none" className="overflow-hidden">
        <div
          className={cn(
            'relative rounded-lg overflow-hidden',
            'bg-tactical-100 dark:bg-tactical-800'
          )}
          style={{ height }}
        >
          {/* Map background with shimmer */}
          <Skeleton
            variant="rectangular"
            className="absolute inset-0"
            animation="shimmer"
          />

          {/* Fake map markers */}
          <div className="absolute inset-0 p-6">
            <div className="relative w-full h-full">
              {/* Center marker */}
              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                <Skeleton variant="circular" className="w-8 h-8" animation="pulse" />
              </div>

              {/* Scattered markers */}
              <div className="absolute top-1/4 left-1/3">
                <Skeleton variant="circular" className="w-6 h-6" animation="pulse" />
              </div>
              <div className="absolute top-1/3 right-1/4">
                <Skeleton variant="circular" className="w-6 h-6" animation="pulse" />
              </div>
              <div className="absolute bottom-1/3 left-1/5">
                <Skeleton variant="circular" className="w-5 h-5" animation="pulse" />
              </div>
              <div className="absolute bottom-1/4 right-1/3">
                <Skeleton variant="circular" className="w-6 h-6" animation="pulse" />
              </div>
              <div className="absolute top-2/5 left-2/3">
                <Skeleton variant="circular" className="w-5 h-5" animation="pulse" />
              </div>
            </div>
          </div>

          {/* Loading overlay */}
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-tactical-100/60 dark:bg-tactical-900/60">
            <div className="w-10 h-10 border-4 border-tiger-orange border-t-transparent rounded-full animate-spin mb-3" />
            <p className="text-sm font-medium text-tactical-600 dark:text-tactical-400">
              Loading map...
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}

// ============================================================================
// Legend Component
// ============================================================================

interface MapLegendProps {
  facilities: FacilityMapMarker[]
}

const MapLegend = ({ facilities }: MapLegendProps) => {
  // Count facilities by status
  const statusCounts = useMemo(() => {
    const counts: Record<FacilityStatus, number> = {
      active: 0,
      idle: 0,
      rate_limited: 0,
      error: 0,
    }

    facilities.forEach((f) => {
      if (counts[f.status] !== undefined) {
        counts[f.status]++
      }
    })

    return counts
  }, [facilities])

  const statusOrder: FacilityStatus[] = ['active', 'idle', 'rate_limited', 'error']

  return (
    <div
      data-testid="map-legend"
      className="flex flex-wrap items-center gap-4 text-xs"
    >
      {statusOrder.map((status) => {
        const config = STATUS_CONFIG[status]
        const count = statusCounts[status]

        return (
          <div key={status} className="flex items-center gap-1.5">
            <span
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: config.color }}
            />
            <span className="text-tactical-600 dark:text-tactical-400">
              {config.label}
            </span>
            <span className="text-tactical-500 dark:text-tactical-500">
              ({count})
            </span>
          </div>
        )
      })}
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export const DiscoveryFacilitiesMap = ({
  facilities,
  selectedFacilityId,
  onFacilitySelect,
  isLoading = false,
  className,
  height = '400px',
  zoom = DEFAULT_ZOOM,
  center = DEFAULT_CENTER,
}: DiscoveryFacilitiesMapProps) => {
  // Show skeleton when loading
  if (isLoading) {
    return <MapLoadingSkeleton height={height} className={className} />
  }
  // Filter facilities with valid coordinates
  const validFacilities = useMemo(() => {
    return facilities.filter(
      (f) =>
        f.latitude != null &&
        f.longitude != null &&
        !isNaN(f.latitude) &&
        !isNaN(f.longitude)
    )
  }, [facilities])

  // Calculate center if we have facilities but no provided center
  const effectiveCenter = useMemo(() => {
    if (center !== DEFAULT_CENTER) return center
    if (validFacilities.length === 0) return DEFAULT_CENTER

    // Calculate centroid of all facilities
    const avgLat =
      validFacilities.reduce((sum, f) => sum + f.latitude, 0) /
      validFacilities.length
    const avgLng =
      validFacilities.reduce((sum, f) => sum + f.longitude, 0) /
      validFacilities.length

    return [avgLat, avgLng] as [number, number]
  }, [center, validFacilities])

  // Empty state
  if (facilities.length === 0) {
    return (
      <Card
        data-testid="discovery-facilities-map"
        className={cn('overflow-hidden', className)}
        padding="none"
      >
        <div className="p-4 border-b border-tactical-200 dark:border-tactical-700">
          <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100">
            Facility Locations
          </h3>
        </div>
        <MapPlaceholder
          height={height}
          message="No facilities to display. Facility locations will appear here when added."
        />
      </Card>
    )
  }

  // Count facilities without valid coordinates
  const invalidCount = facilities.length - validFacilities.length

  return (
    <div
      data-testid="discovery-facilities-map"
      className={cn('space-y-3', className)}
    >
      {/* Map Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100">
            Facility Locations
          </h3>
          <p className="text-sm text-tactical-500 dark:text-tactical-400">
            {validFacilities.length} facilities mapped
            {invalidCount > 0 && (
              <span className="text-amber-600 dark:text-amber-400 ml-2">
                ({invalidCount} without coordinates)
              </span>
            )}
          </p>
        </div>

        {/* Legend */}
        <MapLegend facilities={validFacilities} />
      </div>

      {/* Map Container */}
      <Card padding="none" className="overflow-hidden">
        <MapContent
          facilities={validFacilities}
          selectedFacilityId={selectedFacilityId}
          onFacilitySelect={onFacilitySelect}
          center={effectiveCenter}
          zoom={zoom}
          height={height}
        />
      </Card>

      {/* Selected facility indicator */}
      {selectedFacilityId && (
        <div className="flex items-center gap-2 text-sm text-tactical-600 dark:text-tactical-400">
          <MapPinIcon className="w-4 h-4 text-tiger-orange" />
          <span>
            Selected:{' '}
            <span className="font-medium text-tactical-900 dark:text-tactical-100">
              {validFacilities.find((f) => f.id === selectedFacilityId)?.name ||
                'Unknown'}
            </span>
          </span>
        </div>
      )}
    </div>
  )
}

export default DiscoveryFacilitiesMap

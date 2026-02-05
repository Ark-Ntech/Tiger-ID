import { useMemo, useState, useCallback } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { cn } from '../../utils/cn'
import Badge from '../common/Badge'
import Card from '../common/Card'
import { format } from 'date-fns'

// Types
export interface Facility {
  id: string
  name: string
  type: 'zoo' | 'sanctuary' | 'rescue' | 'breeding' | 'other'
  latitude?: number
  longitude?: number
  country?: string
  region?: string
  tigerCount?: number
  lastDiscovery?: string
  discoveryStatus: 'active' | 'inactive' | 'pending'
}

export interface FacilityMapViewProps {
  facilities: Facility[]
  selectedFacilityId?: string
  onFacilitySelect?: (facility: Facility) => void
  onAddFacility?: (coords: { lat: number; lng: number }) => void
  className?: string
}

// Facility type icons - SVG path data
const facilityTypeIcons: Record<Facility['type'], string> = {
  zoo: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z',
  sanctuary: 'M12 3L2 12h3v8h6v-6h2v6h6v-8h3L12 3zm0 8.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 6.5 12 6.5s2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z',
  rescue: 'M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 3c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6zm7 13H5v-.23c0-.62.28-1.2.76-1.58C7.47 15.82 9.64 15 12 15s4.53.82 6.24 2.19c.48.38.76.97.76 1.58V19z',
  breeding: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z',
  other: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z',
}

// Facility type labels
const facilityTypeLabels: Record<Facility['type'], string> = {
  zoo: 'Zoo',
  sanctuary: 'Sanctuary',
  rescue: 'Rescue Center',
  breeding: 'Breeding Facility',
  other: 'Other',
}

// Colors by facility type
const facilityTypeColors: Record<Facility['type'], string> = {
  zoo: '#3b82f6', // blue
  sanctuary: '#10b981', // green
  rescue: '#f59e0b', // amber
  breeding: '#8b5cf6', // purple
  other: '#6b7280', // gray
}

// Colors by discovery status
const statusColors: Record<Facility['discoveryStatus'], string> = {
  active: '#10b981', // green
  inactive: '#6b7280', // gray
  pending: '#f59e0b', // amber
}

// Status badge variants mapping
const statusVariants: Record<Facility['discoveryStatus'], 'success' | 'default' | 'warning'> = {
  active: 'success',
  inactive: 'default',
  pending: 'warning',
}

// Create custom marker icon
const createFacilityIcon = (
  type: Facility['type'],
  status: Facility['discoveryStatus'],
  isSelected: boolean
) => {
  const typeColor = facilityTypeColors[type]
  const statusColor = statusColors[status]
  const size = isSelected ? 40 : 32
  const borderWidth = isSelected ? 4 : 3

  return L.divIcon({
    className: 'custom-facility-marker',
    html: `
      <div style="
        position: relative;
        width: ${size}px;
        height: ${size}px;
      ">
        <div style="
          position: absolute;
          top: 0;
          left: 0;
          width: ${size}px;
          height: ${size}px;
          background-color: ${typeColor};
          border: ${borderWidth}px solid ${statusColor};
          border-radius: 50% 50% 50% 0;
          transform: rotate(-45deg);
          box-shadow: 0 3px 10px rgba(0,0,0,0.3);
          ${isSelected ? 'animation: pulse 1.5s ease-in-out infinite;' : ''}
        ">
        </div>
        <div style="
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: ${size * 0.5}px;
          height: ${size * 0.5}px;
        ">
          <svg viewBox="0 0 24 24" fill="white" style="width: 100%; height: 100%;">
            <path d="${facilityTypeIcons[type]}"/>
          </svg>
        </div>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
    popupAnchor: [0, -size],
  })
}

// Map click handler component
interface MapClickHandlerProps {
  onMapClick?: (coords: { lat: number; lng: number }) => void
}

const MapClickHandler = ({ onMapClick }: MapClickHandlerProps) => {
  useMapEvents({
    click: (e) => {
      if (onMapClick) {
        onMapClick({ lat: e.latlng.lat, lng: e.latlng.lng })
      }
    },
  })
  return null
}

// Legend component
interface LegendProps {
  showTypes?: boolean
  showStatuses?: boolean
}

const Legend = ({ showTypes = true, showStatuses = true }: LegendProps) => {
  return (
    <div
      data-testid="facility-map-legend"
      className={cn(
        'absolute bottom-4 left-4 z-[1000]',
        'bg-white dark:bg-tactical-800 rounded-lg shadow-lg',
        'border border-tactical-200 dark:border-tactical-700',
        'p-4 max-w-xs'
      )}
    >
      {showTypes && (
        <div className="mb-4">
          <h4 className="text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wider mb-2">
            Facility Types
          </h4>
          <div className="space-y-1.5">
            {(Object.keys(facilityTypeColors) as Facility['type'][]).map((type) => (
              <div key={type} className="flex items-center gap-2">
                <div
                  className="w-4 h-4 rounded-full flex-shrink-0"
                  style={{ backgroundColor: facilityTypeColors[type] }}
                />
                <span className="text-sm text-tactical-700 dark:text-tactical-300">
                  {facilityTypeLabels[type]}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {showStatuses && (
        <div>
          <h4 className="text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wider mb-2">
            Discovery Status
          </h4>
          <div className="space-y-1.5">
            {(Object.keys(statusColors) as Facility['discoveryStatus'][]).map((status) => (
              <div key={status} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full border-2 flex-shrink-0"
                  style={{ borderColor: statusColors[status], backgroundColor: 'transparent' }}
                />
                <span className="text-sm text-tactical-700 dark:text-tactical-300 capitalize">
                  {status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Facility detail panel component
interface FacilityDetailPanelProps {
  facility: Facility
  onClose: () => void
}

const FacilityDetailPanel = ({ facility, onClose }: FacilityDetailPanelProps) => {
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'Never'
    try {
      return format(new Date(dateStr), 'MMM d, yyyy')
    } catch {
      return dateStr
    }
  }

  return (
    <div
      data-testid="facility-detail-panel"
      className={cn(
        'absolute top-4 right-4 z-[1000]',
        'w-80 max-w-[calc(100%-2rem)]',
        'bg-white dark:bg-tactical-800 rounded-lg shadow-xl',
        'border border-tactical-200 dark:border-tactical-700',
        'overflow-hidden'
      )}
    >
      {/* Header */}
      <div
        className="px-4 py-3 flex items-start justify-between"
        style={{ backgroundColor: facilityTypeColors[facility.type] + '20' }}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <div
              className="w-3 h-3 rounded-full flex-shrink-0"
              style={{ backgroundColor: facilityTypeColors[facility.type] }}
            />
            <span className="text-xs font-medium text-tactical-600 dark:text-tactical-400 uppercase">
              {facilityTypeLabels[facility.type]}
            </span>
          </div>
          <h3 className="font-semibold text-tactical-900 dark:text-tactical-100 truncate">
            {facility.name}
          </h3>
        </div>
        <button
          data-testid="facility-detail-close"
          onClick={onClose}
          className={cn(
            'p-1 rounded-full flex-shrink-0 ml-2',
            'text-tactical-500 hover:text-tactical-700',
            'dark:text-tactical-400 dark:hover:text-tactical-200',
            'hover:bg-tactical-200/50 dark:hover:bg-tactical-700/50',
            'transition-colors'
          )}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="px-4 py-3 space-y-3">
        {/* Location */}
        {(facility.country || facility.region) && (
          <div className="flex items-start gap-2">
            <svg className="w-4 h-4 text-tactical-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span className="text-sm text-tactical-700 dark:text-tactical-300">
              {[facility.region, facility.country].filter(Boolean).join(', ')}
            </span>
          </div>
        )}

        {/* Coordinates */}
        {facility.latitude && facility.longitude && (
          <div className="flex items-start gap-2">
            <svg className="w-4 h-4 text-tactical-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
            <span className="text-sm text-tactical-600 dark:text-tactical-400 font-mono">
              {facility.latitude.toFixed(4)}, {facility.longitude.toFixed(4)}
            </span>
          </div>
        )}

        {/* Tiger count */}
        {facility.tigerCount !== undefined && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-tactical-600 dark:text-tactical-400">Tigers</span>
            <span className="text-lg font-semibold text-tiger-orange">{facility.tigerCount}</span>
          </div>
        )}

        {/* Discovery status */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-tactical-600 dark:text-tactical-400">Discovery Status</span>
          <Badge variant={statusVariants[facility.discoveryStatus]} size="sm">
            {facility.discoveryStatus}
          </Badge>
        </div>

        {/* Last discovery */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-tactical-600 dark:text-tactical-400">Last Discovery</span>
          <span className="text-sm text-tactical-700 dark:text-tactical-300">
            {formatDate(facility.lastDiscovery)}
          </span>
        </div>
      </div>
    </div>
  )
}

// Main component
export const FacilityMapView = ({
  facilities,
  selectedFacilityId,
  onFacilitySelect,
  onAddFacility,
  className,
}: FacilityMapViewProps) => {
  const [selectedFacility, setSelectedFacility] = useState<Facility | null>(null)

  // Filter facilities with valid coordinates
  const mappableFacilities = useMemo(() => {
    return facilities.filter(
      (f) => f.latitude !== undefined && f.longitude !== undefined
    )
  }, [facilities])

  // Calculate map center
  const mapCenter = useMemo<[number, number]>(() => {
    if (mappableFacilities.length === 0) {
      return [20, 0] // Default world center
    }

    // If a facility is selected, center on it
    if (selectedFacilityId) {
      const selected = mappableFacilities.find((f) => f.id === selectedFacilityId)
      if (selected && selected.latitude && selected.longitude) {
        return [selected.latitude, selected.longitude]
      }
    }

    // Otherwise, calculate average center
    const avgLat =
      mappableFacilities.reduce((sum, f) => sum + (f.latitude || 0), 0) / mappableFacilities.length
    const avgLng =
      mappableFacilities.reduce((sum, f) => sum + (f.longitude || 0), 0) / mappableFacilities.length

    return [avgLat, avgLng]
  }, [mappableFacilities, selectedFacilityId])

  // Calculate zoom level
  const mapZoom = useMemo(() => {
    if (mappableFacilities.length === 0) return 2
    if (mappableFacilities.length === 1) return 8
    if (selectedFacilityId) return 10

    // Calculate bounds
    const lats = mappableFacilities.map((f) => f.latitude || 0)
    const lngs = mappableFacilities.map((f) => f.longitude || 0)
    const latRange = Math.max(...lats) - Math.min(...lats)
    const lngRange = Math.max(...lngs) - Math.min(...lngs)
    const maxRange = Math.max(latRange, lngRange)

    if (maxRange > 100) return 2
    if (maxRange > 50) return 3
    if (maxRange > 20) return 4
    if (maxRange > 10) return 5
    if (maxRange > 5) return 6
    return 8
  }, [mappableFacilities, selectedFacilityId])

  // Handle facility click
  const handleFacilityClick = useCallback(
    (facility: Facility) => {
      setSelectedFacility(facility)
      onFacilitySelect?.(facility)
    },
    [onFacilitySelect]
  )

  // Handle panel close
  const handlePanelClose = useCallback(() => {
    setSelectedFacility(null)
  }, [])

  // Handle map click for adding facility
  const handleMapClick = useCallback(
    (coords: { lat: number; lng: number }) => {
      if (onAddFacility) {
        onAddFacility(coords)
      }
    },
    [onAddFacility]
  )

  // Empty state
  if (mappableFacilities.length === 0 && !onAddFacility) {
    return (
      <Card
        data-testid="facility-map-empty"
        className={cn('flex flex-col items-center justify-center py-12', className)}
      >
        <svg
          className="w-16 h-16 text-tactical-400 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
          />
        </svg>
        <p className="text-tactical-600 dark:text-tactical-400 text-center">
          No facilities with location data available.
        </p>
        <p className="text-sm text-tactical-500 dark:text-tactical-500 text-center mt-1">
          Facilities need latitude and longitude to appear on the map.
        </p>
      </Card>
    )
  }

  return (
    <div
      data-testid="facility-map-view"
      className={cn('relative rounded-xl overflow-hidden', className)}
    >
      {/* Add custom marker animation styles */}
      <style>
        {`
          @keyframes pulse {
            0%, 100% { transform: rotate(-45deg) scale(1); }
            50% { transform: rotate(-45deg) scale(1.1); }
          }
        `}
      </style>

      {/* Map container */}
      <div className="h-[500px] w-full">
        <MapContainer
          center={mapCenter}
          zoom={mapZoom}
          scrollWheelZoom={true}
          className="h-full w-full"
          data-testid="facility-map-container"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Map click handler for adding facilities */}
          {onAddFacility && <MapClickHandler onMapClick={handleMapClick} />}

          {/* Facility markers */}
          {mappableFacilities.map((facility) => {
            const isSelected = facility.id === selectedFacilityId || facility.id === selectedFacility?.id

            return (
              <Marker
                key={facility.id}
                position={[facility.latitude!, facility.longitude!]}
                icon={createFacilityIcon(facility.type, facility.discoveryStatus, isSelected)}
                eventHandlers={{
                  click: () => handleFacilityClick(facility),
                }}
                data-testid={`facility-marker-${facility.id}`}
              >
                <Popup>
                  <div className="p-2 min-w-[200px]" data-testid={`facility-popup-${facility.id}`}>
                    <div className="flex items-center gap-2 mb-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: facilityTypeColors[facility.type] }}
                      />
                      <span className="text-xs font-medium text-gray-500 uppercase">
                        {facilityTypeLabels[facility.type]}
                      </span>
                    </div>
                    <h4 className="font-semibold text-gray-900 mb-2">{facility.name}</h4>
                    {(facility.region || facility.country) && (
                      <p className="text-sm text-gray-600 mb-2">
                        {[facility.region, facility.country].filter(Boolean).join(', ')}
                      </p>
                    )}
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Status:</span>
                      <Badge variant={statusVariants[facility.discoveryStatus]} size="xs">
                        {facility.discoveryStatus}
                      </Badge>
                    </div>
                    {facility.tigerCount !== undefined && (
                      <div className="flex items-center justify-between text-sm mt-1">
                        <span className="text-gray-500">Tigers:</span>
                        <span className="font-medium text-orange-600">{facility.tigerCount}</span>
                      </div>
                    )}
                  </div>
                </Popup>
              </Marker>
            )
          })}
        </MapContainer>
      </div>

      {/* Legend */}
      <Legend showTypes showStatuses />

      {/* Selected facility detail panel */}
      {selectedFacility && (
        <FacilityDetailPanel facility={selectedFacility} onClose={handlePanelClose} />
      )}

      {/* Add facility hint */}
      {onAddFacility && (
        <div
          data-testid="facility-map-add-hint"
          className={cn(
            'absolute top-4 left-1/2 -translate-x-1/2 z-[1000]',
            'px-3 py-1.5 rounded-full',
            'bg-tactical-900/80 text-white text-sm',
            'pointer-events-none'
          )}
        >
          Click on map to add a new facility
        </div>
      )}

      {/* Stats bar */}
      <div
        data-testid="facility-map-stats"
        className={cn(
          'absolute bottom-4 right-4 z-[1000]',
          'bg-white/90 dark:bg-tactical-800/90 backdrop-blur-sm',
          'rounded-lg shadow-md px-4 py-2',
          'border border-tactical-200 dark:border-tactical-700'
        )}
      >
        <div className="flex items-center gap-4 text-sm">
          <div className="text-tactical-600 dark:text-tactical-400">
            <span className="font-semibold text-tactical-900 dark:text-tactical-100">
              {mappableFacilities.length}
            </span>{' '}
            facilities on map
          </div>
          {facilities.length > mappableFacilities.length && (
            <div className="text-amber-600 dark:text-amber-400">
              {facilities.length - mappableFacilities.length} missing coordinates
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default FacilityMapView

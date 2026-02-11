import React, { useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { TimelineSighting } from '../../../types/investigation2'

const sourceColors: Record<string, string> = {
  database: '#10b981',
  web_search: '#3b82f6',
  investigation: '#8b5cf6',
  discovery: '#f97316',
}

/**
 * Create a numbered, color-coded marker icon.
 */
function createNumberedIcon(color: string, number: number) {
  return L.divIcon({
    className: 'custom-timeline-marker',
    html: `
      <div style="
        background-color: ${color};
        width: 28px;
        height: 28px;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        border: 2px solid white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <span style="
          transform: rotate(45deg);
          color: white;
          font-size: 11px;
          font-weight: 700;
          line-height: 1;
        ">${number}</span>
      </div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 28],
  })
}

interface TimelineMapProps {
  sightings: TimelineSighting[]
}

/**
 * Validate and fix coordinate values. Detects swapped lat/lon and rejects
 * out-of-range values. Returns corrected coordinates or null.
 */
function validateCoordinates(
  coords: { lat: number; lon: number } | null
): { lat: number; lon: number } | null {
  if (!coords) return null

  let { lat, lon } = coords

  // Reject non-finite values
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null

  // Reject (0, 0) - almost certainly invalid for facility data
  if (lat === 0 && lon === 0) return null

  // Detect swapped coordinates: if lat is outside [-90, 90] but would be
  // a valid longitude, and lon is within [-90, 90], swap them
  if (Math.abs(lat) > 90 && Math.abs(lon) <= 90 && Math.abs(lat) <= 180) {
    ;[lat, lon] = [lon, lat]
  }

  // Final range validation
  if (Math.abs(lat) > 90 || Math.abs(lon) > 180) return null

  return { lat, lon }
}

export const TimelineMap: React.FC<TimelineMapProps> = ({ sightings }) => {
  // Filter to sightings with valid coordinates (validates and fixes swapped lat/lon)
  const geoSightings = useMemo(
    () =>
      sightings
        .map((s) => {
          const validCoords = validateCoordinates(s.coordinates ?? null)
          return { ...s, coordinates: validCoords }
        })
        .filter((s) => s.coordinates != null)
        .map((s, idx) => ({ ...s, _index: idx + 1 })),
    [sightings]
  )

  // Calculate center
  const center = useMemo(() => {
    if (geoSightings.length === 0) return [39.8, -98.5] as [number, number]

    const latSum = geoSightings.reduce((sum, s) => sum + s.coordinates!.lat, 0)
    const lonSum = geoSightings.reduce((sum, s) => sum + s.coordinates!.lon, 0)

    return [latSum / geoSightings.length, lonSum / geoSightings.length] as [number, number]
  }, [geoSightings])

  // Calculate zoom level
  const zoom = useMemo(() => {
    if (geoSightings.length === 0) return 4
    if (geoSightings.length === 1) return 10

    const lats = geoSightings.map((s) => s.coordinates!.lat)
    const lons = geoSightings.map((s) => s.coordinates!.lon)
    const latRange = Math.max(...lats) - Math.min(...lats)
    const lonRange = Math.max(...lons) - Math.min(...lons)
    const maxRange = Math.max(latRange, lonRange)

    if (maxRange > 50) return 4
    if (maxRange > 10) return 6
    if (maxRange > 5) return 8
    return 10
  }, [geoSightings])

  // Polyline connecting markers chronologically
  const polylinePositions = useMemo(
    () =>
      geoSightings.map((s) => [s.coordinates!.lat, s.coordinates!.lon] as [number, number]),
    [geoSightings]
  )

  if (geoSightings.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No location data available for timeline map</p>
      </div>
    )
  }

  return (
    <div className="w-full h-[400px] rounded-lg overflow-hidden">
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom={true}
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Chronological connection line */}
        {polylinePositions.length >= 2 && (
          <Polyline
            positions={polylinePositions}
            pathOptions={{
              color: '#6b7280',
              weight: 2,
              dashArray: '6, 4',
              opacity: 0.6,
            }}
          />
        )}

        {/* Numbered markers */}
        {geoSightings.map((sighting) => {
          const color = sourceColors[sighting.source] || sourceColors.database
          return (
            <Marker
              key={sighting.id}
              position={[sighting.coordinates!.lat, sighting.coordinates!.lon]}
              icon={createNumberedIcon(color, sighting._index)}
            >
              <Popup>
                <div className="p-2 min-w-[180px]">
                  <h4 className="font-semibold text-sm mb-1">
                    {sighting.facility_name || 'Unknown Facility'}
                  </h4>
                  {sighting.location && (
                    <p className="text-xs text-gray-600 mb-1">{sighting.location}</p>
                  )}
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className="inline-block px-1.5 py-0.5 text-xs font-medium rounded"
                      style={{
                        backgroundColor: `${color}20`,
                        color: color,
                      }}
                    >
                      {sighting.source.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-gray-500">{sighting.confidence}</span>
                  </div>
                  {sighting.date && (
                    <p className="text-xs text-gray-400">
                      {new Date(sighting.date).toLocaleDateString()}
                    </p>
                  )}
                  <p className="text-xs text-gray-400 mt-1">
                    {sighting.coordinates!.lat.toFixed(4)}, {sighting.coordinates!.lon.toFixed(4)}
                  </p>
                </div>
              </Popup>
            </Marker>
          )
        })}
      </MapContainer>
    </div>
  )
}

export default TimelineMap

import { useMemo } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import Card from '../common/Card'
import LoadingSpinner from '../common/LoadingSpinner'
import Badge from '../common/Badge'
import L from 'leaflet'

// Fix for default marker icons in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

interface GeographicMapProps {
  facilities?: Array<{
    id: string
    name: string
    state?: string
    city?: string
    latitude?: number
    longitude?: number
    tiger_count?: number
    verified?: boolean
  }>
  investigations?: Array<{
    id: string
    title: string
    location?: string
    latitude?: number
    longitude?: number
  }>
  isLoading?: boolean
}

// State coordinates (approximate centers for US states)
const STATE_COORDINATES: Record<string, [number, number]> = {
  'AL': [32.806671, -86.791130],
  'AK': [61.370716, -152.404419],
  'AZ': [33.729759, -111.431221],
  'AR': [34.969704, -92.373123],
  'CA': [36.116203, -119.681564],
  'CO': [39.059811, -105.311104],
  'CT': [41.767, -72.677],
  'DE': [39.318523, -75.507141],
  'FL': [27.766279, -81.686783],
  'GA': [33.040619, -83.643074],
  'HI': [21.094318, -157.498337],
  'ID': [44.240459, -114.478828],
  'IL': [40.349457, -88.986137],
  'IN': [39.849426, -86.258278],
  'IA': [42.011539, -93.210526],
  'KS': [38.526600, -96.726486],
  'KY': [37.668140, -84.670067],
  'LA': [31.169546, -91.867805],
  'ME': [44.323535, -69.765261],
  'MD': [39.063946, -76.802101],
  'MA': [42.2352, -71.5312],
  'MI': [43.326618, -84.536095],
  'MN': [45.694454, -93.900192],
  'MS': [32.741646, -89.678696],
  'MO': [38.572954, -92.189283],
  'MT': [47.052952, -110.454353],
  'NE': [41.125370, -98.268082],
  'NV': [38.313515, -117.055374],
  'NH': [43.452492, -71.563896],
  'NJ': [40.298904, -74.521011],
  'NM': [34.840515, -106.248482],
  'NY': [42.165726, -74.948051],
  'NC': [35.630066, -79.806419],
  'ND': [47.528912, -99.784012],
  'OH': [40.388783, -82.764915],
  'OK': [35.565342, -96.928917],
  'OR': [44.572021, -122.070938],
  'PA': [40.590752, -77.209755],
  'RI': [41.680893, -71.51178],
  'SC': [33.856892, -80.945007],
  'SD': [44.299782, -99.438828],
  'TN': [35.747845, -86.692345],
  'TX': [31.106462, -97.563461],
  'UT': [40.150032, -111.862434],
  'VT': [44.045876, -72.710686],
  'VA': [37.769337, -78.169968],
  'WA': [47.400902, -121.490494],
  'WV': [38.349497, -81.633294],
  'WI': [44.268543, -89.616508],
  'WY': [42.755966, -107.302490],
}

const GeographicMap = ({ facilities = [], investigations = [], isLoading }: GeographicMapProps) => {
  // Calculate map center from data or default to USA center
  const mapCenter: [number, number] = useMemo(() => {
    const allCoords: Array<[number, number]> = []

    facilities.forEach((facility) => {
      if (facility.latitude && facility.longitude) {
        allCoords.push([facility.latitude, facility.longitude])
      } else if (facility.state && STATE_COORDINATES[facility.state]) {
        allCoords.push(STATE_COORDINATES[facility.state])
      }
    })

    investigations.forEach((inv) => {
      if (inv.latitude && inv.longitude) {
        allCoords.push([inv.latitude, inv.longitude])
      }
    })

    if (allCoords.length === 0) {
      return [39.8283, -98.5795] // USA center
    }

    const avgLat = allCoords.reduce((sum, [lat]) => sum + lat, 0) / allCoords.length
    const avgLng = allCoords.reduce((sum, [, lng]) => sum + lng, 0) / allCoords.length

    return [avgLat, avgLng]
  }, [facilities, investigations])

  const mapMarkers = useMemo(() => {
    const markers: Array<{
      id: string
      type: 'facility' | 'investigation'
      name: string
      position: [number, number]
      data: any
    }> = []

    facilities.forEach((facility) => {
      if (facility.latitude && facility.longitude) {
        markers.push({
          id: facility.id,
          type: 'facility',
          name: facility.name,
          position: [facility.latitude, facility.longitude],
          data: facility,
        })
      } else if (facility.state && STATE_COORDINATES[facility.state]) {
        markers.push({
          id: facility.id,
          type: 'facility',
          name: facility.name,
          position: STATE_COORDINATES[facility.state],
          data: facility,
        })
      }
    })

    investigations.forEach((inv) => {
      if (inv.latitude && inv.longitude) {
        markers.push({
          id: inv.id,
          type: 'investigation',
          name: inv.title,
          position: [inv.latitude, inv.longitude],
          data: inv,
        })
      }
    })

    return markers
  }, [facilities, investigations])

  if (isLoading) {
    return (
      <Card>
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner />
        </div>
      </Card>
    )
  }

  if (mapMarkers.length === 0) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Geographic Distribution</h3>
        <div className="text-center text-gray-500 py-12">
          <p>No geographic data available.</p>
        </div>
      </Card>
    )
  }

  return (
    <Card>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Geographic Distribution</h3>
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <span>{facilities.length} facilities</span>
          {investigations.length > 0 && <span>{investigations.length} investigations</span>}
        </div>
      </div>

      {/* Map */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <MapContainer
          center={mapCenter}
          zoom={mapMarkers.length === 1 ? 6 : 4}
          style={{ height: '500px', width: '100%' }}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {mapMarkers.map((marker) => {
            const isFacility = marker.type === 'facility'
            const radius = isFacility
              ? 8 + (marker.data.tiger_count || 0) * 2
              : 6
            const color = isFacility
              ? marker.data.verified
                ? '#10B981' // green for verified
                : '#F59E0B' // amber for unverified
              : '#3B82F6' // blue for investigations

            return (
              <CircleMarker
                key={marker.id}
                center={marker.position}
                radius={radius}
                pathOptions={{
                  fillColor: color,
                  fillOpacity: 0.7,
                  color: '#FFFFFF',
                  weight: 2,
                }}
              >
                <Popup>
                  <div className="p-2">
                    <h4 className="font-semibold text-gray-900 mb-2">{marker.name}</h4>
                    {isFacility && (
                      <>
                        {marker.data.state && (
                          <p className="text-sm text-gray-600">
                            <strong>State:</strong> {marker.data.state}
                          </p>
                        )}
                        {marker.data.city && (
                          <p className="text-sm text-gray-600">
                            <strong>City:</strong> {marker.data.city}
                          </p>
                        )}
                        {marker.data.tiger_count !== undefined && (
                          <p className="text-sm text-gray-600">
                            <strong>Tigers:</strong> {marker.data.tiger_count}
                          </p>
                        )}
                        <Badge
                          variant={marker.data.verified ? 'success' : 'warning'}
                          className="mt-2"
                        >
                          {marker.data.verified ? '✅ Verified' : '⏳ Unverified'}
                        </Badge>
                      </>
                    )}
                    {!isFacility && marker.data.location && (
                      <p className="text-sm text-gray-600">
                        <strong>Location:</strong> {marker.data.location}
                      </p>
                    )}
                  </div>
                </Popup>
                <Tooltip>
                  <div className="text-sm">
                    <div className="font-medium">{marker.name}</div>
                    {marker.data.state && (
                      <div className="text-xs text-gray-500">{marker.data.state}</div>
                    )}
                  </div>
                </Tooltip>
              </CircleMarker>
            )
          })}
        </MapContainer>
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-green-500"></div>
          <span className="text-sm text-gray-600">Verified Facility</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-amber-500"></div>
          <span className="text-sm text-gray-600">Unverified Facility</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-blue-500"></div>
          <span className="text-sm text-gray-600">Investigation</span>
        </div>
      </div>
    </Card>
  )
}

export default GeographicMap


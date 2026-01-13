import React, { useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons in React Leaflet
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

interface LocationMarker {
  type: 'user' | 'exif' | 'facility' | 'web';
  coordinates: { lat: number; lon: number };
  name: string;
  confidence: string;
  details: string;
}

interface Investigation2MapProps {
  locations: LocationMarker[];
}

// Custom colored markers for different location types
const createColoredIcon = (color: string) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        background-color: ${color};
        width: 25px;
        height: 25px;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        border: 2px solid white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
      ">
        <div style="
          width: 8px;
          height: 8px;
          background-color: white;
          border-radius: 50%;
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%) rotate(45deg);
        "></div>
      </div>
    `,
    iconSize: [25, 25],
    iconAnchor: [12, 24],
  });
};

const markerColors = {
  user: '#3b82f6', // blue
  exif: '#10b981', // green
  facility: '#ef4444', // red
  web: '#f97316', // orange
};

export const Investigation2Map: React.FC<Investigation2MapProps> = ({ locations }) => {
  const center = useMemo(() => {
    if (!locations || locations.length === 0) {
      return [39.8, -98.5]; // Center of USA
    }

    const latSum = locations.reduce((sum, loc) => sum + loc.coordinates.lat, 0);
    const lonSum = locations.reduce((sum, loc) => sum + loc.coordinates.lon, 0);

    return [latSum / locations.length, lonSum / locations.length];
  }, [locations]);

  const zoom = useMemo(() => {
    if (!locations || locations.length === 0) return 4;
    if (locations.length === 1) return 10;

    // Calculate bounds
    const lats = locations.map(loc => loc.coordinates.lat);
    const lons = locations.map(loc => loc.coordinates.lon);
    const latRange = Math.max(...lats) - Math.min(...lats);
    const lonRange = Math.max(...lons) - Math.min(...lons);
    const maxRange = Math.max(latRange, lonRange);

    // Rough zoom calculation
    if (maxRange > 50) return 4;
    if (maxRange > 10) return 6;
    if (maxRange > 5) return 8;
    return 10;
  }, [locations]);

  if (!locations || locations.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No location data available</p>
      </div>
    );
  }

  return (
    <div className="w-full h-[500px] rounded-lg overflow-hidden shadow-md">
      <MapContainer
        center={center as [number, number]}
        zoom={zoom}
        scrollWheelZoom={true}
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {locations.map((loc, idx) => (
          <Marker
            key={idx}
            position={[loc.coordinates.lat, loc.coordinates.lon]}
            icon={createColoredIcon(markerColors[loc.type])}
          >
            <Popup>
              <div className="p-2">
                <h4 className="font-semibold text-lg mb-1">{loc.name}</h4>
                <span className="inline-block px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded mb-2">
                  {loc.confidence} confidence
                </span>
                <span className="inline-block px-2 py-1 text-xs font-medium ml-1 rounded mb-2"
                      style={{ backgroundColor: `${markerColors[loc.type]}20`, color: markerColors[loc.type] }}>
                  {loc.type}
                </span>
                <p className="text-sm text-gray-600 mt-2">{loc.details}</p>
                <p className="text-xs text-gray-400 mt-1">
                  {loc.coordinates.lat.toFixed(4)}, {loc.coordinates.lon.toFixed(4)}
                </p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 justify-center text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full" style={{ backgroundColor: markerColors.user }}></div>
          <span>User Context</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full" style={{ backgroundColor: markerColors.exif }}></div>
          <span>EXIF Data</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full" style={{ backgroundColor: markerColors.facility }}></div>
          <span>Facility</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full" style={{ backgroundColor: markerColors.web }}></div>
          <span>Web Intelligence</span>
        </div>
      </div>
    </div>
  );
};

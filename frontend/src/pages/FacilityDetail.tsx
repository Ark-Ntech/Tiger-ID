import { useParams, useNavigate } from 'react-router-dom'
import { useGetFacilityQuery, useGetTigersQuery } from '../app/api'
import Card from '../components/common/Card'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import Button from '../components/common/Button'
import Alert from '../components/common/Alert'
import {
  BuildingOfficeIcon,
  GlobeAltIcon,
  LinkIcon,
  ArrowLeftIcon,
  ShieldCheckIcon,
  MapPinIcon,
  CalendarIcon,
  IdentificationIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { Tiger } from '../types'

const FacilityDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data, isLoading, error } = useGetFacilityQuery(id!)
  const { data: tigersData } = useGetTigersQuery({ page: 1, page_size: 100 })

  const facility = data?.data
  const allTigers = tigersData?.data?.data || []
  const facilityTigers = facility ? allTigers.filter((tiger: Tiger) =>
    tiger.metadata?.origin_facility_id === facility.id
  ) : []

  const formatDate = (dateStr: string | undefined) => {
    if (!dateStr) return null
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    } catch {
      return dateStr
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  if (error || !facility) {
    return (
      <div className="space-y-6">
        <Button
          variant="secondary"
          onClick={() => navigate('/facilities')}
          className="flex items-center space-x-2"
        >
          <ArrowLeftIcon className="h-4 w-4" />
          <span>Back to Facilities</span>
        </Button>
        <Alert type="error">
          {error ? 'Error loading facility' : 'Facility not found'}
        </Alert>
      </div>
    )
  }

  const hasLocation = facility.latitude && facility.longitude
  const hasLinks = facility.website || (facility.social_media_links && Object.keys(facility.social_media_links).length > 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="secondary"
            onClick={() => navigate('/facilities')}
            className="flex items-center space-x-2"
          >
            <ArrowLeftIcon className="h-4 w-4" />
            <span>Back</span>
          </Button>
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gray-100 dark:bg-tactical-800 rounded-lg">
              <BuildingOfficeIcon className="h-8 w-8 text-tiger-orange" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-tactical-50">
                {facility.exhibitor_name || facility.name}
              </h1>
              <div className="flex items-center gap-3 mt-1">
                {(facility.city || facility.state) && (
                  <span className="text-gray-500 dark:text-tactical-400 flex items-center gap-1">
                    <MapPinIcon className="h-4 w-4" />
                    {facility.city && facility.state
                      ? `${facility.city}, ${facility.state}`
                      : facility.state || facility.city}
                  </span>
                )}
                {facility.usda_license && (
                  <span className="text-gray-500 dark:text-tactical-400 flex items-center gap-1">
                    <IdentificationIcon className="h-4 w-4" />
                    USDA: {facility.usda_license}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
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

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="text-center">
          <p className="text-sm text-gray-500 dark:text-tactical-400">Tiger Count</p>
          <p className="text-3xl font-bold text-tiger-orange">{facility.tiger_count || 0}</p>
        </Card>
        <Card className="text-center">
          <p className="text-sm text-gray-500 dark:text-tactical-400">Capacity</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-tactical-100">{facility.tiger_capacity || 'N/A'}</p>
        </Card>
        <Card className="text-center">
          <p className="text-sm text-gray-500 dark:text-tactical-400">Data Source</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-tactical-100 truncate">{facility.data_source || 'Unknown'}</p>
        </Card>
        <Card className="text-center">
          <p className="text-sm text-gray-500 dark:text-tactical-400">Status</p>
          <p className="text-lg font-semibold text-green-600 dark:text-green-400">Active</p>
        </Card>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Location & Details */}
          <Card>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-tactical-100 mb-4 flex items-center gap-2">
              <MapPinIcon className="h-5 w-5 text-gray-400 dark:text-tactical-400" />
              Location & Details
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {facility.address && (
                <div className="md:col-span-2">
                  <p className="text-sm text-gray-500 dark:text-tactical-400">Address</p>
                  <p className="text-gray-900 dark:text-tactical-100">
                    {facility.address}
                    {facility.city && `, ${facility.city}`}
                    {facility.state && `, ${facility.state}`}
                    {facility.country && facility.country !== 'USA' && `, ${facility.country}`}
                  </p>
                </div>
              )}
              {!facility.address && (facility.city || facility.state) && (
                <div className="md:col-span-2">
                  <p className="text-sm text-gray-500 dark:text-tactical-400">Location</p>
                  <p className="text-gray-900 dark:text-tactical-100">
                    {facility.city && facility.city}
                    {facility.city && facility.state && ', '}
                    {facility.state && facility.state}
                  </p>
                </div>
              )}
              {hasLocation && (
                <div>
                  <p className="text-sm text-gray-500 dark:text-tactical-400">Coordinates</p>
                  <p className="text-gray-900 dark:text-tactical-100 font-mono text-sm">
                    {Number(facility.latitude).toFixed(4)}, {Number(facility.longitude).toFixed(4)}
                  </p>
                </div>
              )}
              {facility.usda_license && (
                <div>
                  <p className="text-sm text-gray-500 dark:text-tactical-400">USDA License</p>
                  <p className="text-gray-900 dark:text-tactical-100">{facility.usda_license}</p>
                </div>
              )}
              {facility.ir_date && (
                <div>
                  <p className="text-sm text-gray-500 dark:text-tactical-400">IR Date</p>
                  <p className="text-gray-900 dark:text-tactical-100 flex items-center gap-1">
                    <CalendarIcon className="h-4 w-4 text-gray-400 dark:text-tactical-500" />
                    {formatDate(facility.ir_date)}
                  </p>
                </div>
              )}
              {facility.last_inspection_date && (
                <div>
                  <p className="text-sm text-gray-500 dark:text-tactical-400">Last Inspection</p>
                  <p className="text-gray-900 dark:text-tactical-100 flex items-center gap-1">
                    <CalendarIcon className="h-4 w-4 text-gray-400 dark:text-tactical-500" />
                    {formatDate(facility.last_inspection_date)}
                  </p>
                </div>
              )}
            </div>
          </Card>

          {/* Links */}
          {hasLinks && (
            <Card>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-tactical-100 mb-4 flex items-center gap-2">
                <GlobeAltIcon className="h-5 w-5 text-gray-400 dark:text-tactical-400" />
                Links
              </h2>
              <div className="flex flex-wrap gap-3">
                {facility.website && (
                  <a
                    href={facility.website.startsWith('http') ? facility.website : `https://${facility.website}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-tactical-800 border border-gray-200 dark:border-tactical-700 rounded-lg text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 hover:border-gray-300 dark:hover:border-tactical-600 transition-colors"
                  >
                    <GlobeAltIcon className="h-4 w-4" />
                    Website
                  </a>
                )}
                {facility.social_media_links && Object.entries(facility.social_media_links).map(([platform, url]) => (
                  <a
                    key={platform}
                    href={(url as string).startsWith('http') ? url as string : `https://${url}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-tactical-800 border border-gray-200 dark:border-tactical-700 rounded-lg text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 hover:border-gray-300 dark:hover:border-tactical-600 transition-colors"
                  >
                    <LinkIcon className="h-4 w-4" />
                    <span className="capitalize">{platform}</span>
                  </a>
                ))}
              </div>
            </Card>
          )}

          {/* Associated Tigers */}
          {facilityTigers.length > 0 && (
            <Card>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-tactical-100 mb-4 flex items-center gap-2">
                <ShieldCheckIcon className="h-5 w-5 text-tiger-orange" />
                Associated Tigers ({facilityTigers.length})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {facilityTigers.map((tiger: Tiger) => (
                  <div
                    key={tiger.id}
                    className="p-4 bg-gray-50 dark:bg-tactical-800 border border-gray-200 dark:border-tactical-700 rounded-lg hover:border-gray-300 dark:hover:border-tactical-600 cursor-pointer transition-colors"
                    onClick={() => navigate(`/tigers/${tiger.id}`)}
                  >
                    <p className="font-medium text-gray-900 dark:text-tactical-100">
                      {tiger.name || `Tiger ${tiger.id.substring(0, 8)}`}
                    </p>
                    {tiger.images && tiger.images.length > 0 && (
                      <p className="text-sm text-gray-500 dark:text-tactical-400 mt-1">
                        {tiger.images.length} image{tiger.images.length !== 1 ? 's' : ''}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* Right Column - Metadata & Timeline */}
        <div className="space-y-6">
          {/* Quick Info */}
          <Card>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-tactical-100 mb-4 flex items-center gap-2">
              <ChartBarIcon className="h-5 w-5 text-gray-400 dark:text-tactical-400" />
              Details
            </h2>
            <div className="space-y-3 text-sm">
              {facility.accreditation_status && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 dark:text-tactical-400">Accreditation</span>
                  <Badge variant={facility.accreditation_status === 'Non-Accredited' ? 'warning' : 'info'}>
                    {facility.accreditation_status}
                  </Badge>
                </div>
              )}
              {facility.data_source && (
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-tactical-400">Data Source</span>
                  <span className="text-gray-700 dark:text-tactical-200">{facility.data_source}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-tactical-400">Reference</span>
                <span className="text-gray-700 dark:text-tactical-200">{facility.is_reference_facility ? 'Yes' : 'No'}</span>
              </div>
              {facility.created_at && (
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-tactical-400">Created</span>
                  <span className="text-gray-700 dark:text-tactical-200">{formatDate(facility.created_at)}</span>
                </div>
              )}
              {facility.updated_at && (
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-tactical-400">Updated</span>
                  <span className="text-gray-700 dark:text-tactical-200">{formatDate(facility.updated_at)}</span>
                </div>
              )}
            </div>
          </Card>

          {/* Reference Metadata */}
          {facility.reference_metadata && Object.keys(facility.reference_metadata).length > 0 && (
            <Card>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-tactical-100 mb-4">Reference Data</h2>
              <div className="space-y-3 text-sm">
                {Object.entries(facility.reference_metadata).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-500 dark:text-tactical-400 capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className="text-gray-700 dark:text-tactical-200 text-right max-w-[60%] truncate">{String(value)}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Map if coordinates exist */}
          {hasLocation && (
            <Card>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-tactical-100 mb-3 flex items-center gap-2">
                <MapPinIcon className="h-5 w-5 text-gray-400 dark:text-tactical-400" />
                Location
              </h2>
              <div className="aspect-video rounded-lg overflow-hidden border border-gray-200 dark:border-tactical-700">
                <iframe
                  width="100%"
                  height="100%"
                  style={{ border: 0 }}
                  loading="lazy"
                  src={`https://www.openstreetmap.org/export/embed.html?bbox=${Number(facility.longitude) - 0.02},${Number(facility.latitude) - 0.015},${Number(facility.longitude) + 0.02},${Number(facility.latitude) + 0.015}&layer=mapnik&marker=${facility.latitude},${facility.longitude}`}
                  title={`Map showing ${facility.exhibitor_name || facility.name}`}
                />
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

export default FacilityDetail

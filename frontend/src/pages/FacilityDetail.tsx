import { useState, useEffect } from 'react'
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
  CalendarIcon
} from '@heroicons/react/24/outline'
import { Facility, Tiger } from '../types'

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
        <Alert variant="error">
          {error ? 'Error loading facility' : 'Facility not found'}
        </Alert>
      </div>
    )
  }

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
            <div className="p-3 bg-green-100 rounded-lg">
              <BuildingOfficeIcon className="h-8 w-8 text-green-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {facility.exhibitor_name || facility.name}
              </h1>
              <p className="text-gray-600 mt-1">
                {facility.city && facility.state ? (
                  `${facility.city}, ${facility.state}`
                ) : facility.state || facility.city || 'Location unknown'}
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {facility.is_reference_facility && (
            <Badge variant="success">⭐ Reference Facility</Badge>
          )}
          {facility.accreditation_status && (
            <Badge variant={facility.accreditation_status === 'Non-Accredited' ? 'warning' : 'info'}>
              {facility.accreditation_status}
            </Badge>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Information */}
          <Card>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Basic Information</h2>
            <div className="grid grid-cols-2 gap-4">
              {facility.address && (
                <div className="col-span-2">
                  <div className="flex items-start space-x-2">
                    <MapPinIcon className="h-5 w-5 text-gray-400 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-500">Address</p>
                      <p className="text-gray-900">{facility.address}</p>
                    </div>
                  </div>
                </div>
              )}
              {facility.tiger_count !== undefined && (
                <div>
                  <p className="text-sm text-gray-500">Tiger Count</p>
                  <p className="text-lg font-semibold text-gray-900">{facility.tiger_count}</p>
                </div>
              )}
              {facility.tiger_capacity && (
                <div>
                  <p className="text-sm text-gray-500">Tiger Capacity</p>
                  <p className="text-lg font-semibold text-gray-900">{facility.tiger_capacity}</p>
                </div>
              )}
              {facility.ir_date && (
                <div>
                  <div className="flex items-center space-x-2">
                    <CalendarIcon className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-500">IR Date</p>
                      <p className="text-gray-900">{formatDate(facility.ir_date)}</p>
                    </div>
                  </div>
                </div>
              )}
              {facility.last_inspection_date && (
                <div>
                  <div className="flex items-center space-x-2">
                    <CalendarIcon className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-500">Last Inspection</p>
                      <p className="text-gray-900">{formatDate(facility.last_inspection_date)}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>

          {/* Social Media & Website */}
          {(facility.website || (facility.social_media_links && Object.keys(facility.social_media_links).length > 0)) && (
            <Card>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Links</h2>
              <div className="space-y-3">
                {facility.website && (
                  <a
                    href={facility.website.startsWith('http') ? facility.website : `https://${facility.website}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-2 text-blue-600 hover:text-blue-800"
                  >
                    <GlobeAltIcon className="h-5 w-5" />
                    <span>Website</span>
                  </a>
                )}
                {facility.social_media_links && Object.keys(facility.social_media_links).length > 0 && (
                  <div className="space-y-2">
                    {Object.entries(facility.social_media_links).map(([platform, url]) => (
                      <a
                        key={platform}
                        href={url.startsWith('http') ? url : `https://${url}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center space-x-2 text-blue-600 hover:text-blue-800"
                      >
                        <LinkIcon className="h-5 w-5" />
                        <span className="capitalize">{platform}</span>
                      </a>
                    ))}
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* Associated Tigers */}
          {facilityTigers.length > 0 && (
            <Card>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <ShieldCheckIcon className="h-6 w-6 mr-2 text-primary-600" />
                Associated Tigers ({facilityTigers.length})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {facilityTigers.map((tiger: Tiger) => (
                  <div
                    key={tiger.id}
                    className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                    onClick={() => navigate(`/tigers`)}
                  >
                    <p className="font-medium text-gray-900">
                      {tiger.name || `Tiger ${tiger.id.substring(0, 8)}`}
                    </p>
                    {tiger.images && tiger.images.length > 0 && (
                      <p className="text-sm text-gray-600 mt-1">
                        {tiger.images.length} image{tiger.images.length !== 1 ? 's' : ''}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* Right Column - Metadata */}
        <div className="space-y-6">
          {/* Metadata */}
          <Card>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Metadata</h2>
            <div className="space-y-3 text-sm">
              {facility.data_source && (
                <div>
                  <p className="text-gray-500">Data Source</p>
                  <p className="text-gray-900">{facility.data_source}</p>
                </div>
              )}
              {facility.created_at && (
                <div>
                  <p className="text-gray-500">Created</p>
                  <p className="text-gray-900">{formatDate(facility.created_at)}</p>
                </div>
              )}
              {facility.updated_at && (
                <div>
                  <p className="text-gray-500">Last Updated</p>
                  <p className="text-gray-900">{formatDate(facility.updated_at)}</p>
                </div>
              )}
            </div>
          </Card>

          {/* Reference Metadata */}
          {facility.reference_metadata && Object.keys(facility.reference_metadata).length > 0 && (
            <Card>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Reference Data</h2>
              <div className="space-y-2 text-sm">
                {Object.entries(facility.reference_metadata).map(([key, value]) => (
                  <div key={key}>
                    <p className="text-gray-500 capitalize">{key.replace('_', ' ')}</p>
                    <p className="text-gray-900">{String(value)}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

export default FacilityDetail


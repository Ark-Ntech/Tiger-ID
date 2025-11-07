import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGetFacilitiesQuery } from '../app/api'
import Card from '../components/common/Card'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import { BuildingOfficeIcon, GlobeAltIcon, LinkIcon } from '@heroicons/react/24/outline'
import { Facility } from '../types'

const Facilities = () => {
  const [page, setPage] = useState(1)
  const navigate = useNavigate()
  const { data, isLoading } = useGetFacilitiesQuery({ page, page_size: 50 })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  const facilities = data?.data?.data || []

  const formatDate = (dateStr: string | undefined) => {
    if (!dateStr) return null
    try {
      return new Date(dateStr).toLocaleDateString()
    } catch {
      return dateStr
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Facilities</h1>
        <p className="text-gray-600 mt-2">Track and monitor tiger facilities from TPC dataset</p>
      </div>

      {facilities.length > 0 ? (
        <div className="space-y-4">
          {facilities.map((facility: Facility) => (
            <Card 
              key={facility.id} 
              className="hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => navigate(`/facilities/${facility.id}`)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-start space-x-4">
                    <div className="p-3 bg-green-100 rounded-lg">
                      <BuildingOfficeIcon className="h-6 w-6 text-green-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {facility.exhibitor_name || facility.name}
                          </h3>
                          <p className="text-sm text-gray-600 mt-1">
                            {facility.city && facility.state ? (
                              `${facility.city}, ${facility.state}`
                            ) : facility.state || facility.city || 'Location unknown'}
                          </p>
                          {facility.address && (
                            <p className="text-xs text-gray-500 mt-1">{facility.address}</p>
                          )}
                        </div>
                        <div className="flex flex-col items-end space-y-2">
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
                      
                      <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                        {facility.tiger_count !== undefined && (
                          <div>
                            <span className="text-gray-500">Tiger Count:</span>
                            <p className="font-medium text-gray-900">{facility.tiger_count}</p>
                          </div>
                        )}
                        {facility.ir_date && (
                          <div>
                            <span className="text-gray-500">IR Date:</span>
                            <p className="font-medium text-gray-900">{formatDate(facility.ir_date)}</p>
                          </div>
                        )}
                        {facility.last_inspection_date && (
                          <div>
                            <span className="text-gray-500">Last Inspection:</span>
                            <p className="font-medium text-gray-900">{formatDate(facility.last_inspection_date)}</p>
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
                              className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800"
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
                                  className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800"
                                  title={platform}
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
        <Card className="text-center py-12">
          <BuildingOfficeIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No facilities found</p>
        </Card>
      )}
    </div>
  )
}

export default Facilities


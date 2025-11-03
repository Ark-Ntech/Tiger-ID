import { useState } from 'react'
import { useGetFacilitiesQuery } from '../app/api'
import Card from '../components/common/Card'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import { BuildingOfficeIcon } from '@heroicons/react/24/outline'

const Facilities = () => {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useGetFacilitiesQuery({ page, page_size: 10 })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  const facilities = data?.data?.data || []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Facilities</h1>
        <p className="text-gray-600 mt-2">Track and monitor tiger facilities</p>
      </div>

      {facilities.length > 0 ? (
        <div className="space-y-4">
          {facilities.map((facility: any) => (
            <Card key={facility.id} className="hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4">
                  <div className="p-3 bg-green-100 rounded-lg">
                    <BuildingOfficeIcon className="h-6 w-6 text-green-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{facility.name}</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {facility.city}, {facility.state}, {facility.country}
                    </p>
                    {facility.license_number && (
                      <p className="text-xs text-gray-500 mt-2">
                        License: {facility.license_number}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant={facility.verified ? 'success' : 'warning'}>
                    {facility.verified ? 'Verified' : 'Unverified'}
                  </Badge>
                  <Badge variant={facility.status === 'active' ? 'info' : 'default'}>
                    {facility.status}
                  </Badge>
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


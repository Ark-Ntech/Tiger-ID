import { useState, useEffect } from 'react'
import { useGetTigersQuery } from '../app/api'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import Alert from '../components/common/Alert'
import { ShieldCheckIcon } from '@heroicons/react/24/outline'

const Tigers = () => {
  const [page, setPage] = useState(1)
  const { data, isLoading, error } = useGetTigersQuery({ page, page_size: 12 })

  useEffect(() => {
    if (error) {
      console.error('Error loading tigers:', error)
    }
    if (data) {
      console.log('Tigers data loaded:', data)
      console.log('Tigers array:', data?.data?.data || [])
    }
  }, [error, data])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <Alert type="error">Failed to load tigers. Please try again.</Alert>
      </div>
    )
  }

  const tigers = data?.data?.data || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Tiger Database</h1>
          <p className="text-gray-600 mt-2">Identified tigers and their profiles</p>
        </div>
        <Button 
          variant="primary"
          onClick={() => {
            // TODO: Implement tiger image upload dialog
            alert('Tiger image upload feature coming soon!')
          }}
        >
          Upload Tiger Image
        </Button>
      </div>

      {tigers.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tigers.map((tiger: any) => (
            <Card key={tiger.id} className="hover:shadow-lg transition-shadow">
              <div className="aspect-video bg-gray-200 rounded-lg mb-4 flex items-center justify-center overflow-hidden">
                {tiger.images && tiger.images.length > 0 ? (
                  <img
                    src={`http://localhost:8000${tiger.images[0].url}`}
                    alt={tiger.name || `Tiger ${tiger.id}`}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      // Fallback to icon if image fails to load
                      e.currentTarget.style.display = 'none';
                      e.currentTarget.parentElement?.classList.add('flex', 'items-center', 'justify-center');
                    }}
                  />
                ) : (
                  <ShieldCheckIcon className="h-16 w-16 text-gray-400" />
                )}
              </div>
              <h3 className="font-semibold text-gray-900">
                {tiger.name || `Tiger #${tiger.id.substring(0, 8)}`}
              </h3>
              <div className="mt-2 space-y-1 text-sm text-gray-600">
                {tiger.estimated_age && <p>Age: ~{tiger.estimated_age} years</p>}
                {tiger.sex && <p>Sex: {tiger.sex}</p>}
              </div>
              <div className="mt-3">
                <Badge variant="success">
                  Confidence: {Math.round(tiger.confidence_score * 100)}%
                </Badge>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="text-center py-12">
          <ShieldCheckIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No tigers identified yet</p>
        </Card>
      )}
    </div>
  )
}

export default Tigers


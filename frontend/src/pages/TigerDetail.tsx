import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useGetTigerQuery, useLaunchInvestigationFromTigerMutation } from '../app/api'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import Alert from '../components/common/Alert'
import { ShieldCheckIcon, ArrowLeftIcon, MagnifyingGlassIcon, PhotoIcon, XMarkIcon } from '@heroicons/react/24/outline'

const TigerDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [launchingInvestigation, setLaunchingInvestigation] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [selectedImageIndex, setSelectedImageIndex] = useState<number | null>(null)

  const { data, isLoading, error } = useGetTigerQuery(id || '')
  const [launchInvestigationFromTiger] = useLaunchInvestigationFromTigerMutation()

  const tiger = data?.data?.data || data?.data

  const handleLaunchInvestigation = async () => {
    if (!id) return
    
    setLaunchingInvestigation(true)
    try {
      const result = await launchInvestigationFromTiger({ 
        tiger_id: id,
        tiger_name: tiger?.name 
      }).unwrap()
      
      if (result.data?.investigation_id) {
        // Navigate to investigation workspace
        navigate(`/investigations/${result.data.investigation_id}`)
      } else {
        // Fallback: navigate to launch page
        navigate(`/investigations/launch?tiger_id=${id}`)
      }
    } catch (error: any) {
      console.error('Error launching investigation:', error)
      alert(`Failed to launch investigation: ${error?.data?.detail || error?.message || 'Unknown error'}`)
    } finally {
      setLaunchingInvestigation(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  if (error || !tiger) {
    return (
      <div className="space-y-6">
        <Button
          variant="secondary"
          onClick={() => navigate('/tigers')}
          className="flex items-center gap-2"
        >
          <ArrowLeftIcon className="h-5 w-5" />
          Back to Tigers
        </Button>
        <Alert type="error">
          {error ? 'Failed to load tiger details. Please try again.' : 'Tiger not found.'}
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="secondary"
            onClick={() => navigate('/tigers')}
            className="flex items-center gap-2"
          >
            <ArrowLeftIcon className="h-5 w-5" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {tiger.name || `Tiger #${tiger.tiger_id?.substring(0, 8)}`}
            </h1>
            <p className="text-gray-600 mt-1">
              ID: {tiger.tiger_id?.substring(0, 8)}...
            </p>
          </div>
        </div>
        <Button
          variant="primary"
          onClick={handleLaunchInvestigation}
          disabled={launchingInvestigation}
          className="flex items-center gap-2"
        >
          <MagnifyingGlassIcon className="h-5 w-5" />
          {launchingInvestigation ? 'Launching...' : 'Launch Investigation'}
        </Button>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Images and Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Images */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Images</h2>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setIsEditing(!isEditing)}
              >
                {isEditing ? 'Cancel' : 'Edit'}
              </Button>
            </div>
            {tiger.images && tiger.images.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {tiger.images.map((image: any, index: number) => (
                  <div
                    key={image.id || index}
                    className="aspect-video bg-gray-200 rounded-lg overflow-hidden cursor-pointer hover:opacity-80 transition-opacity relative group"
                    onClick={() => setSelectedImageIndex(index)}
                  >
                    <img
                      src={image.url?.startsWith('http') ? image.url : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${image.url || image.path || ''}`}
                      alt={`${tiger.name} - Image ${index + 1}`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none'
                        e.currentTarget.parentElement?.classList.add('flex', 'items-center', 'justify-center')
                      }}
                    />
                    <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-opacity flex items-center justify-center">
                      <PhotoIcon className="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-gray-400">
                <PhotoIcon className="h-16 w-16 mb-4" />
                <p>No images available</p>
              </div>
            )}
            {tiger.image_count !== undefined && (
              <p className="text-sm text-gray-600 mt-4">
                Total images: {tiger.image_count}
              </p>
            )}
          </Card>

          {/* Image Lightbox Modal */}
          {selectedImageIndex !== null && tiger.images && tiger.images[selectedImageIndex] && (
            <div
              className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4"
              onClick={() => setSelectedImageIndex(null)}
            >
              <div className="relative max-w-7xl max-h-full">
                <button
                  onClick={() => setSelectedImageIndex(null)}
                  className="absolute top-4 right-4 text-white hover:text-gray-300 z-10"
                >
                  <XMarkIcon className="h-8 w-8" />
                </button>
                <img
                  src={tiger.images[selectedImageIndex].url?.startsWith('http') ? tiger.images[selectedImageIndex].url : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${tiger.images[selectedImageIndex].url || tiger.images[selectedImageIndex].path || ''}`}
                  alt={`${tiger.name} - Image ${selectedImageIndex + 1}`}
                  className="max-w-full max-h-[90vh] object-contain"
                  onClick={(e) => e.stopPropagation()}
                />
                {tiger.images.length > 1 && (
                  <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedImageIndex((selectedImageIndex - 1 + tiger.images.length) % tiger.images.length)
                      }}
                      className="px-4 py-2 bg-white bg-opacity-90 rounded hover:bg-opacity-100"
                    >
                      Previous
                    </button>
                    <span className="px-4 py-2 bg-white bg-opacity-90 rounded">
                      {selectedImageIndex + 1} / {tiger.images.length}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedImageIndex((selectedImageIndex + 1) % tiger.images.length)
                      }}
                      className="px-4 py-2 bg-white bg-opacity-90 rounded hover:bg-opacity-100"
                    >
                      Next
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Notes */}
          {tiger.notes && (
            <Card>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Notes</h2>
              <p className="text-gray-700 whitespace-pre-wrap">{tiger.notes}</p>
            </Card>
          )}
        </div>

        {/* Right Column - Metadata */}
        <div className="space-y-6">
          {/* Status Card */}
          <Card>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Status</h2>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-600">Status</label>
                <div className="mt-1">
                  <Badge variant={tiger.status === 'active' ? 'success' : 'warning'}>
                    {tiger.status || 'Unknown'}
                  </Badge>
                </div>
              </div>
              {tiger.alias && (
                <div>
                  <label className="text-sm font-medium text-gray-600">Alias</label>
                  <p className="mt-1 text-gray-900">{tiger.alias}</p>
                </div>
              )}
              {tiger.last_seen_location && (
                <div>
                  <label className="text-sm font-medium text-gray-600">Last Seen Location</label>
                  <p className="mt-1 text-gray-900">{tiger.last_seen_location}</p>
                </div>
              )}
              {tiger.last_seen_date && (
                <div>
                  <label className="text-sm font-medium text-gray-600">Last Seen Date</label>
                  <p className="mt-1 text-gray-900">
                    {new Date(tiger.last_seen_date).toLocaleDateString()}
                  </p>
                </div>
              )}
            </div>
          </Card>

          {/* Related Tigers */}
          {tiger.related_tigers && tiger.related_tigers.length > 0 && (
            <Card>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Related Tigers</h2>
              <div className="space-y-2">
                {tiger.related_tigers.map((relatedTiger: any) => (
                  <div
                    key={relatedTiger.id}
                    className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                    onClick={() => navigate(`/tigers/${relatedTiger.id}`)}
                  >
                    <p className="font-medium text-gray-900">{relatedTiger.name || `Tiger #${relatedTiger.id.substring(0, 8)}`}</p>
                    {relatedTiger.alias && (
                      <p className="text-sm text-gray-600">Alias: {relatedTiger.alias}</p>
                    )}
                    <Badge variant={relatedTiger.status === 'active' ? 'success' : 'warning'} className="mt-2">
                      {relatedTiger.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Quick Actions */}
          <Card>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="space-y-2">
              <Button
                variant="primary"
                onClick={handleLaunchInvestigation}
                disabled={launchingInvestigation}
                className="w-full flex items-center justify-center gap-2"
              >
                <MagnifyingGlassIcon className="h-5 w-5" />
                {launchingInvestigation ? 'Launching...' : 'Launch Investigation'}
              </Button>
              <Button
                variant="secondary"
                onClick={() => navigate(`/tigers`)}
                className="w-full"
              >
                View All Tigers
              </Button>
            </div>
          </Card>

          {/* Metadata */}
          <Card>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Metadata</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Tiger ID:</span>
                <span className="text-gray-900 font-mono text-xs">
                  {tiger.tiger_id?.substring(0, 8)}...
                </span>
              </div>
              {tiger.image_count !== undefined && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Image Count:</span>
                  <span className="text-gray-900">{tiger.image_count}</span>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default TigerDetail


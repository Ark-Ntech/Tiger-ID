import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Modal from '../components/common/Modal'
import { PhotoIcon, ArrowLeftIcon, ArrowDownTrayIcon, TrashIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/outline'

const DatasetManagement = () => {
  const navigate = useNavigate()
  const [selectedTiger, setSelectedTiger] = useState<string>('')
  const [tigers, setTigers] = useState<any[]>([])
  const [tigerImages, setTigerImages] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showAddImagesModal, setShowAddImagesModal] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])

  useEffect(() => {
    fetchTigers()
  }, [])

  useEffect(() => {
    if (selectedTiger) {
      fetchTigerImages(selectedTiger)
    }
  }, [selectedTiger])

  const fetchTigers = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/v1/tigers?page_size=100')
      const data = await response.json()
      setTigers(data.data?.data || [])
    } catch (error) {
      console.error('Error fetching tigers:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchTigerImages = async (tigerId: string) => {
    setIsLoading(true)
    try {
      const response = await fetch(`/api/v1/tigers/${tigerId}`)
      const data = await response.json()
      setTigerImages(data.data?.images || [])
    } catch (error) {
      console.error('Error fetching tiger images:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddImages = async () => {
    if (!selectedTiger || selectedFiles.length === 0) {
      alert('Please select a tiger and at least one image')
      return
    }

    setIsLoading(true)
    try {
      const formData = new FormData()
      selectedFiles.forEach((file) => {
        formData.append('images', file)
      })

      const response = await fetch(`/api/v1/tigers/${selectedTiger}/images`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      })

      if (!response.ok) {
        throw new Error('Failed to add images')
      }

      alert('Images added successfully')
      setShowAddImagesModal(false)
      setSelectedFiles([])
      fetchTigerImages(selectedTiger)
    } catch (error: any) {
      alert(`Failed to add images: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRemoveImage = async (imageId: string) => {
    if (!confirm('Are you sure you want to remove this image from the dataset?')) return

    try {
      const response = await fetch(`/api/v1/tigers/${selectedTiger}/images/${imageId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to remove image')
      }

      fetchTigerImages(selectedTiger)
    } catch (error: any) {
      alert(`Failed to remove image: ${error.message}`)
    }
  }

  const handleExportDataset = async () => {
    if (!selectedTiger) {
      alert('Please select a tiger')
      return
    }

    try {
      const response = await fetch(`/api/v1/tigers/${selectedTiger}/export-dataset`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to export dataset')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `tiger_${selectedTiger}_dataset.zip`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error: any) {
      alert(`Failed to export dataset: ${error.message}`)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="secondary"
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2"
          >
            <ArrowLeftIcon className="h-5 w-5" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dataset Management</h1>
            <p className="text-gray-600 mt-1">Manage training datasets for tiger models</p>
          </div>
        </div>
        {selectedTiger && (
          <div className="flex gap-2">
            <Button
              variant="secondary"
              onClick={() => setShowAddImagesModal(true)}
              className="flex items-center gap-2"
            >
              <PlusIcon className="h-5 w-5" />
              Add Images
            </Button>
            <Button
              variant="secondary"
              onClick={handleExportDataset}
              className="flex items-center gap-2"
            >
              <ArrowDownTrayIcon className="h-5 w-5" />
              Export Dataset
            </Button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tiger Selection */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Tigers</h2>
          {isLoading ? (
            <LoadingSpinner size="sm" />
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {tigers.map((tiger: any) => (
                <div
                  key={tiger.id}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    selectedTiger === tiger.id
                      ? 'bg-blue-50 border border-blue-200'
                      : 'hover:bg-gray-50 border border-transparent'
                  }`}
                  onClick={() => setSelectedTiger(tiger.id)}
                >
                  <p className="font-medium text-gray-900">{tiger.name || `Tiger #${tiger.id.substring(0, 8)}`}</p>
                  <p className="text-sm text-gray-600">
                    {tiger.image_count || 0} images
                  </p>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Images */}
        <div className="lg:col-span-2">
          <Card>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              {selectedTiger ? 'Dataset Images' : 'Select a tiger to view images'}
            </h2>
            {selectedTiger ? (
              isLoading ? (
                <LoadingSpinner size="lg" />
              ) : tigerImages.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {tigerImages.map((image: any) => (
                    <div
                      key={image.id}
                      className="relative aspect-video bg-gray-200 rounded-lg overflow-hidden group"
                    >
                      <img
                        src={image.url?.startsWith('http') ? image.url : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${image.url || ''}`}
                        alt={`Image ${image.id}`}
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-opacity flex items-center justify-center">
                        <button
                          onClick={() => handleRemoveImage(image.id)}
                          className="opacity-0 group-hover:opacity-100 transition-opacity p-2 bg-red-600 text-white rounded hover:bg-red-700"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <PhotoIcon className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>No images in dataset</p>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => setShowAddImagesModal(true)}
                    className="mt-4"
                  >
                    Add Images
                  </Button>
                </div>
              )
            ) : (
              <div className="text-center py-12 text-gray-500">
                <PhotoIcon className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p>Select a tiger to view its dataset</p>
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Add Images Modal */}
      <Modal
        isOpen={showAddImagesModal}
        onClose={() => {
          setShowAddImagesModal(false)
          setSelectedFiles([])
        }}
        title="Add Images to Dataset"
        size="lg"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Images
            </label>
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={(e) => setSelectedFiles(Array.from(e.target.files || []))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            {selectedFiles.length > 0 && (
              <div className="mt-2 space-y-1">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">{file.name}</span>
                    <button
                      onClick={() => setSelectedFiles(prev => prev.filter((_, i) => i !== index))}
                      className="text-red-600 hover:text-red-800"
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="flex gap-2 justify-end">
            <Button
              variant="secondary"
              onClick={() => {
                setShowAddImagesModal(false)
                setSelectedFiles([])
              }}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleAddImages}
              disabled={selectedFiles.length === 0 || isLoading}
            >
              {isLoading ? 'Adding...' : 'Add Images'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default DatasetManagement


import { useState, useEffect, useCallback } from 'react'
import { useGetTigersQuery, useIdentifyTigerMutation, useIdentifyTigersBatchMutation, useGetAvailableModelsQuery } from '../app/api'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import Alert from '../components/common/Alert'
import Modal from '../components/common/Modal'
import { ShieldCheckIcon, PhotoIcon, XMarkIcon, CheckCircleIcon } from '@heroicons/react/24/outline'

const Tigers = () => {
  const [page, setPage] = useState(1)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [useAllModels, setUseAllModels] = useState(false)
  const [uploadResults, setUploadResults] = useState<any[]>([])
  const [isUploading, setIsUploading] = useState(false)

  const { data, isLoading, error } = useGetTigersQuery({ page, page_size: 12 })
  const { data: modelsData } = useGetAvailableModelsQuery()
  const [identifyTiger, { isLoading: identifying }] = useIdentifyTigerMutation()
  const [identifyBatch, { isLoading: batchIdentifying }] = useIdentifyTigersBatchMutation()

  const availableModels = modelsData?.data?.models || []
  const modelNames = Array.isArray(availableModels) ? availableModels : Object.keys(availableModels)

  useEffect(() => {
    if (error) {
      console.error('Error loading tigers:', error)
    }
    if (data) {
      console.log('Tigers data loaded:', data)
      console.log('Tigers array:', data?.data?.data || [])
    }
  }, [error, data])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    setSelectedFiles((prev) => [...prev, ...files])
  }, [])

  const handleRemoveFile = useCallback((index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const handleSingleUpload = async () => {
    if (selectedFiles.length === 0) return

    // Validate file type
    const file = selectedFiles[0]
    if (!file.type.startsWith('image/')) {
      setUploadResults([{
        identified: false,
        error: `Invalid file type: ${file.type}. Only image files are allowed.`
      }])
      return
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setUploadResults([{
        identified: false,
        error: 'File size exceeds 10MB limit'
      }])
      return
    }

    setIsUploading(true)
    setUploadResults([])

    try {
      const formData = new FormData()
      formData.append('image', selectedFiles[0])
      if (selectedModel) {
        formData.append('model_name', selectedModel)
      }
      if (useAllModels) {
        formData.append('use_all_models', 'true')
      }

      const result = await identifyTiger(formData).unwrap()
      setUploadResults([result.data])
    } catch (error: any) {
      console.error('Error identifying tiger:', error)
      const errorMessage = error?.data?.detail || error?.data?.message || 'Failed to identify tiger'
      setUploadResults([{
        identified: false,
        error: errorMessage
      }])
    } finally {
      setIsUploading(false)
    }
  }

  const handleBatchUpload = async () => {
    if (selectedFiles.length === 0) return

    // Validate files
    const invalidFiles: string[] = []
    selectedFiles.forEach((file) => {
      if (!file.type.startsWith('image/')) {
        invalidFiles.push(`${file.name}: Invalid file type`)
      }
      if (file.size > 10 * 1024 * 1024) {
        invalidFiles.push(`${file.name}: File size exceeds 10MB`)
      }
    })

    if (invalidFiles.length > 0) {
      setUploadResults([{
        identified: false,
        error: `Validation errors: ${invalidFiles.join('; ')}`
      }])
      return
    }

    if (selectedFiles.length > 50) {
      setUploadResults([{
        identified: false,
        error: 'Maximum 50 images per batch request'
      }])
      return
    }

    setIsUploading(true)
    setUploadResults([])

    try {
      const formData = new FormData()
      selectedFiles.forEach((file) => {
        formData.append('images', file)
      })
      if (selectedModel) {
        formData.append('model_name', selectedModel)
      }

      const result = await identifyBatch(formData).unwrap()
      setUploadResults(result.data?.results || [])
    } catch (error: any) {
      console.error('Error batch identifying tigers:', error)
      const errorMessage = error?.data?.detail || error?.data?.message || 'Failed to identify tigers'
      setUploadResults([{
        identified: false,
        error: errorMessage
      }])
    } finally {
      setIsUploading(false)
    }
  }

  const handleCloseModal = () => {
    setShowUploadModal(false)
    setSelectedFiles([])
    setUploadResults([])
    setSelectedModel('')
    setUseAllModels(false)
  }

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
          onClick={() => setShowUploadModal(true)}
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
                    src={tiger.images[0].url.startsWith('http') ? tiger.images[0].url : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${tiger.images[0].url}`}
                    alt={tiger.name || `Tiger ${tiger.id}`}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none'
                      e.currentTarget.parentElement?.classList.add('flex', 'items-center', 'justify-center')
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

      {/* Upload Modal */}
      <Modal
        isOpen={showUploadModal}
        onClose={handleCloseModal}
        title="Identify Tiger from Image"
        size="lg"
      >
        <div className="space-y-6">
          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Model (Optional)
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={useAllModels}
            >
              <option value="">Use Default Model</option>
              {modelNames.map((modelName) => (
                <option key={modelName} value={modelName}>
                  {modelName}
                </option>
              ))}
            </select>
          </div>

          {/* Use All Models Option */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="useAllModels"
              checked={useAllModels}
              onChange={(e) => {
                setUseAllModels(e.target.checked)
                if (e.target.checked) {
                  setSelectedModel('')
                }
              }}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="useAllModels" className="ml-2 block text-sm text-gray-700">
              Use all available models (ensemble)
            </label>
          </div>

          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload Images
            </label>
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-gray-400 transition-colors">
              <div className="space-y-1 text-center">
                <PhotoIcon className="mx-auto h-12 w-12 text-gray-400" />
                <div className="flex text-sm text-gray-600">
                  <label className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500">
                    <span>Upload files</span>
                    <input
                      type="file"
                      className="sr-only"
                      multiple
                      accept="image/*"
                      onChange={handleFileSelect}
                    />
                  </label>
                  <p className="pl-1">or drag and drop</p>
                </div>
                <p className="text-xs text-gray-500">PNG, JPG, GIF up to 10MB each</p>
              </div>
            </div>
          </div>

          {/* Selected Files */}
          {selectedFiles.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Selected Files ({selectedFiles.length})
              </label>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {selectedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded-md"
                  >
                    <span className="text-sm text-gray-700 truncate flex-1">
                      {file.name}
                    </span>
                    <button
                      onClick={() => handleRemoveFile(index)}
                      className="ml-2 text-red-600 hover:text-red-800"
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Results */}
          {uploadResults.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Identification Results
              </label>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {uploadResults.map((result, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border ${
                      result.identified
                        ? 'bg-green-50 border-green-200'
                        : 'bg-yellow-50 border-yellow-200'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {result.identified ? (
                        <CheckCircleIcon className="h-5 w-5 text-green-600" />
                      ) : (
                        <XMarkIcon className="h-5 w-5 text-yellow-600" />
                      )}
                      <div className="flex-1">
                        {result.identified ? (
                          <div>
                            <p className="font-medium text-gray-900">
                              Tiger ID: {result.tiger_id || result.tiger_name || 'Unknown'}
                            </p>
                            <p className="text-sm text-gray-600">
                              Confidence: {Math.round((result.confidence || result.similarity || 0) * 100)}%
                            </p>
                            {result.model && (
                              <p className="text-xs text-gray-500">Model: {result.model}</p>
                            )}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-700">
                            {result.message || 'Tiger not found in database'}
                          </p>
                        )}
                        {result.error && (
                          <p className="text-sm text-red-600 mt-1">{result.error}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2">
            {selectedFiles.length === 1 ? (
              <Button
                variant="primary"
                onClick={handleSingleUpload}
                disabled={isUploading || identifying}
                className="flex-1"
              >
                {isUploading || identifying ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Identifying...
                  </>
                ) : (
                  'Identify Tiger'
                )}
              </Button>
            ) : (
              <Button
                variant="primary"
                onClick={handleBatchUpload}
                disabled={isUploading || batchIdentifying || selectedFiles.length === 0}
                className="flex-1"
              >
                {isUploading || batchIdentifying ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Processing...
                  </>
                ) : (
                  `Identify ${selectedFiles.length} Images`
                )}
              </Button>
            )}
            <Button variant="secondary" onClick={handleCloseModal}>
              Close
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default Tigers

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGetTigersQuery, useIdentifyTigerMutation, useIdentifyTigersBatchMutation, useGetAvailableModelsQuery, useCreateInvestigationMutation, useLaunchInvestigationMutation, useCreateTigerMutation, useLaunchInvestigationFromTigerMutation } from '../app/api'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import Alert from '../components/common/Alert'
import Modal from '../components/common/Modal'
import { ShieldCheckIcon, PhotoIcon, XMarkIcon, CheckCircleIcon } from '@heroicons/react/24/outline'

// Model information helper
const getModelInfo = (modelName: string) => {
  const modelInfoMap: Record<string, { name: string; description: string; fullDescription: string; speed: string; accuracy: string }> = {
    'wildlife_tools': {
      name: 'Wildlife Tools (MegaDescriptor)',
      description: 'Best general-purpose',
      fullDescription: 'Robust general wildlife RE-ID model. Best for most use cases with high accuracy.',
      speed: 'Medium',
      accuracy: 'High'
    },
    'tiger_reid': {
      name: 'Tiger ReID',
      description: 'Tiger-specific specialist',
      fullDescription: 'Tiger-specific stripe specialist model. Optimized for tiger stripe patterns.',
      speed: 'Fast',
      accuracy: 'High'
    },
    'rapid': {
      name: 'RAPID',
      description: 'Fast pattern matching',
      fullDescription: 'Real-time animal pattern re-identification. Fast initial screening model.',
      speed: 'Very Fast',
      accuracy: 'Medium'
    },
    'cvwc2019': {
      name: 'CVWC2019',
      description: 'Part-pose guided',
      fullDescription: 'Part-pose guided tiger re-identification. Robust to pose variations.',
      speed: 'Medium',
      accuracy: 'Very High'
    }
  }
  
  return modelInfoMap[modelName] || {
    name: modelName,
    description: 'Custom model',
    fullDescription: 'Custom model configuration',
    speed: 'Unknown',
    accuracy: 'Unknown'
  }
}

const Tigers = () => {
  const navigate = useNavigate()
  const [page, _setPage] = useState(1)
  void _setPage // Reserved for pagination feature
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showRegistrationModal, setShowRegistrationModal] = useState(false)
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [useAllModels, setUseAllModels] = useState(false)
  const [ensembleMode, setEnsembleMode] = useState<string>('') // 'staggered', 'parallel', or ''
  const [similarityThreshold, setSimilarityThreshold] = useState<number>(0.8)
  const [uploadResults, setUploadResults] = useState<any[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [registrationFiles, setRegistrationFiles] = useState<File[]>([])
  const [registrationName, setRegistrationName] = useState('')
  const [registrationAlias, setRegistrationAlias] = useState('')
  const [registrationNotes, setRegistrationNotes] = useState('')
  const [isRegistering, setIsRegistering] = useState(false)

  const { data, isLoading, error, refetch } = useGetTigersQuery({ page, page_size: 12 })
  const { data: modelsData } = useGetAvailableModelsQuery()
  const [identifyTiger, { isLoading: identifying }] = useIdentifyTigerMutation()
  const [identifyBatch, { isLoading: batchIdentifying }] = useIdentifyTigersBatchMutation()
  const [createInvestigation] = useCreateInvestigationMutation()
  const [_launchInvestigation] = useLaunchInvestigationMutation()
  void _launchInvestigation // Alternative launch method
  const [createTiger] = useCreateTigerMutation()
  const [launchInvestigationFromTiger] = useLaunchInvestigationFromTigerMutation()

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
      if (ensembleMode) {
        formData.append('ensemble_mode', ensembleMode)
      }
      formData.append('similarity_threshold', similarityThreshold.toString())

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

  const handleLaunchInvestigation = async (tigerId: string, tigerName?: string) => {
    try {
      // Launch investigation from tiger
      const result = await launchInvestigationFromTiger({ 
        tiger_id: tigerId,
        tiger_name: tigerName 
      }).unwrap()
      
      if (result.data?.investigation_id) {
        // Navigate to investigation page
        navigate(`/investigations/${result.data.investigation_id}`)
      } else {
        // Fallback: create investigation manually
        const investigation = await createInvestigation({
          title: `Investigation: ${tigerName || `Tiger ${tigerId.substring(0, 8)}`}`,
          description: `Investigation launched for tiger ${tigerName || tigerId}`,
          priority: 'medium',
          tags: ['tiger-investigation']
        }).unwrap()
        
        if (investigation.data?.id) {
          navigate(`/investigations/${investigation.data.id}`)
        }
      }
    } catch (error: any) {
      console.error('Error launching investigation:', error)
      // Show error alert
      alert(`Failed to launch investigation: ${error?.data?.detail || error?.message || 'Unknown error'}`)
    }
  }

  const handleRegistrationFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    setRegistrationFiles((prev) => [...prev, ...files])
  }, [])

  const handleRemoveRegistrationFile = useCallback((index: number) => {
    setRegistrationFiles((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const handleRegisterTiger = async () => {
    if (!registrationName.trim() || registrationFiles.length === 0) {
      alert('Please provide a tiger name and at least one image')
      return
    }

    setIsRegistering(true)
    try {
      const formData = new FormData()
      formData.append('name', registrationName)
      if (registrationAlias) {
        formData.append('alias', registrationAlias)
      }
      if (registrationNotes) {
        formData.append('notes', registrationNotes)
      }
      if (selectedModel) {
        formData.append('model_name', selectedModel)
      }
      
      // Add all images
      registrationFiles.forEach((file) => {
        formData.append('images', file)
      })

      const result = await createTiger(formData).unwrap()
      
      const tigerId = result.data?.tiger_id || result.data?.id
      
      // Show success message with option to view
      const viewTiger = confirm(`Tiger registered successfully! ID: ${tigerId}\n\nWould you like to view this tiger?`)
      
      // Close modal and reset form
      setShowRegistrationModal(false)
      setRegistrationName('')
      setRegistrationAlias('')
      setRegistrationNotes('')
      setRegistrationFiles([])
      setSelectedModel('')
      
      // Refresh tiger list
      refetch()
      
      // Navigate to tiger detail if requested
      if (viewTiger && tigerId) {
        navigate(`/tigers/${tigerId}`)
      }
    } catch (error: any) {
      console.error('Error registering tiger:', error)
      alert(`Failed to register tiger: ${error?.data?.detail || error?.message || 'Unknown error'}`)
    } finally {
      setIsRegistering(false)
    }
  }

  const handleCloseRegistrationModal = () => {
    setShowRegistrationModal(false)
    setRegistrationName('')
    setRegistrationAlias('')
    setRegistrationNotes('')
    setRegistrationFiles([])
    setSelectedModel('')
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
          <p className="text-gray-600 mt-2">All identified tigers and their profiles</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="secondary"
            onClick={() => setShowRegistrationModal(true)}
          >
            Register New Tiger
          </Button>
          <Button 
            variant="primary"
            onClick={() => setShowUploadModal(true)}
          >
            Upload Tiger Image
          </Button>
        </div>
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
              <h3 
                className="font-semibold text-gray-900 cursor-pointer hover:text-blue-600"
                onClick={() => navigate(`/tigers/${tiger.id}`)}
              >
                {tiger.name || `Tiger #${tiger.id.substring(0, 8)}`}
              </h3>
              <div className="mt-2 space-y-1 text-sm text-gray-600">
                <p className="text-xs text-gray-500">ID: {tiger.id.substring(0, 8)}...</p>
                {tiger.alias && <p className="text-xs text-gray-500">Alias: {tiger.alias}</p>}
                {tiger.estimated_age && <p>Age: ~{tiger.estimated_age} years</p>}
                {tiger.sex && <p>Sex: {tiger.sex}</p>}
              </div>
              <div className="mt-3 flex gap-2">
                <Badge variant="success">
                  Confidence: {Math.round((tiger.confidence_score || 0.95) * 100)}%
                </Badge>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleLaunchInvestigation(tiger.id, tiger.name)}
                  className="flex-1"
                >
                  Launch Investigation
                </Button>
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
              disabled={useAllModels || ensembleMode !== ''}
            >
              <option value="">Use Default Model (Wildlife Tools)</option>
              {modelNames.map((modelName) => {
                const modelInfo = getModelInfo(modelName)
                return (
                  <option key={modelName} value={modelName}>
                    {modelInfo.name} - {modelInfo.description}
                  </option>
                )
              })}
            </select>
            {selectedModel && (
              <div className="mt-2 p-3 bg-blue-50 rounded-md">
                <p className="text-sm font-medium text-blue-900">
                  {getModelInfo(selectedModel).name}
                </p>
                <p className="text-xs text-blue-700 mt-1">
                  {getModelInfo(selectedModel).fullDescription}
                </p>
                <div className="mt-2 flex gap-2 text-xs">
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                    Speed: {getModelInfo(selectedModel).speed}
                  </span>
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                    Accuracy: {getModelInfo(selectedModel).accuracy}
                  </span>
                </div>
              </div>
            )}
            {!selectedModel && (
              <p className="mt-1 text-xs text-gray-500">
                Default: Wildlife Tools (MegaDescriptor) - Best general-purpose model
              </p>
            )}
          </div>

          {/* Ensemble Mode Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Ensemble Mode (Optional)
            </label>
            <div className="space-y-2">
              <div className="flex items-center">
                <input
                  type="radio"
                  id="ensemble-none"
                  name="ensembleMode"
                  value=""
                  checked={ensembleMode === ''}
                  onChange={(e) => setEnsembleMode(e.target.value)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <label htmlFor="ensemble-none" className="ml-2 block text-sm text-gray-700">
                  Single Model (Default)
                </label>
              </div>
              <div className="flex items-center">
                <input
                  type="radio"
                  id="ensemble-staggered"
                  name="ensembleMode"
                  value="staggered"
                  checked={ensembleMode === 'staggered'}
                  onChange={(e) => setEnsembleMode(e.target.value)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <label htmlFor="ensemble-staggered" className="ml-2 block text-sm text-gray-700">
                  Staggered Ensemble (Sequential, stops on high confidence)
                </label>
              </div>
              <div className="flex items-center">
                <input
                  type="radio"
                  id="ensemble-parallel"
                  name="ensembleMode"
                  value="parallel"
                  checked={ensembleMode === 'parallel'}
                  onChange={(e) => setEnsembleMode(e.target.value)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <label htmlFor="ensemble-parallel" className="ml-2 block text-sm text-gray-700">
                  Parallel Ensemble (All models, consensus decision)
                </label>
              </div>
            </div>
            <p className="mt-2 text-xs text-gray-500">
              Staggered: Fast, stops early on high confidence. Parallel: More accurate, uses all models.
            </p>
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
                  if (!ensembleMode) {
                    setEnsembleMode('parallel')
                  }
                }
              }}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="useAllModels" className="ml-2 block text-sm text-gray-700">
              Use All Models (Forces Parallel Ensemble)
            </label>
          </div>

          {/* Similarity Threshold */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Similarity Threshold: {similarityThreshold.toFixed(2)}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={similarityThreshold}
              onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0.0 (More matches)</span>
              <span>1.0 (Strict matches)</span>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Minimum similarity score required for a match. Lower values = more matches, higher values = stricter matches.
            </p>
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
                            <div className="mt-1">
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-sm font-medium text-gray-700">Confidence:</span>
                                <span className="text-sm font-semibold text-gray-900">
                                  {Math.round((result.confidence || result.similarity || 0) * 100)}%
                                </span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2.5">
                                <div
                                  className={`h-2.5 rounded-full transition-all ${
                                    (result.confidence || result.similarity || 0) >= 0.8
                                      ? 'bg-green-500'
                                      : (result.confidence || result.similarity || 0) >= 0.6
                                      ? 'bg-yellow-500'
                                      : 'bg-red-500'
                                  }`}
                                  style={{
                                    width: `${Math.round((result.confidence || result.similarity || 0) * 100)}%`
                                  }}
                                />
                              </div>
                            </div>
                            {result.model_path && Array.isArray(result.model_path) && result.model_path.length > 0 && (
                              <div className="mt-2">
                                <p className="text-xs font-medium text-gray-700">Models Used:</p>
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {result.model_path.map((model: string, idx: number) => (
                                    <Badge key={idx} variant="info" className="text-xs">
                                      {getModelInfo(model).name || model}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                            {result.model && !result.model_path && (
                              <p className="text-xs text-gray-500 mt-1">Model: {getModelInfo(result.model).name || result.model}</p>
                            )}
                            {result.matches && Array.isArray(result.matches) && result.matches.length > 0 && (
                              <div className="mt-2 space-y-2">
                                <p className="text-xs font-medium text-gray-700">Top Matches:</p>
                                {result.matches.slice(0, 3).map((match: any, idx: number) => {
                                  const similarity = match.similarity || 0
                                  return (
                                    <div key={idx} className="space-y-1">
                                      <div className="flex items-center justify-between">
                                        <span className="text-xs text-gray-700 font-medium">
                                          {match.tiger_name || match.tiger_id}
                                        </span>
                                        <span className="text-xs font-semibold text-gray-900">
                                          {Math.round(similarity * 100)}%
                                        </span>
                                      </div>
                                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                                        <div
                                          className={`h-1.5 rounded-full transition-all ${
                                            similarity >= 0.8
                                              ? 'bg-green-500'
                                              : similarity >= 0.6
                                              ? 'bg-yellow-500'
                                              : 'bg-red-500'
                                          }`}
                                          style={{ width: `${Math.round(similarity * 100)}%` }}
                                        />
                                      </div>
                                    </div>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        ) : (
                          <div>
                            <p className="text-sm text-gray-700">
                              {result.message || 'Tiger not found in database'}
                            </p>
                            {result.model_path && Array.isArray(result.model_path) && result.model_path.length > 0 && (
                              <div className="mt-2">
                                <p className="text-xs font-medium text-gray-700">Models Checked:</p>
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {result.model_path.map((model: string, idx: number) => (
                                    <Badge key={idx} variant="warning" className="text-xs">
                                      {getModelInfo(model).name || model}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
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

      {/* Registration Modal */}
      <Modal
        isOpen={showRegistrationModal}
        onClose={handleCloseRegistrationModal}
        title="Register New Tiger"
        size="lg"
      >
        <div className="space-y-6">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tiger Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={registrationName}
              onChange={(e) => setRegistrationName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter tiger name"
              required
            />
          </div>

          {/* Alias */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Alias (Optional)
            </label>
            <input
              type="text"
              value={registrationAlias}
              onChange={(e) => setRegistrationAlias(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter alias or identifier"
            />
          </div>

          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Model for Embedding Generation (Optional)
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Use Default Model</option>
              {modelNames.map((modelName) => (
                <option key={modelName} value={modelName}>
                  {modelName}
                </option>
              ))}
            </select>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Notes (Optional)
            </label>
            <textarea
              value={registrationNotes}
              onChange={(e) => setRegistrationNotes(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
              placeholder="Additional notes about this tiger"
            />
          </div>

          {/* Image Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tiger Images <span className="text-red-500">*</span>
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
                      onChange={handleRegistrationFileSelect}
                    />
                  </label>
                  <p className="pl-1">or drag and drop</p>
                </div>
                <p className="text-xs text-gray-500">PNG, JPG, GIF up to 10MB each</p>
              </div>
            </div>
          </div>

          {/* Selected Files */}
          {registrationFiles.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Selected Files ({registrationFiles.length})
              </label>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {registrationFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded-md"
                  >
                    <span className="text-sm text-gray-700 truncate flex-1">
                      {file.name}
                    </span>
                    <button
                      onClick={() => handleRemoveRegistrationFile(index)}
                      className="ml-2 text-red-600 hover:text-red-800"
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2">
            <Button
              variant="primary"
              onClick={handleRegisterTiger}
              disabled={isRegistering || !registrationName.trim() || registrationFiles.length === 0}
              className="flex-1"
            >
              {isRegistering ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Registering...
                </>
              ) : (
                'Register Tiger'
              )}
            </Button>
            <Button variant="secondary" onClick={handleCloseRegistrationModal}>
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default Tigers

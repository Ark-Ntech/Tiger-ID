import { useState, useCallback } from 'react'
import { useTestModelMutation, useGetModelsAvailableQuery } from '../app/api'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Alert from '../components/common/Alert'
import Badge from '../components/common/Badge'
import { PhotoIcon, XMarkIcon, CheckCircleIcon } from '@heroicons/react/24/outline'

interface TestResult {
  filename: string
  success: boolean
  embedding_shape?: number[]
  error?: string
}

const ModelTesting = () => {
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [testResults, setTestResults] = useState<TestResult[]>([])
  const [isTesting, setIsTesting] = useState(false)

  const { data: modelsData, isLoading: modelsLoading } = useGetModelsAvailableQuery()
  const [testModel, { isLoading: testLoading }] = useTestModelMutation()

  const availableModels = modelsData?.data?.models || {}
  const modelNames = Object.keys(availableModels)

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    setSelectedFiles((prev) => [...prev, ...files])
  }, [])

  const handleRemoveFile = useCallback((index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const handleTest = async () => {
    if (!selectedModel || selectedFiles.length === 0) {
      return
    }

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
      setTestResults([{
        filename: 'Validation Error',
        success: false,
        error: `Invalid files: ${invalidFiles.join('; ')}`
      }])
      return
    }

    if (selectedFiles.length > 20) {
      setTestResults([{
        filename: 'Validation Error',
        success: false,
        error: 'Maximum 20 images per test request'
      }])
      return
    }

    setIsTesting(true)
    setTestResults([])

    try {
      const formData = new FormData()
      selectedFiles.forEach((file) => {
        formData.append('images', file)
      })
      formData.append('model_name', selectedModel)

      const result = await testModel(formData).unwrap()
      setTestResults(result.data?.results || [])
    } catch (error: any) {
      console.error('Error testing model:', error)
      const errorMessage = error?.data?.detail || error?.data?.message || 'Failed to test model'
      setTestResults([
        {
          filename: 'Error',
          success: false,
          error: errorMessage,
        },
      ])
    } finally {
      setIsTesting(false)
    }
  }

  const handleClear = () => {
    setSelectedFiles([])
    setTestResults([])
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Model Testing</h1>
        <p className="text-gray-600 mt-2">Test RE-ID models on tiger images</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration Card */}
        <Card>
          <h2 className="text-xl font-semibold mb-4">Configuration</h2>

          <div className="space-y-4">
            {/* Model Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Model
              </label>
              {modelsLoading ? (
                <LoadingSpinner size="sm" />
              ) : (
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select a model...</option>
                  {modelNames.map((modelName) => (
                    <option key={modelName} value={modelName}>
                      {modelName}
                    </option>
                  ))}
                </select>
              )}
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

            {/* Actions */}
            <div className="flex gap-2">
              <Button
                variant="primary"
                onClick={handleTest}
                disabled={!selectedModel || selectedFiles.length === 0 || isTesting}
                className="flex-1"
              >
                {isTesting || testLoading ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Testing...
                  </>
                ) : (
                  'Run Test'
                )}
              </Button>
              <Button variant="secondary" onClick={handleClear} disabled={isTesting}>
                Clear
              </Button>
            </div>
          </div>
        </Card>

        {/* Results Card */}
        <Card>
          <h2 className="text-xl font-semibold mb-4">Test Results</h2>

          {testResults.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <PhotoIcon className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>No test results yet. Upload images and run a test.</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {testResults.map((result, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-lg border ${
                    result.success
                      ? 'bg-green-50 border-green-200'
                      : 'bg-red-50 border-red-200'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {result.success ? (
                          <CheckCircleIcon className="h-5 w-5 text-green-600" />
                        ) : (
                          <XMarkIcon className="h-5 w-5 text-red-600" />
                        )}
                        <span className="font-medium text-gray-900">{result.filename}</span>
                        <Badge variant={result.success ? 'success' : 'error'}>
                          {result.success ? 'Success' : 'Failed'}
                        </Badge>
                      </div>
                      {result.success && result.embedding_shape && (
                        <p className="text-sm text-gray-600">
                          Embedding shape: [{result.embedding_shape.join(', ')}]
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
          )}

          {testResults.length > 0 && (
            <div className="mt-4 pt-4 border-t">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">
                  Total: {testResults.length} images
                </span>
                <span className="text-gray-600">
                  Successful:{' '}
                  {testResults.filter((r) => r.success).length}
                </span>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}

export default ModelTesting


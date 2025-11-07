import { useState, useCallback } from 'react'
import { useTestModelMutation, useGetModelsAvailableQuery } from '../../app/api'
import Card from '../common/Card'
import Button from '../common/Button'
import LoadingSpinner from '../common/LoadingSpinner'
import Alert from '../common/Alert'
import Badge from '../common/Badge'
import { PhotoIcon, XMarkIcon, CheckCircleIcon } from '@heroicons/react/24/outline'

interface TestResult {
  filename: string
  success: boolean
  embedding_shape?: number[]
  error?: string
}

const ModelTestingTab = () => {
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
        <h2 className="text-2xl font-bold text-gray-900">Model Testing</h2>
        <p className="text-gray-600 mt-2">Test RE-ID models with tiger images</p>
      </div>

      <Card>
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
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
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:border-primary-500 transition-colors">
              <div className="space-y-1 text-center">
                <PhotoIcon className="mx-auto h-12 w-12 text-gray-400" />
                <div className="flex text-sm text-gray-600">
                  <label
                    htmlFor="file-upload"
                    className="relative cursor-pointer bg-white rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
                  >
                    <span>Upload files</span>
                    <input
                      id="file-upload"
                      name="file-upload"
                      type="file"
                      multiple
                      accept="image/*"
                      className="sr-only"
                      onChange={handleFileSelect}
                    />
                  </label>
                  <p className="pl-1">or drag and drop</p>
                </div>
                <p className="text-xs text-gray-500">PNG, JPG, GIF up to 10MB each (max 20 files)</p>
              </div>
            </div>
          </div>

          {/* Selected Files */}
          {selectedFiles.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Selected Files ({selectedFiles.length})
              </label>
              <div className="space-y-2">
                {selectedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-2">
                      <PhotoIcon className="h-5 w-5 text-gray-400" />
                      <span className="text-sm text-gray-700">{file.name}</span>
                      <span className="text-xs text-gray-500">
                        ({(file.size / 1024 / 1024).toFixed(2)} MB)
                      </span>
                    </div>
                    <button
                      onClick={() => handleRemoveFile(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center space-x-2">
            <Button
              variant="primary"
              onClick={handleTest}
              disabled={!selectedModel || selectedFiles.length === 0 || isTesting || testLoading}
              isLoading={isTesting || testLoading}
            >
              {isTesting || testLoading ? 'Testing...' : 'Test Model'}
            </Button>
            {selectedFiles.length > 0 && (
              <Button variant="outline" onClick={handleClear}>
                Clear
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Test Results */}
      {testResults.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Results</h3>
          <div className="space-y-3">
            {testResults.map((result, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg ${
                  result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {result.success ? (
                      <CheckCircleIcon className="h-5 w-5 text-green-600" />
                    ) : (
                      <XMarkIcon className="h-5 w-5 text-red-600" />
                    )}
                    <span className="font-medium text-gray-900">{result.filename}</span>
                    {result.success && (
                      <Badge variant="success">Success</Badge>
                    )}
                    {!result.success && (
                      <Badge variant="error">Failed</Badge>
                    )}
                  </div>
                </div>
                {result.embedding_shape && (
                  <p className="text-sm text-gray-600 mt-2">
                    Embedding shape: [{result.embedding_shape.join(', ')}]
                  </p>
                )}
                {result.error && (
                  <p className="text-sm text-red-600 mt-2">{result.error}</p>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

export default ModelTestingTab


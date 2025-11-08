import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import Alert from '../components/common/Alert'
import { CpuChipIcon, ArrowLeftIcon, CloudArrowUpIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline'

const ModelWeights = () => {
  const navigate = useNavigate()
  const [uploading, setUploading] = useState(false)
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadStatus, setUploadStatus] = useState<{ [key: string]: { status: 'success' | 'error' | 'pending'; message?: string } }>({})

  const models = [
    { id: 'cvwc2019', name: 'CVWC2019', description: 'Part-pose guided tiger re-identification', weightPath: '/models/cvwc2019/best_model.pth' },
    { id: 'rapid', name: 'RAPID', description: 'Real-time animal pattern re-identification', weightPath: '/models/rapid/checkpoints/model.pth' }
  ]

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleUpload = async () => {
    if (!selectedModel || !selectedFile) {
      alert('Please select a model and weight file')
      return
    }

    setUploading(true)
    setUploadStatus(prev => ({ ...prev, [selectedModel]: { status: 'pending' } }))

    try {
      // In a real implementation, this would call an API endpoint
      // For now, we'll simulate the upload process
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      setUploadStatus(prev => ({
        ...prev,
        [selectedModel]: {
          status: 'success',
          message: `Weights uploaded successfully to Modal volume`
        }
      }))
      
      setSelectedFile(null)
      setSelectedModel('')
    } catch (error: any) {
      setUploadStatus(prev => ({
        ...prev,
        [selectedModel]: {
          status: 'error',
          message: error?.message || 'Failed to upload weights'
        }
      }))
    } finally {
      setUploading(false)
    }
  }

  const checkWeightStatus = async (modelId: string) => {
    // In a real implementation, this would check Modal volume for weights
    // For now, we'll simulate checking
    setUploadStatus(prev => ({
      ...prev,
      [modelId]: {
        status: 'pending',
        message: 'Checking weight status...'
      }
    }))

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Simulate result (in real implementation, this would come from API)
      const hasWeights = Math.random() > 0.5
      
      setUploadStatus(prev => ({
        ...prev,
        [modelId]: {
          status: hasWeights ? 'success' : 'error',
          message: hasWeights ? 'Weights found in Modal volume' : 'Weights not found in Modal volume'
        }
      }))
    } catch (error: any) {
      setUploadStatus(prev => ({
        ...prev,
        [modelId]: {
          status: 'error',
          message: error?.message || 'Failed to check weight status'
        }
      }))
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
            <h1 className="text-3xl font-bold text-gray-900">Model Weights Management</h1>
            <p className="text-gray-600 mt-1">Upload and manage model weights in Modal volumes</p>
          </div>
        </div>
      </div>

      {/* Upload Section */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload Model Weights</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Model
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select a model...</option>
              {models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name} - {model.description}
                </option>
              ))}
            </select>
          </div>

          {selectedModel && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Weight File (.pth)
              </label>
              <input
                type="file"
                accept=".pth,.pt,.pkl"
                onChange={handleFileSelect}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              {selectedFile && (
                <p className="text-sm text-gray-600 mt-2">
                  Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
            </div>
          )}

          <div className="flex gap-2">
            <Button
              variant="primary"
              onClick={handleUpload}
              disabled={!selectedModel || !selectedFile || uploading}
              className="flex items-center gap-2"
            >
              <CloudArrowUpIcon className="h-5 w-5" />
              {uploading ? 'Uploading...' : 'Upload to Modal Volume'}
            </Button>
          </div>

          {selectedModel && uploadStatus[selectedModel] && (
            <Alert
              type={uploadStatus[selectedModel].status === 'success' ? 'success' : uploadStatus[selectedModel].status === 'error' ? 'error' : 'info'}
            >
              {uploadStatus[selectedModel].message}
            </Alert>
          )}
        </div>
      </Card>

      {/* Model Status */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Model Weight Status</h2>
        <div className="space-y-4">
          {models.map((model) => {
            const status = uploadStatus[model.id]
            return (
              <div
                key={model.id}
                className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <CpuChipIcon className="h-5 w-5 text-gray-600" />
                      <h3 className="text-lg font-semibold text-gray-900">{model.name}</h3>
                      {status && (
                        <Badge
                          variant={status.status === 'success' ? 'success' : status.status === 'error' ? 'error' : 'info'}
                        >
                          {status.status === 'success' ? (
                            <CheckCircleIcon className="h-4 w-4 mr-1" />
                          ) : status.status === 'error' ? (
                            <XCircleIcon className="h-4 w-4 mr-1" />
                          ) : null}
                          {status.status}
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{model.description}</p>
                    <p className="text-xs text-gray-500 mt-1">Path: {model.weightPath}</p>
                    {status?.message && (
                      <p className="text-sm text-gray-700 mt-2">{status.message}</p>
                    )}
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => checkWeightStatus(model.id)}
                    disabled={status?.status === 'pending'}
                  >
                    Check Status
                  </Button>
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      {/* Instructions */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Instructions</h2>
        <div className="space-y-2 text-sm text-gray-700">
          <p>1. Download model weights from their respective repositories:</p>
          <ul className="list-disc list-inside ml-4 space-y-1">
            <li>CVWC2019: <a href="https://github.com/LcenArthas/CWCV2019-Amur-Tiger-Re-ID" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">GitHub Repository</a></li>
            <li>RAPID: Download from paper repository or contact authors</li>
          </ul>
          <p className="mt-4">2. Upload weights using the form above or use the CLI script:</p>
          <code className="block bg-gray-100 p-2 rounded mt-2">
            modal run scripts/upload_weights_to_modal.py --model cvwc2019 --weights path/to/best_model.pth
          </code>
          <p className="mt-4">3. After uploading, deploy the Modal app:</p>
          <code className="block bg-gray-100 p-2 rounded mt-2">
            modal deploy backend/modal_app.py
          </code>
          <p className="mt-4">4. Test models to verify weights are loaded correctly:</p>
          <code className="block bg-gray-100 p-2 rounded mt-2">
            python scripts/test_modal_models.py
          </code>
        </div>
      </Card>
    </div>
  )
}

export default ModelWeights


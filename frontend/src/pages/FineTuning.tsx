import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import Alert from '../components/common/Alert'
import Modal from '../components/common/Modal'
import { CpuChipIcon, ArrowLeftIcon, PlayIcon, StopIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline'

// Mock API hooks - these would be replaced with actual RTK Query hooks
const useFineTuningJobs = () => {
  const [jobs, setJobs] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  
  const fetchJobs = async () => {
    setIsLoading(true)
    try {
      // In real implementation, this would call the API
      const response = await fetch('/api/v1/finetuning/jobs')
      const data = await response.json()
      setJobs(data.data?.jobs || [])
    } catch (error) {
      console.error('Error fetching jobs:', error)
    } finally {
      setIsLoading(false)
    }
  }
  
  useEffect(() => {
    fetchJobs()
  }, [])
  
  return { jobs, isLoading, refetch: fetchJobs }
}

const useAvailableTigers = () => {
  const [tigers, setTigers] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  
  const fetchTigers = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/v1/finetuning/available-tigers?min_images=5')
      const data = await response.json()
      setTigers(data.data || [])
    } catch (error) {
      console.error('Error fetching tigers:', error)
    } finally {
      setIsLoading(false)
    }
  }
  
  useEffect(() => {
    fetchTigers()
  }, [])
  
  return { tigers, isLoading, refetch: fetchTigers }
}

const FineTuning = () => {
  const navigate = useNavigate()
  const [showStartModal, setShowStartModal] = useState(false)
  const [selectedModel, setSelectedModel] = useState<string>('tiger_reid')
  const [selectedTigers, setSelectedTigers] = useState<Set<string>>(new Set())
  const [epochs, setEpochs] = useState<number>(50)
  const [batchSize, setBatchSize] = useState<number>(32)
  const [learningRate, setLearningRate] = useState<number>(0.001)
  const [validationSplit, setValidationSplit] = useState<number>(0.2)
  const [lossFunction, setLossFunction] = useState<string>('triplet')
  const [description, setDescription] = useState<string>('')
  const [isStarting, setIsStarting] = useState(false)

  const { jobs, isLoading: jobsLoading, refetch: refetchJobs } = useFineTuningJobs()
  const { tigers, isLoading: tigersLoading } = useAvailableTigers()

  const models = [
    { id: 'tiger_reid', name: 'Tiger ReID', description: 'Tiger-specific stripe specialist model' },
    { id: 'wildlife_tools', name: 'Wildlife Tools', description: 'General wildlife RE-ID model' },
    { id: 'cvwc2019', name: 'CVWC2019', description: 'Part-pose guided tiger re-identification' },
    { id: 'rapid', name: 'RAPID', description: 'Real-time animal pattern re-identification' }
  ]

  const lossFunctions = [
    { id: 'triplet', name: 'Triplet Loss', description: 'Standard triplet loss for metric learning' },
    { id: 'contrastive', name: 'Contrastive Loss', description: 'Contrastive loss for pair-based learning' },
    { id: 'softmax', name: 'Softmax Cross-Entropy', description: 'Classification-based loss' }
  ]

  const handleStartJob = async () => {
    if (selectedTigers.size === 0) {
      alert('Please select at least one tiger for training')
      return
    }

    setIsStarting(true)
    try {
      const response = await fetch('/api/v1/finetuning/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          model_name: selectedModel,
          tiger_ids: Array.from(selectedTigers),
          epochs,
          batch_size: batchSize,
          learning_rate: learningRate,
          validation_split: validationSplit,
          loss_function: lossFunction,
          description
        })
      })

      if (!response.ok) {
        throw new Error('Failed to start fine-tuning job')
      }

      const data = await response.json()
      alert(`Fine-tuning job started! Job ID: ${data.data?.job_id}`)
      setShowStartModal(false)
      refetchJobs()
    } catch (error: any) {
      alert(`Failed to start job: ${error.message}`)
    } finally {
      setIsStarting(false)
    }
  }

  const handleCancelJob = async (jobId: string) => {
    if (!confirm('Are you sure you want to cancel this job?')) return

    try {
      const response = await fetch(`/api/v1/finetuning/jobs/${jobId}/cancel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to cancel job')
      }

      refetchJobs()
    } catch (error: any) {
      alert(`Failed to cancel job: ${error.message}`)
    }
  }

  const toggleTiger = (tigerId: string) => {
    setSelectedTigers(prev => {
      const next = new Set(prev)
      if (next.has(tigerId)) {
        next.delete(tigerId)
      } else {
        next.add(tigerId)
      }
      return next
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'failed':
        return 'error'
      case 'cancelled':
        return 'warning'
      case 'training':
      case 'preparing':
        return 'info'
      default:
        return 'info'
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
            <h1 className="text-3xl font-bold text-gray-900">Model Fine-Tuning</h1>
            <p className="text-gray-600 mt-1">Fine-tune models with selected tiger images</p>
          </div>
        </div>
        <Button
          variant="primary"
          onClick={() => setShowStartModal(true)}
          className="flex items-center gap-2"
        >
          <PlayIcon className="h-5 w-5" />
          Start Fine-Tuning Job
        </Button>
      </div>

      {/* Jobs List */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Fine-Tuning Jobs</h2>
        {jobsLoading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <CpuChipIcon className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p>No fine-tuning jobs yet</p>
            <p className="text-sm mt-2">Start a new job to begin fine-tuning models</p>
          </div>
        ) : (
          <div className="space-y-4">
            {jobs.map((job: any) => (
              <div
                key={job.job_id}
                className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{job.model_name}</h3>
                      <Badge variant={getStatusColor(job.status)}>
                        {job.status}
                      </Badge>
                      {job.progress > 0 && (
                        <span className="text-sm text-gray-600">
                          {Math.round(job.progress * 100)}%
                        </span>
                      )}
                    </div>
                    {job.description && (
                      <p className="text-sm text-gray-600 mb-2">{job.description}</p>
                    )}
                    <div className="flex gap-4 text-sm text-gray-600">
                      <span>Epochs: {job.current_epoch} / {job.epochs}</span>
                      {job.loss && <span>Loss: {job.loss.toFixed(4)}</span>}
                      {job.validation_loss && <span>Val Loss: {job.validation_loss.toFixed(4)}</span>}
                      {job.created_at && (
                        <span>Started: {new Date(job.created_at).toLocaleString()}</span>
                      )}
                    </div>
                    {job.status === 'training' && (
                      <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all"
                          style={{ width: `${job.progress * 100}%` }}
                        />
                      </div>
                    )}
                  </div>
                  {job.status === 'training' || job.status === 'preparing' ? (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleCancelJob(job.job_id)}
                      className="flex items-center gap-2"
                    >
                      <StopIcon className="h-4 w-4" />
                      Cancel
                    </Button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Start Job Modal */}
      <Modal
        isOpen={showStartModal}
        onClose={() => setShowStartModal(false)}
        title="Start Fine-Tuning Job"
        size="lg"
      >
        <div className="space-y-6">
          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Model
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name} - {model.description}
                </option>
              ))}
            </select>
          </div>

          {/* Tiger Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Tigers for Training ({selectedTigers.size} selected)
            </label>
            {tigersLoading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <div className="max-h-60 overflow-y-auto border border-gray-300 rounded-md p-2 space-y-2">
                {tigers.map((tiger: any) => (
                  <div
                    key={tiger.tiger_id}
                    className={`p-2 rounded cursor-pointer transition-colors ${
                      selectedTigers.has(tiger.tiger_id)
                        ? 'bg-blue-50 border border-blue-200'
                        : 'hover:bg-gray-50 border border-transparent'
                    }`}
                    onClick={() => toggleTiger(tiger.tiger_id)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900">{tiger.name || `Tiger #${tiger.tiger_id.substring(0, 8)}`}</p>
                        <p className="text-sm text-gray-600">{tiger.image_count} images</p>
                      </div>
                      {selectedTigers.has(tiger.tiger_id) && (
                        <CheckCircleIcon className="h-5 w-5 text-blue-600" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <p className="text-xs text-gray-500 mt-2">
              Select tigers with at least 5 images for training
            </p>
          </div>

          {/* Training Parameters */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Epochs
              </label>
              <input
                type="number"
                min="1"
                max="1000"
                value={epochs}
                onChange={(e) => setEpochs(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Batch Size
              </label>
              <input
                type="number"
                min="1"
                max="128"
                value={batchSize}
                onChange={(e) => setBatchSize(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Learning Rate
              </label>
              <input
                type="number"
                min="0.0001"
                max="0.1"
                step="0.0001"
                value={learningRate}
                onChange={(e) => setLearningRate(parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Validation Split
              </label>
              <input
                type="number"
                min="0.1"
                max="0.5"
                step="0.05"
                value={validationSplit}
                onChange={(e) => setValidationSplit(parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Loss Function */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Loss Function
            </label>
            <select
              value={lossFunction}
              onChange={(e) => setLossFunction(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {lossFunctions.map((loss) => (
                <option key={loss.id} value={loss.id}>
                  {loss.name} - {loss.description}
                </option>
              ))}
            </select>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (Optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
              placeholder="Describe this fine-tuning run..."
            />
          </div>

          {/* Actions */}
          <div className="flex gap-2 justify-end">
            <Button
              variant="secondary"
              onClick={() => setShowStartModal(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleStartJob}
              disabled={isStarting || selectedTigers.size === 0}
              className="flex items-center gap-2"
            >
              {isStarting ? (
                <>
                  <LoadingSpinner size="sm" />
                  Starting...
                </>
              ) : (
                <>
                  <PlayIcon className="h-5 w-5" />
                  Start Job
                </>
              )}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default FineTuning


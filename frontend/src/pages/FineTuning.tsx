import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Card, { CardHeader, CardTitle, CardDescription } from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import Modal from '../components/common/Modal'
import { cn } from '../utils/cn'
import {
  CpuChipIcon,
  ArrowLeftIcon,
  PlayIcon,
  StopIcon,
  CheckCircleIcon,
  BoltIcon,
  BeakerIcon,
  ChartBarIcon,
  InformationCircleIcon,
  ClockIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FineTunableModel {
  id: string
  name: string
  description: string
  embeddingDim: number
  weight: number
  supportedLibraries: string[]
  supportsUnsloth: boolean
  estimatedTime: string
  color: string
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const FINE_TUNABLE_MODELS: FineTunableModel[] = [
  {
    id: 'wildlife_tools',
    name: 'Wildlife Tools',
    description: 'General wildlife re-identification model -- the highest-weighted model in the ensemble.',
    embeddingDim: 1536,
    weight: 0.40,
    supportedLibraries: ['PyTorch', 'Unsloth', 'LoRA (PEFT)'],
    supportsUnsloth: true,
    estimatedTime: '~2h on A100',
    color: 'emerald',
  },
  {
    id: 'cvwc2019_reid',
    name: 'CVWC2019 ReID',
    description: 'Part-pose guided model trained on the CVWC 2019 Amur Tiger dataset.',
    embeddingDim: 2048,
    weight: 0.30,
    supportedLibraries: ['PyTorch', 'Unsloth', 'LoRA (PEFT)'],
    supportsUnsloth: true,
    estimatedTime: '~3h on A100',
    color: 'blue',
  },
  {
    id: 'transreid',
    name: 'TransReID',
    description: 'Transformer-based backbone with jigsaw patch augmentation for fine-grained stripe features.',
    embeddingDim: 768,
    weight: 0.20,
    supportedLibraries: ['PyTorch', 'LoRA (PEFT)', 'Hugging Face Trainer'],
    supportsUnsloth: false,
    estimatedTime: '~1.5h on A100',
    color: 'purple',
  },
  {
    id: 'megadescriptor_b',
    name: 'MegaDescriptor-B',
    description: 'Large-scale animal descriptor providing robust cross-species embeddings.',
    embeddingDim: 1024,
    weight: 0.15,
    supportedLibraries: ['PyTorch', 'Unsloth', 'LoRA (PEFT)'],
    supportsUnsloth: true,
    estimatedTime: '~2.5h on A100',
    color: 'cyan',
  },
  {
    id: 'tiger_reid',
    name: 'Tiger ReID',
    description: 'Tiger-specific stripe specialist model, best candidate for domain-specific fine-tuning.',
    embeddingDim: 2048,
    weight: 0.10,
    supportedLibraries: ['PyTorch', 'Unsloth', 'LoRA (PEFT)', 'Hugging Face Trainer'],
    supportsUnsloth: true,
    estimatedTime: '~2h on A100',
    color: 'orange',
  },
  {
    id: 'rapid_reid',
    name: 'RAPID ReID',
    description: 'Lightweight real-time model -- fast to fine-tune with minimal compute.',
    embeddingDim: 2048,
    weight: 0.05,
    supportedLibraries: ['PyTorch', 'LoRA (PEFT)'],
    supportsUnsloth: false,
    estimatedTime: '~45m on A100',
    color: 'amber',
  },
]

const LOSS_FUNCTIONS = [
  { id: 'triplet', name: 'Triplet Loss', description: 'Standard triplet loss for metric learning with hard mining' },
  { id: 'arcface', name: 'ArcFace Loss', description: 'Additive angular margin loss for discriminative embeddings' },
  { id: 'contrastive', name: 'Contrastive Loss', description: 'Contrastive loss for pair-based similarity learning' },
  { id: 'softmax', name: 'Softmax Cross-Entropy', description: 'Classification-based loss with label smoothing' },
  { id: 'circle', name: 'Circle Loss', description: 'Unified loss for pair and class-level supervision' },
]

const FINE_TUNING_STRATEGIES = [
  {
    id: 'full',
    name: 'Full Fine-Tuning',
    description: 'Update all model parameters. Highest quality but requires more data and compute.',
    badge: 'danger' as const,
    badgeLabel: 'Full GPU',
  },
  {
    id: 'lora',
    name: 'LoRA (Low-Rank Adaptation)',
    description: 'Add low-rank adapters to attention layers. Efficient with ~1% trainable parameters.',
    badge: 'success' as const,
    badgeLabel: 'Efficient',
  },
  {
    id: 'unsloth',
    name: 'Unsloth Accelerated',
    description: 'Unsloth-optimized LoRA fine-tuning with 2x speed and 60% less memory usage.',
    badge: 'tiger' as const,
    badgeLabel: 'Recommended',
  },
  {
    id: 'head_only',
    name: 'Head Only',
    description: 'Freeze backbone, train only the classification/embedding head. Fastest but least flexible.',
    badge: 'info' as const,
    badgeLabel: 'Fastest',
  },
]

// ---------------------------------------------------------------------------
// Colour helpers
// ---------------------------------------------------------------------------

const colorMap: Record<string, { bg: string; text: string }> = {
  emerald: { bg: 'bg-emerald-100 dark:bg-emerald-900/30', text: 'text-emerald-700 dark:text-emerald-300' },
  blue: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-300' },
  purple: { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-700 dark:text-purple-300' },
  cyan: { bg: 'bg-cyan-100 dark:bg-cyan-900/30', text: 'text-cyan-700 dark:text-cyan-300' },
  orange: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-300' },
  amber: { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-300' },
}

// ---------------------------------------------------------------------------
// Hooks (mock API)
// ---------------------------------------------------------------------------

const useFineTuningJobs = () => {
  const [jobs, setJobs] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const fetchJobs = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/v1/finetuning/jobs', {
        headers: { 'Authorization': `Bearer ${token}` },
      })
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
      const token = localStorage.getItem('token')
      const response = await fetch('/api/v1/finetuning/available-tigers?min_images=5', {
        headers: { 'Authorization': `Bearer ${token}` },
      })
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

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const FineTuning = () => {
  const navigate = useNavigate()
  const [showStartModal, setShowStartModal] = useState(false)

  // Form state
  const [selectedModel, setSelectedModel] = useState<string>('wildlife_tools')
  const [selectedStrategy, setSelectedStrategy] = useState<string>('unsloth')
  const [selectedTigers, setSelectedTigers] = useState<Set<string>>(new Set())
  const [epochs, setEpochs] = useState<number>(50)
  const [batchSize, setBatchSize] = useState<number>(32)
  const [learningRate, setLearningRate] = useState<number>(0.0003)
  const [validationSplit, setValidationSplit] = useState<number>(0.2)
  const [lossFunction, setLossFunction] = useState<string>('triplet')
  const [loraRank, setLoraRank] = useState<number>(16)
  const [description, setDescription] = useState<string>('')
  const [isStarting, setIsStarting] = useState(false)

  const { jobs, isLoading: jobsLoading, refetch: refetchJobs } = useFineTuningJobs()
  const { tigers, isLoading: tigersLoading } = useAvailableTigers()

  // Derived
  const selectedModelInfo = FINE_TUNABLE_MODELS.find((m) => m.id === selectedModel)
  const selectedStrategyInfo = FINE_TUNING_STRATEGIES.find((s) => s.id === selectedStrategy)

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------

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
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          model_name: selectedModel,
          strategy: selectedStrategy,
          tiger_ids: Array.from(selectedTigers),
          epochs,
          batch_size: batchSize,
          learning_rate: learningRate,
          validation_split: validationSplit,
          loss_function: lossFunction,
          lora_rank: selectedStrategy === 'lora' || selectedStrategy === 'unsloth' ? loraRank : undefined,
          description,
        }),
      })

      if (!response.ok) throw new Error('Failed to start fine-tuning job')

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
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
      })
      if (!response.ok) throw new Error('Failed to cancel job')
      refetchJobs()
    } catch (error: any) {
      alert(`Failed to cancel job: ${error.message}`)
    }
  }

  const toggleTiger = (tigerId: string) => {
    setSelectedTigers((prev) => {
      const next = new Set(prev)
      if (next.has(tigerId)) next.delete(tigerId)
      else next.add(tigerId)
      return next
    })
  }

  const getStatusBadge = (status: string) => {
    const map: Record<string, { variant: any; label: string }> = {
      completed: { variant: 'success', label: 'Completed' },
      failed: { variant: 'error', label: 'Failed' },
      cancelled: { variant: 'warning', label: 'Cancelled' },
      training: { variant: 'info', label: 'Training' },
      preparing: { variant: 'default', label: 'Preparing' },
      queued: { variant: 'default', label: 'Queued' },
    }
    const cfg = map[status] || map.queued
    return <Badge variant={cfg.variant} size="sm" dot>{cfg.label}</Badge>
  }

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/dashboard')} className="flex items-center gap-2">
            <ArrowLeftIcon className="h-5 w-5" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-tactical-900 dark:text-tactical-100">Model Fine-Tuning</h1>
            <p className="text-tactical-500 dark:text-tactical-400 mt-1">
              Fine-tune ensemble models on your tiger dataset with modern training strategies
            </p>
          </div>
        </div>
        <Button variant="primary" onClick={() => setShowStartModal(true)} className="flex items-center gap-2">
          <PlayIcon className="h-5 w-5" />
          New Fine-Tuning Job
        </Button>
      </div>

      {/* Available Models Grid */}
      <Card>
        <CardHeader>
          <CardTitle as="h2">
            <CpuChipIcon className="h-5 w-5 inline-block mr-2 text-tiger-orange" />
            Fine-Tunable Models
          </CardTitle>
          <CardDescription>
            All 6 ensemble models support fine-tuning. Models with higher ensemble weights benefit most from domain adaptation.
          </CardDescription>
        </CardHeader>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {FINE_TUNABLE_MODELS.map((model) => {
            const colors = colorMap[model.color]
            return (
              <div
                key={model.id}
                className={cn(
                  'rounded-xl border p-4 transition-all duration-200',
                  'border-tactical-200 dark:border-tactical-700',
                  'hover:border-tactical-300 dark:hover:border-tactical-600 hover:shadow-sm'
                )}
              >
                <div className="flex items-start gap-3 mb-3">
                  <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center shrink-0', colors.bg)}>
                    <CpuChipIcon className={cn('h-4 w-4', colors.text)} />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-sm text-tactical-900 dark:text-tactical-100">{model.name}</h3>
                      <Badge variant={model.color as any} size="xs">
                        {(model.weight * 100).toFixed(0)}%
                      </Badge>
                    </div>
                    <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-0.5 line-clamp-2">
                      {model.description}
                    </p>
                  </div>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-tactical-500 dark:text-tactical-400">Embedding</span>
                    <span className="font-mono font-medium text-tactical-700 dark:text-tactical-300">
                      {model.embeddingDim}d
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-tactical-500 dark:text-tactical-400">Est. Time</span>
                    <span className="font-medium text-tactical-700 dark:text-tactical-300">{model.estimatedTime}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-tactical-500 dark:text-tactical-400">Unsloth</span>
                    {model.supportsUnsloth ? (
                      <Badge variant="success" size="xs">Supported</Badge>
                    ) : (
                      <Badge variant="default" size="xs">Not Available</Badge>
                    )}
                  </div>
                  <div className="pt-1">
                    <div className="flex flex-wrap gap-1">
                      {model.supportedLibraries.map((lib) => (
                        <Badge key={lib} variant="outline" size="xs">
                          {lib}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      {/* Fine-Tuning Strategies */}
      <Card>
        <CardHeader>
          <CardTitle as="h2">
            <BoltIcon className="h-5 w-5 inline-block mr-2 text-tiger-orange" />
            Fine-Tuning Strategies
          </CardTitle>
          <CardDescription>
            Choose how parameters are updated during training. Unsloth-accelerated LoRA is recommended for most use cases.
          </CardDescription>
        </CardHeader>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {FINE_TUNING_STRATEGIES.map((strategy) => (
            <div
              key={strategy.id}
              className={cn(
                'rounded-xl border p-4 transition-all duration-200',
                'border-tactical-200 dark:border-tactical-700'
              )}
            >
              <div className="flex items-center gap-2 mb-2">
                <h3 className="font-semibold text-sm text-tactical-900 dark:text-tactical-100">{strategy.name}</h3>
                <Badge variant={strategy.badge} size="xs">{strategy.badgeLabel}</Badge>
              </div>
              <p className="text-xs text-tactical-500 dark:text-tactical-400 leading-relaxed">
                {strategy.description}
              </p>
            </div>
          ))}
        </div>
      </Card>

      {/* Jobs List */}
      <Card>
        <CardHeader
          action={
            <Button variant="ghost" size="sm" onClick={() => refetchJobs()} className="flex items-center gap-1.5">
              <ArrowPathIcon className="h-4 w-4" />
              Refresh
            </Button>
          }
        >
          <CardTitle as="h2">
            <ChartBarIcon className="h-5 w-5 inline-block mr-2 text-tiger-orange" />
            Fine-Tuning Jobs
          </CardTitle>
          <CardDescription>Track active and completed training runs</CardDescription>
        </CardHeader>

        {jobsLoading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-12">
            <BeakerIcon className="h-12 w-12 mx-auto mb-4 text-tactical-300 dark:text-tactical-600" />
            <p className="text-tactical-500 dark:text-tactical-400 font-medium">No fine-tuning jobs yet</p>
            <p className="text-sm text-tactical-400 dark:text-tactical-500 mt-1">
              Start a new job to begin adapting models to your tiger dataset
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowStartModal(true)}
              className="mt-4 flex items-center gap-2 mx-auto"
            >
              <PlayIcon className="h-4 w-4" />
              Start First Job
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {jobs.map((job: any) => (
              <div
                key={job.job_id}
                className={cn(
                  'rounded-xl border p-4 transition-all duration-200',
                  'border-tactical-200 dark:border-tactical-700',
                  'hover:border-tactical-300 dark:hover:border-tactical-600'
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2 flex-wrap">
                      <h3 className="font-semibold text-tactical-900 dark:text-tactical-100">{job.model_name}</h3>
                      {getStatusBadge(job.status)}
                      {job.progress > 0 && (
                        <span className="text-sm text-tactical-600 dark:text-tactical-400">
                          {Math.round(job.progress * 100)}%
                        </span>
                      )}
                    </div>
                    {job.description && (
                      <p className="text-sm text-tactical-500 dark:text-tactical-400 mb-2">{job.description}</p>
                    )}
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-tactical-600 dark:text-tactical-400">
                      <span>
                        Epochs: {job.current_epoch || 0} / {job.epochs}
                      </span>
                      {job.loss != null && <span>Loss: {job.loss.toFixed(4)}</span>}
                      {job.validation_loss != null && <span>Val Loss: {job.validation_loss.toFixed(4)}</span>}
                      {job.created_at && (
                        <span className="flex items-center gap-1">
                          <ClockIcon className="h-3.5 w-3.5" />
                          {new Date(job.created_at).toLocaleString()}
                        </span>
                      )}
                    </div>
                    {job.status === 'training' && (
                      <div className="mt-3 w-full bg-tactical-100 dark:bg-tactical-800 rounded-full h-2">
                        <div
                          className="bg-tiger-orange h-2 rounded-full transition-all duration-500"
                          style={{ width: `${job.progress * 100}%` }}
                        />
                      </div>
                    )}
                  </div>
                  {(job.status === 'training' || job.status === 'preparing') && (
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleCancelJob(job.job_id)}
                      className="flex items-center gap-1.5 ml-4 shrink-0"
                    >
                      <StopIcon className="h-4 w-4" />
                      Cancel
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Start Job Modal */}
      <Modal isOpen={showStartModal} onClose={() => setShowStartModal(false)} title="Start Fine-Tuning Job" size="xl">
        <div className="space-y-6">
          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-tactical-700 dark:text-tactical-300 mb-2">
              Select Model
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className={cn(
                'w-full px-3 py-2 rounded-lg border transition-colors',
                'bg-white dark:bg-tactical-800',
                'border-tactical-300 dark:border-tactical-600',
                'text-tactical-900 dark:text-tactical-100',
                'focus:outline-none focus:ring-2 focus:ring-tiger-orange/50 focus:border-tiger-orange'
              )}
            >
              {FINE_TUNABLE_MODELS.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name} ({(model.weight * 100).toFixed(0)}% weight) -- {model.description.slice(0, 50)}
                </option>
              ))}
            </select>
            {selectedModelInfo && (
              <div className="mt-2 flex flex-wrap gap-2">
                <Badge variant="info" size="xs">{selectedModelInfo.embeddingDim}d embedding</Badge>
                <Badge variant="default" size="xs">{selectedModelInfo.estimatedTime}</Badge>
                {selectedModelInfo.supportsUnsloth && (
                  <Badge variant="success" size="xs">Unsloth supported</Badge>
                )}
              </div>
            )}
          </div>

          {/* Strategy Selection */}
          <div>
            <label className="block text-sm font-medium text-tactical-700 dark:text-tactical-300 mb-2">
              Fine-Tuning Strategy
            </label>
            <div className="grid grid-cols-2 gap-2">
              {FINE_TUNING_STRATEGIES.map((strategy) => {
                const isActive = selectedStrategy === strategy.id
                const isDisabled =
                  strategy.id === 'unsloth' && selectedModelInfo && !selectedModelInfo.supportsUnsloth
                return (
                  <button
                    key={strategy.id}
                    onClick={() => !isDisabled && setSelectedStrategy(strategy.id)}
                    disabled={!!isDisabled}
                    className={cn(
                      'p-3 rounded-lg border-2 text-left transition-all duration-200 text-sm',
                      isDisabled && 'opacity-40 cursor-not-allowed',
                      isActive
                        ? 'border-tiger-orange bg-tiger-orange/5 dark:bg-tiger-orange/10'
                        : 'border-tactical-200 dark:border-tactical-700 hover:border-tactical-300 dark:hover:border-tactical-600'
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-tactical-900 dark:text-tactical-100">{strategy.name}</span>
                      <Badge variant={strategy.badge} size="xs">{strategy.badgeLabel}</Badge>
                    </div>
                    <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-1">{strategy.description}</p>
                  </button>
                )
              })}
            </div>
          </div>

          {/* LoRA Rank (conditional) */}
          {(selectedStrategy === 'lora' || selectedStrategy === 'unsloth') && (
            <div>
              <label className="block text-sm font-medium text-tactical-700 dark:text-tactical-300 mb-2">
                LoRA Rank
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="4"
                  max="64"
                  step="4"
                  value={loraRank}
                  onChange={(e) => setLoraRank(parseInt(e.target.value))}
                  className="flex-1 accent-tiger-orange"
                />
                <span className="w-12 text-center font-mono font-semibold text-tactical-900 dark:text-tactical-100">
                  {loraRank}
                </span>
              </div>
              <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-1">
                Higher rank = more parameters, more expressive but slower. 16 is a good default.
              </p>
            </div>
          )}

          {/* Tiger Selection */}
          <div>
            <label className="block text-sm font-medium text-tactical-700 dark:text-tactical-300 mb-2">
              Select Tigers for Training ({selectedTigers.size} selected)
            </label>
            {tigersLoading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <div
                className={cn(
                  'max-h-48 overflow-y-auto rounded-lg border p-2 space-y-1',
                  'border-tactical-300 dark:border-tactical-600'
                )}
              >
                {tigers.length === 0 ? (
                  <p className="text-sm text-tactical-500 dark:text-tactical-400 text-center py-4">
                    No tigers with sufficient images found. Add images via Dataset Management.
                  </p>
                ) : (
                  tigers.map((tiger: any) => (
                    <div
                      key={tiger.tiger_id}
                      className={cn(
                        'p-2 rounded-lg cursor-pointer transition-colors',
                        selectedTigers.has(tiger.tiger_id)
                          ? 'bg-tiger-orange/10 border border-tiger-orange/30'
                          : 'hover:bg-tactical-50 dark:hover:bg-tactical-800 border border-transparent'
                      )}
                      onClick={() => toggleTiger(tiger.tiger_id)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-sm text-tactical-900 dark:text-tactical-100">
                            {tiger.name || `Tiger #${tiger.tiger_id.substring(0, 8)}`}
                          </p>
                          <p className="text-xs text-tactical-500 dark:text-tactical-400">{tiger.image_count} images</p>
                        </div>
                        {selectedTigers.has(tiger.tiger_id) && (
                          <CheckCircleIcon className="h-5 w-5 text-tiger-orange" />
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
            <p className="text-xs text-tactical-400 dark:text-tactical-500 mt-1">
              Tigers with 5+ images recommended for training quality
            </p>
          </div>

          {/* Training Parameters */}
          <div>
            <label className="block text-sm font-medium text-tactical-700 dark:text-tactical-300 mb-3">
              Training Parameters
            </label>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-tactical-500 dark:text-tactical-400 mb-1">Epochs</label>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={epochs}
                  onChange={(e) => setEpochs(parseInt(e.target.value))}
                  className={cn(
                    'w-full px-3 py-2 rounded-lg border text-sm',
                    'bg-white dark:bg-tactical-800',
                    'border-tactical-300 dark:border-tactical-600',
                    'text-tactical-900 dark:text-tactical-100',
                    'focus:outline-none focus:ring-2 focus:ring-tiger-orange/50 focus:border-tiger-orange'
                  )}
                />
              </div>
              <div>
                <label className="block text-xs text-tactical-500 dark:text-tactical-400 mb-1">Batch Size</label>
                <input
                  type="number"
                  min="1"
                  max="128"
                  value={batchSize}
                  onChange={(e) => setBatchSize(parseInt(e.target.value))}
                  className={cn(
                    'w-full px-3 py-2 rounded-lg border text-sm',
                    'bg-white dark:bg-tactical-800',
                    'border-tactical-300 dark:border-tactical-600',
                    'text-tactical-900 dark:text-tactical-100',
                    'focus:outline-none focus:ring-2 focus:ring-tiger-orange/50 focus:border-tiger-orange'
                  )}
                />
              </div>
              <div>
                <label className="block text-xs text-tactical-500 dark:text-tactical-400 mb-1">Learning Rate</label>
                <input
                  type="number"
                  min="0.00001"
                  max="0.1"
                  step="0.00001"
                  value={learningRate}
                  onChange={(e) => setLearningRate(parseFloat(e.target.value))}
                  className={cn(
                    'w-full px-3 py-2 rounded-lg border text-sm',
                    'bg-white dark:bg-tactical-800',
                    'border-tactical-300 dark:border-tactical-600',
                    'text-tactical-900 dark:text-tactical-100',
                    'focus:outline-none focus:ring-2 focus:ring-tiger-orange/50 focus:border-tiger-orange'
                  )}
                />
              </div>
              <div>
                <label className="block text-xs text-tactical-500 dark:text-tactical-400 mb-1">Validation Split</label>
                <input
                  type="number"
                  min="0.1"
                  max="0.5"
                  step="0.05"
                  value={validationSplit}
                  onChange={(e) => setValidationSplit(parseFloat(e.target.value))}
                  className={cn(
                    'w-full px-3 py-2 rounded-lg border text-sm',
                    'bg-white dark:bg-tactical-800',
                    'border-tactical-300 dark:border-tactical-600',
                    'text-tactical-900 dark:text-tactical-100',
                    'focus:outline-none focus:ring-2 focus:ring-tiger-orange/50 focus:border-tiger-orange'
                  )}
                />
              </div>
            </div>
          </div>

          {/* Loss Function */}
          <div>
            <label className="block text-sm font-medium text-tactical-700 dark:text-tactical-300 mb-2">
              Loss Function
            </label>
            <select
              value={lossFunction}
              onChange={(e) => setLossFunction(e.target.value)}
              className={cn(
                'w-full px-3 py-2 rounded-lg border transition-colors text-sm',
                'bg-white dark:bg-tactical-800',
                'border-tactical-300 dark:border-tactical-600',
                'text-tactical-900 dark:text-tactical-100',
                'focus:outline-none focus:ring-2 focus:ring-tiger-orange/50 focus:border-tiger-orange'
              )}
            >
              {LOSS_FUNCTIONS.map((loss) => (
                <option key={loss.id} value={loss.id}>
                  {loss.name} -- {loss.description}
                </option>
              ))}
            </select>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-tactical-700 dark:text-tactical-300 mb-2">
              Description (Optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className={cn(
                'w-full px-3 py-2 rounded-lg border transition-colors text-sm',
                'bg-white dark:bg-tactical-800',
                'border-tactical-300 dark:border-tactical-600',
                'text-tactical-900 dark:text-tactical-100',
                'focus:outline-none focus:ring-2 focus:ring-tiger-orange/50 focus:border-tiger-orange'
              )}
              rows={2}
              placeholder="Describe this fine-tuning run..."
            />
          </div>

          {/* Info banner */}
          {selectedModelInfo && selectedStrategyInfo && (
            <div className="bg-tactical-50 dark:bg-tactical-800/50 rounded-lg p-3 flex items-start gap-2">
              <InformationCircleIcon className="h-5 w-5 text-tiger-orange shrink-0 mt-0.5" />
              <div className="text-xs text-tactical-600 dark:text-tactical-400">
                <strong className="text-tactical-800 dark:text-tactical-200">Summary:</strong> Fine-tuning{' '}
                <strong>{selectedModelInfo.name}</strong> with{' '}
                <strong>{selectedStrategyInfo.name}</strong> strategy on{' '}
                {selectedTigers.size} tiger(s) for {epochs} epochs. Estimated time: {selectedModelInfo.estimatedTime}.
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 justify-end pt-2">
            <Button variant="secondary" onClick={() => setShowStartModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleStartJob}
              disabled={isStarting || selectedTigers.size === 0}
              isLoading={isStarting}
              className="flex items-center gap-2"
            >
              <PlayIcon className="h-5 w-5" />
              Start Job
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default FineTuning

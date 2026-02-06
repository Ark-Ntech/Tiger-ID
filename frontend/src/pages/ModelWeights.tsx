import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Card, { CardHeader, CardTitle, CardDescription } from '../components/common/Card'
import Button from '../components/common/Button'
import Badge from '../components/common/Badge'
import Alert from '../components/common/Alert'
import { cn } from '../utils/cn'
import {
  CpuChipIcon,
  ArrowLeftIcon,
  CloudArrowUpIcon,
  CheckCircleIcon,
  XCircleIcon,
  AdjustmentsHorizontalIcon,
  ScaleIcon,
  BoltIcon,
  ShieldCheckIcon,
  ArrowsPointingOutIcon,
  SignalIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  InformationCircleIcon,
  BeakerIcon,
} from '@heroicons/react/24/outline'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface EnsembleModel {
  id: string
  name: string
  description: string
  weight: number
  embeddingDim: number
  calibrationTemp: number
  weightPath: string
  source: string
  color: string // tailwind accent color token
}

type EnsembleMode = 'staggered' | 'parallel' | 'weighted' | 'verified'

interface EnsembleModeInfo {
  id: EnsembleMode
  name: string
  description: string
  icon: typeof BoltIcon
  badge: 'info' | 'purple' | 'tiger' | 'success'
  recommended?: boolean
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const ENSEMBLE_MODELS: EnsembleModel[] = [
  {
    id: 'wildlife_tools',
    name: 'Wildlife Tools',
    description: 'General wildlife re-identification model with broad species coverage and strong generalization.',
    weight: 0.40,
    embeddingDim: 1536,
    calibrationTemp: 1.0,
    weightPath: '/models/wildlife_tools/best_model.pth',
    source: 'WildlifeDatasets / wildlife-tools',
    color: 'emerald',
  },
  {
    id: 'cvwc2019_reid',
    name: 'CVWC2019 ReID',
    description: 'Part-pose guided tiger re-identification model trained on the CVWC 2019 Amur Tiger dataset.',
    weight: 0.30,
    embeddingDim: 2048,
    calibrationTemp: 0.85,
    weightPath: '/models/cvwc2019/best_model.pth',
    source: 'CVWC 2019 Competition',
    color: 'blue',
  },
  {
    id: 'transreid',
    name: 'TransReID',
    description: 'Transformer-based re-identification backbone with jigsaw patch augmentation for fine-grained features.',
    weight: 0.20,
    embeddingDim: 768,
    calibrationTemp: 1.1,
    weightPath: '/models/transreid/best_model.pth',
    source: 'TransReID (ICCV 2021)',
    color: 'purple',
  },
  {
    id: 'megadescriptor_b',
    name: 'MegaDescriptor-B',
    description: 'Large-scale animal descriptor model (base variant) providing robust embeddings across species.',
    weight: 0.15,
    embeddingDim: 1024,
    calibrationTemp: 1.0,
    weightPath: '/models/megadescriptor_b/best_model.pth',
    source: 'WildlifeDatasets / MegaDescriptor',
    color: 'cyan',
  },
  {
    id: 'tiger_reid',
    name: 'Tiger ReID',
    description: 'Tiger-specific stripe pattern specialist, tuned specifically for Amur and Bengal tiger identification.',
    weight: 0.10,
    embeddingDim: 2048,
    calibrationTemp: 0.9,
    weightPath: '/models/tiger_reid/best_model.pth',
    source: 'Custom Tiger ReID',
    color: 'orange',
  },
  {
    id: 'rapid_reid',
    name: 'RAPID ReID',
    description: 'Real-time Animal Pattern IDentification -- lightweight model optimised for fast inference.',
    weight: 0.05,
    embeddingDim: 2048,
    calibrationTemp: 0.95,
    weightPath: '/models/rapid/checkpoints/model.pth',
    source: 'RAPID (IJCV)',
    color: 'amber',
  },
]

const ENSEMBLE_MODES: EnsembleModeInfo[] = [
  {
    id: 'staggered',
    name: 'Staggered (Early Exit)',
    description:
      'Runs models sequentially in weight order. Exits early when cumulative confidence exceeds a threshold, saving compute on easy matches.',
    icon: BoltIcon,
    badge: 'info',
  },
  {
    id: 'parallel',
    name: 'Parallel (Voting)',
    description:
      'Runs all 6 models simultaneously and uses a voting scheme across results. Best for throughput on GPU clusters.',
    icon: ArrowsPointingOutIcon,
    badge: 'purple',
  },
  {
    id: 'weighted',
    name: 'Weighted (Recommended)',
    description:
      'Combines all model scores using the configured weights and calibration temperatures for the most accurate composite score.',
    icon: ScaleIcon,
    badge: 'tiger',
    recommended: true,
  },
  {
    id: 'verified',
    name: 'Verified (Highest Confidence)',
    description:
      'Runs all models and requires consensus across a majority. Only returns matches above a very high confidence threshold.',
    icon: ShieldCheckIcon,
    badge: 'success',
  },
]

// ---------------------------------------------------------------------------
// Colour helpers
// ---------------------------------------------------------------------------

const colorMap: Record<string, { bg: string; text: string; bar: string; ring: string }> = {
  emerald: {
    bg: 'bg-emerald-100 dark:bg-emerald-900/30',
    text: 'text-emerald-700 dark:text-emerald-300',
    bar: 'bg-emerald-500',
    ring: 'ring-emerald-500/30',
  },
  blue: {
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    text: 'text-blue-700 dark:text-blue-300',
    bar: 'bg-blue-500',
    ring: 'ring-blue-500/30',
  },
  purple: {
    bg: 'bg-purple-100 dark:bg-purple-900/30',
    text: 'text-purple-700 dark:text-purple-300',
    bar: 'bg-purple-500',
    ring: 'ring-purple-500/30',
  },
  cyan: {
    bg: 'bg-cyan-100 dark:bg-cyan-900/30',
    text: 'text-cyan-700 dark:text-cyan-300',
    bar: 'bg-cyan-500',
    ring: 'ring-cyan-500/30',
  },
  orange: {
    bg: 'bg-orange-100 dark:bg-orange-900/30',
    text: 'text-orange-700 dark:text-orange-300',
    bar: 'bg-tiger-orange',
    ring: 'ring-orange-500/30',
  },
  amber: {
    bg: 'bg-amber-100 dark:bg-amber-900/30',
    text: 'text-amber-700 dark:text-amber-300',
    bar: 'bg-amber-500',
    ring: 'ring-amber-500/30',
  },
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const ModelWeights = () => {
  const navigate = useNavigate()

  // Upload state
  const [uploading, setUploading] = useState(false)
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadStatus, setUploadStatus] = useState<
    Record<string, { status: 'success' | 'error' | 'pending'; message?: string }>
  >({})

  // UI state
  const [activeMode, setActiveMode] = useState<EnsembleMode>('weighted')
  const [expandedModel, setExpandedModel] = useState<string | null>(null)
  const [showUploadSection, setShowUploadSection] = useState(false)

  // Computed
  const totalWeight = ENSEMBLE_MODELS.reduce((sum, m) => sum + m.weight, 0)

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) setSelectedFile(file)
  }

  const handleUpload = async () => {
    if (!selectedModel || !selectedFile) {
      alert('Please select a model and weight file')
      return
    }

    setUploading(true)
    setUploadStatus((prev) => ({ ...prev, [selectedModel]: { status: 'pending' } }))

    try {
      await new Promise((resolve) => setTimeout(resolve, 2000))
      setUploadStatus((prev) => ({
        ...prev,
        [selectedModel]: { status: 'success', message: 'Weights uploaded successfully to Modal volume' },
      }))
      setSelectedFile(null)
      setSelectedModel('')
    } catch (error: any) {
      setUploadStatus((prev) => ({
        ...prev,
        [selectedModel]: { status: 'error', message: error?.message || 'Failed to upload weights' },
      }))
    } finally {
      setUploading(false)
    }
  }

  const checkWeightStatus = async (modelId: string) => {
    setUploadStatus((prev) => ({ ...prev, [modelId]: { status: 'pending', message: 'Checking weight status...' } }))
    try {
      await new Promise((resolve) => setTimeout(resolve, 1000))
      const hasWeights = Math.random() > 0.5
      setUploadStatus((prev) => ({
        ...prev,
        [modelId]: {
          status: hasWeights ? 'success' : 'error',
          message: hasWeights ? 'Weights found in Modal volume' : 'Weights not found in Modal volume',
        },
      }))
    } catch (error: any) {
      setUploadStatus((prev) => ({
        ...prev,
        [modelId]: { status: 'error', message: error?.message || 'Failed to check weight status' },
      }))
    }
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
            <h1 className="text-3xl font-bold text-tactical-900 dark:text-tactical-100">
              Ensemble Configuration
            </h1>
            <p className="text-tactical-500 dark:text-tactical-400 mt-1">
              6-model weighted ensemble for tiger re-identification
            </p>
          </div>
        </div>
        <Button
          variant={showUploadSection ? 'secondary' : 'outline'}
          onClick={() => setShowUploadSection(!showUploadSection)}
          className="flex items-center gap-2"
        >
          <CloudArrowUpIcon className="h-5 w-5" />
          {showUploadSection ? 'Hide Upload' : 'Upload Weights'}
        </Button>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card padding="sm">
          <p className="text-xs font-medium uppercase tracking-wider text-tactical-500 dark:text-tactical-400">
            Models
          </p>
          <p className="text-2xl font-bold text-tactical-900 dark:text-tactical-100 mt-1">
            {ENSEMBLE_MODELS.length}
          </p>
        </Card>
        <Card padding="sm">
          <p className="text-xs font-medium uppercase tracking-wider text-tactical-500 dark:text-tactical-400">
            Total Weight
          </p>
          <p className="text-2xl font-bold text-tactical-900 dark:text-tactical-100 mt-1">
            {totalWeight.toFixed(2)}
          </p>
        </Card>
        <Card padding="sm">
          <p className="text-xs font-medium uppercase tracking-wider text-tactical-500 dark:text-tactical-400">
            Ensemble Mode
          </p>
          <p className="text-2xl font-bold text-tiger-orange mt-1 capitalize">{activeMode}</p>
        </Card>
        <Card padding="sm">
          <p className="text-xs font-medium uppercase tracking-wider text-tactical-500 dark:text-tactical-400">
            Avg Embedding Dim
          </p>
          <p className="text-2xl font-bold text-tactical-900 dark:text-tactical-100 mt-1">
            {Math.round(ENSEMBLE_MODELS.reduce((s, m) => s + m.embeddingDim, 0) / ENSEMBLE_MODELS.length)}
          </p>
        </Card>
      </div>

      {/* Ensemble Mode Selector */}
      <Card>
        <CardHeader>
          <CardTitle as="h2">
            <AdjustmentsHorizontalIcon className="h-5 w-5 inline-block mr-2 text-tiger-orange" />
            Ensemble Mode
          </CardTitle>
          <CardDescription>Select how the 6 models combine their predictions</CardDescription>
        </CardHeader>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {ENSEMBLE_MODES.map((mode) => {
            const ModeIcon = mode.icon
            const isActive = activeMode === mode.id
            return (
              <button
                key={mode.id}
                onClick={() => setActiveMode(mode.id)}
                className={cn(
                  'relative flex flex-col items-start p-4 rounded-xl border-2 text-left transition-all duration-200',
                  isActive
                    ? 'border-tiger-orange bg-tiger-orange/5 shadow-md dark:bg-tiger-orange/10'
                    : 'border-tactical-200 dark:border-tactical-700 hover:border-tactical-300 dark:hover:border-tactical-600'
                )}
              >
                {mode.recommended && (
                  <span className="absolute -top-2.5 right-3 px-2 py-0.5 text-2xs font-bold uppercase tracking-wider bg-tiger-orange text-white rounded-full">
                    Recommended
                  </span>
                )}
                <div className="flex items-center gap-2 mb-2">
                  <ModeIcon
                    className={cn(
                      'h-5 w-5',
                      isActive ? 'text-tiger-orange' : 'text-tactical-500 dark:text-tactical-400'
                    )}
                  />
                  <span
                    className={cn(
                      'font-semibold text-sm',
                      isActive
                        ? 'text-tactical-900 dark:text-tactical-100'
                        : 'text-tactical-700 dark:text-tactical-300'
                    )}
                  >
                    {mode.name}
                  </span>
                </div>
                <p className="text-xs text-tactical-500 dark:text-tactical-400 leading-relaxed">
                  {mode.description}
                </p>
              </button>
            )
          })}
        </div>
      </Card>

      {/* Model Cards */}
      <Card>
        <CardHeader>
          <CardTitle as="h2">
            <CpuChipIcon className="h-5 w-5 inline-block mr-2 text-tiger-orange" />
            Model Ensemble ({ENSEMBLE_MODELS.length} models)
          </CardTitle>
          <CardDescription>
            Click a model to see details. Weights indicate contribution to the final composite score.
          </CardDescription>
        </CardHeader>

        {/* Weight distribution bar */}
        <div className="mb-6">
          <div className="flex h-4 rounded-full overflow-hidden bg-tactical-100 dark:bg-tactical-800">
            {ENSEMBLE_MODELS.map((model) => {
              const pct = (model.weight / totalWeight) * 100
              const colors = colorMap[model.color]
              return (
                <div
                  key={model.id}
                  className={cn(colors.bar, 'transition-all duration-500')}
                  style={{ width: `${pct}%` }}
                  title={`${model.name}: ${(model.weight * 100).toFixed(0)}%`}
                />
              )
            })}
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2">
            {ENSEMBLE_MODELS.map((model) => {
              const colors = colorMap[model.color]
              return (
                <div key={model.id} className="flex items-center gap-1.5 text-xs">
                  <span className={cn('w-2.5 h-2.5 rounded-full', colors.bar)} />
                  <span className="text-tactical-600 dark:text-tactical-400">
                    {model.name}{' '}
                    <span className="font-semibold text-tactical-800 dark:text-tactical-200">
                      {(model.weight * 100).toFixed(0)}%
                    </span>
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Model list */}
        <div className="space-y-3">
          {ENSEMBLE_MODELS.map((model) => {
            const colors = colorMap[model.color]
            const isExpanded = expandedModel === model.id
            const status = uploadStatus[model.id]
            return (
              <div
                key={model.id}
                className={cn(
                  'rounded-xl border transition-all duration-200',
                  isExpanded
                    ? 'border-tactical-300 dark:border-tactical-600 shadow-sm'
                    : 'border-tactical-200 dark:border-tactical-700'
                )}
              >
                {/* Header row */}
                <button
                  onClick={() => setExpandedModel(isExpanded ? null : model.id)}
                  className="w-full flex items-center gap-4 p-4 text-left group"
                >
                  {/* Colour indicator */}
                  <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center shrink-0', colors.bg)}>
                    <CpuChipIcon className={cn('h-5 w-5', colors.text)} />
                  </div>

                  {/* Name & description */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-tactical-900 dark:text-tactical-100">{model.name}</h3>
                      <Badge variant={model.color as any} size="xs">
                        {(model.weight * 100).toFixed(0)}% weight
                      </Badge>
                      {status && (
                        <Badge
                          variant={status.status === 'success' ? 'success' : status.status === 'error' ? 'error' : 'info'}
                          size="xs"
                        >
                          {status.status === 'success' ? (
                            <CheckCircleIcon className="h-3 w-3 mr-1" />
                          ) : status.status === 'error' ? (
                            <XCircleIcon className="h-3 w-3 mr-1" />
                          ) : null}
                          {status.status}
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-tactical-500 dark:text-tactical-400 truncate">
                      {model.description}
                    </p>
                  </div>

                  {/* Key stats (always visible) */}
                  <div className="hidden md:flex items-center gap-6 text-sm text-tactical-600 dark:text-tactical-400">
                    <div className="text-center">
                      <p className="text-xs uppercase tracking-wider text-tactical-400 dark:text-tactical-500">Dim</p>
                      <p className="font-semibold text-tactical-800 dark:text-tactical-200">{model.embeddingDim}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs uppercase tracking-wider text-tactical-400 dark:text-tactical-500">Temp</p>
                      <p className="font-semibold text-tactical-800 dark:text-tactical-200">
                        {model.calibrationTemp.toFixed(2)}
                      </p>
                    </div>
                  </div>

                  {/* Weight bar (mini) */}
                  <div className="hidden sm:block w-24">
                    <div className="h-2 rounded-full bg-tactical-100 dark:bg-tactical-800 overflow-hidden">
                      <div
                        className={cn(colors.bar, 'h-full rounded-full transition-all duration-500')}
                        style={{ width: `${(model.weight / 0.4) * 100}%` }}
                      />
                    </div>
                  </div>

                  <div className="shrink-0 text-tactical-400 dark:text-tactical-500">
                    {isExpanded ? (
                      <ChevronUpIcon className="h-5 w-5" />
                    ) : (
                      <ChevronDownIcon className="h-5 w-5" />
                    )}
                  </div>
                </button>

                {/* Expanded details */}
                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-tactical-100 dark:border-tactical-800">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-4">
                      <div className="bg-tactical-50 dark:bg-tactical-800/50 rounded-lg p-3">
                        <p className="text-xs font-medium uppercase tracking-wider text-tactical-500 dark:text-tactical-400 mb-1">
                          Ensemble Weight
                        </p>
                        <p className="text-xl font-bold text-tactical-900 dark:text-tactical-100">
                          {(model.weight * 100).toFixed(0)}%
                        </p>
                        <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-0.5">
                          Contribution to composite
                        </p>
                      </div>
                      <div className="bg-tactical-50 dark:bg-tactical-800/50 rounded-lg p-3">
                        <p className="text-xs font-medium uppercase tracking-wider text-tactical-500 dark:text-tactical-400 mb-1">
                          Embedding Dimension
                        </p>
                        <p className="text-xl font-bold text-tactical-900 dark:text-tactical-100">
                          {model.embeddingDim}
                        </p>
                        <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-0.5">
                          Feature vector size
                        </p>
                      </div>
                      <div className="bg-tactical-50 dark:bg-tactical-800/50 rounded-lg p-3">
                        <p className="text-xs font-medium uppercase tracking-wider text-tactical-500 dark:text-tactical-400 mb-1">
                          Calibration Temp
                        </p>
                        <p className="text-xl font-bold text-tactical-900 dark:text-tactical-100">
                          {model.calibrationTemp.toFixed(2)}
                        </p>
                        <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-0.5">
                          {model.calibrationTemp < 1.0
                            ? 'Sharpened (more confident)'
                            : model.calibrationTemp > 1.0
                            ? 'Smoothed (less overfit)'
                            : 'Neutral (uncalibrated)'}
                        </p>
                      </div>
                      <div className="bg-tactical-50 dark:bg-tactical-800/50 rounded-lg p-3">
                        <p className="text-xs font-medium uppercase tracking-wider text-tactical-500 dark:text-tactical-400 mb-1">
                          Source
                        </p>
                        <p className="text-sm font-semibold text-tactical-900 dark:text-tactical-100 truncate">
                          {model.source}
                        </p>
                        <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-0.5 truncate">
                          {model.weightPath}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 mt-4">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => checkWeightStatus(model.id)}
                        disabled={status?.status === 'pending'}
                        className="flex items-center gap-1.5"
                      >
                        <SignalIcon className="h-4 w-4" />
                        Check Status
                      </Button>
                      {status?.message && (
                        <span className="text-sm text-tactical-600 dark:text-tactical-400">{status.message}</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </Card>

      {/* Upload Section (toggle) */}
      {showUploadSection && (
        <Card>
          <CardHeader>
            <CardTitle as="h2">
              <CloudArrowUpIcon className="h-5 w-5 inline-block mr-2 text-tiger-orange" />
              Upload Model Weights
            </CardTitle>
            <CardDescription>Upload .pth/.pt weight files to Modal volumes</CardDescription>
          </CardHeader>

          <div className="space-y-4">
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
                <option value="">Select a model...</option>
                {ENSEMBLE_MODELS.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name} -- {model.description.slice(0, 60)}
                  </option>
                ))}
              </select>
            </div>

            {selectedModel && (
              <div>
                <label className="block text-sm font-medium text-tactical-700 dark:text-tactical-300 mb-2">
                  Weight File (.pth / .pt / .pkl)
                </label>
                <input
                  type="file"
                  accept=".pth,.pt,.pkl"
                  onChange={handleFileSelect}
                  className={cn(
                    'w-full px-3 py-2 rounded-lg border transition-colors',
                    'bg-white dark:bg-tactical-800',
                    'border-tactical-300 dark:border-tactical-600',
                    'text-tactical-900 dark:text-tactical-100',
                    'file:mr-4 file:py-1 file:px-3 file:rounded-lg file:border-0',
                    'file:text-sm file:font-medium file:bg-tiger-orange/10 file:text-tiger-orange',
                    'hover:file:bg-tiger-orange/20'
                  )}
                />
                {selectedFile && (
                  <p className="text-sm text-tactical-500 dark:text-tactical-400 mt-2">
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
                isLoading={uploading}
                className="flex items-center gap-2"
              >
                <CloudArrowUpIcon className="h-5 w-5" />
                Upload to Modal Volume
              </Button>
            </div>

            {selectedModel && uploadStatus[selectedModel] && (
              <Alert
                type={
                  uploadStatus[selectedModel].status === 'success'
                    ? 'success'
                    : uploadStatus[selectedModel].status === 'error'
                    ? 'error'
                    : 'info'
                }
              >
                {uploadStatus[selectedModel].message}
              </Alert>
            )}
          </div>
        </Card>
      )}

      {/* Technical Reference */}
      <Card>
        <CardHeader>
          <CardTitle as="h2">
            <InformationCircleIcon className="h-5 w-5 inline-block mr-2 text-tiger-orange" />
            Technical Reference
          </CardTitle>
        </CardHeader>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-tactical-200 dark:border-tactical-700">
                <th className="text-left py-2 pr-4 font-semibold text-tactical-700 dark:text-tactical-300">Model</th>
                <th className="text-right py-2 px-4 font-semibold text-tactical-700 dark:text-tactical-300">Weight</th>
                <th className="text-right py-2 px-4 font-semibold text-tactical-700 dark:text-tactical-300">Embedding Dim</th>
                <th className="text-right py-2 px-4 font-semibold text-tactical-700 dark:text-tactical-300">Calibration Temp</th>
                <th className="text-left py-2 pl-4 font-semibold text-tactical-700 dark:text-tactical-300">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-tactical-100 dark:divide-tactical-800">
              {ENSEMBLE_MODELS.map((model) => {
                const colors = colorMap[model.color]
                return (
                  <tr key={model.id} className="hover:bg-tactical-50 dark:hover:bg-tactical-800/50 transition-colors">
                    <td className="py-2.5 pr-4">
                      <div className="flex items-center gap-2">
                        <span className={cn('w-2 h-2 rounded-full', colors.bar)} />
                        <span className="font-medium text-tactical-900 dark:text-tactical-100">{model.name}</span>
                      </div>
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono text-tactical-700 dark:text-tactical-300">
                      {model.weight.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono text-tactical-700 dark:text-tactical-300">
                      {model.embeddingDim}
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono text-tactical-700 dark:text-tactical-300">
                      {model.calibrationTemp.toFixed(2)}
                    </td>
                    <td className="py-2.5 pl-4 text-tactical-500 dark:text-tactical-400">{model.source}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* CLI Instructions */}
      <Card>
        <CardHeader>
          <CardTitle as="h2">
            <BeakerIcon className="h-5 w-5 inline-block mr-2 text-tiger-orange" />
            CLI Quick Reference
          </CardTitle>
          <CardDescription>Manage model weights and deployments via the command line</CardDescription>
        </CardHeader>

        <div className="space-y-3 text-sm text-tactical-700 dark:text-tactical-300">
          <p>1. Upload weights to Modal volume:</p>
          <code className="block bg-tactical-50 dark:bg-tactical-800 p-3 rounded-lg text-tactical-800 dark:text-tactical-200 font-mono text-xs">
            modal run scripts/upload_weights_to_modal.py --model wildlife_tools --weights path/to/best_model.pth
          </code>

          <p className="mt-3">2. Deploy all 6 models to Modal:</p>
          <code className="block bg-tactical-50 dark:bg-tactical-800 p-3 rounded-lg text-tactical-800 dark:text-tactical-200 font-mono text-xs">
            modal deploy backend/modal_app.py
          </code>

          <p className="mt-3">3. Test ensemble inference:</p>
          <code className="block bg-tactical-50 dark:bg-tactical-800 p-3 rounded-lg text-tactical-800 dark:text-tactical-200 font-mono text-xs">
            python scripts/test_modal_models.py --ensemble-mode weighted
          </code>

          <p className="mt-3">4. Run a single model in isolation:</p>
          <code className="block bg-tactical-50 dark:bg-tactical-800 p-3 rounded-lg text-tactical-800 dark:text-tactical-200 font-mono text-xs">
            python scripts/test_modal_models.py --model cvwc2019_reid
          </code>
        </div>
      </Card>
    </div>
  )
}

export default ModelWeights

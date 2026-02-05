import { useState, useCallback, useMemo, useEffect } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { Fragment } from 'react'
import {
  XMarkIcon,
  CloudArrowUpIcon,
  PhotoIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  TrashIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline'
import { cn } from '../../utils/cn'
import { formatFileSize } from '../../utils/formatters'
import Button from '../common/Button'
import Input from '../common/Input'
import Textarea from '../common/Textarea'
import Badge from '../common/Badge'
import Alert from '../common/Alert'

// Types
interface TigerUploadWizardProps {
  isOpen: boolean
  onClose: () => void
  onComplete: (data: UploadData) => void
  facilities: Array<{ id: string; name: string }>
  models: Array<{ id: string; name: string; description: string }>
}

interface UploadData {
  images: File[]
  facilityId?: string
  captureDate?: string
  notes?: string
  selectedModels: string[]
}

interface ImageWithPreview {
  file: File
  preview: string
  quality: ImageQuality
}

interface ImageQuality {
  score: number
  issues: string[]
  resolution: { width: number; height: number }
}

type WizardStep = 1 | 2 | 3 | 4 | 5

const STEP_LABELS = [
  'Upload Images',
  'Review Images',
  'Add Context',
  'Select Models',
  'Confirm & Submit',
]

const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB
const MAX_FILES = 20
const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const MIN_RESOLUTION = 200 // minimum width/height in pixels

// Helper to assess image quality
const assessImageQuality = (img: HTMLImageElement): ImageQuality => {
  const issues: string[] = []
  let score = 100

  const width = img.naturalWidth
  const height = img.naturalHeight

  // Check resolution
  if (width < MIN_RESOLUTION || height < MIN_RESOLUTION) {
    issues.push('Low resolution')
    score -= 30
  } else if (width < 400 || height < 400) {
    issues.push('Medium resolution')
    score -= 10
  }

  // Check aspect ratio (extreme ratios may crop important features)
  const ratio = width / height
  if (ratio > 3 || ratio < 0.33) {
    issues.push('Unusual aspect ratio')
    score -= 15
  }

  // Estimate if image might be too dark or too bright based on file size heuristics
  // (Real implementation would use canvas to analyze pixels)

  return {
    score: Math.max(0, score),
    issues,
    resolution: { width, height },
  }
}

// Step indicator component
const StepIndicator = ({
  currentStep,
  totalSteps,
  labels,
  onStepClick,
}: {
  currentStep: number
  totalSteps: number
  labels: string[]
  onStepClick?: (step: number) => void
}) => {
  return (
    <div data-testid="wizard-step-indicator" className="w-full">
      <div className="flex items-center justify-between">
        {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step) => {
          const isCompleted = step < currentStep
          const isCurrent = step === currentStep
          const isClickable = onStepClick && step < currentStep

          return (
            <Fragment key={step}>
              <div className="flex flex-col items-center">
                <button
                  type="button"
                  onClick={() => isClickable && onStepClick(step)}
                  disabled={!isClickable}
                  data-testid={`wizard-step-${step}`}
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-all',
                    isCompleted && 'bg-emerald-500 text-white cursor-pointer hover:bg-emerald-600',
                    isCurrent && 'bg-tiger-orange text-white ring-4 ring-tiger-orange/30',
                    !isCompleted && !isCurrent && 'bg-gray-200 text-gray-500',
                    isClickable && 'cursor-pointer'
                  )}
                >
                  {isCompleted ? (
                    <CheckCircleIcon className="w-5 h-5" />
                  ) : (
                    step
                  )}
                </button>
                <span
                  className={cn(
                    'mt-2 text-xs font-medium',
                    isCurrent ? 'text-tiger-orange' : 'text-gray-500'
                  )}
                >
                  {labels[step - 1]}
                </span>
              </div>
              {step < totalSteps && (
                <div
                  className={cn(
                    'flex-1 h-0.5 mx-2 mt-[-24px]',
                    step < currentStep ? 'bg-emerald-500' : 'bg-gray-200'
                  )}
                />
              )}
            </Fragment>
          )
        })}
      </div>
    </div>
  )
}

// Step 1: Image Upload
const ImageUploadStep = ({
  images,
  onImagesChange,
  error,
}: {
  images: ImageWithPreview[]
  onImagesChange: (images: ImageWithPreview[]) => void
  error: string | null
}) => {
  const [dragActive, setDragActive] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  const validateAndLoadImages = useCallback(
    async (files: FileList | File[]) => {
      setLocalError(null)
      const fileArray = Array.from(files)
      const validImages: ImageWithPreview[] = []

      for (const file of fileArray) {
        // Check file type
        if (!ACCEPTED_TYPES.includes(file.type)) {
          setLocalError(`${file.name} is not a supported image format`)
          continue
        }

        // Check file size
        if (file.size > MAX_FILE_SIZE) {
          setLocalError(`${file.name} exceeds ${formatFileSize(MAX_FILE_SIZE)} limit`)
          continue
        }

        // Check total count
        if (images.length + validImages.length >= MAX_FILES) {
          setLocalError(`Maximum ${MAX_FILES} images allowed`)
          break
        }

        // Create preview and assess quality
        const preview = URL.createObjectURL(file)
        const quality = await new Promise<ImageQuality>((resolve) => {
          const img = new Image()
          img.onload = () => resolve(assessImageQuality(img))
          img.onerror = () =>
            resolve({ score: 0, issues: ['Failed to load'], resolution: { width: 0, height: 0 } })
          img.src = preview
        })

        validImages.push({ file, preview, quality })
      }

      if (validImages.length > 0) {
        onImagesChange([...images, ...validImages])
      }
    },
    [images, onImagesChange]
  )

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setDragActive(false)
      if (e.dataTransfer.files) {
        validateAndLoadImages(e.dataTransfer.files)
      }
    },
    [validateAndLoadImages]
  )

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        validateAndLoadImages(e.target.files)
      }
    },
    [validateAndLoadImages]
  )

  const displayError = error || localError

  return (
    <div data-testid="wizard-step-upload" className="space-y-4">
      <div className="text-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">Upload Tiger Images</h3>
        <p className="text-sm text-gray-500 mt-1">
          Upload one or more images of tigers for identification
        </p>
      </div>

      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        data-testid="upload-dropzone"
        className={cn(
          'relative border-2 border-dashed rounded-xl p-12 text-center transition-all',
          dragActive
            ? 'border-tiger-orange bg-tiger-orange/5'
            : 'border-gray-300 hover:border-tiger-orange/50 hover:bg-gray-50'
        )}
      >
        <input
          type="file"
          accept={ACCEPTED_TYPES.join(',')}
          multiple
          onChange={handleFileChange}
          data-testid="upload-input"
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />

        <CloudArrowUpIcon
          className={cn(
            'h-16 w-16 mx-auto mb-4 transition-colors',
            dragActive ? 'text-tiger-orange' : 'text-gray-400'
          )}
        />

        <p className="text-base font-medium text-gray-900">
          {dragActive ? 'Drop images here' : 'Drag and drop images here'}
        </p>
        <p className="text-sm text-gray-500 mt-2">
          or click to browse
        </p>
        <p className="text-xs text-gray-400 mt-4">
          Supported: JPEG, PNG, WebP | Max size: {formatFileSize(MAX_FILE_SIZE)} | Up to {MAX_FILES} images
        </p>
      </div>

      {displayError && (
        <Alert type="error" data-testid="upload-error">
          {displayError}
        </Alert>
      )}

      {images.length > 0 && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              {images.length} image{images.length !== 1 ? 's' : ''} selected
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onImagesChange([])}
              data-testid="clear-all-images"
            >
              Clear all
            </Button>
          </div>
          <div className="grid grid-cols-4 gap-3">
            {images.slice(0, 8).map((img, idx) => (
              <div
                key={idx}
                className="relative aspect-square rounded-lg overflow-hidden bg-gray-100"
              >
                <img
                  src={img.preview}
                  alt={`Preview ${idx + 1}`}
                  className="w-full h-full object-cover"
                />
                {img.quality.score < 70 && (
                  <div className="absolute top-1 right-1">
                    <ExclamationTriangleIcon className="w-5 h-5 text-amber-500" />
                  </div>
                )}
              </div>
            ))}
            {images.length > 8 && (
              <div className="aspect-square rounded-lg bg-gray-100 flex items-center justify-center">
                <span className="text-sm font-medium text-gray-600">
                  +{images.length - 8} more
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// Step 2: Image Review
const ImageReviewStep = ({
  images,
  onImagesChange,
}: {
  images: ImageWithPreview[]
  onImagesChange: (images: ImageWithPreview[]) => void
}) => {
  const removeImage = useCallback(
    (index: number) => {
      const updated = images.filter((_, i) => i !== index)
      // Clean up preview URL
      URL.revokeObjectURL(images[index].preview)
      onImagesChange(updated)
    },
    [images, onImagesChange]
  )

  const getQualityBadge = (quality: ImageQuality) => {
    if (quality.score >= 80) {
      return <Badge variant="success">Good Quality</Badge>
    } else if (quality.score >= 50) {
      return <Badge variant="warning">Acceptable</Badge>
    } else {
      return <Badge variant="danger">Poor Quality</Badge>
    }
  }

  const lowQualityCount = images.filter((img) => img.quality.score < 50).length

  return (
    <div data-testid="wizard-step-review" className="space-y-4">
      <div className="text-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">Review Images</h3>
        <p className="text-sm text-gray-500 mt-1">
          Review image quality and remove any unsuitable images
        </p>
      </div>

      {lowQualityCount > 0 && (
        <Alert type="warning" title="Quality Warning">
          {lowQualityCount} image{lowQualityCount !== 1 ? 's have' : ' has'} poor quality.
          Consider removing or replacing them for better identification results.
        </Alert>
      )}

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-h-[400px] overflow-y-auto pr-2">
        {images.map((img, idx) => (
          <div
            key={idx}
            data-testid={`image-review-item-${idx}`}
            className={cn(
              'relative rounded-lg border overflow-hidden bg-white',
              img.quality.score < 50
                ? 'border-red-300 ring-2 ring-red-100'
                : img.quality.score < 80
                ? 'border-amber-300'
                : 'border-gray-200'
            )}
          >
            <div className="aspect-video relative">
              <img
                src={img.preview}
                alt={`Image ${idx + 1}`}
                className="w-full h-full object-cover"
              />
              <button
                onClick={() => removeImage(idx)}
                data-testid={`remove-image-${idx}`}
                className="absolute top-2 right-2 p-1.5 bg-white/90 rounded-full text-gray-600 hover:text-red-600 hover:bg-white transition-colors"
              >
                <TrashIcon className="w-4 h-4" />
              </button>
            </div>
            <div className="p-3">
              <div className="flex items-center justify-between mb-2">
                {getQualityBadge(img.quality)}
                <span className="text-xs text-gray-500">
                  {img.quality.resolution.width} x {img.quality.resolution.height}
                </span>
              </div>
              <p className="text-xs text-gray-600 truncate">{img.file.name}</p>
              <p className="text-xs text-gray-400">{formatFileSize(img.file.size)}</p>
              {img.quality.issues.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {img.quality.issues.map((issue, i) => (
                    <span
                      key={i}
                      className="text-xs px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded"
                    >
                      {issue}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between pt-4 border-t">
        <span className="text-sm text-gray-600">
          {images.length} image{images.length !== 1 ? 's' : ''} ready for processing
        </span>
        <div className="flex gap-2">
          {images.filter((img) => img.quality.score < 50).length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onImagesChange(images.filter((img) => img.quality.score >= 50))}
              data-testid="remove-low-quality"
            >
              Remove Poor Quality
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

// Step 3: Context
const ContextStep = ({
  facilityId,
  captureDate,
  notes,
  facilities,
  onFacilityChange,
  onDateChange,
  onNotesChange,
}: {
  facilityId: string | undefined
  captureDate: string | undefined
  notes: string | undefined
  facilities: Array<{ id: string; name: string }>
  onFacilityChange: (id: string | undefined) => void
  onDateChange: (date: string | undefined) => void
  onNotesChange: (notes: string | undefined) => void
}) => {
  return (
    <div data-testid="wizard-step-context" className="space-y-6">
      <div className="text-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">Add Context</h3>
        <p className="text-sm text-gray-500 mt-1">
          Provide additional information to help with identification (optional)
        </p>
      </div>

      <Alert type="info">
        <div className="flex items-start gap-2">
          <InformationCircleIcon className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>
            Adding context helps narrow down search results and improves identification accuracy.
            All fields are optional.
          </span>
        </div>
      </Alert>

      <div className="space-y-4">
        <div>
          <label
            htmlFor="facility-select"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Facility
          </label>
          <select
            id="facility-select"
            value={facilityId || ''}
            onChange={(e) => onFacilityChange(e.target.value || undefined)}
            data-testid="facility-select"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-tiger-orange focus:border-transparent"
          >
            <option value="">Select a facility (optional)</option>
            {facilities.map((facility) => (
              <option key={facility.id} value={facility.id}>
                {facility.name}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-500">
            If known, select the facility where the image was captured
          </p>
        </div>

        <Input
          label="Capture Date"
          type="date"
          value={captureDate || ''}
          onChange={(e) => onDateChange(e.target.value || undefined)}
          data-testid="capture-date-input"
          helperText="When was this image taken?"
        />

        <Textarea
          label="Notes"
          value={notes || ''}
          onChange={(e) => onNotesChange(e.target.value || undefined)}
          placeholder="Add any relevant notes about these images..."
          rows={4}
          data-testid="notes-textarea"
          helperText="Include any observations or context that might help with identification"
        />
      </div>
    </div>
  )
}

// Step 4: Model Selection
const ModelSelectionStep = ({
  models,
  selectedModels,
  onSelectionChange,
}: {
  models: Array<{ id: string; name: string; description: string }>
  selectedModels: string[]
  onSelectionChange: (models: string[]) => void
}) => {
  const toggleModel = useCallback(
    (modelId: string) => {
      if (selectedModels.includes(modelId)) {
        onSelectionChange(selectedModels.filter((id) => id !== modelId))
      } else {
        onSelectionChange([...selectedModels, modelId])
      }
    },
    [selectedModels, onSelectionChange]
  )

  const selectAll = useCallback(() => {
    onSelectionChange(models.map((m) => m.id))
  }, [models, onSelectionChange])

  const selectNone = useCallback(() => {
    onSelectionChange([])
  }, [onSelectionChange])

  return (
    <div data-testid="wizard-step-models" className="space-y-4">
      <div className="text-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">Select ReID Models</h3>
        <p className="text-sm text-gray-500 mt-1">
          Choose which identification models to use for analysis
        </p>
      </div>

      <Alert type="info">
        Using multiple models improves accuracy through ensemble matching.
        The default selection is recommended for most cases.
      </Alert>

      <div className="flex items-center justify-end gap-2 mb-2">
        <Button variant="ghost" size="sm" onClick={selectAll} data-testid="select-all-models">
          Select All
        </Button>
        <Button variant="ghost" size="sm" onClick={selectNone} data-testid="select-none-models">
          Clear
        </Button>
      </div>

      <div className="space-y-3 max-h-[350px] overflow-y-auto pr-2">
        {models.map((model) => {
          const isSelected = selectedModels.includes(model.id)
          return (
            <div
              key={model.id}
              onClick={() => toggleModel(model.id)}
              data-testid={`model-option-${model.id}`}
              className={cn(
                'p-4 rounded-lg border-2 cursor-pointer transition-all',
                isSelected
                  ? 'border-tiger-orange bg-tiger-orange/5'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              )}
            >
              <div className="flex items-start gap-3">
                <div
                  className={cn(
                    'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5',
                    isSelected
                      ? 'border-tiger-orange bg-tiger-orange'
                      : 'border-gray-300'
                  )}
                >
                  {isSelected && <CheckCircleIcon className="w-4 h-4 text-white" />}
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-gray-900">{model.name}</h4>
                  <p className="text-xs text-gray-500 mt-1">{model.description}</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {selectedModels.length === 0 && (
        <Alert type="warning" className="mt-4">
          Please select at least one model to continue.
        </Alert>
      )}

      <div className="pt-4 border-t">
        <span className="text-sm text-gray-600">
          {selectedModels.length} model{selectedModels.length !== 1 ? 's' : ''} selected
        </span>
      </div>
    </div>
  )
}

// Step 5: Confirmation
const ConfirmationStep = ({
  images,
  facilityId,
  captureDate,
  notes,
  selectedModels,
  facilities,
  models,
}: {
  images: ImageWithPreview[]
  facilityId?: string
  captureDate?: string
  notes?: string
  selectedModels: string[]
  facilities: Array<{ id: string; name: string }>
  models: Array<{ id: string; name: string; description: string }>
}) => {
  const facilityName = facilities.find((f) => f.id === facilityId)?.name
  const selectedModelNames = models
    .filter((m) => selectedModels.includes(m.id))
    .map((m) => m.name)

  return (
    <div data-testid="wizard-step-confirm" className="space-y-6">
      <div className="text-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">Confirm Upload</h3>
        <p className="text-sm text-gray-500 mt-1">
          Review your selections before submitting
        </p>
      </div>

      <div className="bg-gray-50 rounded-lg p-4 space-y-4">
        {/* Images Summary */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Images</h4>
          <div className="flex items-center gap-3">
            <div className="flex -space-x-2">
              {images.slice(0, 4).map((img, idx) => (
                <div
                  key={idx}
                  className="w-12 h-12 rounded-lg border-2 border-white overflow-hidden"
                >
                  <img
                    src={img.preview}
                    alt={`Preview ${idx + 1}`}
                    className="w-full h-full object-cover"
                  />
                </div>
              ))}
              {images.length > 4 && (
                <div className="w-12 h-12 rounded-lg border-2 border-white bg-gray-200 flex items-center justify-center">
                  <span className="text-xs font-medium text-gray-600">+{images.length - 4}</span>
                </div>
              )}
            </div>
            <span className="text-sm text-gray-600">
              {images.length} image{images.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>

        {/* Context Summary */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Context</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Facility:</span>
              <span className="ml-2 text-gray-900">{facilityName || 'Not specified'}</span>
            </div>
            <div>
              <span className="text-gray-500">Date:</span>
              <span className="ml-2 text-gray-900">{captureDate || 'Not specified'}</span>
            </div>
            {notes && (
              <div className="col-span-2">
                <span className="text-gray-500">Notes:</span>
                <p className="mt-1 text-gray-900 text-xs bg-white p-2 rounded border">
                  {notes}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Models Summary */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Selected Models</h4>
          <div className="flex flex-wrap gap-2">
            {selectedModelNames.map((name) => (
              <Badge key={name} variant="tiger">
                {name}
              </Badge>
            ))}
          </div>
        </div>
      </div>

      <Alert type="info">
        <div className="flex items-start gap-2">
          <PhotoIcon className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>
            Processing may take a few moments depending on the number of images and selected models.
            You will be notified when the analysis is complete.
          </span>
        </div>
      </Alert>
    </div>
  )
}

// Main Wizard Component
const TigerUploadWizard = ({
  isOpen,
  onClose,
  onComplete,
  facilities,
  models,
}: TigerUploadWizardProps) => {
  // State
  const [currentStep, setCurrentStep] = useState<WizardStep>(1)
  const [images, setImages] = useState<ImageWithPreview[]>([])
  const [facilityId, setFacilityId] = useState<string | undefined>()
  const [captureDate, setCaptureDate] = useState<string | undefined>()
  const [notes, setNotes] = useState<string | undefined>()
  const [selectedModels, setSelectedModels] = useState<string[]>(() =>
    models.slice(0, 3).map((m) => m.id) // Default to first 3 models
  )
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setCurrentStep(1)
      setImages([])
      setFacilityId(undefined)
      setCaptureDate(undefined)
      setNotes(undefined)
      setSelectedModels(models.slice(0, 3).map((m) => m.id))
      setIsSubmitting(false)
      setError(null)
    }
  }, [isOpen, models])

  // Cleanup preview URLs on unmount
  useEffect(() => {
    return () => {
      images.forEach((img) => URL.revokeObjectURL(img.preview))
    }
  }, [images])

  // Validation per step
  const stepValidation = useMemo(() => {
    return {
      1: images.length > 0,
      2: images.length > 0,
      3: true, // Optional step
      4: selectedModels.length > 0,
      5: images.length > 0 && selectedModels.length > 0,
    }
  }, [images, selectedModels])

  const canProceed = stepValidation[currentStep]
  const canSkip = currentStep === 3 // Context step is optional

  // Navigation handlers
  const goToNextStep = useCallback(() => {
    if (currentStep < 5 && canProceed) {
      setCurrentStep((prev) => (prev + 1) as WizardStep)
      setError(null)
    }
  }, [currentStep, canProceed])

  const goToPreviousStep = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep((prev) => (prev - 1) as WizardStep)
      setError(null)
    }
  }, [currentStep])

  const goToStep = useCallback((step: number) => {
    if (step >= 1 && step <= 5) {
      setCurrentStep(step as WizardStep)
      setError(null)
    }
  }, [])

  // Submit handler
  const handleSubmit = useCallback(async () => {
    if (!stepValidation[5]) {
      setError('Please complete all required fields')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const uploadData: UploadData = {
        images: images.map((img) => img.file),
        facilityId,
        captureDate,
        notes,
        selectedModels,
      }

      await onComplete(uploadData)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during upload')
    } finally {
      setIsSubmitting(false)
    }
  }, [images, facilityId, captureDate, notes, selectedModels, stepValidation, onComplete, onClose])

  // Render current step
  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <ImageUploadStep
            images={images}
            onImagesChange={setImages}
            error={error}
          />
        )
      case 2:
        return <ImageReviewStep images={images} onImagesChange={setImages} />
      case 3:
        return (
          <ContextStep
            facilityId={facilityId}
            captureDate={captureDate}
            notes={notes}
            facilities={facilities}
            onFacilityChange={setFacilityId}
            onDateChange={setCaptureDate}
            onNotesChange={setNotes}
          />
        )
      case 4:
        return (
          <ModelSelectionStep
            models={models}
            selectedModels={selectedModels}
            onSelectionChange={setSelectedModels}
          />
        )
      case 5:
        return (
          <ConfirmationStep
            images={images}
            facilityId={facilityId}
            captureDate={captureDate}
            notes={notes}
            selectedModels={selectedModels}
            facilities={facilities}
            models={models}
          />
        )
    }
  }

  return (
    <Transition show={isOpen} as={Fragment}>
      <Dialog onClose={onClose} className="relative z-50" data-testid="tiger-upload-wizard">
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/40" aria-hidden="true" />
        </Transition.Child>

        <div className="fixed inset-0 flex items-center justify-center p-4">
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0 scale-95"
            enterTo="opacity-100 scale-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100 scale-100"
            leaveTo="opacity-0 scale-95"
          >
            <Dialog.Panel
              data-testid="wizard-panel"
              className="w-full max-w-3xl bg-white rounded-2xl shadow-xl overflow-hidden"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b bg-gray-50">
                <Dialog.Title className="text-lg font-semibold text-gray-900">
                  Upload Tiger Images
                </Dialog.Title>
                <button
                  onClick={onClose}
                  data-testid="wizard-close"
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              {/* Step Indicator */}
              <div className="px-6 py-4 border-b bg-white">
                <StepIndicator
                  currentStep={currentStep}
                  totalSteps={5}
                  labels={STEP_LABELS}
                  onStepClick={goToStep}
                />
              </div>

              {/* Content */}
              <div className="px-6 py-6 min-h-[400px] max-h-[calc(100vh-300px)] overflow-y-auto">
                {renderStep()}
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t bg-gray-50 flex items-center justify-between">
                <div>
                  {currentStep > 1 && (
                    <Button
                      variant="ghost"
                      onClick={goToPreviousStep}
                      data-testid="wizard-back"
                    >
                      <ChevronLeftIcon className="w-4 h-4 mr-1" />
                      Back
                    </Button>
                  )}
                </div>

                <div className="flex items-center gap-3">
                  {canSkip && !canProceed && (
                    <Button
                      variant="ghost"
                      onClick={goToNextStep}
                      data-testid="wizard-skip"
                    >
                      Skip
                    </Button>
                  )}

                  {currentStep < 5 ? (
                    <Button
                      onClick={goToNextStep}
                      disabled={!canProceed && !canSkip}
                      data-testid="wizard-next"
                    >
                      Next
                      <ChevronRightIcon className="w-4 h-4 ml-1" />
                    </Button>
                  ) : (
                    <Button
                      onClick={handleSubmit}
                      isLoading={isSubmitting}
                      disabled={!canProceed || isSubmitting}
                      data-testid="wizard-submit"
                    >
                      {isSubmitting ? 'Uploading...' : 'Start Analysis'}
                    </Button>
                  )}
                </div>
              </div>
            </Dialog.Panel>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition>
  )
}

export default TigerUploadWizard

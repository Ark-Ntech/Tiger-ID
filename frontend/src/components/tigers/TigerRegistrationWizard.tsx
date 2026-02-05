import { useState, useCallback, useMemo, useEffect, Fragment } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import {
  XMarkIcon,
  CheckCircleIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  InformationCircleIcon,
  PhotoIcon,
  BuildingOfficeIcon,
  IdentificationIcon,
  DocumentTextIcon,
  CheckIcon,
} from '@heroicons/react/24/outline'
import { cn } from '../../utils/cn'
import Button from '../common/Button'
import Input from '../common/Input'
import Textarea from '../common/Textarea'
import Alert from '../common/Alert'
import Badge from '../common/Badge'

// Types
export interface TigerRegistrationWizardProps {
  isOpen: boolean
  onClose: () => void
  onComplete: (data: TigerRegistrationData) => void
  facilities: Array<{ id: string; name: string }>
  preselectedImages?: Array<{ id: string; url: string; thumbnailUrl?: string }>
}

export interface TigerRegistrationData {
  name: string
  estimatedAge?: number
  sex?: 'male' | 'female' | 'unknown'
  distinctiveMarkings?: string
  notes?: string
  facilityId: string
  enclosure?: string
  referenceImageIds: string[]
}

interface ImageSelection {
  id: string
  url: string
  thumbnailUrl?: string
  isSelected: boolean
}

type WizardStep = 1 | 2 | 3 | 4 | 5

const STEP_LABELS = [
  'Basic Info',
  'Physical Characteristics',
  'Facility Assignment',
  'Reference Images',
  'Review & Submit',
]

const STEP_ICONS = [
  IdentificationIcon,
  DocumentTextIcon,
  BuildingOfficeIcon,
  PhotoIcon,
  CheckIcon,
]

// Step indicator component
const StepIndicator = ({
  currentStep,
  totalSteps,
  labels,
  icons,
  onStepClick,
  completedSteps,
}: {
  currentStep: number
  totalSteps: number
  labels: string[]
  icons: typeof STEP_ICONS
  onStepClick?: (step: number) => void
  completedSteps: Set<number>
}) => {
  return (
    <div data-testid="registration-step-indicator" className="w-full">
      <div className="flex items-center justify-between">
        {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step) => {
          const isCompleted = completedSteps.has(step) && step !== currentStep
          const isCurrent = step === currentStep
          const isClickable = onStepClick && (completedSteps.has(step) || step < currentStep)
          const Icon = icons[step - 1]

          return (
            <Fragment key={step}>
              <div className="flex flex-col items-center">
                <button
                  type="button"
                  onClick={() => isClickable && onStepClick(step)}
                  disabled={!isClickable}
                  data-testid={`registration-step-${step}`}
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center transition-all',
                    isCompleted && 'bg-emerald-500 text-white cursor-pointer hover:bg-emerald-600',
                    isCurrent && 'bg-tiger-orange text-white ring-4 ring-tiger-orange/30',
                    !isCompleted && !isCurrent && 'bg-gray-200 text-gray-500',
                    isClickable && 'cursor-pointer'
                  )}
                >
                  {isCompleted ? (
                    <CheckCircleIcon className="w-5 h-5" />
                  ) : (
                    <Icon className="w-5 h-5" />
                  )}
                </button>
                <span
                  className={cn(
                    'mt-2 text-xs font-medium text-center max-w-[80px]',
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
                    completedSteps.has(step) ? 'bg-emerald-500' : 'bg-gray-200'
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

// Step 1: Basic Info
const BasicInfoStep = ({
  name,
  estimatedAge,
  sex,
  onNameChange,
  onAgeChange,
  onSexChange,
  errors,
}: {
  name: string
  estimatedAge: number | undefined
  sex: 'male' | 'female' | 'unknown' | undefined
  onNameChange: (name: string) => void
  onAgeChange: (age: number | undefined) => void
  onSexChange: (sex: 'male' | 'female' | 'unknown' | undefined) => void
  errors: { name?: string }
}) => {
  const sexOptions: Array<{ value: 'male' | 'female' | 'unknown'; label: string }> = [
    { value: 'male', label: 'Male' },
    { value: 'female', label: 'Female' },
    { value: 'unknown', label: 'Unknown' },
  ]

  return (
    <div data-testid="registration-step-basic-info" className="space-y-6">
      <div className="text-center mb-6">
        <h3 className="text-lg font-medium text-gray-900">Basic Information</h3>
        <p className="text-sm text-gray-500 mt-1">
          Enter the basic details for this tiger
        </p>
      </div>

      <div className="space-y-5">
        <Input
          label="Tiger Name"
          value={name}
          onChange={(e) => onNameChange(e.target.value)}
          placeholder="Enter a name for this tiger"
          required
          error={errors.name}
          data-testid="tiger-name-input"
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Estimated Age (years)
          </label>
          <Input
            type="number"
            value={estimatedAge !== undefined ? estimatedAge.toString() : ''}
            onChange={(e) => {
              const value = e.target.value
              onAgeChange(value ? parseInt(value, 10) : undefined)
            }}
            placeholder="Enter estimated age"
            min={0}
            max={30}
            data-testid="tiger-age-input"
            helperText="Tigers typically live 10-15 years in the wild, up to 20+ in captivity"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Sex
          </label>
          <div className="flex gap-3" data-testid="tiger-sex-options">
            {sexOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => onSexChange(option.value)}
                data-testid={`tiger-sex-${option.value}`}
                className={cn(
                  'flex-1 py-3 px-4 rounded-lg border-2 font-medium transition-all',
                  sex === option.value
                    ? 'border-tiger-orange bg-tiger-orange/5 text-tiger-orange'
                    : 'border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50'
                )}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// Step 2: Physical Characteristics
const PhysicalCharacteristicsStep = ({
  distinctiveMarkings,
  notes,
  onMarkingsChange,
  onNotesChange,
}: {
  distinctiveMarkings: string | undefined
  notes: string | undefined
  onMarkingsChange: (markings: string | undefined) => void
  onNotesChange: (notes: string | undefined) => void
}) => {
  return (
    <div data-testid="registration-step-physical" className="space-y-6">
      <div className="text-center mb-6">
        <h3 className="text-lg font-medium text-gray-900">Physical Characteristics</h3>
        <p className="text-sm text-gray-500 mt-1">
          Describe any distinctive physical features (optional)
        </p>
      </div>

      <Alert type="info">
        <div className="flex items-start gap-2">
          <InformationCircleIcon className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>
            Distinctive markings help with manual identification when automated matching is uncertain.
            Include details about unique stripe patterns, scars, or other identifiable features.
          </span>
        </div>
      </Alert>

      <div className="space-y-5">
        <Textarea
          label="Distinctive Markings"
          value={distinctiveMarkings || ''}
          onChange={(e) => onMarkingsChange(e.target.value || undefined)}
          placeholder="Describe unique stripe patterns, scars, facial markings, tail patterns, or other distinctive features..."
          rows={5}
          data-testid="tiger-markings-textarea"
          helperText="Be as specific as possible - mention location on body, shape, and size of markings"
        />

        <Textarea
          label="Additional Notes"
          value={notes || ''}
          onChange={(e) => onNotesChange(e.target.value || undefined)}
          placeholder="Any additional information about this tiger (behavior, health conditions, history, etc.)"
          rows={4}
          data-testid="tiger-notes-textarea"
        />
      </div>
    </div>
  )
}

// Step 3: Facility Assignment
const FacilityAssignmentStep = ({
  facilityId,
  enclosure,
  facilities,
  onFacilityChange,
  onEnclosureChange,
  errors,
}: {
  facilityId: string
  enclosure: string | undefined
  facilities: Array<{ id: string; name: string }>
  onFacilityChange: (id: string) => void
  onEnclosureChange: (enclosure: string | undefined) => void
  errors: { facilityId?: string }
}) => {
  return (
    <div data-testid="registration-step-facility" className="space-y-6">
      <div className="text-center mb-6">
        <h3 className="text-lg font-medium text-gray-900">Facility Assignment</h3>
        <p className="text-sm text-gray-500 mt-1">
          Assign this tiger to a facility
        </p>
      </div>

      <div className="space-y-5">
        <div>
          <label
            htmlFor="facility-select"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Facility <span className="text-red-500">*</span>
          </label>
          <select
            id="facility-select"
            value={facilityId}
            onChange={(e) => onFacilityChange(e.target.value)}
            data-testid="facility-select"
            className={cn(
              'w-full px-3 py-2 border rounded-lg transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-tiger-orange focus:border-transparent',
              errors.facilityId ? 'border-red-500' : 'border-gray-300'
            )}
          >
            <option value="">Select a facility</option>
            {facilities.map((facility) => (
              <option key={facility.id} value={facility.id}>
                {facility.name}
              </option>
            ))}
          </select>
          {errors.facilityId && (
            <p className="mt-1 text-sm text-red-600" data-testid="facility-error">
              {errors.facilityId}
            </p>
          )}
        </div>

        <Input
          label="Enclosure / Area"
          value={enclosure || ''}
          onChange={(e) => onEnclosureChange(e.target.value || undefined)}
          placeholder="E.g., Enclosure A, North Habitat, Tiger Valley"
          data-testid="enclosure-input"
          helperText="Specify the specific area or enclosure within the facility"
        />

        {facilityId && (
          <Alert type="success">
            <div className="flex items-center gap-2">
              <BuildingOfficeIcon className="w-5 h-5" />
              <span>
                Tiger will be registered at:{' '}
                <strong>{facilities.find((f) => f.id === facilityId)?.name}</strong>
              </span>
            </div>
          </Alert>
        )}
      </div>
    </div>
  )
}

// Step 4: Reference Images
const ReferenceImagesStep = ({
  availableImages,
  selectedImageIds,
  onSelectionChange,
}: {
  availableImages: ImageSelection[]
  selectedImageIds: string[]
  onSelectionChange: (ids: string[]) => void
}) => {
  const toggleImage = useCallback(
    (imageId: string) => {
      if (selectedImageIds.includes(imageId)) {
        onSelectionChange(selectedImageIds.filter((id) => id !== imageId))
      } else {
        onSelectionChange([...selectedImageIds, imageId])
      }
    },
    [selectedImageIds, onSelectionChange]
  )

  const selectAll = useCallback(() => {
    onSelectionChange(availableImages.map((img) => img.id))
  }, [availableImages, onSelectionChange])

  const clearSelection = useCallback(() => {
    onSelectionChange([])
  }, [onSelectionChange])

  return (
    <div data-testid="registration-step-images" className="space-y-4">
      <div className="text-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">Reference Images</h3>
        <p className="text-sm text-gray-500 mt-1">
          Select images to use as reference for this tiger
        </p>
      </div>

      {availableImages.length > 0 ? (
        <>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">
              {selectedImageIds.length} of {availableImages.length} selected
            </span>
            <div className="flex gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={selectAll}
                data-testid="select-all-images"
              >
                Select All
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearSelection}
                data-testid="clear-image-selection"
              >
                Clear
              </Button>
            </div>
          </div>

          <div
            className="grid grid-cols-3 md:grid-cols-4 gap-3 max-h-[350px] overflow-y-auto pr-2"
            data-testid="image-grid"
          >
            {availableImages.map((image) => {
              const isSelected = selectedImageIds.includes(image.id)
              return (
                <button
                  key={image.id}
                  type="button"
                  onClick={() => toggleImage(image.id)}
                  data-testid={`image-option-${image.id}`}
                  className={cn(
                    'relative aspect-square rounded-lg overflow-hidden border-2 transition-all',
                    isSelected
                      ? 'border-tiger-orange ring-2 ring-tiger-orange/30'
                      : 'border-gray-200 hover:border-gray-300'
                  )}
                >
                  <img
                    src={image.thumbnailUrl || image.url}
                    alt={`Reference image ${image.id}`}
                    className="w-full h-full object-cover"
                  />
                  {isSelected && (
                    <div className="absolute inset-0 bg-tiger-orange/20 flex items-center justify-center">
                      <div className="w-8 h-8 rounded-full bg-tiger-orange flex items-center justify-center">
                        <CheckCircleIcon className="w-5 h-5 text-white" />
                      </div>
                    </div>
                  )}
                </button>
              )
            })}
          </div>
        </>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <PhotoIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-900">No images available</p>
          <p className="text-xs text-gray-500 mt-1">
            No preselected images were provided for this registration
          </p>
        </div>
      )}

      {selectedImageIds.length === 0 && availableImages.length > 0 && (
        <Alert type="warning">
          Select at least one reference image for better identification accuracy.
        </Alert>
      )}
    </div>
  )
}

// Step 5: Review & Submit
const ReviewStep = ({
  name,
  estimatedAge,
  sex,
  distinctiveMarkings,
  notes,
  facilityId,
  enclosure,
  selectedImageIds,
  facilities,
  availableImages,
}: {
  name: string
  estimatedAge: number | undefined
  sex: 'male' | 'female' | 'unknown' | undefined
  distinctiveMarkings: string | undefined
  notes: string | undefined
  facilityId: string
  enclosure: string | undefined
  selectedImageIds: string[]
  facilities: Array<{ id: string; name: string }>
  availableImages: ImageSelection[]
}) => {
  const facilityName = facilities.find((f) => f.id === facilityId)?.name
  const selectedImages = availableImages.filter((img) => selectedImageIds.includes(img.id))

  const getSexLabel = (sex: 'male' | 'female' | 'unknown' | undefined) => {
    switch (sex) {
      case 'male':
        return 'Male'
      case 'female':
        return 'Female'
      case 'unknown':
        return 'Unknown'
      default:
        return 'Not specified'
    }
  }

  return (
    <div data-testid="registration-step-review" className="space-y-6">
      <div className="text-center mb-6">
        <h3 className="text-lg font-medium text-gray-900">Review & Submit</h3>
        <p className="text-sm text-gray-500 mt-1">
          Review the information before registering this tiger
        </p>
      </div>

      <div className="bg-gray-50 rounded-xl p-5 space-y-5">
        {/* Basic Info Section */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <IdentificationIcon className="w-4 h-4" />
            Basic Information
          </h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Name:</span>
              <span className="ml-2 font-medium text-gray-900">{name}</span>
            </div>
            <div>
              <span className="text-gray-500">Sex:</span>
              <span className="ml-2 text-gray-900">{getSexLabel(sex)}</span>
            </div>
            <div>
              <span className="text-gray-500">Estimated Age:</span>
              <span className="ml-2 text-gray-900">
                {estimatedAge !== undefined ? `${estimatedAge} years` : 'Not specified'}
              </span>
            </div>
          </div>
        </div>

        {/* Physical Characteristics Section */}
        {(distinctiveMarkings || notes) && (
          <div className="border-t pt-5">
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <DocumentTextIcon className="w-4 h-4" />
              Physical Characteristics
            </h4>
            {distinctiveMarkings && (
              <div className="mb-3">
                <span className="text-xs text-gray-500 block mb-1">Distinctive Markings:</span>
                <p className="text-sm text-gray-900 bg-white p-3 rounded border">
                  {distinctiveMarkings}
                </p>
              </div>
            )}
            {notes && (
              <div>
                <span className="text-xs text-gray-500 block mb-1">Notes:</span>
                <p className="text-sm text-gray-900 bg-white p-3 rounded border">
                  {notes}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Facility Section */}
        <div className="border-t pt-5">
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <BuildingOfficeIcon className="w-4 h-4" />
            Facility Assignment
          </h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Facility:</span>
              <span className="ml-2 font-medium text-gray-900">{facilityName}</span>
            </div>
            {enclosure && (
              <div>
                <span className="text-gray-500">Enclosure:</span>
                <span className="ml-2 text-gray-900">{enclosure}</span>
              </div>
            )}
          </div>
        </div>

        {/* Reference Images Section */}
        <div className="border-t pt-5">
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <PhotoIcon className="w-4 h-4" />
            Reference Images
          </h4>
          {selectedImages.length > 0 ? (
            <div className="flex items-center gap-3">
              <div className="flex -space-x-2">
                {selectedImages.slice(0, 5).map((img) => (
                  <div
                    key={img.id}
                    className="w-12 h-12 rounded-lg border-2 border-white overflow-hidden shadow-sm"
                  >
                    <img
                      src={img.thumbnailUrl || img.url}
                      alt={`Reference ${img.id}`}
                      className="w-full h-full object-cover"
                    />
                  </div>
                ))}
                {selectedImages.length > 5 && (
                  <div className="w-12 h-12 rounded-lg border-2 border-white bg-gray-200 flex items-center justify-center shadow-sm">
                    <span className="text-xs font-medium text-gray-600">
                      +{selectedImages.length - 5}
                    </span>
                  </div>
                )}
              </div>
              <span className="text-sm text-gray-600">
                {selectedImages.length} image{selectedImages.length !== 1 ? 's' : ''} selected
              </span>
            </div>
          ) : (
            <Badge variant="warning">No reference images selected</Badge>
          )}
        </div>
      </div>

      <Alert type="info">
        <div className="flex items-start gap-2">
          <InformationCircleIcon className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>
            After registration, this tiger will be added to the database and can be used
            for identification matching in investigations.
          </span>
        </div>
      </Alert>
    </div>
  )
}

// Main Wizard Component
const TigerRegistrationWizard = ({
  isOpen,
  onClose,
  onComplete,
  facilities,
  preselectedImages = [],
}: TigerRegistrationWizardProps) => {
  // State
  const [currentStep, setCurrentStep] = useState<WizardStep>(1)
  const [name, setName] = useState('')
  const [estimatedAge, setEstimatedAge] = useState<number | undefined>()
  const [sex, setSex] = useState<'male' | 'female' | 'unknown' | undefined>()
  const [distinctiveMarkings, setDistinctiveMarkings] = useState<string | undefined>()
  const [notes, setNotes] = useState<string | undefined>()
  const [facilityId, setFacilityId] = useState('')
  const [enclosure, setEnclosure] = useState<string | undefined>()
  const [selectedImageIds, setSelectedImageIds] = useState<string[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errors, setErrors] = useState<{ name?: string; facilityId?: string }>({})
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set())

  // Available images from preselected
  const availableImages: ImageSelection[] = useMemo(
    () =>
      preselectedImages.map((img) => ({
        ...img,
        isSelected: selectedImageIds.includes(img.id),
      })),
    [preselectedImages, selectedImageIds]
  )

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setCurrentStep(1)
      setName('')
      setEstimatedAge(undefined)
      setSex(undefined)
      setDistinctiveMarkings(undefined)
      setNotes(undefined)
      setFacilityId('')
      setEnclosure(undefined)
      setSelectedImageIds(preselectedImages.map((img) => img.id))
      setIsSubmitting(false)
      setErrors({})
      setCompletedSteps(new Set())
    }
  }, [isOpen, preselectedImages])

  // Validation per step
  const validateStep = useCallback(
    (step: WizardStep): boolean => {
      const newErrors: { name?: string; facilityId?: string } = {}

      switch (step) {
        case 1:
          if (!name.trim()) {
            newErrors.name = 'Tiger name is required'
          }
          break
        case 2:
          // Optional step - always valid
          break
        case 3:
          if (!facilityId) {
            newErrors.facilityId = 'Please select a facility'
          }
          break
        case 4:
          // Optional step - always valid (but show warning)
          break
        case 5:
          if (!name.trim()) {
            newErrors.name = 'Tiger name is required'
          }
          if (!facilityId) {
            newErrors.facilityId = 'Please select a facility'
          }
          break
      }

      setErrors(newErrors)
      return Object.keys(newErrors).length === 0
    },
    [name, facilityId]
  )

  // Check if current step can proceed
  const canProceed = useMemo(() => {
    switch (currentStep) {
      case 1:
        return name.trim().length > 0
      case 2:
        return true // Optional step
      case 3:
        return facilityId.length > 0
      case 4:
        return true // Optional but recommended
      case 5:
        return name.trim().length > 0 && facilityId.length > 0
      default:
        return false
    }
  }, [currentStep, name, facilityId])

  // Navigation handlers
  const goToNextStep = useCallback(() => {
    if (currentStep < 5 && validateStep(currentStep)) {
      setCompletedSteps((prev) => new Set([...prev, currentStep]))
      setCurrentStep((prev) => (prev + 1) as WizardStep)
    }
  }, [currentStep, validateStep])

  const goToPreviousStep = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep((prev) => (prev - 1) as WizardStep)
      setErrors({})
    }
  }, [currentStep])

  const goToStep = useCallback(
    (step: number) => {
      if (step >= 1 && step <= 5 && (completedSteps.has(step) || step < currentStep)) {
        setCurrentStep(step as WizardStep)
        setErrors({})
      }
    },
    [completedSteps, currentStep]
  )

  // Submit handler
  const handleSubmit = useCallback(async () => {
    if (!validateStep(5)) {
      return
    }

    setIsSubmitting(true)

    try {
      const registrationData: TigerRegistrationData = {
        name: name.trim(),
        estimatedAge,
        sex,
        distinctiveMarkings: distinctiveMarkings?.trim(),
        notes: notes?.trim(),
        facilityId,
        enclosure: enclosure?.trim(),
        referenceImageIds: selectedImageIds,
      }

      await onComplete(registrationData)
      onClose()
    } catch (err) {
      setErrors({
        name: err instanceof Error ? err.message : 'An error occurred during registration',
      })
    } finally {
      setIsSubmitting(false)
    }
  }, [
    name,
    estimatedAge,
    sex,
    distinctiveMarkings,
    notes,
    facilityId,
    enclosure,
    selectedImageIds,
    validateStep,
    onComplete,
    onClose,
  ])

  // Render current step
  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <BasicInfoStep
            name={name}
            estimatedAge={estimatedAge}
            sex={sex}
            onNameChange={setName}
            onAgeChange={setEstimatedAge}
            onSexChange={setSex}
            errors={errors}
          />
        )
      case 2:
        return (
          <PhysicalCharacteristicsStep
            distinctiveMarkings={distinctiveMarkings}
            notes={notes}
            onMarkingsChange={setDistinctiveMarkings}
            onNotesChange={setNotes}
          />
        )
      case 3:
        return (
          <FacilityAssignmentStep
            facilityId={facilityId}
            enclosure={enclosure}
            facilities={facilities}
            onFacilityChange={setFacilityId}
            onEnclosureChange={setEnclosure}
            errors={errors}
          />
        )
      case 4:
        return (
          <ReferenceImagesStep
            availableImages={availableImages}
            selectedImageIds={selectedImageIds}
            onSelectionChange={setSelectedImageIds}
          />
        )
      case 5:
        return (
          <ReviewStep
            name={name}
            estimatedAge={estimatedAge}
            sex={sex}
            distinctiveMarkings={distinctiveMarkings}
            notes={notes}
            facilityId={facilityId}
            enclosure={enclosure}
            selectedImageIds={selectedImageIds}
            facilities={facilities}
            availableImages={availableImages}
          />
        )
    }
  }

  return (
    <Transition show={isOpen} as={Fragment}>
      <Dialog
        onClose={onClose}
        className="relative z-50"
        data-testid="tiger-registration-wizard"
      >
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
              data-testid="registration-wizard-panel"
              className="w-full max-w-2xl bg-white rounded-2xl shadow-xl overflow-hidden"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-tactical-800 to-tactical-900">
                <Dialog.Title className="text-lg font-semibold text-white">
                  Register New Tiger
                </Dialog.Title>
                <button
                  onClick={onClose}
                  data-testid="registration-wizard-close"
                  className="text-white/70 hover:text-white transition-colors"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              {/* Step Indicator */}
              <div className="px-6 py-4 border-b bg-gray-50">
                <StepIndicator
                  currentStep={currentStep}
                  totalSteps={5}
                  labels={STEP_LABELS}
                  icons={STEP_ICONS}
                  onStepClick={goToStep}
                  completedSteps={completedSteps}
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
                      data-testid="registration-back"
                    >
                      <ChevronLeftIcon className="w-4 h-4 mr-1" />
                      Back
                    </Button>
                  )}
                </div>

                <div className="flex items-center gap-3">
                  <Button
                    variant="ghost"
                    onClick={onClose}
                    data-testid="registration-cancel"
                  >
                    Cancel
                  </Button>

                  {currentStep < 5 ? (
                    <Button
                      onClick={goToNextStep}
                      disabled={!canProceed}
                      data-testid="registration-next"
                    >
                      Next
                      <ChevronRightIcon className="w-4 h-4 ml-1" />
                    </Button>
                  ) : (
                    <Button
                      onClick={handleSubmit}
                      isLoading={isSubmitting}
                      disabled={!canProceed || isSubmitting}
                      data-testid="registration-submit"
                    >
                      {isSubmitting ? 'Registering...' : 'Register Tiger'}
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

export default TigerRegistrationWizard

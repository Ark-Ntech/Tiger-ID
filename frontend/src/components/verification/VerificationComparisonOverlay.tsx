import { useEffect, useCallback, useState, Fragment } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { cn } from '../../utils/cn'
import Card from '../common/Card'
import Badge from '../common/Badge'
import Button from '../common/Button'
import {
  XMarkIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowsRightLeftIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassPlusIcon,
  MagnifyingGlassMinusIcon,
  BuildingOffice2Icon,
} from '@heroicons/react/24/outline'

export interface ComparisonImage {
  url: string
  tiger_id?: string
  tiger_name?: string
  facility?: string
  confidence?: number
  model?: string
  metadata?: Record<string, unknown>
}

export interface ModelScore {
  model: string
  score: number
}

export interface VerificationComparisonOverlayProps {
  isOpen: boolean
  onClose: () => void
  queryImage: ComparisonImage
  matchImage: ComparisonImage
  modelScores?: ModelScore[]
  onApprove?: () => void
  onReject?: () => void
  onSkip?: () => void
  className?: string
}

// Model display names mapping
const MODEL_DISPLAY_NAMES: Record<string, string> = {
  wildlife_tools: 'Wildlife Tools',
  cvwc2019_reid: 'CVWC2019 ReID',
  transreid: 'TransReID',
  megadescriptor_b: 'MegaDescriptor-B',
  tiger_reid: 'Tiger ReID',
  rapid_reid: 'Rapid ReID',
}

// Score threshold constants
const HIGH_CONFIDENCE_THRESHOLD = 0.85
const MEDIUM_CONFIDENCE_THRESHOLD = 0.70

// Get confidence indicator for a score
const getScoreIndicator = (score: number): { icon: string; variant: 'success' | 'warning' | 'danger' } => {
  if (score >= HIGH_CONFIDENCE_THRESHOLD) {
    return { icon: 'check', variant: 'success' }
  }
  if (score >= MEDIUM_CONFIDENCE_THRESHOLD) {
    return { icon: 'warning', variant: 'warning' }
  }
  return { icon: 'x', variant: 'danger' }
}

// Image preview component with zoom
interface ImagePreviewProps {
  image: ComparisonImage
  label: string
  testId: string
}

const ImagePreview = ({ image, label, testId }: ImagePreviewProps) => {
  const [isZoomed, setIsZoomed] = useState(false)
  const [zoomPosition, setZoomPosition] = useState({ x: 50, y: 50 })

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!isZoomed) return
    const rect = e.currentTarget.getBoundingClientRect()
    const x = ((e.clientX - rect.left) / rect.width) * 100
    const y = ((e.clientY - rect.top) / rect.height) * 100
    setZoomPosition({ x, y })
  }, [isZoomed])

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-tactical-700 dark:text-tactical-300">
            {label}
          </span>
          {image.tiger_name && (
            <Badge variant="tiger" size="sm">
              {image.tiger_name}
            </Badge>
          )}
        </div>
        <button
          onClick={() => setIsZoomed(!isZoomed)}
          className={cn(
            'p-1.5 rounded-lg transition-colors',
            'text-tactical-500 hover:text-tactical-700',
            'dark:text-tactical-400 dark:hover:text-tactical-200',
            'hover:bg-tactical-100 dark:hover:bg-tactical-700'
          )}
          title={isZoomed ? 'Zoom out' : 'Zoom in'}
        >
          {isZoomed ? (
            <MagnifyingGlassMinusIcon className="w-5 h-5" />
          ) : (
            <MagnifyingGlassPlusIcon className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* Image container */}
      <div
        data-testid={testId}
        className={cn(
          'relative flex-1 rounded-xl overflow-hidden',
          'bg-tactical-100 dark:bg-tactical-900',
          'border border-tactical-200 dark:border-tactical-700',
          isZoomed && 'cursor-crosshair'
        )}
        onClick={() => setIsZoomed(!isZoomed)}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setIsZoomed(false)}
      >
        <img
          src={image.url}
          alt={label}
          className={cn(
            'w-full h-full object-contain transition-transform duration-200',
            isZoomed && 'scale-150'
          )}
          style={
            isZoomed
              ? {
                  transformOrigin: `${zoomPosition.x}% ${zoomPosition.y}%`,
                }
              : undefined
          }
        />

        {/* Confidence badge overlay */}
        {image.confidence !== undefined && (
          <div className="absolute top-3 right-3">
            <Badge
              variant={
                image.confidence >= HIGH_CONFIDENCE_THRESHOLD
                  ? 'success'
                  : image.confidence >= MEDIUM_CONFIDENCE_THRESHOLD
                  ? 'warning'
                  : 'danger'
              }
              size="sm"
            >
              {(image.confidence * 100).toFixed(1)}% match
            </Badge>
          </div>
        )}
      </div>

      {/* Metadata */}
      <div className="mt-3 space-y-2">
        {image.tiger_id && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-tactical-500 dark:text-tactical-400">ID:</span>
            <span className="font-mono text-tactical-700 dark:text-tactical-300">
              {image.tiger_id}
            </span>
          </div>
        )}
        {image.facility && (
          <div className="flex items-center gap-2 text-sm">
            <BuildingOffice2Icon className="w-4 h-4 text-tactical-500 dark:text-tactical-400" />
            <span className="text-tactical-700 dark:text-tactical-300">
              {image.facility}
            </span>
          </div>
        )}
        {image.model && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-tactical-500 dark:text-tactical-400">Model:</span>
            <Badge variant="info" size="xs">
              {MODEL_DISPLAY_NAMES[image.model] || image.model}
            </Badge>
          </div>
        )}
      </div>
    </div>
  )
}

// Model scores visualization component
interface ModelScoresVisualizationProps {
  scores: ModelScore[]
}

const ModelScoresVisualization = ({ scores }: ModelScoresVisualizationProps) => {
  // Sort scores by value descending
  const sortedScores = [...scores].sort((a, b) => b.score - a.score)

  return (
    <div data-testid="comparison-model-scores" className="space-y-3">
      {sortedScores.map((item) => {
        const percentage = item.score * 100
        const indicator = getScoreIndicator(item.score)
        const displayName = MODEL_DISPLAY_NAMES[item.model] || item.model

        return (
          <div key={item.model} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-tactical-700 dark:text-tactical-300">
                {displayName}
              </span>
              <div className="flex items-center gap-2">
                <span className="font-mono text-tactical-600 dark:text-tactical-400">
                  {percentage.toFixed(0)}%
                </span>
                {indicator.icon === 'check' && (
                  <CheckCircleIcon className="w-4 h-4 text-emerald-500" />
                )}
                {indicator.icon === 'warning' && (
                  <ExclamationTriangleIcon className="w-4 h-4 text-amber-500" />
                )}
                {indicator.icon === 'x' && (
                  <XCircleIcon className="w-4 h-4 text-red-500" />
                )}
              </div>
            </div>
            {/* Progress bar */}
            <div className="h-2 rounded-full bg-tactical-200 dark:bg-tactical-700 overflow-hidden">
              <div
                className={cn(
                  'h-full rounded-full transition-all duration-500',
                  indicator.variant === 'success' && 'bg-emerald-500',
                  indicator.variant === 'warning' && 'bg-amber-500',
                  indicator.variant === 'danger' && 'bg-red-500'
                )}
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

export const VerificationComparisonOverlay = ({
  isOpen,
  onClose,
  queryImage,
  matchImage,
  modelScores,
  onApprove,
  onReject,
  onSkip,
  className,
}: VerificationComparisonOverlayProps) => {
  // Keyboard shortcuts
  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is typing in an input
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return
      }

      switch (e.key.toLowerCase()) {
        case 'a':
          e.preventDefault()
          onApprove?.()
          break
        case 'r':
          e.preventDefault()
          onReject?.()
          break
        case 's':
          e.preventDefault()
          onSkip?.()
          break
        case 'escape':
          e.preventDefault()
          onClose()
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onApprove, onReject, onSkip, onClose])

  // Calculate overall agreement
  const agreementStats = modelScores
    ? {
        total: modelScores.length,
        agreeing: modelScores.filter((s) => s.score >= MEDIUM_CONFIDENCE_THRESHOLD).length,
        highConfidence: modelScores.filter((s) => s.score >= HIGH_CONFIDENCE_THRESHOLD).length,
      }
    : null

  return (
    <Transition show={isOpen} as={Fragment}>
      <Dialog onClose={onClose} className="relative z-50">
        {/* Backdrop */}
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div
            className="fixed inset-0 bg-tactical-950/80 backdrop-blur-sm"
            aria-hidden="true"
          />
        </Transition.Child>

        {/* Full-screen container */}
        <div className="fixed inset-0 overflow-y-auto">
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
              data-testid="verification-comparison-overlay"
              className={cn(
                'w-full h-full flex flex-col',
                'bg-white dark:bg-tactical-800',
                className
              )}
            >
              {/* Header */}
              <div
                className={cn(
                  'flex items-center justify-between px-6 py-4',
                  'border-b border-tactical-200 dark:border-tactical-700',
                  'bg-tactical-50 dark:bg-tactical-900'
                )}
              >
                <div className="flex items-center gap-4">
                  <Dialog.Title className="text-xl font-semibold text-tactical-900 dark:text-tactical-100">
                    Verification Comparison
                  </Dialog.Title>
                  {agreementStats && (
                    <Badge
                      variant={
                        agreementStats.highConfidence === agreementStats.total
                          ? 'success'
                          : agreementStats.agreeing >= agreementStats.total / 2
                          ? 'warning'
                          : 'danger'
                      }
                      size="sm"
                    >
                      {agreementStats.agreeing}/{agreementStats.total} models agree
                    </Badge>
                  )}
                </div>

                <div className="flex items-center gap-3">
                  {/* Keyboard shortcuts hint */}
                  <div className="hidden md:flex items-center gap-2 text-xs text-tactical-500 dark:text-tactical-400">
                    <kbd className="px-2 py-1 rounded bg-tactical-200 dark:bg-tactical-700 font-mono">A</kbd>
                    <span>Approve</span>
                    <kbd className="px-2 py-1 rounded bg-tactical-200 dark:bg-tactical-700 font-mono ml-2">R</kbd>
                    <span>Reject</span>
                    <kbd className="px-2 py-1 rounded bg-tactical-200 dark:bg-tactical-700 font-mono ml-2">S</kbd>
                    <span>Skip</span>
                    <kbd className="px-2 py-1 rounded bg-tactical-200 dark:bg-tactical-700 font-mono ml-2">Esc</kbd>
                    <span>Close</span>
                  </div>

                  <button
                    data-testid="comparison-close-button"
                    onClick={onClose}
                    className={cn(
                      'p-2 rounded-lg transition-colors',
                      'text-tactical-500 hover:text-tactical-700',
                      'dark:text-tactical-400 dark:hover:text-tactical-200',
                      'hover:bg-tactical-200 dark:hover:bg-tactical-700'
                    )}
                    title="Close (Esc)"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-auto p-6">
                <div className="h-full flex flex-col lg:flex-row gap-6">
                  {/* Images comparison section */}
                  <div className="flex-1 flex flex-col md:flex-row gap-4 md:gap-6">
                    {/* Query Image */}
                    <Card
                      variant="default"
                      padding="md"
                      className="flex-1 flex flex-col min-h-[300px] md:min-h-0"
                    >
                      <ImagePreview
                        image={queryImage}
                        label="QUERY IMAGE"
                        testId="comparison-query-image"
                      />
                    </Card>

                    {/* Comparison indicator */}
                    <div className="flex items-center justify-center">
                      <div
                        className={cn(
                          'w-12 h-12 rounded-full flex items-center justify-center',
                          'bg-tactical-100 dark:bg-tactical-700',
                          'text-tactical-500 dark:text-tactical-400'
                        )}
                      >
                        <ArrowsRightLeftIcon className="w-6 h-6" />
                      </div>
                    </div>

                    {/* Match Image */}
                    <Card
                      variant="match"
                      padding="md"
                      className="flex-1 flex flex-col min-h-[300px] md:min-h-0"
                    >
                      <ImagePreview
                        image={matchImage}
                        label={`MATCH${matchImage.tiger_name ? `: ${matchImage.tiger_name}` : ''}`}
                        testId="comparison-match-image"
                      />
                    </Card>
                  </div>

                  {/* Model Agreement section */}
                  {modelScores && modelScores.length > 0 && (
                    <div className="lg:w-80 xl:w-96">
                      <Card variant="default" padding="md" className="h-full">
                        <div className="space-y-4">
                          <div className="flex items-center justify-between">
                            <h3 className="text-sm font-semibold text-tactical-900 dark:text-tactical-100 uppercase tracking-wide">
                              Model Agreement
                            </h3>
                            {agreementStats && (
                              <span className="text-xs text-tactical-500 dark:text-tactical-400">
                                {agreementStats.highConfidence} high confidence
                              </span>
                            )}
                          </div>
                          <ModelScoresVisualization scores={modelScores} />
                        </div>
                      </Card>
                    </div>
                  )}
                </div>
              </div>

              {/* Footer with actions */}
              <div
                className={cn(
                  'flex flex-col sm:flex-row items-center justify-center gap-4 px-6 py-4',
                  'border-t border-tactical-200 dark:border-tactical-700',
                  'bg-tactical-50 dark:bg-tactical-900'
                )}
              >
                {onReject && (
                  <Button
                    data-testid="comparison-reject-button"
                    variant="danger"
                    size="lg"
                    onClick={onReject}
                    className="w-full sm:w-auto min-w-[140px]"
                  >
                    <XCircleIcon className="w-5 h-5 mr-2" />
                    Reject
                  </Button>
                )}

                {onSkip && (
                  <Button
                    data-testid="comparison-skip-button"
                    variant="secondary"
                    size="lg"
                    onClick={onSkip}
                    className="w-full sm:w-auto min-w-[140px]"
                  >
                    Skip
                  </Button>
                )}

                {onApprove && (
                  <Button
                    data-testid="comparison-approve-button"
                    variant="primary"
                    size="lg"
                    onClick={onApprove}
                    className={cn(
                      'w-full sm:w-auto min-w-[140px]',
                      'bg-emerald-600 hover:bg-emerald-700 focus:ring-emerald-500'
                    )}
                  >
                    <CheckCircleIcon className="w-5 h-5 mr-2" />
                    Approve
                  </Button>
                )}
              </div>
            </Dialog.Panel>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition>
  )
}

export default VerificationComparisonOverlay

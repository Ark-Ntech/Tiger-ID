import { Fragment } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { XMarkIcon, PlusIcon, TrashIcon, DocumentArrowDownIcon } from '@heroicons/react/24/outline'
import { cn } from '../../../utils/cn'
import Card from '../../common/Card'
import Badge, { ConfidenceBadge } from '../../common/Badge'

/**
 * Tiger comparison data structure
 */
export interface TigerComparison {
  id: string
  name: string
  image_path: string
  confidence: number
  model: string
  facility?: {
    name: string
    location?: string
  }
  metadata?: Record<string, unknown>
}

/**
 * Props for the ComparisonDrawer component
 */
export interface ComparisonDrawerProps {
  /** Whether the drawer is open */
  isOpen: boolean
  /** Callback when drawer is closed */
  onClose: () => void
  /** Array of tigers to compare */
  tigers: TigerComparison[]
  /** Maximum number of tigers allowed (default: 4) */
  maxTigers?: number
  /** Callback when a tiger is removed */
  onRemoveTiger?: (tigerId: string) => void
  /** Callback to clear all tigers */
  onClearAll?: () => void
  /** Callback when export is clicked */
  onExport?: () => void
  /** Additional CSS classes */
  className?: string
}

/**
 * Get confidence color based on score
 */
function getConfidenceColor(confidence: number): 'success' | 'warning' | 'orange' | 'danger' {
  const normalized = confidence > 1 ? confidence / 100 : confidence
  if (normalized >= 0.85) return 'success'
  if (normalized >= 0.65) return 'warning'
  if (normalized >= 0.4) return 'orange'
  return 'danger'
}

/**
 * Get model display color based on model name
 */
function getModelColor(model: string): 'purple' | 'cyan' | 'info' | 'emerald' | 'amber' | 'default' {
  const modelColors: Record<string, 'purple' | 'cyan' | 'info' | 'emerald' | 'amber' | 'default'> = {
    wildlife_tools: 'emerald',
    cvwc2019_reid: 'purple',
    cvwc2019: 'purple',
    transreid: 'cyan',
    megadescriptor_b: 'info',
    megadescriptor: 'info',
    tiger_reid: 'amber',
    rapid_reid: 'default',
  }
  return modelColors[model.toLowerCase()] || 'default'
}

/**
 * Tiger comparison card component
 */
interface TigerCardProps {
  tiger: TigerComparison
  onRemove?: () => void
}

function TigerCard({ tiger, onRemove }: TigerCardProps) {
  const confidenceColor = getConfidenceColor(tiger.confidence)
  const modelColor = getModelColor(tiger.model)
  const confidencePercent = tiger.confidence > 1 ? tiger.confidence : tiger.confidence * 100

  return (
    <Card
      variant="default"
      padding="none"
      className="group relative overflow-hidden"
      data-testid={`comparison-tiger-${tiger.id}`}
    >
      {/* Image container with zoom on hover */}
      <div className="relative aspect-square overflow-hidden bg-tactical-100 dark:bg-tactical-800">
        <img
          src={tiger.image_path}
          alt={tiger.name}
          className={cn(
            'h-full w-full object-cover',
            'transition-transform duration-300 ease-out',
            'group-hover:scale-110'
          )}
          onError={(e) => {
            const target = e.target as HTMLImageElement
            target.src = '/placeholder-tiger.png'
            target.onerror = null
          }}
        />
        {/* Gradient overlay for better text visibility */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

        {/* Remove button */}
        {onRemove && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              onRemove()
            }}
            className={cn(
              'absolute top-2 right-2 p-1.5 rounded-full',
              'bg-red-500/90 text-white',
              'opacity-0 group-hover:opacity-100',
              'hover:bg-red-600',
              'transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-red-400 focus:ring-offset-2'
            )}
            data-testid={`comparison-remove-${tiger.id}`}
            aria-label={`Remove ${tiger.name} from comparison`}
          >
            <XMarkIcon className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Info section */}
      <div className="p-3 space-y-2">
        {/* Tiger name */}
        <h4 className="font-semibold text-tactical-900 dark:text-tactical-100 truncate" title={tiger.name}>
          {tiger.name}
        </h4>

        {/* Confidence score */}
        <div className="flex items-center gap-2">
          <ConfidenceBadge score={tiger.confidence} size="sm" showLabel={false} />
          <span className={cn(
            'text-sm font-medium',
            confidenceColor === 'success' && 'text-emerald-600 dark:text-emerald-400',
            confidenceColor === 'warning' && 'text-amber-600 dark:text-amber-400',
            confidenceColor === 'orange' && 'text-orange-600 dark:text-orange-400',
            confidenceColor === 'danger' && 'text-red-600 dark:text-red-400'
          )}>
            {confidencePercent.toFixed(0)}% match
          </span>
        </div>

        {/* Facility info */}
        {tiger.facility && (
          <p className="text-sm text-tactical-600 dark:text-tactical-400 truncate" title={tiger.facility.name}>
            {tiger.facility.name}
            {tiger.facility.location && (
              <span className="text-tactical-400 dark:text-tactical-500"> - {tiger.facility.location}</span>
            )}
          </p>
        )}

        {/* Model badge */}
        <Badge variant={modelColor} size="xs" className="capitalize">
          {tiger.model.replace(/_/g, ' ')}
        </Badge>
      </div>
    </Card>
  )
}

/**
 * Empty slot placeholder component
 */
function EmptySlot() {
  return (
    <div
      className={cn(
        'aspect-square rounded-xl border-2 border-dashed',
        'border-tactical-300 dark:border-tactical-600',
        'bg-tactical-50 dark:bg-tactical-800/50',
        'flex flex-col items-center justify-center gap-2',
        'text-tactical-400 dark:text-tactical-500'
      )}
    >
      <PlusIcon className="h-8 w-8" />
      <span className="text-sm font-medium">Add Tiger</span>
    </div>
  )
}

/**
 * ComparisonDrawer - A slide-out drawer for comparing up to 4 tigers side-by-side
 *
 * Features:
 * - Slide-in from right animation
 * - Backdrop with click-to-close
 * - Responsive: full-width on mobile, fixed width on desktop
 * - Image comparison with zoom on hover
 * - Confidence score with color coding
 * - Model and facility info
 * - Remove individual tigers
 * - Clear all button
 * - Export button
 */
export function ComparisonDrawer({
  isOpen,
  onClose,
  tigers,
  maxTigers = 4,
  onRemoveTiger,
  onClearAll,
  onExport,
  className,
}: ComparisonDrawerProps) {
  const tigerCount = tigers.length
  const emptySlots = Math.max(0, maxTigers - tigerCount)

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
            className="fixed inset-0 bg-black/40 backdrop-blur-sm"
            aria-hidden="true"
            data-testid="comparison-drawer-backdrop"
          />
        </Transition.Child>

        {/* Drawer container */}
        <div className="fixed inset-0 overflow-hidden">
          <div className="absolute inset-0 overflow-hidden">
            <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10 sm:pl-16">
              <Transition.Child
                as={Fragment}
                enter="transform transition ease-in-out duration-300"
                enterFrom="translate-x-full"
                enterTo="translate-x-0"
                leave="transform transition ease-in-out duration-300"
                leaveFrom="translate-x-0"
                leaveTo="translate-x-full"
              >
                <Dialog.Panel
                  className={cn(
                    'pointer-events-auto w-screen max-w-2xl',
                    className
                  )}
                  data-testid="comparison-drawer"
                >
                  <div className="flex h-full flex-col bg-white dark:bg-tactical-900 shadow-2xl">
                    {/* Header */}
                    <div className="flex items-center justify-between px-6 py-4 border-b border-tactical-200 dark:border-tactical-700">
                      <Dialog.Title className="flex items-center gap-3">
                        <span className="text-lg font-semibold text-tactical-900 dark:text-tactical-100">
                          Compare Tigers
                        </span>
                        <Badge variant="info" size="sm">
                          {tigerCount}
                        </Badge>
                      </Dialog.Title>
                      <button
                        type="button"
                        onClick={onClose}
                        className={cn(
                          'p-2 rounded-lg',
                          'text-tactical-500 hover:text-tactical-700',
                          'dark:text-tactical-400 dark:hover:text-tactical-200',
                          'hover:bg-tactical-100 dark:hover:bg-tactical-800',
                          'transition-colors duration-200',
                          'focus:outline-none focus:ring-2 focus:ring-tiger-orange focus:ring-offset-2'
                        )}
                        data-testid="comparison-drawer-close"
                        aria-label="Close comparison drawer"
                      >
                        <XMarkIcon className="h-6 w-6" />
                      </button>
                    </div>

                    {/* Content */}
                    <div className="flex-1 overflow-y-auto px-6 py-6">
                      {tigerCount === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-center">
                          <div className="p-4 rounded-full bg-tactical-100 dark:bg-tactical-800 mb-4">
                            <PlusIcon className="h-12 w-12 text-tactical-400 dark:text-tactical-500" />
                          </div>
                          <h3 className="text-lg font-medium text-tactical-900 dark:text-tactical-100 mb-2">
                            No tigers to compare
                          </h3>
                          <p className="text-tactical-600 dark:text-tactical-400 max-w-sm">
                            Add tigers from your search results to compare them side by side.
                          </p>
                        </div>
                      ) : (
                        <div className="grid grid-cols-2 gap-4">
                          {/* Tiger cards */}
                          {tigers.map((tiger) => (
                            <TigerCard
                              key={tiger.id}
                              tiger={tiger}
                              onRemove={onRemoveTiger ? () => onRemoveTiger(tiger.id) : undefined}
                            />
                          ))}

                          {/* Empty slots */}
                          {Array.from({ length: emptySlots }).map((_, index) => (
                            <EmptySlot key={`empty-${index}`} />
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Footer */}
                    <div className="flex items-center justify-between px-6 py-4 border-t border-tactical-200 dark:border-tactical-700 bg-tactical-50 dark:bg-tactical-800/50">
                      <button
                        type="button"
                        onClick={onClearAll}
                        disabled={tigerCount === 0}
                        className={cn(
                          'flex items-center gap-2 px-4 py-2 rounded-lg',
                          'text-sm font-medium',
                          'text-red-600 dark:text-red-400',
                          'hover:bg-red-50 dark:hover:bg-red-900/20',
                          'disabled:opacity-50 disabled:cursor-not-allowed',
                          'transition-colors duration-200',
                          'focus:outline-none focus:ring-2 focus:ring-red-400 focus:ring-offset-2'
                        )}
                        data-testid="comparison-clear-all"
                      >
                        <TrashIcon className="h-4 w-4" />
                        Clear All
                      </button>

                      <button
                        type="button"
                        onClick={onExport}
                        disabled={tigerCount === 0}
                        className={cn(
                          'flex items-center gap-2 px-4 py-2 rounded-lg',
                          'text-sm font-medium',
                          'bg-tiger-orange text-white',
                          'hover:bg-tiger-orange-dark',
                          'disabled:opacity-50 disabled:cursor-not-allowed',
                          'transition-colors duration-200',
                          'focus:outline-none focus:ring-2 focus:ring-tiger-orange focus:ring-offset-2'
                        )}
                        data-testid="comparison-export"
                      >
                        <DocumentArrowDownIcon className="h-4 w-4" />
                        Export Comparison Report
                      </button>
                    </div>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}

export default ComparisonDrawer

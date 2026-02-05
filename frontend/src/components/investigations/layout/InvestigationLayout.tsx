import { useState, useCallback, useRef, useEffect, type ReactNode } from 'react'
import { cn } from '../../../utils/cn'
import {
  ChevronDownIcon,
  ChevronUpIcon,
  PhotoIcon,
  ClockIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline'

/**
 * Props for the InvestigationLayout component.
 */
export interface InvestigationLayoutProps {
  /** The upload panel content (image upload, context fields) */
  uploadPanel: ReactNode
  /** The progress panel content (progress steps, model status) */
  progressPanel: ReactNode
  /** The results panel content (investigation results, report) */
  resultsPanel?: ReactNode
  /** When true, upload section collapses on mobile after image is selected */
  hasImage?: boolean
  /** When true, shows results instead of progress panel */
  isComplete?: boolean
  /** Additional CSS classes for the root container */
  className?: string
}

/**
 * Investigation status indicator for mobile sticky header.
 */
interface StatusIndicatorProps {
  hasImage: boolean
  isComplete: boolean
}

const StatusIndicator = ({ hasImage, isComplete }: StatusIndicatorProps) => {
  if (isComplete) {
    return (
      <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
        <CheckCircleIcon className="w-5 h-5" />
        <span className="font-medium">Complete</span>
      </div>
    )
  }

  if (hasImage) {
    return (
      <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
        <ClockIcon className="w-5 h-5 animate-pulse" />
        <span className="font-medium">In Progress</span>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2 text-tactical-500 dark:text-tactical-400">
      <PhotoIcon className="w-5 h-5" />
      <span className="font-medium">Awaiting Image</span>
    </div>
  )
}

/**
 * Mobile collapsible section component.
 */
interface CollapsibleSectionProps {
  title: string
  children: ReactNode
  isOpen: boolean
  onToggle: () => void
  testId: string
  icon?: ReactNode
  badge?: string
}

const CollapsibleSection = ({
  title,
  children,
  isOpen,
  onToggle,
  testId,
  icon,
  badge,
}: CollapsibleSectionProps) => {
  return (
    <div
      className="border border-tactical-200 dark:border-tactical-700 rounded-xl overflow-hidden"
      data-testid={testId}
    >
      <button
        type="button"
        onClick={onToggle}
        className={cn(
          'w-full flex items-center justify-between px-4 py-3',
          'bg-tactical-50 dark:bg-tactical-800/50',
          'hover:bg-tactical-100 dark:hover:bg-tactical-700/50',
          'transition-colors duration-200'
        )}
        aria-expanded={isOpen}
        data-testid={`${testId}-toggle`}
      >
        <div className="flex items-center gap-3">
          {icon && (
            <span className="text-tactical-500 dark:text-tactical-400">
              {icon}
            </span>
          )}
          <span className="font-medium text-tactical-900 dark:text-tactical-100">
            {title}
          </span>
          {badge && (
            <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300">
              {badge}
            </span>
          )}
        </div>
        <span className="text-tactical-400">
          {isOpen ? (
            <ChevronUpIcon className="w-5 h-5" />
          ) : (
            <ChevronDownIcon className="w-5 h-5" />
          )}
        </span>
      </button>
      <div
        className={cn(
          'transition-all duration-300 ease-in-out overflow-hidden',
          isOpen ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
        )}
        data-testid={`${testId}-content`}
      >
        <div className="p-4">{children}</div>
      </div>
    </div>
  )
}

/**
 * Responsive layout component for Investigation 2.0 pages.
 *
 * Layout behavior:
 * - Desktop (lg+): 2-column grid - upload panel on left, progress/results on right
 * - Tablet (md): Stacked single column with full-width sections
 * - Mobile (sm): Collapsible upload section after image is selected
 *
 * Features:
 * - Smooth CSS transitions when collapsing/expanding
 * - Sticky header on mobile with investigation status
 * - Touch-friendly collapsible sections on mobile
 * - Proper focus management and accessibility
 */
const InvestigationLayout = ({
  uploadPanel,
  progressPanel,
  resultsPanel,
  hasImage = false,
  isComplete = false,
  className,
}: InvestigationLayoutProps) => {
  // Mobile collapsible state - auto-collapse upload when image is selected
  const [uploadExpanded, setUploadExpanded] = useState(!hasImage)
  const [progressExpanded, setProgressExpanded] = useState(true)

  // Track touch start for swipe detection
  const touchStartRef = useRef<{ x: number; y: number } | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Auto-collapse upload section on mobile when image is added
  useEffect(() => {
    if (hasImage) {
      // Small delay to allow user to see the preview before collapsing
      const timer = setTimeout(() => {
        setUploadExpanded(false)
      }, 500)
      return () => clearTimeout(timer)
    } else {
      setUploadExpanded(true)
    }
  }, [hasImage])

  // Expand progress section when investigation starts
  useEffect(() => {
    if (hasImage && !isComplete) {
      setProgressExpanded(true)
    }
  }, [hasImage, isComplete])

  // Swipe gesture handlers (optional enhancement for mobile)
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    touchStartRef.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY,
    }
  }, [])

  const handleTouchEnd = useCallback(
    (e: React.TouchEvent) => {
      if (!touchStartRef.current) return

      const touchEnd = {
        x: e.changedTouches[0].clientX,
        y: e.changedTouches[0].clientY,
      }

      const deltaX = touchEnd.x - touchStartRef.current.x
      const deltaY = touchEnd.y - touchStartRef.current.y

      // Only detect horizontal swipes (more horizontal than vertical movement)
      if (Math.abs(deltaX) > 50 && Math.abs(deltaX) > Math.abs(deltaY)) {
        // Swipe left - collapse upload, expand progress
        if (deltaX < 0 && hasImage) {
          setUploadExpanded(false)
          setProgressExpanded(true)
        }
        // Swipe right - expand upload, collapse progress
        if (deltaX > 0) {
          setUploadExpanded(true)
          setProgressExpanded(false)
        }
      }

      touchStartRef.current = null
    },
    [hasImage]
  )

  const toggleUpload = useCallback(() => {
    setUploadExpanded((prev) => !prev)
  }, [])

  const toggleProgress = useCallback(() => {
    setProgressExpanded((prev) => !prev)
  }, [])

  // Determine which panel to show in the right column
  const rightPanelContent = isComplete && resultsPanel ? resultsPanel : progressPanel

  return (
    <div
      ref={containerRef}
      className={cn('w-full', className)}
      data-testid="investigation-layout"
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {/* Mobile Sticky Header - Only visible on small screens */}
      <div
        className={cn(
          'lg:hidden sticky top-0 z-30 -mx-4 px-4 py-3 mb-4',
          'bg-white/95 dark:bg-tactical-900/95 backdrop-blur-sm',
          'border-b border-tactical-200 dark:border-tactical-700',
          'shadow-sm'
        )}
        data-testid="investigation-layout-mobile-header"
      >
        <div className="flex items-center justify-between">
          <StatusIndicator hasImage={hasImage} isComplete={isComplete} />
          {hasImage && !isComplete && (
            <span className="text-xs text-tactical-500 dark:text-tactical-400">
              Swipe to navigate
            </span>
          )}
        </div>
      </div>

      {/* Desktop Layout (lg+): 2-column grid */}
      <div
        className="hidden lg:grid lg:grid-cols-2 lg:gap-6"
        data-testid="investigation-layout-desktop"
      >
        {/* Left Column - Upload Panel */}
        <div
          className="space-y-6"
          data-testid="investigation-layout-upload-column"
        >
          {uploadPanel}
        </div>

        {/* Right Column - Progress or Results Panel */}
        <div
          className="space-y-6"
          data-testid="investigation-layout-right-column"
        >
          {rightPanelContent}
        </div>
      </div>

      {/* Tablet Layout (md): Stacked full-width sections */}
      <div
        className="hidden md:block lg:hidden space-y-6"
        data-testid="investigation-layout-tablet"
      >
        {/* Upload Section - Full width */}
        <div data-testid="investigation-layout-tablet-upload">
          {uploadPanel}
        </div>

        {/* Progress/Results Section - Full width */}
        <div data-testid="investigation-layout-tablet-progress">
          {rightPanelContent}
        </div>
      </div>

      {/* Mobile Layout (sm): Collapsible sections */}
      <div
        className="md:hidden space-y-4"
        data-testid="investigation-layout-mobile"
      >
        {/* Collapsible Upload Section */}
        <CollapsibleSection
          title="Upload Image"
          isOpen={uploadExpanded}
          onToggle={toggleUpload}
          testId="investigation-layout-mobile-upload"
          icon={<PhotoIcon className="w-5 h-5" />}
          badge={hasImage ? 'Ready' : undefined}
        >
          {uploadPanel}
        </CollapsibleSection>

        {/* Progress/Results Section - Always visible but collapsible */}
        {(hasImage || isComplete) && (
          <CollapsibleSection
            title={isComplete ? 'Results' : 'Progress'}
            isOpen={progressExpanded}
            onToggle={toggleProgress}
            testId="investigation-layout-mobile-progress"
            icon={
              isComplete ? (
                <CheckCircleIcon className="w-5 h-5" />
              ) : (
                <ClockIcon className="w-5 h-5" />
              )
            }
            badge={isComplete ? 'Complete' : 'Active'}
          >
            {rightPanelContent}
          </CollapsibleSection>
        )}
      </div>
    </div>
  )
}

export default InvestigationLayout

// Re-export for convenience
export { CollapsibleSection, StatusIndicator }

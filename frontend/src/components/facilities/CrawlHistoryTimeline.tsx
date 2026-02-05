import { useState, useMemo } from 'react'
import { cn } from '../../utils/cn'
import Card, { CardHeader, CardTitle } from '../common/Card'
import Button from '../common/Button'
import Badge from '../common/Badge'
import LoadingSpinner from '../common/LoadingSpinner'
import {
  PlayIcon,
  CheckCircleIcon,
  PhotoIcon,
  FingerPrintIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'

/**
 * Represents a single crawl event in a facility's history
 */
export interface CrawlEvent {
  id: string
  timestamp: string
  type: 'crawl_started' | 'crawl_completed' | 'images_found' | 'tigers_detected' | 'rate_limited' | 'error'
  details: {
    imageCount?: number
    tigerCount?: number
    duration?: number
    errorMessage?: string
    waitTime?: number
  }
}

/**
 * Props for the CrawlHistoryTimeline component
 */
export interface CrawlHistoryTimelineProps {
  events: CrawlEvent[]
  facilityId: string
  maxEvents?: number
  onLoadMore?: () => void
  hasMore?: boolean
  isLoading?: boolean
  className?: string
}

/**
 * Event type configuration with icons and colors
 */
const eventTypeConfig: Record<
  CrawlEvent['type'],
  {
    icon: typeof PlayIcon
    label: string
    dotColor: string
    iconColor: string
    bgColor: string
    variant: 'info' | 'success' | 'warning' | 'danger' | 'purple' | 'tiger'
  }
> = {
  crawl_started: {
    icon: PlayIcon,
    label: 'Crawl Started',
    dotColor: 'bg-blue-500',
    iconColor: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    variant: 'info',
  },
  crawl_completed: {
    icon: CheckCircleIcon,
    label: 'Crawl Completed',
    dotColor: 'bg-emerald-500',
    iconColor: 'text-emerald-600 dark:text-emerald-400',
    bgColor: 'bg-emerald-50 dark:bg-emerald-900/20',
    variant: 'success',
  },
  images_found: {
    icon: PhotoIcon,
    label: 'Images Found',
    dotColor: 'bg-purple-500',
    iconColor: 'text-purple-600 dark:text-purple-400',
    bgColor: 'bg-purple-50 dark:bg-purple-900/20',
    variant: 'purple',
  },
  tigers_detected: {
    icon: FingerPrintIcon,
    label: 'Tigers Detected',
    dotColor: 'bg-tiger-orange',
    iconColor: 'text-tiger-orange dark:text-tiger-orange-light',
    bgColor: 'bg-orange-50 dark:bg-orange-900/20',
    variant: 'tiger',
  },
  rate_limited: {
    icon: ClockIcon,
    label: 'Rate Limited',
    dotColor: 'bg-amber-500',
    iconColor: 'text-amber-600 dark:text-amber-400',
    bgColor: 'bg-amber-50 dark:bg-amber-900/20',
    variant: 'warning',
  },
  error: {
    icon: ExclamationTriangleIcon,
    label: 'Error',
    dotColor: 'bg-red-500',
    iconColor: 'text-red-600 dark:text-red-400',
    bgColor: 'bg-red-50 dark:bg-red-900/20',
    variant: 'danger',
  },
}

/**
 * Format a timestamp into relative and absolute formats
 */
function formatTimestamp(timestamp: string): { relative: string; absolute: string } {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffMinutes = Math.floor(diffMs / (1000 * 60))

  let relative: string
  if (diffMinutes < 1) {
    relative = 'Just now'
  } else if (diffMinutes < 60) {
    relative = `${diffMinutes}m ago`
  } else if (diffHours < 24) {
    relative = `${diffHours}h ago`
  } else if (diffDays < 7) {
    relative = `${diffDays}d ago`
  } else if (diffDays < 30) {
    const weeks = Math.floor(diffDays / 7)
    relative = `${weeks}w ago`
  } else if (diffDays < 365) {
    const months = Math.floor(diffDays / 30)
    relative = `${months}mo ago`
  } else {
    const years = Math.floor(diffDays / 365)
    relative = `${years}y ago`
  }

  const absolute = date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

  return { relative, absolute }
}

/**
 * Format duration in milliseconds to human-readable string
 */
function formatDuration(durationMs: number): string {
  if (durationMs < 1000) {
    return `${durationMs}ms`
  }
  const seconds = Math.floor(durationMs / 1000)
  if (seconds < 60) {
    return `${seconds}s`
  }
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes < 60) {
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`
  }
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`
}

/**
 * Single timeline event component
 */
interface TimelineEventItemProps {
  event: CrawlEvent
  isLast: boolean
}

function TimelineEventItem({ event, isLast }: TimelineEventItemProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const config = eventTypeConfig[event.type]
  const Icon = config.icon
  const { relative, absolute } = formatTimestamp(event.timestamp)

  // Determine if event has expandable details
  const hasDetails =
    event.details.duration !== undefined ||
    event.details.imageCount !== undefined ||
    event.details.tigerCount !== undefined ||
    event.details.errorMessage !== undefined ||
    event.details.waitTime !== undefined

  const handleToggle = () => {
    if (hasDetails) {
      setIsExpanded(!isExpanded)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (hasDetails && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault()
      handleToggle()
    }
  }

  return (
    <div
      data-testid={`crawl-event-${event.id}`}
      className={cn('relative pl-10', !isLast && 'pb-6')}
    >
      {/* Timeline connector line */}
      {!isLast && (
        <div
          className={cn(
            'absolute left-[15px] top-8 w-0.5 h-[calc(100%-20px)]',
            'bg-tactical-200 dark:bg-tactical-700'
          )}
          aria-hidden="true"
          data-testid="timeline-connector"
        />
      )}

      {/* Event icon */}
      <div
        className={cn(
          'absolute left-0 top-0 w-8 h-8 rounded-full',
          'flex items-center justify-center',
          config.bgColor,
          'border-2 border-white dark:border-tactical-900',
          'shadow-sm'
        )}
        data-testid={`event-icon-${event.type}`}
      >
        <Icon
          className={cn('w-4 h-4', config.iconColor)}
          aria-hidden="true"
        />
      </div>

      {/* Event content */}
      <div
        className={cn(
          'rounded-lg border transition-all duration-200',
          'bg-white dark:bg-tactical-800',
          'border-tactical-200 dark:border-tactical-700',
          hasDetails && 'cursor-pointer hover:border-tactical-300 dark:hover:border-tactical-600',
          isExpanded && 'shadow-tactical-md'
        )}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        tabIndex={hasDetails ? 0 : undefined}
        role={hasDetails ? 'button' : undefined}
        aria-expanded={hasDetails ? isExpanded : undefined}
      >
        {/* Event header */}
        <div className="p-3">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-2">
              <Badge
                variant={config.variant}
                size="sm"
                data-testid={`event-badge-${event.type}`}
              >
                {config.label}
              </Badge>

              {/* Quick stats inline for certain event types */}
              {event.type === 'images_found' && event.details.imageCount !== undefined && (
                <span className="text-sm font-medium text-tactical-700 dark:text-tactical-300">
                  {event.details.imageCount} image{event.details.imageCount !== 1 ? 's' : ''}
                </span>
              )}
              {event.type === 'tigers_detected' && event.details.tigerCount !== undefined && (
                <span className="text-sm font-medium text-tiger-orange dark:text-tiger-orange-light">
                  {event.details.tigerCount} tiger{event.details.tigerCount !== 1 ? 's' : ''}
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              <span
                className="text-xs text-tactical-500 dark:text-tactical-400"
                title={absolute}
                data-testid="event-timestamp"
              >
                {relative}
              </span>

              {hasDetails && (
                <span className="text-tactical-400 dark:text-tactical-500">
                  {isExpanded ? (
                    <ChevronUpIcon className="w-4 h-4" />
                  ) : (
                    <ChevronDownIcon className="w-4 h-4" />
                  )}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Expandable details */}
        {hasDetails && isExpanded && (
          <div
            className={cn(
              'px-3 pb-3 pt-0',
              'border-t border-tactical-100 dark:border-tactical-700/50'
            )}
            data-testid="event-details"
          >
            <div className="pt-3 space-y-2">
              {/* Crawl completed details */}
              {event.type === 'crawl_completed' && (
                <>
                  {event.details.duration !== undefined && (
                    <DetailRow
                      label="Duration"
                      value={formatDuration(event.details.duration)}
                      testId="detail-duration"
                    />
                  )}
                  {event.details.imageCount !== undefined && (
                    <DetailRow
                      label="Images found"
                      value={event.details.imageCount.toString()}
                      testId="detail-image-count"
                    />
                  )}
                  {event.details.tigerCount !== undefined && (
                    <DetailRow
                      label="Tigers detected"
                      value={event.details.tigerCount.toString()}
                      highlight
                      testId="detail-tiger-count"
                    />
                  )}
                </>
              )}

              {/* Rate limited details */}
              {event.type === 'rate_limited' && event.details.waitTime !== undefined && (
                <DetailRow
                  label="Wait time"
                  value={formatDuration(event.details.waitTime)}
                  testId="detail-wait-time"
                />
              )}

              {/* Error details */}
              {event.type === 'error' && event.details.errorMessage && (
                <div className="mt-2" data-testid="detail-error-message">
                  <p className="text-xs font-medium text-tactical-500 dark:text-tactical-400 mb-1">
                    Error message
                  </p>
                  <p className="text-sm text-red-600 dark:text-red-400 font-mono bg-red-50 dark:bg-red-900/20 rounded px-2 py-1.5">
                    {event.details.errorMessage}
                  </p>
                </div>
              )}

              {/* Full timestamp */}
              <DetailRow
                label="Timestamp"
                value={absolute}
                testId="detail-timestamp"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Detail row component for expanded event details
 */
interface DetailRowProps {
  label: string
  value: string
  highlight?: boolean
  testId?: string
}

function DetailRow({ label, value, highlight = false, testId }: DetailRowProps) {
  return (
    <div className="flex items-center justify-between text-sm" data-testid={testId}>
      <span className="text-tactical-500 dark:text-tactical-400">{label}</span>
      <span
        className={cn(
          'font-medium',
          highlight
            ? 'text-tiger-orange dark:text-tiger-orange-light'
            : 'text-tactical-700 dark:text-tactical-300'
        )}
      >
        {value}
      </span>
    </div>
  )
}

/**
 * Empty state component when no events exist
 */
function EmptyState() {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 px-4',
        'text-center'
      )}
      data-testid="crawl-history-empty"
    >
      <div
        className={cn(
          'w-16 h-16 rounded-full mb-4',
          'bg-tactical-100 dark:bg-tactical-800',
          'flex items-center justify-center'
        )}
      >
        <ArrowPathIcon className="w-8 h-8 text-tactical-400 dark:text-tactical-500" />
      </div>
      <h4 className="text-lg font-medium text-tactical-700 dark:text-tactical-300 mb-2">
        No crawl history
      </h4>
      <p className="text-sm text-tactical-500 dark:text-tactical-400 max-w-sm">
        This facility has not been crawled yet. Crawl events will appear here once the
        discovery pipeline processes this facility.
      </p>
    </div>
  )
}

/**
 * CrawlHistoryTimeline component
 *
 * Displays a chronological timeline of all crawl events for a specific facility.
 * Events include crawl starts, completions, image discoveries, tiger detections,
 * rate limiting events, and errors.
 *
 * @example
 * ```tsx
 * <CrawlHistoryTimeline
 *   events={crawlEvents}
 *   facilityId="facility-123"
 *   maxEvents={10}
 *   onLoadMore={() => fetchMoreEvents()}
 *   hasMore={true}
 *   isLoading={false}
 * />
 * ```
 */
export function CrawlHistoryTimeline({
  events,
  facilityId: _facilityId,
  maxEvents,
  onLoadMore,
  hasMore = false,
  isLoading = false,
  className,
}: CrawlHistoryTimelineProps) {
  // Note: facilityId is available for future use (e.g., linking to facility details)
  void _facilityId
  const [isExpanded, setIsExpanded] = useState(false)

  // Sort events by timestamp (most recent first)
  const sortedEvents = useMemo(() => {
    return [...events].sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )
  }, [events])

  // Determine if we need to show the internal "show more" toggle
  const shouldShowToggle =
    maxEvents !== undefined && sortedEvents.length > maxEvents && !onLoadMore
  const displayedEvents =
    isExpanded || !shouldShowToggle
      ? sortedEvents
      : sortedEvents.slice(0, maxEvents)
  const hiddenCount = sortedEvents.length - (maxEvents ?? sortedEvents.length)

  // Count summary stats
  const summaryStats = useMemo(() => {
    const completed = events.filter((e) => e.type === 'crawl_completed').length
    const errors = events.filter((e) => e.type === 'error').length
    const totalTigers = events
      .filter((e) => e.type === 'tigers_detected')
      .reduce((sum, e) => sum + (e.details.tigerCount ?? 0), 0)
    return { completed, errors, totalTigers }
  }, [events])

  return (
    <Card
      data-testid="crawl-history-timeline"
      className={className}
      padding="none"
    >
      <div className="p-6 pb-4">
        <CardHeader>
          <CardTitle>Crawl History</CardTitle>
        </CardHeader>

        {/* Summary stats */}
        {events.length > 0 && (
          <div
            className="flex items-center gap-4 text-sm"
            data-testid="crawl-summary-stats"
          >
            <div className="flex items-center gap-1.5">
              <CheckCircleIcon className="w-4 h-4 text-emerald-500" />
              <span className="text-tactical-600 dark:text-tactical-400">
                {summaryStats.completed} crawl{summaryStats.completed !== 1 ? 's' : ''}
              </span>
            </div>
            {summaryStats.totalTigers > 0 && (
              <div className="flex items-center gap-1.5">
                <FingerPrintIcon className="w-4 h-4 text-tiger-orange" />
                <span className="text-tactical-600 dark:text-tactical-400">
                  {summaryStats.totalTigers} tiger{summaryStats.totalTigers !== 1 ? 's' : ''}
                </span>
              </div>
            )}
            {summaryStats.errors > 0 && (
              <div className="flex items-center gap-1.5">
                <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />
                <span className="text-tactical-600 dark:text-tactical-400">
                  {summaryStats.errors} error{summaryStats.errors !== 1 ? 's' : ''}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {events.length === 0 ? (
        <EmptyState />
      ) : (
        <>
          {/* Timeline events */}
          <div
            data-testid="crawl-events-list"
            className="px-6 py-2"
            role="list"
            aria-label="Crawl history events"
          >
            {displayedEvents.map((event, index) => (
              <TimelineEventItem
                key={event.id}
                event={event}
                isLast={index === displayedEvents.length - 1 && !hasMore}
              />
            ))}
          </div>

          {/* Loading indicator */}
          {isLoading && (
            <div
              className="flex items-center justify-center py-4"
              data-testid="crawl-history-loading"
            >
              <LoadingSpinner size="sm" />
              <span className="ml-2 text-sm text-tactical-500 dark:text-tactical-400">
                Loading more events...
              </span>
            </div>
          )}

          {/* Load more button (for paginated data from server) */}
          {hasMore && onLoadMore && !isLoading && (
            <div className="px-6 pb-6 pt-2">
              <Button
                data-testid="crawl-history-load-more"
                variant="secondary"
                size="sm"
                onClick={onLoadMore}
                className="w-full"
              >
                <ArrowPathIcon className="w-4 h-4 mr-2" />
                Load more events
              </Button>
            </div>
          )}

          {/* Show more/less toggle (for local data limiting) */}
          {shouldShowToggle && (
            <div className="px-6 pb-6 pt-2">
              <button
                data-testid="crawl-history-show-more"
                type="button"
                onClick={() => setIsExpanded(!isExpanded)}
                className={cn(
                  'w-full flex items-center justify-center gap-2 py-2.5 px-4',
                  'text-sm font-medium rounded-lg',
                  'text-tactical-600 dark:text-tactical-300',
                  'bg-tactical-50 dark:bg-tactical-800/50',
                  'hover:bg-tactical-100 dark:hover:bg-tactical-700/50',
                  'border border-tactical-200 dark:border-tactical-700',
                  'transition-colors'
                )}
              >
                {isExpanded ? (
                  <>
                    <ChevronUpIcon className="w-4 h-4" />
                    Show less
                  </>
                ) : (
                  <>
                    <ChevronDownIcon className="w-4 h-4" />
                    Show {hiddenCount} more event{hiddenCount === 1 ? '' : 's'}
                  </>
                )}
              </button>
            </div>
          )}
        </>
      )}
    </Card>
  )
}

export default CrawlHistoryTimeline

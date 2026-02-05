import { useState, useMemo } from 'react'
import { cn } from '../../utils/cn'
import Card, { CardHeader, CardTitle } from '../common/Card'
import {
  PlusCircleIcon,
  FingerPrintIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowsPointingInIcon,
  ClockIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline'

/**
 * Represents a single identification event in a tiger's history
 */
export interface IdentificationEvent {
  id: string
  timestamp: string
  type: 'matched' | 'registered' | 'verified' | 'disputed' | 'merged'
  investigation_id?: string
  confidence?: number
  matched_with?: {
    tiger_id: string
    tiger_name: string
  }
  facility?: string
  user?: string
  notes?: string
}

/**
 * Props for the TigerIdentificationTimeline component
 */
export interface TigerIdentificationTimelineProps {
  events: IdentificationEvent[]
  tigerId: string
  tigerName: string
  onEventClick?: (event: IdentificationEvent) => void
  maxEvents?: number
  className?: string
}

/**
 * Event type configuration with icons and colors
 */
const eventTypeConfig: Record<
  IdentificationEvent['type'],
  {
    icon: typeof PlusCircleIcon
    label: string
    dotColor: string
    iconColor: string
    bgColor: string
  }
> = {
  registered: {
    icon: PlusCircleIcon,
    label: 'Registered',
    dotColor: 'bg-blue-500',
    iconColor: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
  },
  matched: {
    icon: FingerPrintIcon,
    label: 'Matched',
    dotColor: 'bg-tiger-orange',
    iconColor: 'text-tiger-orange dark:text-tiger-orange-light',
    bgColor: 'bg-orange-50 dark:bg-orange-900/20',
  },
  verified: {
    icon: CheckCircleIcon,
    label: 'Verified',
    dotColor: 'bg-emerald-500',
    iconColor: 'text-emerald-600 dark:text-emerald-400',
    bgColor: 'bg-emerald-50 dark:bg-emerald-900/20',
  },
  disputed: {
    icon: ExclamationTriangleIcon,
    label: 'Disputed',
    dotColor: 'bg-amber-500',
    iconColor: 'text-amber-600 dark:text-amber-400',
    bgColor: 'bg-amber-50 dark:bg-amber-900/20',
  },
  merged: {
    icon: ArrowsPointingInIcon,
    label: 'Merged',
    dotColor: 'bg-purple-500',
    iconColor: 'text-purple-600 dark:text-purple-400',
    bgColor: 'bg-purple-50 dark:bg-purple-900/20',
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
    relative = `${diffMinutes} minute${diffMinutes === 1 ? '' : 's'} ago`
  } else if (diffHours < 24) {
    relative = `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`
  } else if (diffDays < 7) {
    relative = `${diffDays} day${diffDays === 1 ? '' : 's'} ago`
  } else if (diffDays < 30) {
    const weeks = Math.floor(diffDays / 7)
    relative = `${weeks} week${weeks === 1 ? '' : 's'} ago`
  } else if (diffDays < 365) {
    const months = Math.floor(diffDays / 30)
    relative = `${months} month${months === 1 ? '' : 's'} ago`
  } else {
    const years = Math.floor(diffDays / 365)
    relative = `${years} year${years === 1 ? '' : 's'} ago`
  }

  const absolute = date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })

  return { relative, absolute }
}

/**
 * Format confidence score as percentage
 */
function formatConfidence(confidence: number): string {
  const normalized = confidence > 1 ? confidence : confidence * 100
  return `${Math.round(normalized)}%`
}

/**
 * Single timeline event component
 */
interface TimelineEventItemProps {
  event: IdentificationEvent
  isLast: boolean
  onClick?: () => void
}

function TimelineEventItem({ event, isLast, onClick }: TimelineEventItemProps) {
  const config = eventTypeConfig[event.type]
  const Icon = config.icon
  const { relative, absolute } = formatTimestamp(event.timestamp)

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (onClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault()
      onClick()
    }
  }

  return (
    <div
      data-testid={`timeline-event-${event.id}`}
      className={cn(
        'relative pl-8',
        onClick && 'cursor-pointer',
        !isLast && 'pb-6'
      )}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      tabIndex={onClick ? 0 : undefined}
      role={onClick ? 'button' : undefined}
    >
      {/* Timeline connector line */}
      {!isLast && (
        <div
          className={cn(
            'absolute left-[11px] top-6 w-0.5 h-[calc(100%-12px)]',
            'bg-tactical-200 dark:bg-tactical-700'
          )}
          aria-hidden="true"
        />
      )}

      {/* Event dot */}
      <div
        className={cn(
          'absolute left-0 top-0.5 w-6 h-6 rounded-full',
          'flex items-center justify-center',
          config.bgColor
        )}
      >
        <span
          className={cn('w-2.5 h-2.5 rounded-full', config.dotColor)}
          aria-hidden="true"
        />
      </div>

      {/* Event content */}
      <div
        className={cn(
          'rounded-lg p-3 transition-colors',
          onClick && 'hover:bg-tactical-50 dark:hover:bg-tactical-800/50'
        )}
      >
        {/* Header with date and type */}
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className="text-sm font-medium text-tactical-900 dark:text-tactical-100"
            title={absolute}
          >
            {absolute}
          </span>
          <span className="text-tactical-400 dark:text-tactical-500">-</span>
          <div className="flex items-center gap-1.5">
            <Icon className={cn('w-4 h-4', config.iconColor)} aria-hidden="true" />
            <span className={cn('text-sm font-semibold', config.iconColor)}>
              {config.label}
              {event.type === 'matched' && event.confidence !== undefined && (
                <span className="ml-1">({formatConfidence(event.confidence)})</span>
              )}
              {event.type === 'verified' && (
                <span className="ml-1" aria-label="Verified">
                  <CheckCircleIcon className="w-4 h-4 inline-block" />
                </span>
              )}
            </span>
          </div>
          <span
            className="text-xs text-tactical-500 dark:text-tactical-400 ml-auto"
            title={absolute}
          >
            {relative}
          </span>
        </div>

        {/* Event details */}
        <div className="mt-2 space-y-1">
          {/* Investigation ID */}
          {event.investigation_id && (
            <p className="text-sm text-tactical-600 dark:text-tactical-400">
              Investigation{' '}
              <span className="font-mono text-tactical-700 dark:text-tactical-300">
                #{event.investigation_id}
              </span>
            </p>
          )}

          {/* Matched with */}
          {event.matched_with && (
            <p className="text-sm text-tactical-600 dark:text-tactical-400">
              Matched with{' '}
              <span className="font-medium text-tactical-700 dark:text-tactical-300">
                {event.matched_with.tiger_name}
              </span>
            </p>
          )}

          {/* Facility */}
          {event.facility && (
            <p className="text-sm text-tactical-600 dark:text-tactical-400">
              {event.type === 'registered' ? 'First sighting at ' : 'Location: '}
              <span className="font-medium text-tactical-700 dark:text-tactical-300">
                {event.facility}
              </span>
            </p>
          )}

          {/* User */}
          {event.user && (
            <p className="text-sm text-tactical-500 dark:text-tactical-400">
              By:{' '}
              <span className="text-tactical-600 dark:text-tactical-300">
                {event.user}
              </span>
            </p>
          )}

          {/* Notes */}
          {event.notes && (
            <p className="text-sm text-tactical-600 dark:text-tactical-400 mt-2 italic">
              {event.notes}
            </p>
          )}

          {/* View Investigation Link */}
          {event.investigation_id && (
            <button
              data-testid="timeline-view-investigation"
              type="button"
              className={cn(
                'inline-flex items-center gap-1 mt-2',
                'text-sm font-medium',
                'text-blue-600 hover:text-blue-700',
                'dark:text-blue-400 dark:hover:text-blue-300',
                'transition-colors'
              )}
              onClick={(e) => {
                e.stopPropagation()
                // Navigate to investigation - this would be handled by parent
              }}
            >
              View Investigation
              <svg
                className="w-3.5 h-3.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * Empty state component when no events exist
 */
function EmptyState({ tigerName }: { tigerName: string }) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 px-4',
        'text-center'
      )}
    >
      <div
        className={cn(
          'w-16 h-16 rounded-full mb-4',
          'bg-tactical-100 dark:bg-tactical-800',
          'flex items-center justify-center'
        )}
      >
        <ClockIcon className="w-8 h-8 text-tactical-400 dark:text-tactical-500" />
      </div>
      <h4 className="text-lg font-medium text-tactical-700 dark:text-tactical-300 mb-2">
        No identification history
      </h4>
      <p className="text-sm text-tactical-500 dark:text-tactical-400 max-w-sm">
        {tigerName} has no recorded identification events yet. Events will appear
        here as they occur.
      </p>
    </div>
  )
}

/**
 * TigerIdentificationTimeline component
 *
 * Displays a chronological timeline of all identification events for a specific tiger.
 * Events include registrations, matches, verifications, disputes, and merges.
 *
 * @example
 * ```tsx
 * <TigerIdentificationTimeline
 *   events={identificationEvents}
 *   tigerId="tiger-123"
 *   tigerName="Rajah"
 *   onEventClick={(event) => console.log('Clicked:', event)}
 *   maxEvents={5}
 * />
 * ```
 */
export function TigerIdentificationTimeline({
  events,
  tigerId: _tigerId,
  tigerName,
  onEventClick,
  maxEvents,
  className,
}: TigerIdentificationTimelineProps) {
  // Note: tigerId is available for future use (e.g., linking to tiger details)
  void _tigerId
  const [isExpanded, setIsExpanded] = useState(false)

  // Sort events by timestamp (most recent first)
  const sortedEvents = useMemo(() => {
    return [...events].sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )
  }, [events])

  // Determine if we need to show the "show more" button
  const shouldShowToggle = maxEvents !== undefined && sortedEvents.length > maxEvents
  const displayedEvents = isExpanded || !shouldShowToggle
    ? sortedEvents
    : sortedEvents.slice(0, maxEvents)
  const hiddenCount = sortedEvents.length - (maxEvents ?? sortedEvents.length)

  return (
    <Card
      data-testid="tiger-identification-timeline"
      className={className}
      padding="none"
    >
      <div className="p-6 pb-2">
        <CardHeader>
          <CardTitle>Identification History</CardTitle>
        </CardHeader>
      </div>

      {events.length === 0 ? (
        <EmptyState tigerName={tigerName} />
      ) : (
        <>
          {/* Timeline events */}
          <div
            data-testid="timeline-events"
            className="px-6 py-2"
            role="list"
            aria-label={`Identification history for ${tigerName}`}
          >
            {displayedEvents.map((event, index) => (
              <TimelineEventItem
                key={event.id}
                event={event}
                isLast={index === displayedEvents.length - 1}
                onClick={onEventClick ? () => onEventClick(event) : undefined}
              />
            ))}
          </div>

          {/* Show more/less toggle */}
          {shouldShowToggle && (
            <div className="px-6 pb-6 pt-2">
              <button
                data-testid="timeline-show-more"
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

export default TigerIdentificationTimeline

import { useRef, useEffect, useState, useCallback } from 'react'
import { cn } from '../../../utils/cn'
import {
  PlayIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  SparklesIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'

/**
 * Activity event types for the live feed
 */
export interface ActivityEvent {
  id: string
  timestamp: string
  type: 'phase_started' | 'phase_completed' | 'model_started' | 'model_completed' | 'match_found' | 'error' | 'info'
  message: string
  phase?: string
  model?: string
  metadata?: Record<string, unknown>
}

/**
 * Props for the LiveActivityFeed component
 */
export interface LiveActivityFeedProps {
  /** Array of activity events to display */
  events: ActivityEvent[]
  /** Maximum number of events to display (default: 100) */
  maxEvents?: number
  /** Auto-scroll to bottom when new events arrive (default: true) */
  autoScroll?: boolean
  /** Show timestamp prefix for each event (default: true) */
  showTimestamp?: boolean
  /** Use compact mode with smaller text (default: false) */
  compact?: boolean
  /** Callback when an event is clicked */
  onEventClick?: (event: ActivityEvent) => void
  /** Additional CSS classes */
  className?: string
}

/**
 * Format a timestamp string to HH:MM:SS format
 */
function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return '--:--:--'
  }
}

/**
 * Get the icon component for an event type
 */
function getEventIcon(type: ActivityEvent['type']): React.ReactNode {
  const baseIconClass = 'flex-shrink-0'

  switch (type) {
    case 'phase_started':
      return <PlayIcon className={cn(baseIconClass, 'w-4 h-4 text-blue-500')} />
    case 'phase_completed':
      return <CheckCircleIcon className={cn(baseIconClass, 'w-4 h-4 text-emerald-500')} />
    case 'model_started':
      return <ArrowPathIcon className={cn(baseIconClass, 'w-4 h-4 text-tiger-orange animate-spin')} />
    case 'model_completed':
      return <CheckCircleIcon className={cn(baseIconClass, 'w-4 h-4 text-green-500')} />
    case 'match_found':
      return <SparklesIcon className={cn(baseIconClass, 'w-4 h-4 text-purple-500')} />
    case 'error':
      return <XCircleIcon className={cn(baseIconClass, 'w-4 h-4 text-red-500')} />
    case 'info':
    default:
      return <InformationCircleIcon className={cn(baseIconClass, 'w-4 h-4 text-tactical-400')} />
  }
}

/**
 * Get the text color class for an event type
 */
function getEventTextClass(type: ActivityEvent['type']): string {
  switch (type) {
    case 'phase_started':
      return 'text-blue-700 dark:text-blue-300'
    case 'phase_completed':
      return 'text-emerald-700 dark:text-emerald-300'
    case 'model_started':
      return 'text-tiger-orange dark:text-tiger-orange-light'
    case 'model_completed':
      return 'text-green-700 dark:text-green-300'
    case 'match_found':
      return 'text-purple-700 dark:text-purple-300'
    case 'error':
      return 'text-red-700 dark:text-red-300'
    case 'info':
    default:
      return 'text-tactical-600 dark:text-tactical-400'
  }
}

/**
 * LiveActivityFeed displays a scrolling feed of investigation activity events
 * with auto-scroll, event icons, timestamps, and interactive click handling.
 */
export function LiveActivityFeed({
  events,
  maxEvents = 100,
  autoScroll: initialAutoScroll = true,
  showTimestamp = true,
  compact = false,
  onEventClick,
  className,
}: LiveActivityFeedProps): React.ReactElement {
  const containerRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(initialAutoScroll)
  const [userScrolled, setUserScrolled] = useState(false)
  const prevEventsLengthRef = useRef(events.length)

  // Truncate events to maxEvents
  const displayedEvents = events.slice(-maxEvents)

  // Handle scroll to detect if user scrolled up
  const handleScroll = useCallback(() => {
    if (!listRef.current) return

    const { scrollTop, scrollHeight, clientHeight } = listRef.current
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 10

    // If user scrolled up, disable auto-scroll
    if (!isAtBottom && autoScroll) {
      setUserScrolled(true)
      setAutoScroll(false)
    }
    // If user scrolled back to bottom, re-enable auto-scroll
    if (isAtBottom && userScrolled) {
      setUserScrolled(false)
      setAutoScroll(true)
    }
  }, [autoScroll, userScrolled])

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (!listRef.current) return

    // Only auto-scroll if enabled and we have new events
    if (autoScroll && events.length > prevEventsLengthRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight
    }

    prevEventsLengthRef.current = events.length
  }, [events, autoScroll])

  // Toggle auto-scroll
  const toggleAutoScroll = () => {
    const newAutoScroll = !autoScroll
    setAutoScroll(newAutoScroll)
    setUserScrolled(!newAutoScroll)

    // If enabling auto-scroll, scroll to bottom immediately
    if (newAutoScroll && listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight
    }
  }

  // Handle event click
  const handleEventClick = (event: ActivityEvent) => {
    if (onEventClick) {
      onEventClick(event)
    }
  }

  return (
    <div
      ref={containerRef}
      data-testid="live-activity-feed"
      className={cn(
        'flex flex-col rounded-xl border',
        'bg-white dark:bg-tactical-800',
        'border-tactical-200 dark:border-tactical-700',
        'shadow-tactical',
        className
      )}
    >
      {/* Header */}
      <div className={cn(
        'flex items-center justify-between px-4 py-3',
        'border-b border-tactical-200 dark:border-tactical-700'
      )}>
        <h3 className={cn(
          'font-semibold text-tactical-900 dark:text-tactical-100',
          compact ? 'text-sm' : 'text-base'
        )}>
          Activity Log
        </h3>
        <button
          type="button"
          data-testid="activity-autoscroll-toggle"
          onClick={toggleAutoScroll}
          className={cn(
            'flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium',
            'transition-colors duration-150',
            autoScroll
              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
              : 'bg-tactical-100 text-tactical-600 dark:bg-tactical-700 dark:text-tactical-400',
            'hover:bg-blue-200 dark:hover:bg-blue-900/50'
          )}
          aria-pressed={autoScroll}
          aria-label={autoScroll ? 'Disable auto-scroll' : 'Enable auto-scroll'}
        >
          <span className={cn(
            'w-2 h-2 rounded-full',
            autoScroll ? 'bg-blue-500 animate-pulse' : 'bg-tactical-400'
          )} />
          Auto-scroll
        </button>
      </div>

      {/* Events List */}
      <div
        ref={listRef}
        data-testid="activity-feed-list"
        onScroll={handleScroll}
        className={cn(
          'flex-1 overflow-y-auto',
          'max-h-80',
          compact ? 'p-2' : 'p-3'
        )}
      >
        {displayedEvents.length === 0 ? (
          <div
            data-testid="activity-empty-state"
            className={cn(
              'flex flex-col items-center justify-center py-8',
              'text-tactical-500 dark:text-tactical-400'
            )}
          >
            <InformationCircleIcon className="w-8 h-8 mb-2 opacity-50" />
            <p className={cn(
              'text-center',
              compact ? 'text-xs' : 'text-sm'
            )}>
              No activity yet. Events will appear here as the investigation progresses.
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            {displayedEvents.map((event, index) => (
              <div
                key={event.id}
                data-testid={`activity-event-${event.id}`}
                onClick={() => handleEventClick(event)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    handleEventClick(event)
                  }
                }}
                role={onEventClick ? 'button' : undefined}
                tabIndex={onEventClick ? 0 : undefined}
                className={cn(
                  'flex items-start gap-2 rounded-md',
                  compact ? 'px-2 py-1' : 'px-2.5 py-1.5',
                  'transition-all duration-200',
                  // New event animation for the last 3 events
                  index >= displayedEvents.length - 3 && 'animate-fade-in-up',
                  // Hover state when clickable
                  onEventClick && cn(
                    'cursor-pointer',
                    'hover:bg-tactical-100 dark:hover:bg-tactical-700/50',
                    'focus:outline-none focus:ring-2 focus:ring-tiger-orange focus:ring-offset-1',
                    'dark:focus:ring-offset-tactical-800'
                  )
                )}
              >
                {/* Timestamp */}
                {showTimestamp && (
                  <span className={cn(
                    'flex-shrink-0 font-mono text-tactical-400 dark:text-tactical-500',
                    compact ? 'text-2xs' : 'text-xs'
                  )}>
                    {formatTimestamp(event.timestamp)}
                  </span>
                )}

                {/* Icon */}
                <span className="flex-shrink-0 mt-0.5">
                  {getEventIcon(event.type)}
                </span>

                {/* Message */}
                <span className={cn(
                  'flex-1 min-w-0',
                  getEventTextClass(event.type),
                  compact ? 'text-xs' : 'text-sm'
                )}>
                  {event.message}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default LiveActivityFeed

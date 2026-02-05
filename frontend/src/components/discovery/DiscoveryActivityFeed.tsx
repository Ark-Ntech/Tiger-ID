/**
 * DiscoveryActivityFeed Component
 *
 * Real-time activity feed displaying discovery events as they occur.
 * Shows crawl starts, completions, image discoveries, rate limiting,
 * errors, and tiger detections with appropriate color coding and icons.
 *
 * Design: Tactical/professional aesthetic matching the Tiger ID system.
 * Uses status colors for event types with smooth animations for new events.
 */

import { useEffect, useRef, useState } from 'react'
import { cn } from '../../utils/cn'
import {
  PhotoIcon,
  PlayIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationCircleIcon,
  SparklesIcon,
  SignalIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline'

// ============================================================================
// Types
// ============================================================================

export type DiscoveryEventType =
  | 'image_found'
  | 'crawl_started'
  | 'crawl_completed'
  | 'rate_limited'
  | 'error'
  | 'tiger_detected'

export interface DiscoveryEvent {
  id: string
  timestamp: string
  type: DiscoveryEventType
  facilityId?: string
  facilityName?: string
  message: string
  metadata?: Record<string, unknown>
}

export interface DiscoveryActivityFeedProps {
  events: DiscoveryEvent[]
  maxEvents?: number
  autoScroll?: boolean
  className?: string
  onEventClick?: (event: DiscoveryEvent) => void
}

// ============================================================================
// Constants
// ============================================================================

const EVENT_CONFIG: Record<DiscoveryEventType, {
  icon: React.ComponentType<{ className?: string }>
  bgClass: string
  textClass: string
  dotClass: string
  label: string
}> = {
  image_found: {
    icon: PhotoIcon,
    bgClass: 'bg-blue-50 dark:bg-blue-900/20',
    textClass: 'text-status-info',
    dotClass: 'bg-status-info',
    label: 'Image Found',
  },
  crawl_started: {
    icon: PlayIcon,
    bgClass: 'bg-tiger-orange/10 dark:bg-tiger-orange/20',
    textClass: 'text-tiger-orange',
    dotClass: 'bg-tiger-orange',
    label: 'Crawl Started',
  },
  crawl_completed: {
    icon: CheckCircleIcon,
    bgClass: 'bg-emerald-50 dark:bg-emerald-900/20',
    textClass: 'text-status-success',
    dotClass: 'bg-status-success',
    label: 'Crawl Complete',
  },
  rate_limited: {
    icon: ClockIcon,
    bgClass: 'bg-amber-50 dark:bg-amber-900/20',
    textClass: 'text-status-warning',
    dotClass: 'bg-status-warning',
    label: 'Rate Limited',
  },
  error: {
    icon: ExclamationCircleIcon,
    bgClass: 'bg-red-50 dark:bg-red-900/20',
    textClass: 'text-status-danger',
    dotClass: 'bg-status-danger',
    label: 'Error',
  },
  tiger_detected: {
    icon: SparklesIcon,
    bgClass: 'bg-purple-50 dark:bg-purple-900/20',
    textClass: 'text-purple-600 dark:text-purple-400',
    dotClass: 'bg-purple-500',
    label: 'Tiger Detected',
  },
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Formats a timestamp into HH:MM:SS format
 */
function formatTime(timestamp: string): string {
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
 * Formats a timestamp into relative time (e.g., "2s ago", "5m ago")
 */
function formatRelativeTime(timestamp: string): string {
  try {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffSec = Math.floor(diffMs / 1000)
    const diffMin = Math.floor(diffSec / 60)
    const diffHr = Math.floor(diffMin / 60)

    if (diffSec < 5) return 'just now'
    if (diffSec < 60) return `${diffSec}s ago`
    if (diffMin < 60) return `${diffMin}m ago`
    if (diffHr < 24) return `${diffHr}h ago`
    return formatTime(timestamp)
  } catch {
    return ''
  }
}

// ============================================================================
// Sub-Components
// ============================================================================

interface LiveIndicatorProps {
  isLive: boolean
}

const LiveIndicator = ({ isLive }: LiveIndicatorProps) => (
  <div
    data-testid="live-indicator"
    className="flex items-center gap-2"
  >
    <div className="relative flex items-center">
      <SignalIcon className={cn(
        'w-4 h-4',
        isLive ? 'text-status-success' : 'text-tactical-400'
      )} />
      {isLive && (
        <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-status-success animate-pulse" />
      )}
    </div>
    <span className={cn(
      'text-xs font-semibold uppercase tracking-wider',
      isLive ? 'text-status-success' : 'text-tactical-500'
    )}>
      {isLive ? 'Live' : 'Paused'}
    </span>
  </div>
)

interface AutoScrollToggleProps {
  enabled: boolean
  onToggle: () => void
}

const AutoScrollToggle = ({ enabled, onToggle }: AutoScrollToggleProps) => (
  <button
    data-testid="auto-scroll-toggle"
    onClick={onToggle}
    className={cn(
      'flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium transition-colors',
      enabled
        ? 'bg-status-info/10 text-status-info'
        : 'bg-tactical-100 dark:bg-tactical-700 text-tactical-500 dark:text-tactical-400'
    )}
    aria-pressed={enabled}
    title={enabled ? 'Auto-scroll enabled' : 'Auto-scroll disabled'}
  >
    <ChevronDownIcon className={cn(
      'w-3.5 h-3.5 transition-transform',
      enabled && 'animate-bounce'
    )} />
    Auto-scroll
  </button>
)

interface EventItemProps {
  event: DiscoveryEvent
  onClick?: () => void
  isNew?: boolean
}

const EventItem = ({ event, onClick, isNew = false }: EventItemProps) => {
  const config = EVENT_CONFIG[event.type]
  const Icon = config.icon
  const isClickable = !!onClick

  return (
    <div
      data-testid={`event-item-${event.id}`}
      data-event-type={event.type}
      onClick={onClick}
      className={cn(
        'flex items-start gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
        config.bgClass,
        isClickable && 'cursor-pointer hover:opacity-80',
        isNew && 'animate-fade-in-up'
      )}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={isClickable ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick?.()
        }
      } : undefined}
    >
      {/* Event Type Indicator */}
      <div className="flex-shrink-0 mt-0.5">
        <div className={cn(
          'w-2 h-2 rounded-full',
          config.dotClass
        )} />
      </div>

      {/* Timestamp */}
      <div className="flex-shrink-0 w-16">
        <span
          data-testid={`event-timestamp-${event.id}`}
          className="font-mono text-xs text-tactical-500 dark:text-tactical-400"
          title={formatRelativeTime(event.timestamp)}
        >
          {formatTime(event.timestamp)}
        </span>
      </div>

      {/* Icon */}
      <div className="flex-shrink-0">
        <Icon className={cn('w-4 h-4', config.textClass)} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {event.facilityName && (
          <span
            data-testid={`event-facility-${event.id}`}
            className={cn(
              'font-semibold text-sm',
              config.textClass
            )}
          >
            {event.facilityName}:{' '}
          </span>
        )}
        <span
          data-testid={`event-message-${event.id}`}
          className="text-sm text-tactical-700 dark:text-tactical-300"
        >
          {event.message}
        </span>

        {/* Metadata badges */}
        {event.metadata && Object.keys(event.metadata).length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-1.5">
            {event.metadata.imageCount !== undefined && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-2xs bg-tactical-100 dark:bg-tactical-700 text-tactical-600 dark:text-tactical-300">
                <PhotoIcon className="w-3 h-3" />
                {String(event.metadata.imageCount)}
              </span>
            )}
            {event.metadata.waitSeconds !== undefined && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-2xs bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">
                <ClockIcon className="w-3 h-3" />
                {String(event.metadata.waitSeconds)}s
              </span>
            )}
            {event.metadata.confidence !== undefined && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-2xs bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400">
                {(Number(event.metadata.confidence) * 100).toFixed(0)}%
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

interface EmptyStateProps {
  className?: string
}

const EmptyState = ({ className }: EmptyStateProps) => (
  <div
    data-testid="activity-feed-empty"
    className={cn(
      'flex flex-col items-center justify-center py-12 text-center',
      className
    )}
  >
    <SignalIcon className="w-10 h-10 text-tactical-300 dark:text-tactical-600 mb-3" />
    <p className="text-tactical-600 dark:text-tactical-400 font-medium text-sm">
      No activity yet
    </p>
    <p className="text-xs text-tactical-500 dark:text-tactical-500 mt-1">
      Discovery events will appear here in real-time
    </p>
  </div>
)

// ============================================================================
// Main Component
// ============================================================================

export const DiscoveryActivityFeed = ({
  events,
  maxEvents = 50,
  autoScroll: initialAutoScroll = true,
  className,
  onEventClick,
}: DiscoveryActivityFeedProps) => {
  const [autoScroll, setAutoScroll] = useState(initialAutoScroll)
  const [newEventIds, setNewEventIds] = useState<Set<string>>(new Set())
  const feedRef = useRef<HTMLDivElement>(null)
  const prevEventsLengthRef = useRef(events.length)

  // Track new events for animation
  useEffect(() => {
    if (events.length > prevEventsLengthRef.current) {
      const newIds = new Set(
        events
          .slice(0, events.length - prevEventsLengthRef.current)
          .map(e => e.id)
      )
      setNewEventIds(newIds)

      // Clear animation class after animation completes
      const timer = setTimeout(() => {
        setNewEventIds(new Set())
      }, 300)

      return () => clearTimeout(timer)
    }
    prevEventsLengthRef.current = events.length
  }, [events])

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (autoScroll && feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight
    }
  }, [events, autoScroll])

  // Limit displayed events
  const displayedEvents = events.slice(0, maxEvents)
  const isLive = events.length > 0 && autoScroll

  return (
    <div
      data-testid="discovery-activity-feed"
      className={cn(
        'flex flex-col rounded-xl border border-tactical-200 dark:border-tactical-700',
        'bg-white dark:bg-tactical-800/50',
        'overflow-hidden',
        className
      )}
    >
      {/* Header */}
      <div
        data-testid="activity-feed-header"
        className={cn(
          'flex items-center justify-between px-4 py-3',
          'border-b border-tactical-200 dark:border-tactical-700',
          'bg-tactical-50 dark:bg-tactical-800'
        )}
      >
        <div className="flex items-center gap-3">
          <h3 className="font-semibold text-sm text-tactical-900 dark:text-tactical-100 uppercase tracking-wide">
            Live Activity Feed
          </h3>
          <LiveIndicator isLive={isLive} />
        </div>

        <div className="flex items-center gap-2">
          {events.length > 0 && (
            <span
              data-testid="event-count"
              className="text-xs text-tactical-500 dark:text-tactical-400"
            >
              {events.length} event{events.length !== 1 ? 's' : ''}
            </span>
          )}
          <AutoScrollToggle
            enabled={autoScroll}
            onToggle={() => setAutoScroll(prev => !prev)}
          />
        </div>
      </div>

      {/* Event List */}
      <div
        ref={feedRef}
        data-testid="activity-feed-list"
        className={cn(
          'flex-1 overflow-y-auto',
          'max-h-96 min-h-48',
          'scrollbar-thin scrollbar-thumb-tactical-300 dark:scrollbar-thumb-tactical-600',
          'scrollbar-track-transparent'
        )}
      >
        {displayedEvents.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="p-3 space-y-2">
            {displayedEvents.map((event) => (
              <EventItem
                key={event.id}
                event={event}
                onClick={onEventClick ? () => onEventClick(event) : undefined}
                isNew={newEventIds.has(event.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer - shows when events are truncated */}
      {events.length > maxEvents && (
        <div
          data-testid="activity-feed-truncation-notice"
          className={cn(
            'px-4 py-2 text-center text-xs',
            'border-t border-tactical-200 dark:border-tactical-700',
            'bg-tactical-50 dark:bg-tactical-800',
            'text-tactical-500 dark:text-tactical-400'
          )}
        >
          Showing {maxEvents} of {events.length} events
        </div>
      )}
    </div>
  )
}

export default DiscoveryActivityFeed

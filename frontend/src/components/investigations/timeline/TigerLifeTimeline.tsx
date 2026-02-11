import { useMemo } from 'react'
import { cn } from '../../../utils/cn'
import { getImageUrl } from '../../../utils/imageUrl'
import { format, parseISO } from 'date-fns'
import { useGetTigerTimelineQuery } from '../../../app/api'
import Badge from '../../common/Badge'
import Card from '../../common/Card'
import LoadingSpinner from '../../common/LoadingSpinner'
import { TimelineMap } from './TimelineMap'
import {
  GlobeAltIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
  ArrowTopRightOnSquareIcon,
  BuildingOffice2Icon,
  CameraIcon,
} from '@heroicons/react/24/outline'
import type { TimelineSighting } from '../../../types/investigation2'

interface TigerLifeTimelineProps {
  tigerId: string
  tigerName: string
  className?: string
  /** Pre-built timeline sightings from the investigation (bypasses API fetch) */
  inlineSightings?: TimelineSighting[]
}

type SourceConfigEntry = { label: string; color: string; bgClass: string; textClass: string; Icon: React.ComponentType<{ className?: string }> }

const sourceConfig: Record<string, SourceConfigEntry> = {
  database: {
    label: 'Database',
    color: '#10b981',
    bgClass: 'bg-emerald-100 dark:bg-emerald-900/30',
    textClass: 'text-emerald-700 dark:text-emerald-300',
    Icon: BuildingOffice2Icon,
  },
  database_image: {
    label: 'Database',
    color: '#10b981',
    bgClass: 'bg-emerald-100 dark:bg-emerald-900/30',
    textClass: 'text-emerald-700 dark:text-emerald-300',
    Icon: BuildingOffice2Icon,
  },
  web_search: {
    label: 'Web Search',
    color: '#3b82f6',
    bgClass: 'bg-blue-100 dark:bg-blue-900/30',
    textClass: 'text-blue-700 dark:text-blue-300',
    Icon: GlobeAltIcon,
  },
  web_match: {
    label: 'Web Match',
    color: '#3b82f6',
    bgClass: 'bg-blue-100 dark:bg-blue-900/30',
    textClass: 'text-blue-700 dark:text-blue-300',
    Icon: GlobeAltIcon,
  },
  web_citation: {
    label: 'Web Citation',
    color: '#6366f1',
    bgClass: 'bg-indigo-100 dark:bg-indigo-900/30',
    textClass: 'text-indigo-700 dark:text-indigo-300',
    Icon: GlobeAltIcon,
  },
  investigation: {
    label: 'Investigation',
    color: '#8b5cf6',
    bgClass: 'bg-purple-100 dark:bg-purple-900/30',
    textClass: 'text-purple-700 dark:text-purple-300',
    Icon: MagnifyingGlassIcon,
  },
  user_context: {
    label: 'User Provided',
    color: '#8b5cf6',
    bgClass: 'bg-purple-100 dark:bg-purple-900/30',
    textClass: 'text-purple-700 dark:text-purple-300',
    Icon: MagnifyingGlassIcon,
  },
  exif: {
    label: 'EXIF Data',
    color: '#8b5cf6',
    bgClass: 'bg-purple-100 dark:bg-purple-900/30',
    textClass: 'text-purple-700 dark:text-purple-300',
    Icon: CameraIcon,
  },
  discovery: {
    label: 'Discovery',
    color: '#f97316',
    bgClass: 'bg-orange-100 dark:bg-orange-900/30',
    textClass: 'text-orange-700 dark:text-orange-300',
    Icon: SparklesIcon,
  },
  deep_research: {
    label: 'Deep Research',
    color: '#f97316',
    bgClass: 'bg-orange-100 dark:bg-orange-900/30',
    textClass: 'text-orange-700 dark:text-orange-300',
    Icon: SparklesIcon,
  },
}

const confidenceColors: Record<string, string> = {
  high: 'bg-emerald-500',
  medium: 'bg-amber-500',
  low: 'bg-red-400',
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Unknown date'
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy')
  } catch {
    return dateStr
  }
}

export function TigerLifeTimeline({ tigerId, tigerName, className, inlineSightings }: TigerLifeTimelineProps) {
  // Only fetch from API if no inline data provided
  const skipApiQuery = !!inlineSightings && inlineSightings.length > 0
  const { data, isLoading, error } = useGetTigerTimelineQuery(tigerId, { skip: skipApiQuery })

  // Build timeline from inline sightings or API data
  const timeline = useMemo(() => {
    if (inlineSightings && inlineSightings.length > 0) {
      const facilities = new Set(inlineSightings.map(s => s.facility_name).filter(Boolean))
      const dates = inlineSightings.map(s => s.date).filter(Boolean) as string[]
      dates.sort()
      return {
        sightings: inlineSightings,
        total_sightings: inlineSightings.length,
        facilities_visited: facilities.size,
        date_range: {
          earliest: dates[0] || null,
          latest: dates[dates.length - 1] || null,
        },
      }
    }
    return data?.data
  }, [inlineSightings, data])

  const sightingsWithCoords = useMemo(
    () => (timeline?.sightings || []).filter((s) => s.coordinates != null),
    [timeline]
  )

  if (!skipApiQuery && isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-tactical-600 dark:text-tactical-400">Loading timeline...</span>
      </div>
    )
  }

  if (!skipApiQuery && error) {
    return (
      <Card variant="default" padding="lg">
        <p className="text-red-600 dark:text-red-400 text-sm">
          Failed to load timeline data. Please try again.
        </p>
      </Card>
    )
  }

  if (!timeline || timeline.sightings.length === 0) {
    return (
      <Card variant="default" padding="lg">
        <div className="text-center py-8">
          <MagnifyingGlassIcon className="w-12 h-12 mx-auto text-tactical-400 mb-3" />
          <p className="text-tactical-600 dark:text-tactical-400">
            No timeline data available for {tigerName}.
          </p>
        </div>
      </Card>
    )
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100">
            {tigerName} - Life Timeline
          </h3>
          <p className="text-sm text-tactical-600 dark:text-tactical-400 mt-1">
            {timeline.total_sightings} record{timeline.total_sightings !== 1 ? 's' : ''} across{' '}
            {timeline.facilities_visited} facilit{timeline.facilities_visited !== 1 ? 'ies' : 'y'}
            {timeline.date_range.earliest && timeline.date_range.latest && (
              <span>
                {' '}
                &middot; {formatDate(timeline.date_range.earliest)} &ndash;{' '}
                {formatDate(timeline.date_range.latest)}
              </span>
            )}
          </p>
        </div>

        {/* Source legend - only show types present in data */}
        <div className="flex flex-wrap gap-2">
          {(() => {
            const presentSources = new Set(timeline.sightings.map(s => s.source))
            const shownLabels = new Set<string>()
            return Array.from(presentSources).map((source) => {
              const config = sourceConfig[source] || sourceConfig.database
              // Deduplicate by label (database and database_image share a label)
              if (shownLabels.has(config.label)) return null
              shownLabels.add(config.label)
              return (
                <span
                  key={source}
                  className={cn(
                    'inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium',
                    config.bgClass,
                    config.textClass
                  )}
                >
                  <config.Icon className="w-3.5 h-3.5" />
                  {config.label}
                </span>
              )
            })
          })()}
        </div>
      </div>

      {/* Map */}
      {sightingsWithCoords.length > 0 && (
        <Card variant="default" padding="none">
          <TimelineMap sightings={timeline.sightings} />
        </Card>
      )}

      {/* Vertical Timeline */}
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-tactical-200 dark:bg-tactical-700" />

        <div className="space-y-4">
          {timeline.sightings.map((sighting, idx) => {
            const config = sourceConfig[sighting.source] || sourceConfig.database
            const SourceIcon = config.Icon

            return (
              <div
                key={sighting.id}
                className={cn(
                  'relative pl-12 animate-fade-in-up',
                )}
                style={{ animationDelay: `${idx * 50}ms` }}
              >
                {/* Timeline dot */}
                <div
                  className={cn(
                    'absolute left-3.5 w-4 h-4 rounded-full border-2 border-white dark:border-tactical-800',
                    'shadow-sm z-10'
                  )}
                  style={{ backgroundColor: config.color }}
                />

                {/* Sighting card */}
                <Card variant="default" padding="md">
                  <div className="flex items-start gap-3">
                    <div className="flex-1 min-w-0">
                      {/* Date and source */}
                      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                        <span className="text-sm font-medium text-tactical-900 dark:text-tactical-100">
                          {formatDate(sighting.date)}
                          {sighting.date_type === 'catalog' && (
                            <span className="text-xs font-normal text-tactical-500 dark:text-tactical-400 ml-1" title="This date reflects when the record was added to the database, not necessarily when the tiger was physically observed">
                              (catalog date)
                            </span>
                          )}
                        </span>
                        <Badge size="sm" className={cn(config.bgClass, config.textClass, 'gap-1')}>
                          <SourceIcon className="w-3 h-3" />
                          {config.label}
                        </Badge>
                        <span
                          className={cn(
                            'w-2 h-2 rounded-full flex-shrink-0',
                            confidenceColors[sighting.confidence] || confidenceColors.medium
                          )}
                          title={`${sighting.confidence} confidence`}
                        />
                      </div>

                      {/* Facility name */}
                      <p className="text-sm font-medium text-tactical-800 dark:text-tactical-200">
                        {sighting.facility_name || 'Unknown Facility'}
                      </p>

                      {/* Location */}
                      {sighting.location && (
                        <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-0.5">
                          {sighting.location}
                        </p>
                      )}

                      {/* Notes/snippet */}
                      {sighting.notes && (
                        <p className="text-xs text-tactical-600 dark:text-tactical-400 mt-1 line-clamp-2 italic">
                          &ldquo;{sighting.notes}&rdquo;
                        </p>
                      )}

                      {/* Source link */}
                      {sighting.source_url && (
                        <a
                          href={sighting.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={cn(
                            'inline-flex items-center gap-1 mt-2 text-xs',
                            'text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300'
                          )}
                        >
                          <ArrowTopRightOnSquareIcon className="w-3.5 h-3.5" />
                          {sighting.source_title || 'View source'}
                        </a>
                      )}
                    </div>

                    {/* Thumbnail */}
                    {sighting.image_url && (
                      <img
                        src={getImageUrl(sighting.image_url)}
                        alt={sighting.facility_name || 'Tiger record'}
                        className="w-12 h-12 rounded-lg object-cover flex-shrink-0"
                        onError={(e) => {
                          ;(e.target as HTMLImageElement).style.display = 'none'
                        }}
                      />
                    )}
                  </div>
                </Card>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default TigerLifeTimeline

import { useMemo } from 'react'
import { useGetInvestigationEventsQuery } from '../../app/api'
import Card from '../common/Card'
import LoadingSpinner from '../common/LoadingSpinner'
import Badge from '../common/Badge'
import { formatDate, formatDateTime } from '../../utils/formatters'
import { InvestigationEvent } from '../../types'

interface TimelineViewProps {
  investigationId: string
}

const TimelineView = ({ investigationId }: TimelineViewProps) => {
  const { data, isLoading, error } = useGetInvestigationEventsQuery({
    investigation_id: investigationId,
    limit: 100,
  })

  const events = useMemo(() => {
    if (!data?.data) return []
    return data.data.events || []
  }, [data])

  const groupedEvents = useMemo(() => {
    const grouped: Record<string, InvestigationEvent[]> = {}
    events.forEach((event) => {
      const date = new Date(event.timestamp).toLocaleDateString()
      if (!grouped[date]) {
        grouped[date] = []
      }
      grouped[date].push(event)
    })
    return grouped
  }, [events])

  const getEventIcon = (eventType: string) => {
    switch (eventType.toLowerCase()) {
      case 'created':
      case 'investigation_created':
        return '🆕'
      case 'step_added':
      case 'step_completed':
        return '✅'
      case 'evidence_added':
      case 'evidence_collected':
        return '📎'
      case 'status_changed':
        return '🔄'
      case 'comment_added':
        return '💬'
      case 'agent_started':
      case 'agent_completed':
        return '🤖'
      case 'annotation_added':
        return '📝'
      default:
        return '📌'
    }
  }

  const getEventColor = (eventType: string) => {
    switch (eventType.toLowerCase()) {
      case 'created':
      case 'investigation_created':
        return 'bg-blue-100 text-blue-800'
      case 'step_completed':
        return 'bg-green-100 text-green-800'
      case 'evidence_added':
        return 'bg-purple-100 text-purple-800'
      case 'status_changed':
        return 'bg-yellow-100 text-yellow-800'
      case 'agent_started':
      case 'agent_completed':
        return 'bg-indigo-100 text-indigo-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (isLoading) {
    return (
      <Card>
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner />
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <div className="text-center text-red-600 py-8">
          Failed to load timeline events
        </div>
      </Card>
    )
  }

  if (events.length === 0) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Timeline</h3>
        <div className="text-center text-gray-500 py-8">
          No events yet. Events will appear here as the investigation progresses.
        </div>
      </Card>
    )
  }

  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 mb-6">Timeline</h3>
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />

        <div className="space-y-6">
          {Object.entries(groupedEvents)
            .sort(([a], [b]) => new Date(b).getTime() - new Date(a).getTime())
            .map(([date, dateEvents]) => (
              <div key={date} className="relative">
                {/* Date header */}
                <div className="flex items-center mb-4">
                  <div className="bg-white px-3 py-1 rounded-lg border border-gray-200 shadow-sm">
                    <span className="text-sm font-medium text-gray-700">
                      {new Date(date).toLocaleDateString('en-US', {
                        weekday: 'short',
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </span>
                  </div>
                </div>

                {/* Events for this date */}
                <div className="space-y-4 ml-12">
                  {dateEvents
                    .sort(
                      (a, b) =>
                        new Date(b.timestamp).getTime() -
                        new Date(a.timestamp).getTime()
                    )
                    .map((event, index) => (
                      <div key={`${event.timestamp}-${index}`} className="relative">
                        {/* Event dot */}
                        <div className="absolute -left-8 top-2">
                          <div className="w-8 h-8 rounded-full bg-white border-2 border-gray-300 flex items-center justify-center">
                            <span className="text-lg">
                              {getEventIcon(event.event_type)}
                            </span>
                          </div>
                        </div>

                        {/* Event card */}
                        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:shadow-md transition-shadow">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center space-x-2">
                              <Badge
                                variant="info"
                                className={getEventColor(event.event_type)}
                              >
                                {event.event_type.replace(/_/g, ' ')}
                              </Badge>
                            </div>
                            <span className="text-xs text-gray-500">
                              {formatDateTime(event.timestamp)}
                            </span>
                          </div>

                          {event.data && Object.keys(event.data).length > 0 && (
                            <div className="mt-3 space-y-2">
                              {Object.entries(event.data).map(([key, value]) => {
                                if (
                                  typeof value === 'object' ||
                                  value === null ||
                                  value === undefined
                                ) {
                                  return null
                                }
                                return (
                                  <div
                                    key={key}
                                    className="text-sm text-gray-600"
                                  >
                                    <span className="font-medium capitalize">
                                      {key.replace(/_/g, ' ')}:
                                    </span>{' '}
                                    <span className="text-gray-800">
                                      {String(value)}
                                    </span>
                                  </div>
                                )
                              })}
                            </div>
                          )}

                          {event.metadata && (
                            <div className="mt-2 text-xs text-gray-400">
                              {event.metadata.description || ''}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            ))}
        </div>
      </div>
    </Card>
  )
}

export default TimelineView


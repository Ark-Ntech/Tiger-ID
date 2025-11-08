import { useState } from 'react'
import Card from '../common/Card'
import Badge from '../common/Badge'
import StatusBadge from './StatusBadge'
import ProgressDisplay from './ProgressDisplay'
import InvestigationActions from './InvestigationActions'
import {
  FolderOpenIcon,
  ClockIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline'
import { formatDate } from '../../utils/formatters'

interface InvestigationCardProps {
  investigation: any
  extended?: any
  onResume?: (id: string) => void
  onPause?: (id: string) => void
  onView?: (id: string) => void
  onApprove?: (id: string) => void
  onExport?: (id: string) => void
  onEdit?: (id: string) => void
  onDelete?: (id: string) => void
  onSelect?: (id: string) => void
  selected?: boolean
  showCheckbox?: boolean
}

const InvestigationCard = ({
  investigation,
  extended,
  onResume,
  onPause,
  onView,
  onApprove,
  onExport,
  onEdit,
  onDelete,
  onSelect,
  selected,
  showCheckbox
}: InvestigationCardProps) => {
  const [expanded, setExpanded] = useState(false)

  const status = investigation.status
  const priority = investigation.priority

  const getStatusColor = () => {
    switch (status) {
      case 'active':
      case 'in_progress':
        return 'bg-green-500'
      case 'paused':
        return 'bg-yellow-500'
      case 'completed':
        return 'bg-blue-500'
      case 'cancelled':
        return 'bg-red-500'
      default:
        return 'bg-gray-300'
    }
  }

  const getPriorityVariant = () => {
    switch (priority) {
      case 'critical':
        return 'danger'
      case 'high':
        return 'warning'
      case 'medium':
        return 'info'
      default:
        return 'default'
    }
  }

  const timeAgo = (timestamp: string) => {
    const now = new Date()
    const then = new Date(timestamp)
    const seconds = Math.floor((now.getTime() - then.getTime()) / 1000)
    
    if (seconds < 60) return `${seconds}s ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return `${Math.floor(seconds / 86400)}d ago`
  }

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
    const hours = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    return `${hours}h ${mins}m`
  }

  return (
    <Card className="relative overflow-hidden hover:shadow-lg transition-shadow">
      {/* Status Indicator Strip */}
      <div className={`absolute top-0 left-0 right-0 h-1 ${getStatusColor()}`} />
      
      <div className="pt-2">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-3 flex-1">
            {/* Checkbox for bulk selection */}
            {showCheckbox && onSelect && (
              <input
                type="checkbox"
                checked={selected}
                onChange={() => onSelect(investigation.id)}
                onClick={(e) => e.stopPropagation()}
                className="mt-1 h-4 w-4 text-primary-600 rounded"
              />
            )}
            
            <div className="p-2 bg-primary-100 rounded-lg mt-0.5">
              <FolderOpenIcon className="h-5 w-5 text-primary-600" />
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                <h3 className="text-lg font-semibold text-gray-900">
                  {investigation.title}
                </h3>
                <StatusBadge 
                  status={status} 
                  phase={extended?.current_phase}
                />
                <Badge variant={getPriorityVariant()}>
                  {priority}
                </Badge>
              </div>

              {/* Progress Bar for Active Investigations */}
              {(status === 'active' || status === 'in_progress') && extended && (
                <div className="mb-3">
                  <ProgressDisplay
                    phase={extended.current_phase}
                    percentage={extended.progress_percentage || 0}
                    timeElapsed={extended.time_elapsed_seconds}
                  />
                </div>
              )}

              {/* Pending Approval Warning */}
              {extended?.pending_approval && (
                <div className="flex items-center gap-2 text-sm text-yellow-700 bg-yellow-50 px-3 py-1.5 rounded mb-3">
                  <ClockIcon className="h-4 w-4" />
                  <span>Waiting for approval: {extended.pending_approval.approval_type}</span>
                </div>
              )}

              {/* Description */}
              <p className="text-sm text-gray-700 mb-3 line-clamp-2">
                {investigation.description || 'No description provided'}
              </p>

              {/* Quick Info - Always Visible */}
              {extended && (
                <div className="grid grid-cols-4 gap-3 p-3 bg-gray-50 rounded-lg mb-3">
                  <div>
                    <div className="text-xs text-gray-500">Entities</div>
                    <div className="text-sm font-medium text-gray-900">
                      {extended.entities_identified?.length || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Evidence</div>
                    <div className="text-sm font-medium text-gray-900">
                      {extended.evidence_count || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Cost</div>
                    <div className="text-sm font-medium text-gray-900">
                      ${(extended.cost_so_far || 0).toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Duration</div>
                    <div className="text-sm font-medium text-gray-900">
                      {extended.time_elapsed_seconds ? formatDuration(extended.time_elapsed_seconds) : '-'}
                    </div>
                  </div>
                </div>
              )}

              {/* Latest Activity */}
              {extended?.last_activity && (
                <div className="flex items-center gap-2 text-xs text-gray-600 mb-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full" />
                  <span>
                    {extended.last_activity.agent ? extended.last_activity.agent.replace('_', ' ') : 'Agent'}: {' '}
                    {extended.last_activity.action || 'Working'}
                  </span>
                  {extended.last_activity.timestamp && (
                    <span className="text-gray-400">
                      ({timeAgo(extended.last_activity.timestamp)})
                    </span>
                  )}
                </div>
              )}

              {/* Expandable Details */}
              {expanded && extended && (
                <div className="space-y-3 pt-3 border-t">
                  {/* Entities */}
                  {extended.entities_identified && extended.entities_identified.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-gray-700 mb-1">Entities</div>
                      <div className="flex flex-wrap gap-1">
                        {extended.entities_identified.map((entity: string, idx: number) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {entity}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Evidence by Type */}
                  {extended.evidence_by_type && Object.keys(extended.evidence_by_type).length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-gray-700 mb-1">Evidence Types</div>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(extended.evidence_by_type).map(([type, count]: [string, any]) => (
                          <span key={type} className="text-xs bg-gray-100 px-2 py-1 rounded">
                            {type}: {count}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Steps Count */}
                  {extended.steps_count > 0 && (
                    <div className="text-xs text-gray-600">
                      <DocumentTextIcon className="h-3 w-3 inline mr-1" />
                      {extended.steps_count} investigation steps recorded
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <InvestigationActions
            investigation={investigation}
            extended={extended}
            onResume={() => onResume?.(investigation.id)}
            onPause={() => onPause?.(investigation.id)}
            onView={() => onView?.(investigation.id)}
            onApprove={() => onApprove?.(investigation.id)}
            onExport={() => onExport?.(investigation.id)}
            onEdit={() => onEdit?.(investigation.id)}
            onDelete={() => onDelete?.(investigation.id)}
          />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t">
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span>Created {formatDate(investigation.created_at)}</span>
            {investigation.updated_at && investigation.created_at !== investigation.updated_at && (
              <>
                <span>•</span>
                <span>Last active {timeAgo(investigation.updated_at)}</span>
              </>
            )}
          </div>

          <div className="flex items-center gap-3">
            {/* Tags */}
            {investigation.tags && investigation.tags.length > 0 && (
              <div className="flex gap-1">
                {investigation.tags.slice(0, 3).map((tag: string) => (
                  <Badge key={tag} variant="outline" className="text-xs">
                    {tag}
                  </Badge>
                ))}
                {investigation.tags.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{investigation.tags.length - 3}
                  </Badge>
                )}
              </div>
            )}

            {/* Expand/Collapse Button */}
            {extended && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setExpanded(!expanded)
                }}
                className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
              >
                {expanded ? (
                  <>
                    <span>Less</span>
                    <ChevronUpIcon className="h-3 w-3" />
                  </>
                ) : (
                  <>
                    <span>More</span>
                    <ChevronDownIcon className="h-3 w-3" />
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </Card>
  )
}

export default InvestigationCard


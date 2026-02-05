import { cn } from '../../utils/cn'
import Badge from '../common/Badge'
import Button from '../common/Button'
import { Skeleton } from '../common/Skeleton'
import type {
  VerificationQueueItem,
  VerificationEntityType,
  VerificationSource,
  VerificationPriority,
  VerificationQueueStatus,
} from '../../types/verification'
import {
  ChevronDownIcon,
  ChevronUpIcon,
  EyeIcon,
  CheckIcon,
  XMarkIcon,
  BuildingOffice2Icon,
} from '@heroicons/react/24/outline'

// Custom tiger icon
const TigerIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M12 4.5c-4.5 0-7.5 3-7.5 6 0 1.5.5 3 1.5 4l-1 4.5 3-1.5c1.2.5 2.5.75 4 .75s2.8-.25 4-.75l3 1.5-1-4.5c1-1 1.5-2.5 1.5-4 0-3-3-6-7.5-6z" />
    <path d="M9 10.5v1" />
    <path d="M15 10.5v1" />
    <path d="M10.5 14c.5.5 1.5.75 1.5.75s1-.25 1.5-.75" />
  </svg>
)

interface VerificationTableProps {
  items: VerificationQueueItem[]
  isLoading?: boolean
  expandedId: string | null
  onExpandToggle: (id: string | null) => void
  onView: (item: VerificationQueueItem) => void
  onApprove: (item: VerificationQueueItem) => void
  onReject: (item: VerificationQueueItem) => void
  className?: string
}

// Badge variant mappings
const entityTypeBadgeVariant: Record<VerificationEntityType, 'tiger' | 'purple'> = {
  tiger: 'tiger',
  facility: 'purple',
}

const sourceBadgeVariant: Record<VerificationSource, 'info' | 'cyan'> = {
  auto_discovery: 'info',
  user_upload: 'cyan',
}

const priorityBadgeVariant: Record<VerificationPriority, 'danger' | 'warning' | 'default'> = {
  critical: 'danger',
  high: 'danger',
  medium: 'warning',
  low: 'default',
}

const statusBadgeVariant: Record<VerificationQueueStatus, 'warning' | 'success' | 'danger' | 'info'> = {
  pending: 'warning',
  in_review: 'info',
  approved: 'success',
  rejected: 'danger',
}

const formatDate = (dateString?: string) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const formatSource = (source?: VerificationSource) => {
  if (!source) return 'Unknown'
  return source
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export const VerificationTable = ({
  items,
  isLoading,
  expandedId,
  onExpandToggle,
  onView,
  onApprove,
  onReject,
  className,
}: VerificationTableProps) => {
  if (isLoading) {
    return (
      <div className={cn('space-y-2', className)}>
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="flex items-center gap-4 p-4 bg-white dark:bg-tactical-800 rounded-lg border border-tactical-200 dark:border-tactical-700"
          >
            <Skeleton variant="circular" className="w-10 h-10" />
            <div className="flex-1 space-y-2">
              <Skeleton variant="text" className="h-5 w-1/3" />
              <Skeleton variant="text" className="h-4 w-1/4" />
            </div>
            <Skeleton variant="rounded" className="h-6 w-16" />
            <Skeleton variant="rounded" className="h-6 w-20" />
            <Skeleton variant="rounded" className="h-8 w-24" />
          </div>
        ))}
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div
        className={cn(
          'flex flex-col items-center justify-center py-16',
          'bg-white dark:bg-tactical-800',
          'rounded-xl border border-tactical-200 dark:border-tactical-700',
          className
        )}
      >
        <div className="w-16 h-16 mb-4 rounded-full bg-tactical-100 dark:bg-tactical-700 flex items-center justify-center">
          <CheckIcon className="w-8 h-8 text-tactical-400 dark:text-tactical-500" />
        </div>
        <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100 mb-1">
          No items to review
        </h3>
        <p className="text-sm text-tactical-500 dark:text-tactical-400">
          The verification queue is empty or no items match your filters.
        </p>
      </div>
    )
  }

  return (
    <div className={cn('space-y-2', className)}>
      {/* Table Header */}
      <div className="hidden lg:grid grid-cols-[auto_1fr_auto_auto_auto_auto_auto] gap-4 px-4 py-3 text-xs font-semibold text-tactical-500 dark:text-tactical-400 uppercase tracking-wide">
        <div className="w-10" />
        <div>Entity</div>
        <div>Source</div>
        <div>Priority</div>
        <div>Status</div>
        <div>Created</div>
        <div className="text-right">Actions</div>
      </div>

      {/* Table Rows */}
      {items.map((item) => {
        const isExpanded = expandedId === item.queue_id

        return (
          <div key={item.queue_id} className="group">
            {/* Main Row */}
            <div
              className={cn(
                'grid grid-cols-1 lg:grid-cols-[auto_1fr_auto_auto_auto_auto_auto] gap-4',
                'p-4 bg-white dark:bg-tactical-800',
                'border border-tactical-200 dark:border-tactical-700',
                'rounded-xl',
                'transition-all duration-200',
                'hover:border-tactical-300 dark:hover:border-tactical-600',
                'hover:shadow-tactical',
                isExpanded && 'rounded-b-none border-b-0'
              )}
            >
              {/* Entity Icon */}
              <div className="flex items-center justify-center">
                <div
                  className={cn(
                    'w-10 h-10 rounded-lg flex items-center justify-center',
                    item.entity_type === 'tiger'
                      ? 'bg-tiger-orange/10 text-tiger-orange'
                      : 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400'
                  )}
                >
                  {item.entity_type === 'tiger' ? (
                    <TigerIcon className="w-5 h-5" />
                  ) : (
                    <BuildingOffice2Icon className="w-5 h-5" />
                  )}
                </div>
              </div>

              {/* Entity Info */}
              <div className="flex flex-col justify-center min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-tactical-900 dark:text-tactical-100 truncate">
                    {item.entity_name || item.entity_id}
                  </span>
                  <Badge variant={entityTypeBadgeVariant[item.entity_type]} size="xs">
                    {item.entity_type === 'tiger' ? 'Tiger' : 'Facility'}
                  </Badge>
                </div>
                <span className="text-xs text-tactical-500 dark:text-tactical-400 font-mono truncate">
                  ID: {item.entity_id}
                </span>
              </div>

              {/* Source */}
              <div className="flex items-center lg:justify-center">
                <Badge
                  variant={item.source ? sourceBadgeVariant[item.source] : 'default'}
                  size="sm"
                >
                  {formatSource(item.source)}
                </Badge>
              </div>

              {/* Priority */}
              <div className="flex items-center lg:justify-center">
                <Badge
                  variant={priorityBadgeVariant[item.priority]}
                  size="sm"
                  dot
                >
                  {item.priority.charAt(0).toUpperCase() + item.priority.slice(1)}
                </Badge>
              </div>

              {/* Status */}
              <div className="flex items-center lg:justify-center">
                <Badge
                  variant={statusBadgeVariant[item.status]}
                  size="sm"
                >
                  {item.status === 'in_review'
                    ? 'In Review'
                    : item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                </Badge>
              </div>

              {/* Created Date */}
              <div className="flex items-center text-sm text-tactical-500 dark:text-tactical-400 whitespace-nowrap">
                {formatDate(item.created_at)}
              </div>

              {/* Actions */}
              <div className="flex items-center justify-end gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onView(item)}
                  title="View Details"
                >
                  <EyeIcon className="w-4 h-4" />
                </Button>

                {item.status === 'pending' && (
                  <>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onApprove(item)}
                      title="Approve"
                      className="text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-900/20"
                    >
                      <CheckIcon className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onReject(item)}
                      title="Reject"
                      className="text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                    >
                      <XMarkIcon className="w-4 h-4" />
                    </Button>
                  </>
                )}

                {/* Expand Toggle */}
                <button
                  onClick={() => onExpandToggle(isExpanded ? null : item.queue_id)}
                  className={cn(
                    'p-1.5 rounded-lg',
                    'text-tactical-400 hover:text-tactical-600',
                    'dark:text-tactical-500 dark:hover:text-tactical-300',
                    'hover:bg-tactical-100 dark:hover:bg-tactical-700',
                    'transition-all duration-200'
                  )}
                  title={isExpanded ? 'Collapse' : 'Expand'}
                >
                  {isExpanded ? (
                    <ChevronUpIcon className="w-4 h-4" />
                  ) : (
                    <ChevronDownIcon className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Expanded Details Panel */}
            {isExpanded && (
              <div
                className={cn(
                  'p-4 bg-tactical-50 dark:bg-tactical-900',
                  'border border-t-0 border-tactical-200 dark:border-tactical-700',
                  'rounded-b-xl',
                  'animate-fade-in-up'
                )}
              >
                <ExpandedDetails item={item} />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

// Expanded details sub-component
const ExpandedDetails = ({ item }: { item: VerificationQueueItem }) => {
  const details = item.entity_details

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* Entity Details */}
      <div className="space-y-3">
        <h4 className="text-xs font-semibold text-tactical-500 dark:text-tactical-400 uppercase tracking-wide">
          Entity Details
        </h4>
        <div className="space-y-2">
          {item.entity_type === 'tiger' && details && 'name' in details && (
            <>
              {details.name && (
                <DetailRow label="Name" value={details.name} />
              )}
              {details.alias && (
                <DetailRow label="Alias" value={details.alias} />
              )}
              {details.status && (
                <DetailRow label="Status" value={details.status} />
              )}
              {details.last_seen_location && (
                <DetailRow label="Last Seen" value={details.last_seen_location} />
              )}
            </>
          )}
          {item.entity_type === 'facility' && details && 'exhibitor_name' in details && (
            <>
              {details.exhibitor_name && (
                <DetailRow label="Exhibitor" value={details.exhibitor_name} />
              )}
              {details.usda_license && (
                <DetailRow label="USDA License" value={details.usda_license} />
              )}
              {(details.city || details.state) && (
                <DetailRow
                  label="Location"
                  value={[details.city, details.state].filter(Boolean).join(', ')}
                />
              )}
              {details.tiger_count !== undefined && (
                <DetailRow label="Tiger Count" value={String(details.tiger_count)} />
              )}
            </>
          )}
        </div>
      </div>

      {/* Review Info */}
      <div className="space-y-3">
        <h4 className="text-xs font-semibold text-tactical-500 dark:text-tactical-400 uppercase tracking-wide">
          Review Information
        </h4>
        <div className="space-y-2">
          <DetailRow label="Queue ID" value={item.queue_id} mono />
          <DetailRow label="Requires Review" value={item.requires_human_review ? 'Yes' : 'No'} />
          {item.assigned_to && (
            <DetailRow label="Assigned To" value={item.assigned_to} />
          )}
          {item.reviewed_by && (
            <DetailRow label="Reviewed By" value={item.reviewed_by} />
          )}
          {item.reviewed_at && (
            <DetailRow label="Reviewed At" value={formatDate(item.reviewed_at)} />
          )}
        </div>
      </div>

      {/* Notes */}
      {item.review_notes && (
        <div className="space-y-3 md:col-span-2 lg:col-span-1">
          <h4 className="text-xs font-semibold text-tactical-500 dark:text-tactical-400 uppercase tracking-wide">
            Review Notes
          </h4>
          <p className="text-sm text-tactical-700 dark:text-tactical-300 bg-white dark:bg-tactical-800 p-3 rounded-lg border border-tactical-200 dark:border-tactical-700">
            {item.review_notes}
          </p>
        </div>
      )}
    </div>
  )
}

// Detail row helper component
const DetailRow = ({
  label,
  value,
  mono = false,
}: {
  label: string
  value: string
  mono?: boolean
}) => (
  <div className="flex items-start gap-2">
    <span className="text-xs text-tactical-500 dark:text-tactical-400 min-w-[80px]">
      {label}:
    </span>
    <span
      className={cn(
        'text-sm text-tactical-900 dark:text-tactical-100',
        mono && 'font-mono text-xs'
      )}
    >
      {value}
    </span>
  </div>
)

export default VerificationTable

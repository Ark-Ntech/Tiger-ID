import { cn } from '../../utils/cn'
import Card, { StatCard } from '../common/Card'
import { Skeleton } from '../common/Skeleton'
import type { VerificationStatsResponse } from '../../types/verification'
import {
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  BuildingOffice2Icon,
} from '@heroicons/react/24/outline'

// Custom tiger icon as SVG since heroicons doesn't have one
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

interface VerificationStatsPanelProps {
  stats?: VerificationStatsResponse
  isLoading?: boolean
  className?: string
}

export const VerificationStatsPanel = ({
  stats,
  isLoading,
  className,
}: VerificationStatsPanelProps) => {
  if (isLoading) {
    return (
      <div className={cn('grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4', className)}>
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i} padding="md">
            <div className="space-y-2">
              <Skeleton variant="text" className="h-4 w-20" />
              <Skeleton variant="text" className="h-8 w-12" />
            </div>
          </Card>
        ))}
      </div>
    )
  }

  if (!stats) return null

  const pendingCount = stats.by_status?.pending ?? 0
  const approvedCount = stats.by_status?.approved ?? 0
  const rejectedCount = stats.by_status?.rejected ?? 0
  const inReviewCount = stats.by_status?.in_review ?? 0

  const tigerCount = stats.by_entity_type?.tiger ?? 0
  const facilityCount = stats.by_entity_type?.facility ?? 0

  const highPriorityCount = stats.by_priority?.high ?? 0
  const criticalCount = stats.by_priority?.critical ?? 0
  const urgentCount = highPriorityCount + criticalCount

  return (
    <div className={cn('space-y-4', className)}>
      {/* Primary Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {/* Pending */}
        <StatCard
          label="Pending Review"
          value={pendingCount}
          icon={<ClockIcon className="w-5 h-5" />}
          variant="default"
        />

        {/* In Review */}
        <StatCard
          label="In Review"
          value={inReviewCount}
          icon={<ExclamationTriangleIcon className="w-5 h-5" />}
          variant="default"
        />

        {/* Approved (24h) */}
        <StatCard
          label="Approved (24h)"
          value={stats.total_approved_24h ?? approvedCount}
          icon={<CheckCircleIcon className="w-5 h-5 text-emerald-500" />}
          variant="evidence"
        />

        {/* Rejected (24h) */}
        <StatCard
          label="Rejected (24h)"
          value={stats.total_rejected_24h ?? rejectedCount}
          icon={<XCircleIcon className="w-5 h-5 text-red-500" />}
          variant="critical"
        />

        {/* Tigers */}
        <StatCard
          label="Tigers"
          value={tigerCount}
          icon={<TigerIcon className="w-5 h-5" />}
          variant="default"
        />

        {/* Facilities */}
        <StatCard
          label="Facilities"
          value={facilityCount}
          icon={<BuildingOffice2Icon className="w-5 h-5" />}
          variant="default"
        />
      </div>

      {/* Urgent Items Alert */}
      {urgentCount > 0 && (
        <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 border border-amber-300 dark:border-amber-700 rounded-lg">
          <ExclamationTriangleIcon className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0" />
          <div className="flex-1">
            <span className="text-sm font-medium text-amber-800 dark:text-amber-200">
              {urgentCount} high-priority item{urgentCount !== 1 ? 's' : ''} require{urgentCount === 1 ? 's' : ''} attention
            </span>
          </div>
          <span className="text-xs font-mono text-amber-600 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/50 px-2 py-0.5 rounded">
            {criticalCount > 0 ? `${criticalCount} critical` : `${highPriorityCount} high`}
          </span>
        </div>
      )}
    </div>
  )
}

export default VerificationStatsPanel

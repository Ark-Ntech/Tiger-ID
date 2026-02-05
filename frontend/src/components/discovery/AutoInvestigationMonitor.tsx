/**
 * AutoInvestigationMonitor Component
 *
 * Real-time monitoring dashboard for auto-triggered tiger investigations.
 * Displays stats, trends, and recent auto-investigation activity from
 * the continuous discovery pipeline.
 *
 * Design: Tactical/professional aesthetic with clear data hierarchy.
 * Uses the tiger-orange accent for key metrics and status indicators.
 */

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { cn } from '../../utils/cn'
import Card, { StatCard } from '../common/Card'
import Badge from '../common/Badge'
import { Skeleton, StatCardSkeleton } from '../common/Skeleton'
import {
  useGetAutoInvestigationStatsQuery,
  useGetRecentAutoInvestigationsQuery,
} from '../../app/api'
import type { TimeRange, AutoInvestigationStatusFilter, AutoInvestigationRecord } from '../../types/discovery'
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  PlayCircleIcon,
  DocumentMagnifyingGlassIcon,
  BuildingOffice2Icon,
  EyeIcon,
} from '@heroicons/react/24/outline'
import { BoltIcon } from '@heroicons/react/24/solid'

// ============================================================================
// Types
// ============================================================================

interface TimeRangeOption {
  value: TimeRange
  label: string
  shortLabel: string
}

interface InvestigationStatus {
  value: AutoInvestigationStatusFilter
  label: string
  color: 'success' | 'danger' | 'warning' | 'info' | 'default'
}

// ============================================================================
// Constants
// ============================================================================

const TIME_RANGE_OPTIONS: TimeRangeOption[] = [
  { value: '24h', label: 'Last 24 Hours', shortLabel: '24h' },
  { value: '7d', label: 'Last 7 Days', shortLabel: '7d' },
  { value: '30d', label: 'Last 30 Days', shortLabel: '30d' },
]

const STATUS_CONFIG: Record<string, InvestigationStatus> = {
  completed: { value: 'completed', label: 'Completed', color: 'success' },
  cancelled: { value: 'failed', label: 'Failed', color: 'danger' },
  failed: { value: 'failed', label: 'Failed', color: 'danger' },
  active: { value: 'active', label: 'Active', color: 'info' },
  draft: { value: 'pending', label: 'Pending', color: 'warning' },
  pending_verification: { value: 'pending', label: 'Pending', color: 'warning' },
}

const AUTO_REFRESH_INTERVAL = 30000 // 30 seconds

// ============================================================================
// Utility Functions
// ============================================================================

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  const seconds = Math.floor(ms / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes < 60) return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`
}

function formatRelativeTime(dateStr: string | undefined | null): string {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

function calculateTrendPercentage(current: number, total: number): number {
  if (total === 0) return 0
  return Math.round((current / total) * 100)
}

// ============================================================================
// Sub-Components
// ============================================================================

interface TimeRangeSelectorProps {
  value: TimeRange
  onChange: (value: TimeRange) => void
  disabled?: boolean
}

const TimeRangeSelector = ({ value, onChange, disabled }: TimeRangeSelectorProps) => {
  return (
    <div className="inline-flex rounded-lg bg-tactical-100 dark:bg-tactical-800 p-1 gap-1">
      {TIME_RANGE_OPTIONS.map((option) => (
        <button
          key={option.value}
          onClick={() => onChange(option.value)}
          disabled={disabled}
          className={cn(
            'px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200',
            'focus:outline-none focus:ring-2 focus:ring-tiger-orange focus:ring-offset-2',
            'dark:focus:ring-offset-tactical-900',
            value === option.value
              ? 'bg-white text-tactical-900 shadow-sm dark:bg-tactical-700 dark:text-tactical-100'
              : 'text-tactical-600 hover:text-tactical-900 hover:bg-white/50 dark:text-tactical-400 dark:hover:text-tactical-200 dark:hover:bg-tactical-700/50',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          <span className="hidden sm:inline">{option.label}</span>
          <span className="sm:hidden">{option.shortLabel}</span>
        </button>
      ))}
    </div>
  )
}

interface InvestigationStatusBadgeProps {
  status: string
  size?: 'xs' | 'sm' | 'md'
}

const InvestigationStatusBadge = ({ status, size = 'sm' }: InvestigationStatusBadgeProps) => {
  const config = STATUS_CONFIG[status] || { label: status, color: 'default' as const }

  const iconMap: Record<string, React.ReactNode> = {
    completed: <CheckCircleIcon className="w-3.5 h-3.5" />,
    failed: <XCircleIcon className="w-3.5 h-3.5" />,
    cancelled: <XCircleIcon className="w-3.5 h-3.5" />,
    active: <PlayCircleIcon className="w-3.5 h-3.5" />,
    draft: <ClockIcon className="w-3.5 h-3.5" />,
    pending_verification: <ExclamationTriangleIcon className="w-3.5 h-3.5" />,
  }

  return (
    <Badge variant={config.color} size={size} className="gap-1">
      {iconMap[status]}
      {config.label}
    </Badge>
  )
}

interface StatsGridProps {
  stats: {
    total_triggered: number
    completed: number
    failed: number
    pending: number
    avg_duration_ms: number
  } | undefined
  isLoading: boolean
  previousStats?: {
    total_triggered: number
  }
}

const StatsGrid = ({ stats, isLoading, previousStats }: StatsGridProps) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="col-span-full text-center py-8">
          <p className="text-tactical-500 dark:text-tactical-400">
            Unable to load statistics
          </p>
        </Card>
      </div>
    )
  }

  const trendValue = previousStats
    ? stats.total_triggered - previousStats.total_triggered
    : undefined

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {/* Total Triggered */}
      <StatCard
        label="Total Triggered"
        value={stats.total_triggered}
        icon={<BoltIcon className="w-5 h-5 text-tiger-orange" />}
        trend={trendValue !== undefined ? {
          value: trendValue,
          isPositive: trendValue >= 0,
        } : undefined}
        variant="default"
      />

      {/* Completed */}
      <StatCard
        label="Completed"
        value={stats.completed}
        icon={<CheckCircleIcon className="w-5 h-5 text-emerald-500" />}
        variant="default"
      />

      {/* Failed */}
      <StatCard
        label="Failed"
        value={stats.failed}
        icon={<XCircleIcon className="w-5 h-5 text-red-500" />}
        variant={stats.failed > 0 ? 'critical' : 'default'}
      />

      {/* Pending/Active */}
      <StatCard
        label="Pending"
        value={stats.pending}
        icon={<ClockIcon className="w-5 h-5 text-amber-500" />}
        variant="default"
      />

      {/* Average Duration */}
      <StatCard
        label="Avg Duration"
        value={formatDuration(stats.avg_duration_ms)}
        icon={<ClockIcon className="w-5 h-5 text-blue-500" />}
        variant="default"
      />
    </div>
  )
}

interface InvestigationRowProps {
  investigation: AutoInvestigationRecord
}

const InvestigationRow = ({ investigation }: InvestigationRowProps) => {
  return (
    <div className={cn(
      'group flex items-center gap-4 p-4 rounded-lg border transition-all duration-200',
      'bg-white border-tactical-200/60 hover:border-tactical-300 hover:shadow-tactical',
      'dark:bg-tactical-800/50 dark:border-tactical-700/60 dark:hover:border-tactical-600'
    )}>
      {/* Status indicator */}
      <div className="flex-shrink-0">
        <InvestigationStatusBadge status={investigation.status} />
      </div>

      {/* Main content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="text-sm font-semibold text-tactical-900 dark:text-tactical-100 truncate">
            {investigation.title || `Investigation ${investigation.investigation_id.substring(0, 8)}`}
          </h4>
          {investigation.priority && (
            <Badge
              size="xs"
              variant={
                investigation.priority === 'critical' ? 'danger'
                  : investigation.priority === 'high' ? 'warning'
                    : 'default'
              }
            >
              {investigation.priority}
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-3 text-xs text-tactical-500 dark:text-tactical-400">
          {investigation.facility_name && (
            <span className="flex items-center gap-1">
              <BuildingOffice2Icon className="w-3.5 h-3.5" />
              <span className="truncate max-w-[120px]">{investigation.facility_name}</span>
            </span>
          )}
          {investigation.tiger_name && (
            <span className="flex items-center gap-1">
              <DocumentMagnifyingGlassIcon className="w-3.5 h-3.5" />
              <span className="truncate max-w-[100px]">{investigation.tiger_name}</span>
            </span>
          )}
        </div>
      </div>

      {/* Timestamps */}
      <div className="hidden sm:flex flex-col items-end text-xs text-tactical-500 dark:text-tactical-400">
        <span>Created {formatRelativeTime(investigation.created_at)}</span>
        {investigation.completed_at && (
          <span className="text-emerald-600 dark:text-emerald-400">
            Completed {formatRelativeTime(investigation.completed_at)}
          </span>
        )}
      </div>

      {/* View link */}
      <Link
        to={`/investigations/${investigation.investigation_id}`}
        className={cn(
          'flex-shrink-0 p-2 rounded-lg transition-all',
          'text-tactical-400 hover:text-tiger-orange hover:bg-tiger-orange/10',
          'dark:text-tactical-500 dark:hover:text-tiger-orange',
          'opacity-0 group-hover:opacity-100 focus:opacity-100'
        )}
      >
        <EyeIcon className="w-5 h-5" />
      </Link>
    </div>
  )
}

interface RecentInvestigationsListProps {
  investigations: AutoInvestigationRecord[] | undefined
  isLoading: boolean
  statusFilter: AutoInvestigationStatusFilter
  onStatusFilterChange: (status: AutoInvestigationStatusFilter) => void
}

const RecentInvestigationsList = ({
  investigations,
  isLoading,
  statusFilter,
  onStatusFilterChange,
}: RecentInvestigationsListProps) => {
  const statusOptions: { value: AutoInvestigationStatusFilter; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'active', label: 'Active' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' },
    { value: 'pending', label: 'Pending' },
  ]

  return (
    <Card padding="none" className="overflow-hidden">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 border-b border-tactical-200 dark:border-tactical-700">
        <h3 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100">
          Recent Auto-Investigations
        </h3>

        {/* Status filter tabs */}
        <div className="flex gap-1 overflow-x-auto scrollbar-hide">
          {statusOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => onStatusFilterChange(option.value)}
              className={cn(
                'px-3 py-1.5 text-sm font-medium rounded-md whitespace-nowrap transition-all',
                'focus:outline-none focus:ring-2 focus:ring-tiger-orange focus:ring-offset-1',
                statusFilter === option.value
                  ? 'bg-tiger-orange text-white'
                  : 'text-tactical-600 hover:bg-tactical-100 dark:text-tactical-400 dark:hover:bg-tactical-700'
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* List content */}
      <div className="p-4">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="flex items-center gap-4 p-4 rounded-lg border border-tactical-200 dark:border-tactical-700"
              >
                <Skeleton variant="rounded" className="w-20 h-6" />
                <div className="flex-1 space-y-2">
                  <Skeleton variant="text" className="h-4 w-2/3" />
                  <Skeleton variant="text" className="h-3 w-1/3" />
                </div>
                <Skeleton variant="text" className="h-3 w-16 hidden sm:block" />
              </div>
            ))}
          </div>
        ) : !investigations || investigations.length === 0 ? (
          <div className="text-center py-12">
            <DocumentMagnifyingGlassIcon className="w-12 h-12 mx-auto mb-4 text-tactical-300 dark:text-tactical-600" />
            <p className="text-tactical-600 dark:text-tactical-400 font-medium">
              No auto-investigations found
            </p>
            <p className="text-sm text-tactical-500 dark:text-tactical-500 mt-1">
              {statusFilter !== 'all'
                ? `No ${statusFilter} investigations in this time range`
                : 'Auto-investigations will appear here when triggered by discovery'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {investigations.map((investigation) => (
              <InvestigationRow
                key={investigation.investigation_id}
                investigation={investigation}
              />
            ))}
          </div>
        )}
      </div>
    </Card>
  )
}

interface CompletionRateIndicatorProps {
  completed: number
  total: number
}

const CompletionRateIndicator = ({ completed, total }: CompletionRateIndicatorProps) => {
  const rate = total > 0 ? (completed / total) * 100 : 0
  const rateColor: 'emerald' | 'amber' | 'red' = rate >= 80 ? 'emerald' : rate >= 50 ? 'amber' : 'red'

  return (
    <Card padding="md" className="col-span-full md:col-span-1">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-tactical-600 dark:text-tactical-400">
          Completion Rate
        </h4>
        <span className={cn(
          'text-2xl font-bold',
          rateColor === 'emerald' && 'text-emerald-600 dark:text-emerald-400',
          rateColor === 'amber' && 'text-amber-600 dark:text-amber-400',
          rateColor === 'red' && 'text-red-600 dark:text-red-400',
        )}>
          {rate.toFixed(0)}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-2 rounded-full bg-tactical-200 dark:bg-tactical-700 overflow-hidden">
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500',
            rateColor === 'emerald' && 'bg-emerald-500',
            rateColor === 'amber' && 'bg-amber-500',
            rateColor === 'red' && 'bg-red-500',
          )}
          style={{ width: `${rate}%` }}
        />
      </div>

      <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-2">
        {completed} of {total} investigations completed successfully
      </p>
    </Card>
  )
}

// ============================================================================
// Main Component
// ============================================================================

interface AutoInvestigationMonitorProps {
  className?: string
  defaultTimeRange?: TimeRange
  autoRefresh?: boolean
}

const AutoInvestigationMonitor = ({
  className,
  defaultTimeRange = '24h',
  autoRefresh = true,
}: AutoInvestigationMonitorProps) => {
  const [timeRange, setTimeRange] = useState<TimeRange>(defaultTimeRange)
  const [statusFilter, setStatusFilter] = useState<AutoInvestigationStatusFilter>('all')

  // Fetch stats with auto-refresh
  const {
    data: statsResponse,
    isLoading: isLoadingStats,
    isFetching: isFetchingStats,
  } = useGetAutoInvestigationStatsQuery(
    { time_range: timeRange },
    {
      pollingInterval: autoRefresh ? AUTO_REFRESH_INTERVAL : undefined,
      refetchOnMountOrArgChange: true,
    }
  )

  // Fetch recent investigations with auto-refresh
  const {
    data: investigationsResponse,
    isLoading: isLoadingInvestigations,
    isFetching: isFetchingInvestigations,
  } = useGetRecentAutoInvestigationsQuery(
    {
      limit: 20,
      status: statusFilter === 'all' ? undefined : statusFilter,
    },
    {
      pollingInterval: autoRefresh ? AUTO_REFRESH_INTERVAL : undefined,
      refetchOnMountOrArgChange: true,
    }
  )

  // Extract data from response wrapper
  const stats = statsResponse?.data
  const investigations = investigationsResponse?.data?.investigations

  // Show fetching indicator (subtle pulse on header)
  const isRefreshing = (isFetchingStats || isFetchingInvestigations) &&
    !isLoadingStats && !isLoadingInvestigations

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className={cn(
            'p-2 rounded-lg bg-tiger-orange/10',
            isRefreshing && 'animate-pulse'
          )}>
            <BoltIcon className="w-6 h-6 text-tiger-orange" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-tactical-900 dark:text-tactical-100">
              Auto-Investigation Monitor
            </h2>
            <p className="text-sm text-tactical-500 dark:text-tactical-400">
              Tracking automated investigations from the discovery pipeline
            </p>
          </div>
        </div>

        <TimeRangeSelector
          value={timeRange}
          onChange={setTimeRange}
          disabled={isLoadingStats}
        />
      </div>

      {/* Stats Grid */}
      <StatsGrid
        stats={stats}
        isLoading={isLoadingStats}
      />

      {/* Secondary metrics row */}
      {stats && stats.total_triggered > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <CompletionRateIndicator
            completed={stats.completed}
            total={stats.total_triggered}
          />

          {/* Quick stats cards */}
          <Card padding="md" className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <ArrowTrendingUpIcon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-tactical-500 dark:text-tactical-400">Active Now</p>
              <p className="text-2xl font-bold text-tactical-900 dark:text-tactical-100">
                {stats.pending}
              </p>
            </div>
          </Card>

          <Card padding="md" className="flex items-center gap-4">
            <div className={cn(
              'p-3 rounded-lg',
              stats.failed > 0
                ? 'bg-red-100 dark:bg-red-900/30'
                : 'bg-emerald-100 dark:bg-emerald-900/30'
            )}>
              {stats.failed > 0 ? (
                <ArrowTrendingDownIcon className="w-5 h-5 text-red-600 dark:text-red-400" />
              ) : (
                <CheckCircleIcon className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              )}
            </div>
            <div>
              <p className="text-sm text-tactical-500 dark:text-tactical-400">
                {stats.failed > 0 ? 'Failed Rate' : 'Success'}
              </p>
              <p className={cn(
                'text-2xl font-bold',
                stats.failed > 0
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-emerald-600 dark:text-emerald-400'
              )}>
                {stats.failed > 0
                  ? `${calculateTrendPercentage(stats.failed, stats.total_triggered)}%`
                  : '100%'}
              </p>
            </div>
          </Card>
        </div>
      )}

      {/* Recent Investigations List */}
      <RecentInvestigationsList
        investigations={investigations}
        isLoading={isLoadingInvestigations}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
      />

      {/* Auto-refresh indicator */}
      {autoRefresh && (
        <p className="text-center text-xs text-tactical-400 dark:text-tactical-500">
          Auto-refreshing every 30 seconds
          {isRefreshing && (
            <span className="ml-2 inline-flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-tiger-orange animate-pulse" />
              Updating...
            </span>
          )}
        </p>
      )}
    </div>
  )
}

export default AutoInvestigationMonitor

import { useState, useEffect } from 'react'
import {
  CpuChipIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  PhotoIcon,
  GlobeAltIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  ArrowPathIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline'
import Card, { CardHeader, CardTitle, CardContent } from '../common/Card'
import { cn } from '../../utils/cn'

// Types
export type SubagentTaskType =
  | 'ml_inference'
  | 'research'
  | 'report_generation'
  | 'image_processing'
  | 'web_crawl'

export type SubagentTaskStatus = 'running' | 'queued' | 'completed' | 'error'

export interface SubagentTask {
  id: string
  type: SubagentTaskType
  status: SubagentTaskStatus
  investigation_id?: string
  started_at?: string
  progress?: number
  model?: string // for ml_inference type
}

export interface PoolStats {
  ml_inference: { active: number; max: number }
  research: { active: number; max: number }
  report_generation: { active: number; max: number }
}

export interface SubagentActivityPanelProps {
  tasks: SubagentTask[]
  poolStats?: PoolStats
  onTaskClick?: (taskId: string) => void
  className?: string
}

// Helper functions
const getTaskTypeIcon = (type: SubagentTaskType) => {
  const iconClass = 'w-4 h-4'
  switch (type) {
    case 'ml_inference':
      return <CpuChipIcon className={iconClass} />
    case 'research':
      return <MagnifyingGlassIcon className={iconClass} />
    case 'report_generation':
      return <DocumentTextIcon className={iconClass} />
    case 'image_processing':
      return <PhotoIcon className={iconClass} />
    case 'web_crawl':
      return <GlobeAltIcon className={iconClass} />
    default:
      return <CpuChipIcon className={iconClass} />
  }
}

const getTaskTypeLabel = (type: SubagentTaskType): string => {
  const labels: Record<SubagentTaskType, string> = {
    ml_inference: 'ML Inference',
    research: 'Research',
    report_generation: 'Report Gen',
    image_processing: 'Image Processing',
    web_crawl: 'Web Crawl',
  }
  return labels[type]
}

const getStatusIcon = (status: SubagentTaskStatus) => {
  const iconClass = 'w-4 h-4'
  switch (status) {
    case 'running':
      return <ArrowPathIcon className={cn(iconClass, 'animate-spin')} />
    case 'completed':
      return <CheckCircleIcon className={iconClass} />
    case 'error':
      return <ExclamationCircleIcon className={iconClass} />
    case 'queued':
      return <ClockIcon className={iconClass} />
    default:
      return <ClockIcon className={iconClass} />
  }
}

const getStatusColor = (status: SubagentTaskStatus): string => {
  switch (status) {
    case 'running':
      return 'text-tiger-orange'
    case 'completed':
      return 'text-emerald-500'
    case 'error':
      return 'text-red-500'
    case 'queued':
      return 'text-tactical-400'
    default:
      return 'text-tactical-400'
  }
}

const getStatusBgColor = (status: SubagentTaskStatus): string => {
  switch (status) {
    case 'running':
      return 'bg-tiger-orange/10'
    case 'completed':
      return 'bg-emerald-500/10'
    case 'error':
      return 'bg-red-500/10'
    case 'queued':
      return 'bg-tactical-400/10'
    default:
      return 'bg-tactical-400/10'
  }
}

const formatTimeAgo = (dateString?: string): string => {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSecs = Math.floor(diffMs / 1000)
  const diffMins = Math.floor(diffSecs / 60)
  const diffHours = Math.floor(diffMins / 60)

  if (diffSecs < 60) return `${diffSecs}s ago`
  if (diffMins < 60) return `${diffMins}m ago`
  return `${diffHours}h ago`
}

// Pool utilization bar component
interface PoolBarProps {
  type: SubagentTaskType
  active: number
  max: number
  testId: string
}

const PoolBar = ({ type, active, max, testId }: PoolBarProps) => {
  const percentage = max > 0 ? Math.round((active / max) * 100) : 0
  const isIdle = active === 0
  const label = getTaskTypeLabel(type)

  return (
    <div data-testid={testId} className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <span className="text-tactical-500 dark:text-tactical-400">
            {getTaskTypeIcon(type)}
          </span>
          <span className="font-medium text-tactical-700 dark:text-tactical-300">
            {label}
          </span>
        </div>
        <span className={cn(
          'text-xs font-mono',
          isIdle
            ? 'text-tactical-400 dark:text-tactical-500'
            : 'text-tiger-orange'
        )}>
          {active}/{max} {isIdle ? 'idle' : 'running'}
        </span>
      </div>

      <div className="relative h-2 bg-tactical-200 dark:bg-tactical-700 rounded-full overflow-hidden">
        <div
          className={cn(
            'absolute inset-y-0 left-0 rounded-full transition-all duration-500',
            isIdle
              ? 'bg-tactical-300 dark:bg-tactical-600'
              : 'bg-tiger-orange'
          )}
          style={{ width: `${percentage}%` }}
        />
        {/* Animated shine effect for running tasks */}
        {!isIdle && (
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-progress" />
          </div>
        )}
      </div>

      <div className="text-xs text-tactical-500 dark:text-tactical-400 text-right">
        {percentage}%
      </div>
    </div>
  )
}

// Task item component
interface TaskItemProps {
  task: SubagentTask
  onClick?: () => void
}

const TaskItem = ({ task, onClick }: TaskItemProps) => {
  const displayName = task.model || task.type
  const hasClickHandler = onClick && task.investigation_id

  return (
    <div
      data-testid={`subagent-task-${task.id}`}
      className={cn(
        'flex items-center justify-between py-2 px-3 rounded-lg transition-colors',
        getStatusBgColor(task.status),
        hasClickHandler && 'cursor-pointer hover:bg-opacity-20'
      )}
      onClick={hasClickHandler ? onClick : undefined}
      role={hasClickHandler ? 'button' : undefined}
      tabIndex={hasClickHandler ? 0 : undefined}
      onKeyDown={hasClickHandler ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick?.()
        }
      } : undefined}
    >
      <div className="flex items-center gap-3 min-w-0">
        <span className={cn('flex-shrink-0', getStatusColor(task.status))}>
          {getStatusIcon(task.status)}
        </span>

        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-tactical-800 dark:text-tactical-200 truncate">
              {displayName}
            </span>
            <span className={cn(
              'text-xs px-1.5 py-0.5 rounded font-medium',
              getStatusColor(task.status),
              getStatusBgColor(task.status)
            )}>
              {task.status}
            </span>
          </div>

          {task.started_at && (
            <span className="text-xs text-tactical-500 dark:text-tactical-400">
              {formatTimeAgo(task.started_at)}
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 flex-shrink-0">
        {task.status === 'running' && task.progress !== undefined && (
          <div className="flex items-center gap-1.5">
            <div className="w-16 h-1.5 bg-tactical-200 dark:bg-tactical-600 rounded-full overflow-hidden">
              <div
                className="h-full bg-tiger-orange rounded-full transition-all duration-300"
                style={{ width: `${task.progress}%` }}
              />
            </div>
            <span className="text-xs font-mono text-tiger-orange">
              {task.progress}%
            </span>
          </div>
        )}

        {task.status === 'completed' && (
          <CheckCircleIcon className="w-4 h-4 text-emerald-500" />
        )}
      </div>
    </div>
  )
}

// Main component
export function SubagentActivityPanel({
  tasks,
  poolStats,
  onTaskClick,
  className,
}: SubagentActivityPanelProps) {
  const [isCompact, setIsCompact] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Auto-refresh animation effect
  useEffect(() => {
    const interval = setInterval(() => {
      setIsRefreshing(true)
      setTimeout(() => setIsRefreshing(false), 500)
    }, 30000) // Pulse every 30 seconds

    return () => clearInterval(interval)
  }, [])

  // Sort tasks: running first, then queued, then completed, then error
  const sortedTasks = [...tasks].sort((a, b) => {
    const statusOrder: Record<SubagentTaskStatus, number> = {
      running: 0,
      queued: 1,
      completed: 2,
      error: 3,
    }
    return statusOrder[a.status] - statusOrder[b.status]
  })

  // Limit tasks shown in compact view
  const visibleTasks = isCompact ? sortedTasks.slice(0, 5) : sortedTasks.slice(0, 10)
  const hiddenCount = sortedTasks.length - visibleTasks.length

  // Count tasks by status
  const runningCount = tasks.filter(t => t.status === 'running').length
  const queuedCount = tasks.filter(t => t.status === 'queued').length

  return (
    <Card
      data-testid="subagent-activity-panel"
      className={cn('relative overflow-hidden', className)}
      padding="none"
    >
      {/* Refresh indicator */}
      {isRefreshing && (
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-tiger-orange/30">
          <div className="h-full w-1/3 bg-tiger-orange animate-progress" />
        </div>
      )}

      <div className="p-6">
        <CardHeader
          action={
            <button
              onClick={() => setIsCompact(!isCompact)}
              className="p-1.5 rounded-lg hover:bg-tactical-100 dark:hover:bg-tactical-700 transition-colors"
              aria-label={isCompact ? 'Expand panel' : 'Collapse panel'}
            >
              {isCompact ? (
                <ChevronDownIcon className="w-4 h-4 text-tactical-500" />
              ) : (
                <ChevronUpIcon className="w-4 h-4 text-tactical-500" />
              )}
            </button>
          }
        >
          <div className="flex items-center gap-3">
            <CardTitle className="uppercase tracking-wide text-sm">
              Subagent Activity
            </CardTitle>

            {/* Status indicators */}
            <div className="flex items-center gap-2">
              {runningCount > 0 && (
                <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-tiger-orange/10 text-tiger-orange">
                  <ArrowPathIcon className="w-3 h-3 animate-spin" />
                  {runningCount} running
                </span>
              )}
              {queuedCount > 0 && (
                <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-tactical-400/10 text-tactical-500 dark:text-tactical-400">
                  <ClockIcon className="w-3 h-3" />
                  {queuedCount} queued
                </span>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {/* Pool Stats */}
          {poolStats && (
            <div
              data-testid="subagent-pool-stats"
              className={cn(
                'space-y-4 pb-4 mb-4 border-b border-tactical-200 dark:border-tactical-700',
                isCompact && 'space-y-3'
              )}
            >
              <PoolBar
                type="ml_inference"
                active={poolStats.ml_inference.active}
                max={poolStats.ml_inference.max}
                testId="subagent-pool-ml_inference"
              />
              <PoolBar
                type="research"
                active={poolStats.research.active}
                max={poolStats.research.max}
                testId="subagent-pool-research"
              />
              <PoolBar
                type="report_generation"
                active={poolStats.report_generation.active}
                max={poolStats.report_generation.max}
                testId="subagent-pool-report_generation"
              />
            </div>
          )}

          {/* Tasks List */}
          <div data-testid="subagent-tasks-list" className="space-y-2">
            <h4 className="text-xs font-medium uppercase tracking-wider text-tactical-500 dark:text-tactical-400 mb-3">
              Recent Tasks
            </h4>

            {visibleTasks.length === 0 ? (
              <div className="text-center py-6 text-tactical-500 dark:text-tactical-400">
                <CpuChipIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No active tasks</p>
              </div>
            ) : (
              <div className="space-y-1.5">
                {visibleTasks.map((task) => (
                  <TaskItem
                    key={task.id}
                    task={task}
                    onClick={
                      onTaskClick && task.investigation_id
                        ? () => onTaskClick(task.id)
                        : undefined
                    }
                  />
                ))}
              </div>
            )}

            {hiddenCount > 0 && (
              <button
                onClick={() => setIsCompact(false)}
                className="w-full mt-2 py-2 text-xs text-tactical-500 dark:text-tactical-400 hover:text-tiger-orange dark:hover:text-tiger-orange transition-colors"
              >
                + {hiddenCount} more tasks
              </button>
            )}
          </div>
        </CardContent>
      </div>
    </Card>
  )
}

export default SubagentActivityPanel

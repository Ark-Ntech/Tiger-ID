import { cn } from '../../utils/cn'
import { FunnelIcon, XMarkIcon } from '@heroicons/react/24/outline'
import type {
  VerificationEntityType,
  VerificationSource,
  VerificationPriority,
  VerificationQueueStatus,
} from '../../types/verification'

export interface VerificationFiltersState {
  entity_type: VerificationEntityType | 'all'
  source: VerificationSource | 'all'
  priority: VerificationPriority | 'all'
  status: VerificationQueueStatus | 'all'
}

interface VerificationFiltersProps {
  filters: VerificationFiltersState
  onChange: (filters: VerificationFiltersState) => void
  className?: string
}

const selectBaseStyles = cn(
  'h-10 px-3 pr-8 rounded-lg text-sm font-medium',
  'bg-white dark:bg-tactical-800',
  'border border-tactical-300 dark:border-tactical-600',
  'text-tactical-900 dark:text-tactical-100',
  'focus:outline-none focus:ring-2 focus:ring-tiger-orange/30 focus:border-tiger-orange',
  'cursor-pointer appearance-none',
  'transition-all duration-200'
)

const selectArrowStyles = `
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 0.5rem center;
  background-repeat: no-repeat;
  background-size: 1.5em 1.5em;
`

export const VerificationFilters = ({
  filters,
  onChange,
  className,
}: VerificationFiltersProps) => {
  const handleChange = (key: keyof VerificationFiltersState, value: string) => {
    onChange({
      ...filters,
      [key]: value,
    })
  }

  const hasActiveFilters =
    filters.entity_type !== 'all' ||
    filters.source !== 'all' ||
    filters.priority !== 'all' ||
    filters.status !== 'all'

  const clearFilters = () => {
    onChange({
      entity_type: 'all',
      source: 'all',
      priority: 'all',
      status: 'all',
    })
  }

  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-3 p-4',
        'bg-tactical-50 dark:bg-tactical-900/50',
        'border border-tactical-200 dark:border-tactical-700',
        'rounded-xl',
        className
      )}
    >
      {/* Filter Icon */}
      <div className="flex items-center gap-2 text-tactical-500 dark:text-tactical-400">
        <FunnelIcon className="w-4 h-4" />
        <span className="text-sm font-medium hidden sm:inline">Filters</span>
      </div>

      {/* Divider */}
      <div className="hidden sm:block w-px h-6 bg-tactical-300 dark:bg-tactical-600" />

      {/* Entity Type */}
      <div className="flex flex-col gap-1">
        <label className="text-2xs font-medium text-tactical-500 dark:text-tactical-400 uppercase tracking-wide">
          Entity Type
        </label>
        <select
          value={filters.entity_type}
          onChange={(e) => handleChange('entity_type', e.target.value)}
          className={selectBaseStyles}
          style={{ ...Object.fromEntries(selectArrowStyles.split(';').filter(s => s.trim()).map(s => {
            const [key, ...val] = s.split(':')
            return [key.trim().replace(/-([a-z])/g, (_, c) => c.toUpperCase()), val.join(':').trim()]
          })) }}
        >
          <option value="all">All Types</option>
          <option value="tiger">Tigers</option>
          <option value="facility">Facilities</option>
        </select>
      </div>

      {/* Source */}
      <div className="flex flex-col gap-1">
        <label className="text-2xs font-medium text-tactical-500 dark:text-tactical-400 uppercase tracking-wide">
          Source
        </label>
        <select
          value={filters.source}
          onChange={(e) => handleChange('source', e.target.value)}
          className={selectBaseStyles}
          style={{ ...Object.fromEntries(selectArrowStyles.split(';').filter(s => s.trim()).map(s => {
            const [key, ...val] = s.split(':')
            return [key.trim().replace(/-([a-z])/g, (_, c) => c.toUpperCase()), val.join(':').trim()]
          })) }}
        >
          <option value="all">All Sources</option>
          <option value="auto_discovery">Auto Discovery</option>
          <option value="user_upload">User Upload</option>
        </select>
      </div>

      {/* Priority */}
      <div className="flex flex-col gap-1">
        <label className="text-2xs font-medium text-tactical-500 dark:text-tactical-400 uppercase tracking-wide">
          Priority
        </label>
        <select
          value={filters.priority}
          onChange={(e) => handleChange('priority', e.target.value)}
          className={selectBaseStyles}
          style={{ ...Object.fromEntries(selectArrowStyles.split(';').filter(s => s.trim()).map(s => {
            const [key, ...val] = s.split(':')
            return [key.trim().replace(/-([a-z])/g, (_, c) => c.toUpperCase()), val.join(':').trim()]
          })) }}
        >
          <option value="all">All Priorities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* Status */}
      <div className="flex flex-col gap-1">
        <label className="text-2xs font-medium text-tactical-500 dark:text-tactical-400 uppercase tracking-wide">
          Status
        </label>
        <select
          value={filters.status}
          onChange={(e) => handleChange('status', e.target.value)}
          className={selectBaseStyles}
          style={{ ...Object.fromEntries(selectArrowStyles.split(';').filter(s => s.trim()).map(s => {
            const [key, ...val] = s.split(':')
            return [key.trim().replace(/-([a-z])/g, (_, c) => c.toUpperCase()), val.join(':').trim()]
          })) }}
        >
          <option value="all">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="in_review">In Review</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      {/* Clear Filters */}
      {hasActiveFilters && (
        <>
          <div className="flex-1" />
          <button
            onClick={clearFilters}
            className={cn(
              'flex items-center gap-1.5 px-3 py-2 rounded-lg',
              'text-sm font-medium text-tactical-600 dark:text-tactical-300',
              'hover:bg-tactical-200 dark:hover:bg-tactical-700',
              'transition-colors duration-200'
            )}
          >
            <XMarkIcon className="w-4 h-4" />
            Clear Filters
          </button>
        </>
      )}
    </div>
  )
}

export default VerificationFilters

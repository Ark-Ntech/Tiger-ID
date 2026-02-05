import { useState, useEffect, useCallback, useMemo } from 'react'
import { cn } from '../../utils/cn'

// Filter state interface
export interface TigerFilterState {
  search: string
  facility: string
  status: 'all' | 'verified' | 'pending' | 'unverified'
  minConfidence: number
  sortBy: 'name' | 'confidence' | 'created_at' | 'facility'
  sortOrder: 'asc' | 'desc'
}

// Props interface
export interface TigerFiltersProps {
  filters: TigerFilterState
  facilities: { id: string; name: string }[]
  totalCount: number
  filteredCount: number
  onFilterChange: (filters: Partial<TigerFilterState>) => void
  onReset: () => void
  className?: string
}

// Confidence threshold options
const CONFIDENCE_OPTIONS = [
  { value: 0, label: 'All Confidence' },
  { value: 95, label: '> 95%' },
  { value: 85, label: '> 85%' },
  { value: 70, label: '> 70%' },
  { value: 50, label: '> 50%' },
]

// Status options
const STATUS_OPTIONS = [
  { value: 'all', label: 'All Status' },
  { value: 'verified', label: 'Verified' },
  { value: 'pending', label: 'Pending' },
  { value: 'unverified', label: 'Unverified' },
] as const

// Sort options
const SORT_OPTIONS = [
  { value: 'name', label: 'Name' },
  { value: 'confidence', label: 'Confidence' },
  { value: 'created_at', label: 'Date Added' },
  { value: 'facility', label: 'Facility' },
] as const

// Chevron icon component
const ChevronDownIcon = ({ className }: { className?: string }) => (
  <svg
    className={cn('w-4 h-4', className)}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
)

// Search icon component
const SearchIcon = ({ className }: { className?: string }) => (
  <svg
    className={cn('w-4 h-4', className)}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
    />
  </svg>
)

// Close icon component
const CloseIcon = ({ className }: { className?: string }) => (
  <svg
    className={cn('w-3 h-3', className)}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
)

// Arrow sort icons
const SortAscIcon = ({ className }: { className?: string }) => (
  <svg
    className={cn('w-4 h-4', className)}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
  </svg>
)

const SortDescIcon = ({ className }: { className?: string }) => (
  <svg
    className={cn('w-4 h-4', className)}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
)

// Filter chip component
interface FilterChipProps {
  label: string
  onRemove: () => void
}

const FilterChip = ({ label, onRemove }: FilterChipProps) => (
  <span
    data-testid="tiger-filter-chip"
    className={cn(
      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full',
      'text-xs font-medium',
      'bg-tiger-orange/15 text-tiger-orange',
      'dark:bg-tiger-orange/25 dark:text-tiger-orange-light',
      'border border-tiger-orange/30',
      'transition-all duration-200',
      'hover:bg-tiger-orange/25 dark:hover:bg-tiger-orange/35'
    )}
  >
    {label}
    <button
      type="button"
      onClick={onRemove}
      className={cn(
        'p-0.5 rounded-full',
        'hover:bg-tiger-orange/30 dark:hover:bg-tiger-orange/40',
        'transition-colors duration-150'
      )}
      aria-label={`Remove ${label} filter`}
    >
      <CloseIcon />
    </button>
  </span>
)

// Dropdown select component
interface SelectDropdownProps {
  value: string | number
  options: readonly { value: string | number; label: string }[]
  onChange: (value: string) => void
  'data-testid'?: string
  className?: string
}

const SelectDropdown = ({
  value,
  options,
  onChange,
  'data-testid': testId,
  className,
}: SelectDropdownProps) => (
  <div className="relative">
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      data-testid={testId}
      className={cn(
        'appearance-none cursor-pointer',
        'pl-3 pr-8 py-2 rounded-lg',
        'text-sm font-medium',
        'bg-white text-tactical-700',
        'border border-tactical-200',
        'hover:border-tactical-300 hover:bg-tactical-50',
        'focus:outline-none focus:ring-2 focus:ring-tiger-orange/30 focus:border-tiger-orange',
        'dark:bg-tactical-800 dark:text-tactical-200 dark:border-tactical-600',
        'dark:hover:border-tactical-500 dark:hover:bg-tactical-700/80',
        'dark:focus:border-tiger-orange',
        'transition-all duration-200',
        className
      )}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
    <ChevronDownIcon
      className={cn(
        'absolute right-2.5 top-1/2 -translate-y-1/2',
        'text-tactical-400 dark:text-tactical-500',
        'pointer-events-none'
      )}
    />
  </div>
)

export const TigerFilters = ({
  filters,
  facilities,
  totalCount,
  filteredCount,
  onFilterChange,
  onReset,
  className,
}: TigerFiltersProps) => {
  // Local search state for debouncing
  const [localSearch, setLocalSearch] = useState(filters.search)

  // Sync local search with external filters
  useEffect(() => {
    setLocalSearch(filters.search)
  }, [filters.search])

  // Debounced search handler
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localSearch !== filters.search) {
        onFilterChange({ search: localSearch })
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [localSearch, filters.search, onFilterChange])

  // Check if any filters are active
  const hasActiveFilters = useMemo(() => {
    return (
      filters.search !== '' ||
      filters.facility !== '' ||
      filters.status !== 'all' ||
      filters.minConfidence > 0
    )
  }, [filters])

  // Get active filter chips
  const activeFilterChips = useMemo(() => {
    const chips: { label: string; onRemove: () => void }[] = []

    if (filters.facility) {
      const facilityName = facilities.find((f) => f.id === filters.facility)?.name || filters.facility
      chips.push({
        label: facilityName,
        onRemove: () => onFilterChange({ facility: '' }),
      })
    }

    if (filters.status !== 'all') {
      const statusLabel = STATUS_OPTIONS.find((s) => s.value === filters.status)?.label || filters.status
      chips.push({
        label: statusLabel,
        onRemove: () => onFilterChange({ status: 'all' }),
      })
    }

    if (filters.minConfidence > 0) {
      chips.push({
        label: `> ${filters.minConfidence}%`,
        onRemove: () => onFilterChange({ minConfidence: 0 }),
      })
    }

    return chips
  }, [filters, facilities, onFilterChange])

  // Handlers
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalSearch(e.target.value)
  }, [])

  const handleFacilityChange = useCallback(
    (value: string) => {
      onFilterChange({ facility: value })
    },
    [onFilterChange]
  )

  const handleStatusChange = useCallback(
    (value: string) => {
      onFilterChange({ status: value as TigerFilterState['status'] })
    },
    [onFilterChange]
  )

  const handleConfidenceChange = useCallback(
    (value: string) => {
      onFilterChange({ minConfidence: parseInt(value, 10) })
    },
    [onFilterChange]
  )

  const handleSortChange = useCallback(
    (value: string) => {
      onFilterChange({ sortBy: value as TigerFilterState['sortBy'] })
    },
    [onFilterChange]
  )

  const handleSortOrderToggle = useCallback(() => {
    onFilterChange({ sortOrder: filters.sortOrder === 'asc' ? 'desc' : 'asc' })
  }, [filters.sortOrder, onFilterChange])

  const handleReset = useCallback(() => {
    setLocalSearch('')
    onReset()
  }, [onReset])

  // Build facility options with "All Facilities" option
  const facilityOptions = useMemo(
    () => [{ value: '', label: 'All Facilities' }, ...facilities.map((f) => ({ value: f.id, label: f.name }))],
    [facilities]
  )

  return (
    <div
      data-testid="tiger-filters"
      className={cn(
        'rounded-xl',
        'bg-white dark:bg-tactical-800',
        'border border-tactical-200 dark:border-tactical-700',
        'shadow-tactical',
        'overflow-hidden',
        className
      )}
    >
      {/* Top row: Dropdown filters */}
      <div
        className={cn(
          'px-4 py-3',
          'border-b border-tactical-100 dark:border-tactical-700/50',
          'bg-tactical-50/50 dark:bg-tactical-800/50'
        )}
      >
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-sm font-semibold text-tactical-600 dark:text-tactical-400 tracking-wide uppercase">
            Filters:
          </span>

          {/* Facility dropdown */}
          <SelectDropdown
            value={filters.facility}
            options={facilityOptions}
            onChange={handleFacilityChange}
            data-testid="tiger-filter-facility"
          />

          {/* Status dropdown */}
          <SelectDropdown
            value={filters.status}
            options={STATUS_OPTIONS}
            onChange={handleStatusChange}
            data-testid="tiger-filter-status"
          />

          {/* Confidence dropdown */}
          <SelectDropdown
            value={filters.minConfidence}
            options={CONFIDENCE_OPTIONS}
            onChange={handleConfidenceChange}
            data-testid="tiger-filter-confidence"
          />

          {/* Sort dropdown */}
          <div className="flex items-center gap-1">
            <SelectDropdown
              value={filters.sortBy}
              options={SORT_OPTIONS}
              onChange={handleSortChange}
              data-testid="tiger-filter-sort"
            />

            {/* Sort order toggle */}
            <button
              type="button"
              onClick={handleSortOrderToggle}
              data-testid="tiger-filter-order"
              className={cn(
                'p-2 rounded-lg',
                'text-tactical-500 hover:text-tactical-700',
                'dark:text-tactical-400 dark:hover:text-tactical-200',
                'hover:bg-tactical-100 dark:hover:bg-tactical-700',
                'focus:outline-none focus:ring-2 focus:ring-tiger-orange/30',
                'transition-all duration-200'
              )}
              aria-label={`Sort ${filters.sortOrder === 'asc' ? 'ascending' : 'descending'}`}
              title={filters.sortOrder === 'asc' ? 'Ascending' : 'Descending'}
            >
              {filters.sortOrder === 'asc' ? <SortAscIcon /> : <SortDescIcon />}
            </button>
          </div>
        </div>
      </div>

      {/* Bottom row: Search and count */}
      <div className="px-4 py-3">
        <div className="flex flex-wrap items-center gap-4">
          {/* Search input */}
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <SearchIcon
              className={cn(
                'absolute left-3 top-1/2 -translate-y-1/2',
                'text-tactical-400 dark:text-tactical-500'
              )}
            />
            <input
              type="text"
              value={localSearch}
              onChange={handleSearchChange}
              placeholder="Search tigers..."
              data-testid="tiger-filter-search"
              className={cn(
                'w-full pl-10 pr-4 py-2 rounded-lg',
                'text-sm',
                'bg-tactical-50 text-tactical-900 placeholder-tactical-400',
                'border border-tactical-200',
                'hover:border-tactical-300 hover:bg-white',
                'focus:outline-none focus:ring-2 focus:ring-tiger-orange/30 focus:border-tiger-orange focus:bg-white',
                'dark:bg-tactical-900/50 dark:text-tactical-100 dark:placeholder-tactical-500',
                'dark:border-tactical-600 dark:hover:border-tactical-500 dark:hover:bg-tactical-800',
                'dark:focus:bg-tactical-800 dark:focus:border-tiger-orange',
                'transition-all duration-200'
              )}
            />
          </div>

          {/* Results count */}
          <div className="ml-auto text-sm text-tactical-500 dark:text-tactical-400 whitespace-nowrap">
            Showing{' '}
            <span className="font-semibold text-tactical-700 dark:text-tactical-200">{filteredCount}</span>
            {' '}of{' '}
            <span className="font-semibold text-tactical-700 dark:text-tactical-200">{totalCount}</span>
          </div>
        </div>

        {/* Active filter chips row */}
        {hasActiveFilters && (
          <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-tactical-100 dark:border-tactical-700/50">
            <span className="text-xs font-medium text-tactical-500 dark:text-tactical-400 uppercase tracking-wide">
              Active:
            </span>

            {activeFilterChips.map((chip, index) => (
              <FilterChip key={`${chip.label}-${index}`} label={chip.label} onRemove={chip.onRemove} />
            ))}

            {/* Clear all button */}
            <button
              type="button"
              onClick={handleReset}
              data-testid="tiger-filter-clear"
              className={cn(
                'ml-auto px-3 py-1 rounded-lg',
                'text-xs font-medium',
                'text-tactical-600 hover:text-tactical-800',
                'dark:text-tactical-400 dark:hover:text-tactical-200',
                'hover:bg-tactical-100 dark:hover:bg-tactical-700',
                'focus:outline-none focus:ring-2 focus:ring-tiger-orange/30',
                'transition-all duration-200'
              )}
            >
              Clear All
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default TigerFilters

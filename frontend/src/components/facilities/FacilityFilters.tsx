import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { cn } from '../../utils/cn'
import Badge from '../common/Badge'

// Props interface
export interface FacilityFiltersProps {
  filters: {
    search?: string
    type?: string[]
    country?: string[]
    discoveryStatus?: string[]
    hasTigers?: boolean
  }
  onFiltersChange: (filters: FacilityFiltersProps['filters']) => void
  facilityTypes: string[]
  countries: string[]
  className?: string
}

// Default facility types if none provided
const DEFAULT_FACILITY_TYPES = ['zoo', 'sanctuary', 'rescue', 'breeding', 'other']

// Discovery status options
const DISCOVERY_STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
  { value: 'pending', label: 'Pending' },
]

// Icon components
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

const FunnelIcon = ({ className }: { className?: string }) => (
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
      d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
    />
  </svg>
)

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

const XMarkIcon = ({ className }: { className?: string }) => (
  <svg
    className={cn('w-4 h-4', className)}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
)

const CheckIcon = ({ className }: { className?: string }) => (
  <svg
    className={cn('w-4 h-4', className)}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
)

// Multi-select dropdown component
interface MultiSelectProps {
  label: string
  options: { value: string; label: string }[]
  selected: string[]
  onChange: (selected: string[]) => void
  placeholder?: string
  'data-testid'?: string
}

const MultiSelect = ({
  label,
  options,
  selected,
  onChange,
  placeholder = 'Select...',
  'data-testid': testId,
}: MultiSelectProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const toggleOption = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value))
    } else {
      onChange([...selected, value])
    }
  }

  const displayText = selected.length > 0
    ? selected.length === 1
      ? options.find((o) => o.value === selected[0])?.label || selected[0]
      : `${selected.length} selected`
    : placeholder

  return (
    <div ref={containerRef} className="relative" data-testid={testId}>
      <label className="block text-2xs font-medium text-tactical-500 dark:text-tactical-400 uppercase tracking-wide mb-1">
        {label}
      </label>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        data-testid={`${testId}-trigger`}
        className={cn(
          'flex items-center justify-between gap-2 w-full min-w-[140px]',
          'h-10 px-3 rounded-lg text-sm font-medium',
          'bg-white dark:bg-tactical-800',
          'border border-tactical-300 dark:border-tactical-600',
          'text-tactical-900 dark:text-tactical-100',
          'hover:border-tactical-400 dark:hover:border-tactical-500',
          'focus:outline-none focus:ring-2 focus:ring-tiger-orange/30 focus:border-tiger-orange',
          'transition-all duration-200',
          selected.length > 0 && 'border-tiger-orange/50'
        )}
      >
        <span className={cn(selected.length === 0 && 'text-tactical-400 dark:text-tactical-500')}>
          {displayText}
        </span>
        <ChevronDownIcon
          className={cn(
            'text-tactical-400 transition-transform duration-200',
            isOpen && 'rotate-180'
          )}
        />
      </button>

      {isOpen && (
        <div
          data-testid={`${testId}-dropdown`}
          className={cn(
            'absolute z-50 mt-1 w-full min-w-[180px]',
            'bg-white dark:bg-tactical-800',
            'border border-tactical-200 dark:border-tactical-600',
            'rounded-lg shadow-tactical-lg',
            'py-1 max-h-60 overflow-y-auto',
            'animate-fade-in-down'
          )}
        >
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => toggleOption(option.value)}
              data-testid={`${testId}-option-${option.value}`}
              className={cn(
                'flex items-center gap-2 w-full px-3 py-2 text-sm text-left',
                'hover:bg-tactical-50 dark:hover:bg-tactical-700',
                'transition-colors duration-150',
                selected.includes(option.value) && 'bg-tiger-orange/10 dark:bg-tiger-orange/20'
              )}
            >
              <span
                className={cn(
                  'flex items-center justify-center w-4 h-4 rounded border',
                  selected.includes(option.value)
                    ? 'bg-tiger-orange border-tiger-orange text-white'
                    : 'border-tactical-300 dark:border-tactical-500'
                )}
              >
                {selected.includes(option.value) && <CheckIcon className="w-3 h-3" />}
              </span>
              <span className="text-tactical-700 dark:text-tactical-200">{option.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// Toggle switch component
interface ToggleSwitchProps {
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
  'data-testid'?: string
}

const ToggleSwitch = ({
  label,
  checked,
  onChange,
  'data-testid': testId,
}: ToggleSwitchProps) => (
  <div className="flex flex-col gap-1" data-testid={testId}>
    <label className="text-2xs font-medium text-tactical-500 dark:text-tactical-400 uppercase tracking-wide">
      {label}
    </label>
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      data-testid={`${testId}-switch`}
      className={cn(
        'relative inline-flex items-center h-10 px-3 rounded-lg',
        'border transition-all duration-200',
        checked
          ? 'bg-tiger-orange/10 border-tiger-orange text-tiger-orange dark:bg-tiger-orange/20'
          : 'bg-white dark:bg-tactical-800 border-tactical-300 dark:border-tactical-600 text-tactical-500 dark:text-tactical-400',
        'hover:border-tiger-orange/50',
        'focus:outline-none focus:ring-2 focus:ring-tiger-orange/30'
      )}
    >
      <span
        className={cn(
          'w-4 h-4 rounded-full mr-2 transition-colors duration-200',
          checked ? 'bg-tiger-orange' : 'bg-tactical-300 dark:bg-tactical-500'
        )}
      />
      <span className="text-sm font-medium whitespace-nowrap">Has Tigers</span>
    </button>
  </div>
)

export const FacilityFilters = ({
  filters,
  onFiltersChange,
  facilityTypes,
  countries,
  className,
}: FacilityFiltersProps) => {
  // Local search state for debouncing
  const [localSearch, setLocalSearch] = useState(filters.search || '')
  // Mobile dropdown state
  const [isMobileOpen, setIsMobileOpen] = useState(false)

  // Sync local search with external filters
  useEffect(() => {
    setLocalSearch(filters.search || '')
  }, [filters.search])

  // Debounced search handler
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localSearch !== (filters.search || '')) {
        onFiltersChange({ ...filters, search: localSearch || undefined })
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [localSearch, filters, onFiltersChange])

  // Compute facility type options
  const facilityTypeOptions = useMemo(() => {
    const types = facilityTypes.length > 0 ? facilityTypes : DEFAULT_FACILITY_TYPES
    return types.map((type) => ({
      value: type,
      label: type.charAt(0).toUpperCase() + type.slice(1),
    }))
  }, [facilityTypes])

  // Compute country options
  const countryOptions = useMemo(() => {
    return countries.map((country) => ({
      value: country,
      label: country,
    }))
  }, [countries])

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0
    if (filters.search && filters.search.trim()) count++
    if (filters.type && filters.type.length > 0) count++
    if (filters.country && filters.country.length > 0) count++
    if (filters.discoveryStatus && filters.discoveryStatus.length > 0) count++
    if (filters.hasTigers === true) count++
    return count
  }, [filters])

  // Check if any filters are active
  const hasActiveFilters = activeFilterCount > 0

  // Handlers
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalSearch(e.target.value)
  }, [])

  const handleTypeChange = useCallback(
    (types: string[]) => {
      onFiltersChange({ ...filters, type: types.length > 0 ? types : undefined })
    },
    [filters, onFiltersChange]
  )

  const handleCountryChange = useCallback(
    (countries: string[]) => {
      onFiltersChange({ ...filters, country: countries.length > 0 ? countries : undefined })
    },
    [filters, onFiltersChange]
  )

  const handleDiscoveryStatusChange = useCallback(
    (statuses: string[]) => {
      onFiltersChange({ ...filters, discoveryStatus: statuses.length > 0 ? statuses : undefined })
    },
    [filters, onFiltersChange]
  )

  const handleHasTigersChange = useCallback(
    (hasTigers: boolean) => {
      onFiltersChange({ ...filters, hasTigers: hasTigers || undefined })
    },
    [filters, onFiltersChange]
  )

  const handleClearAll = useCallback(() => {
    setLocalSearch('')
    onFiltersChange({})
    setIsMobileOpen(false)
  }, [onFiltersChange])

  // Filter controls component (shared between mobile and desktop)
  const FilterControls = () => (
    <>
      {/* Facility Type */}
      <MultiSelect
        label="Facility Type"
        options={facilityTypeOptions}
        selected={filters.type || []}
        onChange={handleTypeChange}
        placeholder="All Types"
        data-testid="facility-filter-type"
      />

      {/* Country */}
      <MultiSelect
        label="Country"
        options={countryOptions}
        selected={filters.country || []}
        onChange={handleCountryChange}
        placeholder="All Countries"
        data-testid="facility-filter-country"
      />

      {/* Discovery Status */}
      <MultiSelect
        label="Discovery Status"
        options={DISCOVERY_STATUS_OPTIONS}
        selected={filters.discoveryStatus || []}
        onChange={handleDiscoveryStatusChange}
        placeholder="All Statuses"
        data-testid="facility-filter-discovery-status"
      />

      {/* Has Tigers Toggle */}
      <ToggleSwitch
        label="Tiger Presence"
        checked={filters.hasTigers === true}
        onChange={handleHasTigersChange}
        data-testid="facility-filter-has-tigers"
      />
    </>
  )

  return (
    <div
      data-testid="facility-filters"
      className={cn(
        'rounded-xl',
        'bg-white dark:bg-tactical-800',
        'border border-tactical-200 dark:border-tactical-700',
        'shadow-tactical',
        'overflow-visible',
        className
      )}
    >
      {/* Desktop Filter Bar */}
      <div className="hidden md:block">
        <div
          className={cn(
            'flex flex-wrap items-end gap-4 p-4',
            'border-b border-tactical-100 dark:border-tactical-700/50'
          )}
        >
          {/* Filter Icon and Label */}
          <div className="flex items-center gap-2 text-tactical-500 dark:text-tactical-400 pb-2">
            <FunnelIcon />
            <span className="text-sm font-medium">Filters</span>
            {activeFilterCount > 0 && (
              <Badge
                variant="tiger"
                size="xs"
                data-testid="facility-filter-count-badge"
              >
                {activeFilterCount}
              </Badge>
            )}
          </div>

          {/* Divider */}
          <div className="w-px h-10 bg-tactical-200 dark:bg-tactical-600 mb-1" />

          {/* Filter Controls */}
          <FilterControls />

          {/* Spacer */}
          <div className="flex-1" />

          {/* Clear All Button */}
          {hasActiveFilters && (
            <button
              type="button"
              onClick={handleClearAll}
              data-testid="facility-filter-clear-all"
              className={cn(
                'flex items-center gap-1.5 px-3 py-2 rounded-lg mb-1',
                'text-sm font-medium text-tactical-600 dark:text-tactical-300',
                'hover:bg-tactical-100 dark:hover:bg-tactical-700',
                'focus:outline-none focus:ring-2 focus:ring-tiger-orange/30',
                'transition-colors duration-200'
              )}
            >
              <XMarkIcon />
              Clear All
            </button>
          )}
        </div>

        {/* Search Input Row */}
        <div className="p-4">
          <div className="relative max-w-md">
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
              placeholder="Search facilities by name..."
              data-testid="facility-filter-search"
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
        </div>
      </div>

      {/* Mobile Filter Bar */}
      <div className="md:hidden">
        {/* Mobile Header */}
        <div className="flex items-center gap-3 p-4">
          {/* Search Input */}
          <div className="relative flex-1">
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
              placeholder="Search facilities..."
              data-testid="facility-filter-search-mobile"
              className={cn(
                'w-full pl-10 pr-4 py-2 rounded-lg',
                'text-sm',
                'bg-tactical-50 text-tactical-900 placeholder-tactical-400',
                'border border-tactical-200',
                'focus:outline-none focus:ring-2 focus:ring-tiger-orange/30 focus:border-tiger-orange focus:bg-white',
                'dark:bg-tactical-900/50 dark:text-tactical-100 dark:placeholder-tactical-500',
                'dark:border-tactical-600 dark:focus:bg-tactical-800',
                'transition-all duration-200'
              )}
            />
          </div>

          {/* Filter Toggle Button */}
          <button
            type="button"
            onClick={() => setIsMobileOpen(!isMobileOpen)}
            data-testid="facility-filter-mobile-toggle"
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-lg',
              'text-sm font-medium',
              'border transition-all duration-200',
              isMobileOpen || hasActiveFilters
                ? 'bg-tiger-orange/10 border-tiger-orange text-tiger-orange dark:bg-tiger-orange/20'
                : 'bg-white dark:bg-tactical-800 border-tactical-300 dark:border-tactical-600 text-tactical-600 dark:text-tactical-300',
              'focus:outline-none focus:ring-2 focus:ring-tiger-orange/30'
            )}
          >
            <FunnelIcon />
            <span>Filters</span>
            {activeFilterCount > 0 && (
              <Badge variant="tiger" size="xs">
                {activeFilterCount}
              </Badge>
            )}
          </button>
        </div>

        {/* Mobile Filter Dropdown */}
        {isMobileOpen && (
          <div
            data-testid="facility-filter-mobile-dropdown"
            className={cn(
              'px-4 pb-4 pt-2',
              'border-t border-tactical-100 dark:border-tactical-700/50',
              'animate-fade-in-down'
            )}
          >
            <div className="flex flex-col gap-4">
              <FilterControls />

              {/* Clear All Button */}
              {hasActiveFilters && (
                <button
                  type="button"
                  onClick={handleClearAll}
                  data-testid="facility-filter-clear-all-mobile"
                  className={cn(
                    'flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg',
                    'text-sm font-medium text-tactical-600 dark:text-tactical-300',
                    'bg-tactical-100 dark:bg-tactical-700',
                    'hover:bg-tactical-200 dark:hover:bg-tactical-600',
                    'focus:outline-none focus:ring-2 focus:ring-tiger-orange/30',
                    'transition-colors duration-200'
                  )}
                >
                  <XMarkIcon />
                  Clear All Filters
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default FacilityFilters

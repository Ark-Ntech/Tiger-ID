import { useState } from 'react'
import { cn } from '../../utils/cn'
import Badge from '../common/Badge'
import {
  InformationCircleIcon,
  DocumentTextIcon,
  EyeIcon,
  BeakerIcon,
  ShieldCheckIcon,
  LightBulbIcon,
  GlobeAltIcon,
  LinkIcon,
  MapIcon,
  ChevronDownIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'

// Tab definition
interface Tab {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  count?: number | null
  highlight?: boolean
  disabled?: boolean
}

// Tab group definition
interface TabGroup {
  id: string
  label: string
  priority: 'primary' | 'secondary' | 'tertiary'
  tabs: Tab[]
}

interface Investigation2TabNavProps {
  activeTab: string
  onTabChange: (tabId: string) => void
  counts?: {
    detection?: number
    matches?: number
    verification?: number
    external?: number
    citations?: number
  }
  verificationDisagreement?: boolean
  className?: string
}

export const Investigation2TabNav = ({
  activeTab,
  onTabChange,
  counts = {},
  verificationDisagreement = false,
  className,
}: Investigation2TabNavProps) => {
  const [mobileDropdownOpen, setMobileDropdownOpen] = useState(false)

  // Define tab groups
  const tabGroups: TabGroup[] = [
    {
      id: 'investigation',
      label: 'Investigation',
      priority: 'primary',
      tabs: [
        { id: 'overview', label: 'Overview', icon: InformationCircleIcon },
        { id: 'report', label: 'Full Report', icon: DocumentTextIcon },
      ],
    },
    {
      id: 'analysis',
      label: 'Analysis',
      priority: 'secondary',
      tabs: [
        { id: 'detection', label: 'Detection', icon: EyeIcon, count: counts.detection },
        { id: 'matching', label: 'Matches', icon: BeakerIcon, count: counts.matches },
        {
          id: 'verification',
          label: 'Verification',
          icon: ShieldCheckIcon,
          count: counts.verification,
          highlight: verificationDisagreement,
        },
        { id: 'methodology', label: 'Methodology', icon: LightBulbIcon },
      ],
    },
    {
      id: 'intelligence',
      label: 'Intelligence',
      priority: 'tertiary',
      tabs: [
        { id: 'external', label: 'External Intel', icon: GlobeAltIcon, count: counts.external },
        { id: 'citations', label: 'Citations', icon: LinkIcon, count: counts.citations },
        { id: 'location', label: 'Location', icon: MapIcon },
      ],
    },
  ]

  // Get all tabs flat
  const allTabs = tabGroups.flatMap(group => group.tabs)
  const activeTabData = allTabs.find(t => t.id === activeTab)

  // Priority-based sizing
  const priorityClasses = {
    primary: 'px-4 py-2.5 text-sm font-semibold',
    secondary: 'px-3 py-2 text-sm font-medium',
    tertiary: 'px-2.5 py-1.5 text-xs font-medium',
  }

  const priorityIconSizes = {
    primary: 'w-5 h-5',
    secondary: 'w-4 h-4',
    tertiary: 'w-4 h-4',
  }

  // Render a single tab
  const renderTab = (tab: Tab, priority: TabGroup['priority']) => {
    const Icon = tab.icon
    const isActive = activeTab === tab.id
    const isHighlighted = tab.highlight

    return (
      <button
        key={tab.id}
        onClick={() => {
          onTabChange(tab.id)
          setMobileDropdownOpen(false)
        }}
        disabled={tab.disabled}
        className={cn(
          'flex items-center gap-2 rounded-lg transition-all duration-200 whitespace-nowrap',
          priorityClasses[priority],
          isActive
            ? isHighlighted
              ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-200 shadow-sm'
              : 'bg-white text-tactical-900 shadow-sm dark:bg-tactical-700 dark:text-tactical-100'
            : isHighlighted
            ? 'text-amber-600 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-900/30'
            : 'text-tactical-600 hover:bg-tactical-100/80 dark:text-tactical-400 dark:hover:bg-tactical-700/50',
          tab.disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <Icon className={cn(priorityIconSizes[priority])} />
        <span>{tab.label}</span>

        {/* Highlight indicator */}
        {isHighlighted && !isActive && (
          <span className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" />
        )}

        {/* Count badge */}
        {tab.count !== undefined && tab.count !== null && (
          <Badge
            size="sm"
            variant={
              isHighlighted
                ? 'warning'
                : isActive
                ? 'primary'
                : tab.count > 0
                ? 'info'
                : 'default'
            }
          >
            {tab.count}
          </Badge>
        )}
      </button>
    )
  }

  return (
    <div className={cn('', className)}>
      {/* Desktop Navigation */}
      <div className="hidden lg:block">
        <div className="space-y-3">
          {tabGroups.map(group => (
            <div key={group.id} className="flex items-center gap-2">
              {/* Group label */}
              <span className={cn(
                'text-xs font-medium uppercase tracking-wider w-20 flex-shrink-0',
                'text-tactical-400 dark:text-tactical-500'
              )}>
                {group.label}
              </span>

              {/* Tabs container */}
              <div className={cn(
                'flex items-center gap-1 p-1 rounded-lg',
                'bg-tactical-100/80 dark:bg-tactical-800/80'
              )}>
                {group.tabs.map(tab => renderTab(tab, group.priority))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tablet Navigation - Horizontal scroll */}
      <div className="hidden md:block lg:hidden">
        <div className={cn(
          'flex items-center gap-1 p-1 rounded-lg overflow-x-auto scrollbar-hide',
          'bg-tactical-100/80 dark:bg-tactical-800/80'
        )}>
          {allTabs.map(tab => {
            const group = tabGroups.find(g => g.tabs.some(t => t.id === tab.id))!
            return renderTab(tab, group.priority)
          })}
        </div>
      </div>

      {/* Mobile Navigation - Dropdown */}
      <div className="md:hidden relative">
        <button
          onClick={() => setMobileDropdownOpen(!mobileDropdownOpen)}
          className={cn(
            'w-full flex items-center justify-between gap-2 px-4 py-3 rounded-lg',
            'bg-white dark:bg-tactical-800 border border-tactical-200 dark:border-tactical-700',
            'text-tactical-900 dark:text-tactical-100 font-medium',
            'shadow-tactical hover:shadow-tactical-md transition-all'
          )}
        >
          <div className="flex items-center gap-3">
            {activeTabData && (
              <>
                <activeTabData.icon className="w-5 h-5 text-tactical-600 dark:text-tactical-400" />
                <span>{activeTabData.label}</span>
              </>
            )}
          </div>
          <ChevronDownIcon
            className={cn(
              'w-5 h-5 text-tactical-400 transition-transform duration-200',
              mobileDropdownOpen && 'rotate-180'
            )}
          />
        </button>

        {/* Dropdown menu */}
        {mobileDropdownOpen && (
          <div className={cn(
            'absolute top-full left-0 right-0 mt-2 z-50',
            'bg-white dark:bg-tactical-800 rounded-xl shadow-tactical-lg',
            'border border-tactical-200 dark:border-tactical-700',
            'overflow-hidden animate-fade-in-down'
          )}>
            {tabGroups.map((group, groupIdx) => (
              <div key={group.id}>
                {/* Group header */}
                <div className={cn(
                  'px-4 py-2 text-xs font-medium uppercase tracking-wider',
                  'text-tactical-400 dark:text-tactical-500 bg-tactical-50 dark:bg-tactical-900/50',
                  groupIdx > 0 && 'border-t border-tactical-200 dark:border-tactical-700'
                )}>
                  {group.label}
                </div>

                {/* Group tabs */}
                {group.tabs.map(tab => {
                  const Icon = tab.icon
                  const isActive = activeTab === tab.id
                  const isHighlighted = tab.highlight

                  return (
                    <button
                      key={tab.id}
                      onClick={() => {
                        onTabChange(tab.id)
                        setMobileDropdownOpen(false)
                      }}
                      className={cn(
                        'w-full flex items-center gap-3 px-4 py-3 text-left',
                        'transition-colors',
                        isActive
                          ? isHighlighted
                            ? 'bg-amber-50 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200'
                            : 'bg-tactical-100 text-tactical-900 dark:bg-tactical-700 dark:text-tactical-100'
                          : 'hover:bg-tactical-50 dark:hover:bg-tactical-700/50 text-tactical-700 dark:text-tactical-300'
                      )}
                    >
                      <Icon className={cn(
                        'w-5 h-5',
                        isHighlighted
                          ? 'text-amber-600 dark:text-amber-400'
                          : 'text-tactical-500 dark:text-tactical-400'
                      )} />
                      <span className="flex-1 font-medium">{tab.label}</span>

                      {/* Indicators */}
                      <div className="flex items-center gap-2">
                        {isHighlighted && (
                          <ExclamationTriangleIcon className="w-4 h-4 text-amber-500" />
                        )}
                        {tab.count !== undefined && tab.count !== null && (
                          <Badge
                            size="sm"
                            variant={isHighlighted ? 'warning' : tab.count > 0 ? 'info' : 'default'}
                          >
                            {tab.count}
                          </Badge>
                        )}
                      </div>
                    </button>
                  )
                })}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Verification Alert Banner (shown when there's disagreement) */}
      {verificationDisagreement && (
        <div className={cn(
          'mt-4 flex items-center gap-3 px-4 py-3 rounded-lg',
          'bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20',
          'border border-amber-300 dark:border-amber-700',
          'text-amber-800 dark:text-amber-200'
        )}>
          <ExclamationTriangleIcon className="w-5 h-5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold">Verification Disagreement Detected</p>
            <p className="text-xs opacity-80">
              Geometric verification results differ from ReID rankings. Review recommended.
            </p>
          </div>
          <button
            onClick={() => onTabChange('verification')}
            className={cn(
              'flex-shrink-0 px-3 py-1.5 rounded-lg text-sm font-medium',
              'bg-amber-200/50 hover:bg-amber-200 dark:bg-amber-800/50 dark:hover:bg-amber-800',
              'transition-colors'
            )}
          >
            View Details
          </button>
        </div>
      )}
    </div>
  )
}

export default Investigation2TabNav

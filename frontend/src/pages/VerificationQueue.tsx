import { useState, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { cn } from '../utils/cn'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import Alert from '../components/common/Alert'
import Badge from '../components/common/Badge'
import {
  VerificationStatsPanel,
  VerificationFilters,
  VerificationActionModal,
  VerificationPagination,
  BulkVerificationActions,
  VerificationComparisonOverlay,
  ModelAgreementBadge,
  type VerificationFiltersState,
  type VerificationActionType,
  type ComparisonImage,
  type ModelScore,
} from '../components/verification'
import type {
  VerificationQueueItem,
  VerificationStatsResponse,
} from '../types/verification'
import {
  ArrowPathIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  EyeIcon,
  CheckIcon,
  XMarkIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline'

// Mock data for demonstration - in production, this would come from RTK Query hooks
const mockStats: VerificationStatsResponse = {
  by_status: {
    pending: 23,
    approved: 156,
    rejected: 12,
    in_review: 5,
  },
  by_source: {
    auto_discovery: 18,
    user_upload: 10,
  },
  by_priority: {
    critical: 2,
    high: 8,
    medium: 15,
    low: 3,
  },
  by_entity_type: {
    tiger: 16,
    facility: 12,
  },
  recent_activity: {
    approved_24h: 24,
    rejected_24h: 3,
    hourly_breakdown: [],
  },
  total_pending: 23,
  total_approved_24h: 24,
  total_rejected_24h: 3,
  total_items: 196,
  timestamp: new Date().toISOString(),
}

// Extended mock item interface for display purposes
interface ExtendedVerificationItem extends VerificationQueueItem {
  queryImageUrl?: string
  matchImageUrl?: string
  confidence?: number
  modelScores?: Record<string, number>
  facilityName?: string
}

const mockItems: ExtendedVerificationItem[] = [
  {
    queue_id: 'vq-001',
    entity_type: 'tiger',
    entity_id: 'tiger-abc123',
    entity_name: 'Rajah',
    priority: 'high',
    status: 'pending',
    requires_human_review: true,
    source: 'auto_discovery',
    created_at: new Date(Date.now() - 3600000).toISOString(),
    queryImageUrl: '/images/query/tiger-001.jpg',
    matchImageUrl: '/images/match/rajah-001.jpg',
    confidence: 0.92,
    facilityName: 'Big Cat Rescue, Tampa FL',
    modelScores: {
      wildlife_tools: 0.94,
      cvwc2019_reid: 0.91,
      transreid: 0.89,
      megadescriptor_b: 0.93,
      tiger_reid: 0.90,
      rapid_reid: 0.88,
    },
    entity_details: {
      name: 'Rajah',
      alias: 'The Big One',
      status: 'active',
      last_seen_location: 'Big Cat Rescue, Tampa FL',
    },
  },
  {
    queue_id: 'vq-002',
    entity_type: 'tiger',
    entity_id: 'tiger-def456',
    entity_name: 'Luna',
    priority: 'critical',
    status: 'pending',
    requires_human_review: true,
    source: 'auto_discovery',
    created_at: new Date(Date.now() - 7200000).toISOString(),
    queryImageUrl: '/images/query/tiger-002.jpg',
    matchImageUrl: '/images/match/luna-001.jpg',
    confidence: 0.78,
    facilityName: 'Unknown Facility',
    modelScores: {
      wildlife_tools: 0.82,
      cvwc2019_reid: 0.75,
      transreid: 0.79,
      megadescriptor_b: 0.71,
      tiger_reid: 0.68,
      rapid_reid: 0.72,
    },
    entity_details: {
      name: 'Luna',
      status: 'unknown',
      last_seen_location: 'Unknown Facility',
      last_seen_date: '2025-12-15',
    },
  },
  {
    queue_id: 'vq-003',
    entity_type: 'tiger',
    entity_id: 'tiger-ghi789',
    entity_name: 'Shere Khan',
    priority: 'medium',
    status: 'pending',
    requires_human_review: true,
    source: 'user_upload',
    created_at: new Date(Date.now() - 14400000).toISOString(),
    queryImageUrl: '/images/query/tiger-003.jpg',
    matchImageUrl: '/images/match/sherekhan-001.jpg',
    confidence: 0.65,
    facilityName: 'Wildlife Sanctuary, FL',
    modelScores: {
      wildlife_tools: 0.72,
      cvwc2019_reid: 0.68,
      transreid: 0.55,
      megadescriptor_b: 0.62,
      tiger_reid: 0.58,
      rapid_reid: 0.52,
    },
    entity_details: {
      name: 'Shere Khan',
      alias: 'Khan',
      status: 'active',
    },
  },
  {
    queue_id: 'vq-004',
    entity_type: 'facility',
    entity_id: 'fac-xyz789',
    entity_name: 'Wildlife Wonders Zoo',
    priority: 'medium',
    status: 'pending',
    requires_human_review: true,
    source: 'user_upload',
    created_at: new Date(Date.now() - 21600000).toISOString(),
    entity_details: {
      exhibitor_name: 'Wildlife Wonders LLC',
      usda_license: '93-C-0123',
      city: 'Orlando',
      state: 'FL',
      tiger_count: 8,
    },
  },
  {
    queue_id: 'vq-005',
    entity_type: 'tiger',
    entity_id: 'tiger-jkl012',
    entity_name: 'Tigger',
    priority: 'low',
    status: 'approved',
    requires_human_review: false,
    source: 'auto_discovery',
    reviewed_by: 'admin@tigerid.org',
    reviewed_at: new Date(Date.now() - 86400000).toISOString(),
    review_notes: 'Verified through cross-reference with sanctuary records.',
    created_at: new Date(Date.now() - 172800000).toISOString(),
    queryImageUrl: '/images/query/tiger-005.jpg',
    matchImageUrl: '/images/match/tigger-001.jpg',
    confidence: 0.96,
    facilityName: 'Exotic Animal Encounters',
    modelScores: {
      wildlife_tools: 0.97,
      cvwc2019_reid: 0.96,
      transreid: 0.94,
      megadescriptor_b: 0.95,
      tiger_reid: 0.96,
      rapid_reid: 0.93,
    },
    entity_details: {
      name: 'Tigger',
      status: 'verified',
    },
  },
]

// Helper to count agreeing models
const countAgreeingModels = (
  modelScores: Record<string, number> | undefined,
  threshold = 0.7
): { agreeing: number; total: number } => {
  if (!modelScores) return { agreeing: 0, total: 0 }
  const scores = Object.values(modelScores)
  const agreeing = scores.filter((score) => score >= threshold).length
  return { agreeing, total: scores.length }
}

// Convert model scores object to ModelScore array
const toModelScoreArray = (
  modelScores: Record<string, number> | undefined
): ModelScore[] => {
  if (!modelScores) return []
  return Object.entries(modelScores).map(([model, score]) => ({ model, score }))
}

/**
 * VerificationQueue Page
 *
 * Admin dashboard for reviewing and processing verification queue items.
 * Displays tigers and facilities pending verification with filtering,
 * pagination, bulk actions, and comparison workflows.
 */
const VerificationQueue = () => {
  const navigate = useNavigate()

  // State
  const [filters, setFilters] = useState<VerificationFiltersState>({
    entity_type: 'all',
    source: 'all',
    priority: 'all',
    status: 'all',
  })
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [selectedItem, setSelectedItem] = useState<ExtendedVerificationItem | null>(null)
  const [actionType, setActionType] = useState<VerificationActionType>('approve')
  const [isActionModalOpen, setIsActionModalOpen] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Selection state for bulk operations
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [isBulkProcessing, setIsBulkProcessing] = useState(false)

  // Comparison overlay state
  const [comparisonItem, setComparisonItem] = useState<ExtendedVerificationItem | null>(null)
  const [isComparisonOpen, setIsComparisonOpen] = useState(false)

  // Simulated loading states
  const statsLoading = false
  const queueLoading = false
  const isUpdating = false

  // Filter items based on current filters
  const filteredItems = useMemo(() => {
    return mockItems.filter((item) => {
      if (filters.entity_type !== 'all' && item.entity_type !== filters.entity_type) {
        return false
      }
      if (filters.source !== 'all' && item.source !== filters.source) {
        return false
      }
      if (filters.priority !== 'all' && item.priority !== filters.priority) {
        return false
      }
      if (filters.status !== 'all' && item.status !== filters.status) {
        return false
      }
      return true
    })
  }, [filters])

  // Calculate pagination
  const totalItems = filteredItems.length
  const totalPages = Math.ceil(totalItems / pageSize)
  const paginatedItems = filteredItems.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  )

  // Selection helpers
  const isAllSelected =
    paginatedItems.length > 0 && paginatedItems.every((item) => selectedIds.has(item.queue_id))

  const handleSelectItem = useCallback((queueId: string, checked: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (checked) {
        next.add(queueId)
      } else {
        next.delete(queueId)
      }
      return next
    })
  }, [])

  const handleSelectAll = useCallback(() => {
    const allPageIds = paginatedItems.map((item) => item.queue_id)
    setSelectedIds((prev) => {
      const next = new Set(prev)
      allPageIds.forEach((id) => next.add(id))
      return next
    })
  }, [paginatedItems])

  const handleDeselectAll = useCallback(() => {
    setSelectedIds(new Set())
  }, [])

  // Handlers
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true)
    await new Promise((resolve) => setTimeout(resolve, 1000))
    setIsRefreshing(false)
    setSuccessMessage('Queue refreshed successfully')
    setTimeout(() => setSuccessMessage(null), 3000)
  }, [])

  const handleFiltersChange = useCallback((newFilters: VerificationFiltersState) => {
    setFilters(newFilters)
    setCurrentPage(1)
    setExpandedId(null)
    setSelectedIds(new Set())
  }, [])

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page)
    setExpandedId(null)
  }, [])

  const handlePageSizeChange = useCallback((size: number) => {
    setPageSize(size)
    setCurrentPage(1)
    setExpandedId(null)
  }, [])

  const handleExpandToggle = useCallback((id: string | null) => {
    setExpandedId(id)
  }, [])

  const handleView = useCallback((item: ExtendedVerificationItem) => {
    // Open comparison overlay for tiger items with images
    if (item.entity_type === 'tiger' && item.queryImageUrl && item.matchImageUrl) {
      setComparisonItem(item)
      setIsComparisonOpen(true)
    } else {
      // Navigate to detail view for facilities or items without images
      const basePath = item.entity_type === 'tiger' ? '/tigers' : '/facilities'
      navigate(`${basePath}/${item.entity_id}`)
    }
  }, [navigate])

  const handleApprove = useCallback((item: ExtendedVerificationItem) => {
    setSelectedItem(item)
    setActionType('approve')
    setIsActionModalOpen(true)
  }, [])

  const handleReject = useCallback((item: ExtendedVerificationItem) => {
    setSelectedItem(item)
    setActionType('reject')
    setIsActionModalOpen(true)
  }, [])

  const handleActionConfirm = useCallback(async (_notes: string) => {
    if (!selectedItem) return

    try {
      await new Promise((resolve) => setTimeout(resolve, 800))

      setIsActionModalOpen(false)
      setSelectedItem(null)
      setSuccessMessage(
        `Successfully ${actionType === 'approve' ? 'approved' : 'rejected'} ${
          selectedItem.entity_name || selectedItem.entity_id
        }`
      )
      setTimeout(() => setSuccessMessage(null), 5000)
    } catch (error) {
      setErrorMessage('Failed to update verification status. Please try again.')
      setTimeout(() => setErrorMessage(null), 5000)
    }
  }, [selectedItem, actionType])

  const handleActionModalClose = useCallback(() => {
    if (!isUpdating) {
      setIsActionModalOpen(false)
      setSelectedItem(null)
    }
  }, [isUpdating])

  // Bulk action handlers
  const handleBulkApprove = useCallback(async () => {
    setIsBulkProcessing(true)
    try {
      await new Promise((resolve) => setTimeout(resolve, 1500))
      setSuccessMessage(`Successfully approved ${selectedIds.size} item(s)`)
      setSelectedIds(new Set())
      setTimeout(() => setSuccessMessage(null), 5000)
    } catch (error) {
      setErrorMessage('Failed to process bulk approval. Please try again.')
      setTimeout(() => setErrorMessage(null), 5000)
    } finally {
      setIsBulkProcessing(false)
    }
  }, [selectedIds])

  const handleBulkReject = useCallback(async () => {
    setIsBulkProcessing(true)
    try {
      await new Promise((resolve) => setTimeout(resolve, 1500))
      setSuccessMessage(`Successfully rejected ${selectedIds.size} item(s)`)
      setSelectedIds(new Set())
      setTimeout(() => setSuccessMessage(null), 5000)
    } catch (error) {
      setErrorMessage('Failed to process bulk rejection. Please try again.')
      setTimeout(() => setErrorMessage(null), 5000)
    } finally {
      setIsBulkProcessing(false)
    }
  }, [selectedIds])

  // Comparison overlay handlers
  const handleComparisonClose = useCallback(() => {
    setIsComparisonOpen(false)
    setComparisonItem(null)
  }, [])

  const handleComparisonApprove = useCallback(async () => {
    if (!comparisonItem) return
    setIsComparisonOpen(false)
    setComparisonItem(null)
    setSuccessMessage(`Successfully approved ${comparisonItem.entity_name || comparisonItem.entity_id}`)
    setTimeout(() => setSuccessMessage(null), 5000)
  }, [comparisonItem])

  const handleComparisonReject = useCallback(async () => {
    if (!comparisonItem) return
    setIsComparisonOpen(false)
    setComparisonItem(null)
    setSuccessMessage(`Successfully rejected ${comparisonItem.entity_name || comparisonItem.entity_id}`)
    setTimeout(() => setSuccessMessage(null), 5000)
  }, [comparisonItem])

  const handleComparisonSkip = useCallback(() => {
    setIsComparisonOpen(false)
    setComparisonItem(null)
  }, [])

  // Prepare comparison overlay props
  const comparisonQueryImage: ComparisonImage | undefined = comparisonItem
    ? {
        url: comparisonItem.queryImageUrl || '',
        tiger_name: 'Query Image',
        facility: 'Unknown',
      }
    : undefined

  const comparisonMatchImage: ComparisonImage | undefined = comparisonItem
    ? {
        url: comparisonItem.matchImageUrl || '',
        tiger_id: comparisonItem.entity_id,
        tiger_name: comparisonItem.entity_name,
        facility: comparisonItem.facilityName,
        confidence: comparisonItem.confidence,
      }
    : undefined

  // Get priority badge variant
  const getPriorityVariant = (priority: string): 'danger' | 'warning' | 'info' | 'default' => {
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

  // Get status badge variant
  const getStatusVariant = (status: string): 'success' | 'danger' | 'warning' | 'info' => {
    switch (status) {
      case 'approved':
        return 'success'
      case 'rejected':
        return 'danger'
      case 'in_review':
        return 'warning'
      default:
        return 'info'
    }
  }

  return (
    <div
      data-testid="verification-queue-page"
      className="min-h-screen bg-tactical-50 dark:bg-tactical-950"
    >
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-4">
              <div
                className={cn(
                  'w-12 h-12 rounded-xl flex items-center justify-center',
                  'bg-gradient-to-br from-tiger-orange to-tiger-orange-dark',
                  'shadow-tiger'
                )}
              >
                <ShieldCheckIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-tactical-900 dark:text-tactical-100">
                  Verification Queue
                </h1>
                <p className="text-sm text-tactical-500 dark:text-tactical-400 mt-0.5">
                  Review and approve tigers and facilities awaiting verification
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Badge variant="warning" size="md" data-testid="pending-count-badge">
                {mockStats.total_pending} pending
              </Badge>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => navigate('/analytics/verification')}
                className="hidden sm:flex"
              >
                <ChartBarIcon className="w-4 h-4 mr-2" />
                Analytics
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleRefresh}
                disabled={isRefreshing}
                isLoading={isRefreshing}
                data-testid="refresh-button"
              >
                <ArrowPathIcon
                  className={cn('w-4 h-4 mr-2', isRefreshing && 'animate-spin')}
                />
                Refresh
              </Button>
            </div>
          </div>
        </div>

        {/* Success/Error Messages */}
        {successMessage && (
          <Alert
            type="success"
            message={successMessage}
            className="mb-6 animate-fade-in-down"
            onClose={() => setSuccessMessage(null)}
            data-testid="success-alert"
          />
        )}
        {errorMessage && (
          <Alert
            type="error"
            message={errorMessage}
            className="mb-6 animate-fade-in-down"
            onClose={() => setErrorMessage(null)}
            data-testid="error-alert"
          />
        )}

        {/* Stats Panel */}
        <div className="mb-6" data-testid="stats-panel">
          <VerificationStatsPanel stats={mockStats} isLoading={statsLoading} />
        </div>

        {/* Filters */}
        <div className="mb-6" data-testid="filters-panel">
          <VerificationFilters filters={filters} onChange={handleFiltersChange} />
        </div>

        {/* Bulk Actions Toolbar */}
        {paginatedItems.length > 0 && (
          <div className="mb-4">
            <BulkVerificationActions
              selectedCount={selectedIds.size}
              totalCount={paginatedItems.length}
              onSelectAll={handleSelectAll}
              onDeselectAll={handleDeselectAll}
              onBulkApprove={handleBulkApprove}
              onBulkReject={handleBulkReject}
              isAllSelected={isAllSelected}
              isProcessing={isBulkProcessing}
              data-testid="bulk-actions-toolbar"
            />
          </div>
        )}

        {/* Queue Table */}
        <Card padding="none" className="mb-6 overflow-hidden" data-testid="queue-table-card">
          <div className="px-6 py-4 border-b border-tactical-200 dark:border-tactical-700">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-tactical-900 dark:text-tactical-100">
                Queue Items
              </h2>
              <span className="text-sm text-tactical-500 dark:text-tactical-400">
                {totalItems} item{totalItems !== 1 ? 's' : ''} found
              </span>
            </div>
          </div>

          {/* Custom Table with Selection */}
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="verification-table">
              <thead className="bg-tactical-50 dark:bg-tactical-900/50">
                <tr>
                  <th className="w-12 px-4 py-3 text-left">
                    <span className="sr-only">Select</span>
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wide">
                    Query Image
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wide">
                    Match
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wide">
                    Confidence
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wide">
                    Models
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wide">
                    Priority
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wide">
                    Status
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-tactical-600 dark:text-tactical-400 uppercase tracking-wide">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-tactical-200 dark:divide-tactical-700">
                {queueLoading ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-12 text-center">
                      <div className="flex items-center justify-center">
                        <div className="w-8 h-8 border-4 border-tiger-orange border-t-transparent rounded-full animate-spin" />
                      </div>
                    </td>
                  </tr>
                ) : paginatedItems.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-12 text-center text-tactical-500 dark:text-tactical-400">
                      No items match your filters
                    </td>
                  </tr>
                ) : (
                  paginatedItems.map((item) => {
                    const isSelected = selectedIds.has(item.queue_id)
                    const isExpanded = expandedId === item.queue_id
                    const agreement = countAgreeingModels(item.modelScores)

                    return (
                      <>
                        <tr
                          key={item.queue_id}
                          data-testid={`queue-row-${item.queue_id}`}
                          className={cn(
                            'transition-colors',
                            isSelected
                              ? 'bg-tiger-orange/5 dark:bg-tiger-orange/10'
                              : 'hover:bg-tactical-50 dark:hover:bg-tactical-800/50'
                          )}
                        >
                          {/* Selection Checkbox */}
                          <td className="px-4 py-4">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={(e) => handleSelectItem(item.queue_id, e.target.checked)}
                              data-testid={`select-checkbox-${item.queue_id}`}
                              className={cn(
                                'w-4 h-4 rounded',
                                'border-tactical-300 dark:border-tactical-600',
                                'text-tiger-orange',
                                'focus:ring-tiger-orange focus:ring-offset-0'
                              )}
                            />
                          </td>

                          {/* Query Image */}
                          <td className="px-4 py-4">
                            {item.queryImageUrl ? (
                              <div className="w-16 h-16 rounded-lg overflow-hidden bg-tactical-100 dark:bg-tactical-800">
                                <img
                                  src={item.queryImageUrl}
                                  alt="Query"
                                  className="w-full h-full object-cover"
                                  onError={(e) => {
                                    e.currentTarget.src = '/placeholder-tiger.png'
                                  }}
                                />
                              </div>
                            ) : (
                              <div className="w-16 h-16 rounded-lg bg-tactical-100 dark:bg-tactical-800 flex items-center justify-center">
                                <span className="text-xs text-tactical-400">N/A</span>
                              </div>
                            )}
                          </td>

                          {/* Match Info */}
                          <td className="px-4 py-4">
                            <div className="flex flex-col gap-1">
                              <span className="font-medium text-tactical-900 dark:text-tactical-100">
                                {item.entity_name || item.entity_id}
                              </span>
                              {item.facilityName && (
                                <span className="text-xs text-tactical-500 dark:text-tactical-400">
                                  {item.facilityName}
                                </span>
                              )}
                              <Badge
                                variant={item.entity_type === 'tiger' ? 'tiger' : 'info'}
                                size="xs"
                              >
                                {item.entity_type}
                              </Badge>
                            </div>
                          </td>

                          {/* Confidence */}
                          <td className="px-4 py-4">
                            {item.confidence !== undefined ? (
                              <div className="flex flex-col gap-1">
                                <span
                                  className={cn(
                                    'font-semibold',
                                    item.confidence >= 0.85
                                      ? 'text-emerald-600 dark:text-emerald-400'
                                      : item.confidence >= 0.7
                                      ? 'text-amber-600 dark:text-amber-400'
                                      : 'text-red-600 dark:text-red-400'
                                  )}
                                >
                                  {(item.confidence * 100).toFixed(0)}%
                                </span>
                              </div>
                            ) : (
                              <span className="text-tactical-400">-</span>
                            )}
                          </td>

                          {/* Model Agreement */}
                          <td className="px-4 py-4">
                            {item.modelScores ? (
                              <ModelAgreementBadge
                                agreementCount={agreement.agreeing}
                                totalModels={agreement.total}
                                size="md"
                                showDetails
                                data-testid={`model-agreement-${item.queue_id}`}
                              />
                            ) : (
                              <span className="text-tactical-400">-</span>
                            )}
                          </td>

                          {/* Priority */}
                          <td className="px-4 py-4">
                            <Badge
                              variant={getPriorityVariant(item.priority)}
                              size="sm"
                            >
                              {item.priority}
                            </Badge>
                          </td>

                          {/* Status */}
                          <td className="px-4 py-4">
                            <Badge
                              variant={getStatusVariant(item.status)}
                              size="sm"
                            >
                              {item.status}
                            </Badge>
                          </td>

                          {/* Actions */}
                          <td className="px-4 py-4">
                            <div className="flex items-center justify-end gap-2">
                              {/* View/Compare Button */}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleView(item)}
                                title="View comparison"
                                data-testid={`view-button-${item.queue_id}`}
                              >
                                <EyeIcon className="w-4 h-4" />
                              </Button>

                              {/* Approve Button */}
                              {item.status === 'pending' && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleApprove(item)}
                                  className="text-emerald-600 hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-900/20"
                                  title="Approve"
                                  data-testid={`approve-button-${item.queue_id}`}
                                >
                                  <CheckIcon className="w-4 h-4" />
                                </Button>
                              )}

                              {/* Reject Button */}
                              {item.status === 'pending' && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleReject(item)}
                                  className="text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                                  title="Reject"
                                  data-testid={`reject-button-${item.queue_id}`}
                                >
                                  <XMarkIcon className="w-4 h-4" />
                                </Button>
                              )}

                              {/* Expand/Collapse Button */}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleExpandToggle(isExpanded ? null : item.queue_id)}
                                title={isExpanded ? 'Collapse' : 'Expand'}
                                data-testid={`expand-button-${item.queue_id}`}
                              >
                                {isExpanded ? (
                                  <ChevronUpIcon className="w-4 h-4" />
                                ) : (
                                  <ChevronDownIcon className="w-4 h-4" />
                                )}
                              </Button>
                            </div>
                          </td>
                        </tr>

                        {/* Expanded Row */}
                        {isExpanded && (
                          <tr key={`${item.queue_id}-expanded`}>
                            <td colSpan={8} className="px-4 py-4 bg-tactical-50 dark:bg-tactical-900/30">
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {/* Entity Details */}
                                <div>
                                  <h4 className="text-sm font-semibold text-tactical-700 dark:text-tactical-300 mb-2">
                                    Entity Details
                                  </h4>
                                  <dl className="space-y-1 text-sm">
                                    <div className="flex justify-between">
                                      <dt className="text-tactical-500 dark:text-tactical-400">ID:</dt>
                                      <dd className="font-mono text-tactical-700 dark:text-tactical-300">
                                        {item.entity_id}
                                      </dd>
                                    </div>
                                    <div className="flex justify-between">
                                      <dt className="text-tactical-500 dark:text-tactical-400">Source:</dt>
                                      <dd className="text-tactical-700 dark:text-tactical-300">
                                        {item.source?.replace('_', ' ')}
                                      </dd>
                                    </div>
                                    <div className="flex justify-between">
                                      <dt className="text-tactical-500 dark:text-tactical-400">Created:</dt>
                                      <dd className="text-tactical-700 dark:text-tactical-300">
                                        {item.created_at
                                          ? new Date(item.created_at).toLocaleDateString()
                                          : '-'}
                                      </dd>
                                    </div>
                                  </dl>
                                </div>

                                {/* Model Scores (if available) */}
                                {item.modelScores && (
                                  <div className="md:col-span-2">
                                    <h4 className="text-sm font-semibold text-tactical-700 dark:text-tactical-300 mb-2">
                                      Model Scores
                                    </h4>
                                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                      {Object.entries(item.modelScores).map(([model, score]) => (
                                        <div
                                          key={model}
                                          className="flex items-center justify-between p-2 rounded-lg bg-white dark:bg-tactical-800 border border-tactical-200 dark:border-tactical-700"
                                        >
                                          <span className="text-xs text-tactical-600 dark:text-tactical-400 truncate">
                                            {model.replace(/_/g, ' ')}
                                          </span>
                                          <span
                                            className={cn(
                                              'text-sm font-semibold ml-2',
                                              score >= 0.85
                                                ? 'text-emerald-600 dark:text-emerald-400'
                                                : score >= 0.7
                                                ? 'text-amber-600 dark:text-amber-400'
                                                : 'text-red-600 dark:text-red-400'
                                            )}
                                          >
                                            {(score * 100).toFixed(0)}%
                                          </span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Review Notes (if reviewed) */}
                                {item.review_notes && (
                                  <div className="md:col-span-3">
                                    <h4 className="text-sm font-semibold text-tactical-700 dark:text-tactical-300 mb-2">
                                      Review Notes
                                    </h4>
                                    <p className="text-sm text-tactical-600 dark:text-tactical-400 bg-white dark:bg-tactical-800 p-3 rounded-lg border border-tactical-200 dark:border-tactical-700">
                                      {item.review_notes}
                                    </p>
                                    {item.reviewed_by && (
                                      <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-2">
                                        Reviewed by {item.reviewed_by}{' '}
                                        {item.reviewed_at &&
                                          `on ${new Date(item.reviewed_at).toLocaleDateString()}`}
                                      </p>
                                    )}
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 0 && (
            <div className="px-6 py-4 border-t border-tactical-200 dark:border-tactical-700 bg-tactical-50 dark:bg-tactical-900/50">
              <VerificationPagination
                currentPage={currentPage}
                totalPages={totalPages}
                totalItems={totalItems}
                pageSize={pageSize}
                onPageChange={handlePageChange}
                onPageSizeChange={handlePageSizeChange}
              />
            </div>
          )}
        </Card>

        {/* Action Modal */}
        <VerificationActionModal
          isOpen={isActionModalOpen}
          onClose={handleActionModalClose}
          item={selectedItem}
          action={actionType}
          onConfirm={handleActionConfirm}
          isLoading={isUpdating}
        />

        {/* Comparison Overlay */}
        {comparisonQueryImage && comparisonMatchImage && (
          <VerificationComparisonOverlay
            isOpen={isComparisonOpen}
            onClose={handleComparisonClose}
            queryImage={comparisonQueryImage}
            matchImage={comparisonMatchImage}
            modelScores={toModelScoreArray(comparisonItem?.modelScores)}
            onApprove={handleComparisonApprove}
            onReject={handleComparisonReject}
            onSkip={handleComparisonSkip}
          />
        )}
      </div>
    </div>
  )
}

export default VerificationQueue

import { useState, useCallback } from 'react'
import { cn } from '../../utils/cn'
import Button from '../common/Button'
import {
  CheckIcon,
  XMarkIcon,
  ForwardIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'

export interface BulkVerificationActionsProps {
  selectedCount: number
  totalCount: number
  onSelectAll: () => void
  onDeselectAll: () => void
  onBulkApprove: () => void
  onBulkReject: () => void
  onBulkSkip?: () => void
  isAllSelected: boolean
  isProcessing?: boolean
  className?: string
}

type ConfirmAction = 'approve' | 'reject' | null

export const BulkVerificationActions = ({
  selectedCount,
  totalCount,
  onSelectAll,
  onDeselectAll,
  onBulkApprove,
  onBulkReject,
  onBulkSkip,
  isAllSelected,
  isProcessing = false,
  className,
}: BulkVerificationActionsProps) => {
  const [confirmAction, setConfirmAction] = useState<ConfirmAction>(null)

  const hasSelection = selectedCount > 0
  const isIndeterminate = selectedCount > 0 && selectedCount < totalCount

  const handleSelectAllToggle = useCallback(() => {
    if (isAllSelected || isIndeterminate) {
      onDeselectAll()
    } else {
      onSelectAll()
    }
  }, [isAllSelected, isIndeterminate, onSelectAll, onDeselectAll])

  const handleApproveClick = useCallback(() => {
    setConfirmAction('approve')
  }, [])

  const handleRejectClick = useCallback(() => {
    setConfirmAction('reject')
  }, [])

  const handleConfirm = useCallback(() => {
    if (confirmAction === 'approve') {
      onBulkApprove()
    } else if (confirmAction === 'reject') {
      onBulkReject()
    }
    setConfirmAction(null)
  }, [confirmAction, onBulkApprove, onBulkReject])

  const handleCancel = useCallback(() => {
    setConfirmAction(null)
  }, [])

  const handleSkip = useCallback(() => {
    if (onBulkSkip) {
      onBulkSkip()
    }
  }, [onBulkSkip])

  return (
    <div
      data-testid="bulk-verification-actions"
      className={cn(
        'sticky top-0 z-10',
        'px-4 py-3',
        'bg-tactical-50/95 dark:bg-tactical-900/95',
        'backdrop-blur-sm',
        'border border-tactical-200 dark:border-tactical-700',
        'rounded-xl',
        'shadow-sm',
        className
      )}
    >
      {/* Confirmation Dialog Overlay */}
      {confirmAction && (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-tactical-900/50 dark:bg-tactical-950/70 rounded-xl backdrop-blur-sm">
          <div className="flex items-center gap-4 px-6 py-4 bg-white dark:bg-tactical-800 rounded-lg shadow-xl border border-tactical-200 dark:border-tactical-700">
            <div
              className={cn(
                'w-10 h-10 rounded-full flex items-center justify-center',
                confirmAction === 'approve'
                  ? 'bg-emerald-100 dark:bg-emerald-900/30'
                  : 'bg-red-100 dark:bg-red-900/30'
              )}
            >
              <ExclamationTriangleIcon
                className={cn(
                  'w-5 h-5',
                  confirmAction === 'approve'
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-red-600 dark:text-red-400'
                )}
              />
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-tactical-900 dark:text-tactical-100">
                {confirmAction === 'approve' ? 'Approve' : 'Reject'} {selectedCount} item
                {selectedCount !== 1 ? 's' : ''}?
              </span>
              <span className="text-sm text-tactical-500 dark:text-tactical-400">
                This action cannot be undone.
              </span>
            </div>
            <div className="flex items-center gap-2 ml-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCancel}
                disabled={isProcessing}
              >
                Cancel
              </Button>
              <Button
                variant={confirmAction === 'approve' ? 'primary' : 'danger'}
                size="sm"
                onClick={handleConfirm}
                isLoading={isProcessing}
                className={
                  confirmAction === 'approve'
                    ? 'bg-emerald-600 hover:bg-emerald-700 focus:ring-emerald-500'
                    : ''
                }
              >
                {confirmAction === 'approve' ? 'Approve' : 'Reject'}
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        {/* Select All Checkbox and Count */}
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer group">
            <div className="relative">
              <input
                type="checkbox"
                data-testid="verification-select-all"
                checked={isAllSelected}
                ref={(el) => {
                  if (el) {
                    el.indeterminate = isIndeterminate
                  }
                }}
                onChange={handleSelectAllToggle}
                disabled={totalCount === 0 || isProcessing}
                className={cn(
                  'w-4 h-4 rounded',
                  'border-tactical-300 dark:border-tactical-600',
                  'text-tiger-orange',
                  'focus:ring-tiger-orange focus:ring-offset-0',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  'transition-colors duration-150'
                )}
              />
            </div>
            <span className="text-sm font-medium text-tactical-700 dark:text-tactical-300 group-hover:text-tactical-900 dark:group-hover:text-tactical-100 transition-colors">
              Select All
            </span>
          </label>

          <div className="h-4 w-px bg-tactical-300 dark:bg-tactical-600" />

          <span
            data-testid="verification-selected-count"
            className={cn(
              'text-sm',
              hasSelection
                ? 'font-semibold text-tiger-orange'
                : 'text-tactical-500 dark:text-tactical-400'
            )}
          >
            {selectedCount} selected
          </span>
        </div>

        {/* Bulk Action Buttons */}
        <div className="flex items-center gap-2 sm:ml-auto">
          <span className="text-xs font-medium text-tactical-500 dark:text-tactical-400 uppercase tracking-wide mr-1">
            Bulk Actions:
          </span>

          <Button
            data-testid="bulk-approve-button"
            variant="ghost"
            size="sm"
            onClick={handleApproveClick}
            disabled={!hasSelection || isProcessing}
            isLoading={isProcessing && confirmAction === 'approve'}
            className={cn(
              'gap-1.5',
              hasSelection
                ? 'text-emerald-600 hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-900/20'
                : ''
            )}
          >
            <CheckIcon className="w-4 h-4" />
            <span>Approve Selected</span>
          </Button>

          <Button
            data-testid="bulk-reject-button"
            variant="ghost"
            size="sm"
            onClick={handleRejectClick}
            disabled={!hasSelection || isProcessing}
            isLoading={isProcessing && confirmAction === 'reject'}
            className={cn(
              'gap-1.5',
              hasSelection
                ? 'text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20'
                : ''
            )}
          >
            <XMarkIcon className="w-4 h-4" />
            <span>Reject Selected</span>
          </Button>

          {onBulkSkip && (
            <Button
              data-testid="bulk-skip-button"
              variant="ghost"
              size="sm"
              onClick={handleSkip}
              disabled={!hasSelection || isProcessing}
              className="gap-1.5"
            >
              <ForwardIcon className="w-4 h-4" />
              <span>Skip</span>
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

export default BulkVerificationActions

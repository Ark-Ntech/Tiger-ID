import { useState } from 'react'
import { Fragment } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { cn } from '../../utils/cn'
import Button from '../common/Button'
import Badge from '../common/Badge'
import type { VerificationQueueItem } from '../../types/verification'
import {
  XMarkIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
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

export type VerificationActionType = 'approve' | 'reject'

interface VerificationActionModalProps {
  isOpen: boolean
  onClose: () => void
  item: VerificationQueueItem | null
  action: VerificationActionType
  onConfirm: (notes: string) => void
  isLoading?: boolean
}

export const VerificationActionModal = ({
  isOpen,
  onClose,
  item,
  action,
  onConfirm,
  isLoading = false,
}: VerificationActionModalProps) => {
  const [notes, setNotes] = useState('')

  const handleConfirm = () => {
    onConfirm(notes)
    setNotes('')
  }

  const handleClose = () => {
    if (!isLoading) {
      setNotes('')
      onClose()
    }
  }

  if (!item) return null

  const isApprove = action === 'approve'
  const ActionIcon = isApprove ? CheckCircleIcon : XCircleIcon

  return (
    <Transition show={isOpen} as={Fragment}>
      <Dialog onClose={handleClose} className="relative z-50">
        {/* Backdrop */}
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div
            className="fixed inset-0 bg-tactical-950/50 backdrop-blur-sm"
            aria-hidden="true"
          />
        </Transition.Child>

        {/* Modal container */}
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0 scale-95"
            enterTo="opacity-100 scale-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100 scale-100"
            leaveTo="opacity-0 scale-95"
          >
            <Dialog.Panel
              className={cn(
                'w-full max-w-md',
                'bg-white dark:bg-tactical-800',
                'rounded-2xl shadow-2xl',
                'border border-tactical-200 dark:border-tactical-700',
                'overflow-hidden'
              )}
            >
              {/* Header */}
              <div
                className={cn(
                  'flex items-center gap-3 px-6 py-4',
                  'border-b border-tactical-200 dark:border-tactical-700',
                  isApprove
                    ? 'bg-gradient-to-r from-emerald-50 to-green-50 dark:from-emerald-900/20 dark:to-green-900/20'
                    : 'bg-gradient-to-r from-red-50 to-rose-50 dark:from-red-900/20 dark:to-rose-900/20'
                )}
              >
                <div
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center',
                    isApprove
                      ? 'bg-emerald-100 dark:bg-emerald-900/50'
                      : 'bg-red-100 dark:bg-red-900/50'
                  )}
                >
                  <ActionIcon
                    className={cn(
                      'w-5 h-5',
                      isApprove
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-red-600 dark:text-red-400'
                    )}
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <Dialog.Title
                    className={cn(
                      'text-lg font-semibold',
                      isApprove
                        ? 'text-emerald-900 dark:text-emerald-100'
                        : 'text-red-900 dark:text-red-100'
                    )}
                  >
                    {isApprove ? 'Approve' : 'Reject'} Verification
                  </Dialog.Title>
                  <p className="text-sm text-tactical-500 dark:text-tactical-400">
                    Confirm your decision
                  </p>
                </div>
                <button
                  onClick={handleClose}
                  disabled={isLoading}
                  className={cn(
                    'p-2 rounded-lg',
                    'text-tactical-400 hover:text-tactical-600',
                    'dark:text-tactical-500 dark:hover:text-tactical-300',
                    'hover:bg-tactical-100 dark:hover:bg-tactical-700',
                    'transition-colors',
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>

              {/* Content */}
              <div className="px-6 py-5 space-y-5">
                {/* Item Info */}
                <div
                  className={cn(
                    'flex items-center gap-4 p-4',
                    'bg-tactical-50 dark:bg-tactical-900',
                    'rounded-xl border border-tactical-200 dark:border-tactical-700'
                  )}
                >
                  <div
                    className={cn(
                      'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0',
                      item.entity_type === 'tiger'
                        ? 'bg-tiger-orange/10 text-tiger-orange'
                        : 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400'
                    )}
                  >
                    {item.entity_type === 'tiger' ? (
                      <TigerIcon className="w-6 h-6" />
                    ) : (
                      <BuildingOffice2Icon className="w-6 h-6" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-tactical-900 dark:text-tactical-100 truncate">
                        {item.entity_name || item.entity_id}
                      </span>
                      <Badge
                        variant={item.entity_type === 'tiger' ? 'tiger' : 'purple'}
                        size="xs"
                      >
                        {item.entity_type === 'tiger' ? 'Tiger' : 'Facility'}
                      </Badge>
                    </div>
                    <span className="text-xs text-tactical-500 dark:text-tactical-400 font-mono">
                      {item.queue_id}
                    </span>
                  </div>
                </div>

                {/* Warning for rejection */}
                {!isApprove && (
                  <div
                    className={cn(
                      'flex items-start gap-3 p-3',
                      'bg-amber-50 dark:bg-amber-900/20',
                      'border border-amber-200 dark:border-amber-800',
                      'rounded-lg'
                    )}
                  >
                    <ExclamationTriangleIcon className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-amber-800 dark:text-amber-200">
                      Rejecting this item will prevent it from being added to the database.
                      This action can be undone by an administrator.
                    </p>
                  </div>
                )}

                {/* Notes Input */}
                <div className="space-y-2">
                  <label
                    htmlFor="review-notes"
                    className="block text-sm font-medium text-tactical-700 dark:text-tactical-300"
                  >
                    Review Notes {!isApprove && <span className="text-red-500">*</span>}
                  </label>
                  <textarea
                    id="review-notes"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder={
                      isApprove
                        ? 'Optional notes for this approval...'
                        : 'Please provide a reason for rejection...'
                    }
                    rows={3}
                    className={cn(
                      'w-full px-3 py-2 rounded-lg',
                      'bg-white dark:bg-tactical-900',
                      'border border-tactical-300 dark:border-tactical-600',
                      'text-tactical-900 dark:text-tactical-100',
                      'placeholder-tactical-400 dark:placeholder-tactical-500',
                      'focus:outline-none focus:ring-2 focus:ring-tiger-orange/30 focus:border-tiger-orange',
                      'transition-all duration-200',
                      'resize-none'
                    )}
                    disabled={isLoading}
                  />
                </div>
              </div>

              {/* Footer */}
              <div
                className={cn(
                  'flex items-center justify-end gap-3 px-6 py-4',
                  'bg-tactical-50 dark:bg-tactical-900',
                  'border-t border-tactical-200 dark:border-tactical-700'
                )}
              >
                <Button
                  variant="secondary"
                  onClick={handleClose}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
                <Button
                  variant={isApprove ? 'primary' : 'danger'}
                  onClick={handleConfirm}
                  disabled={(!isApprove && !notes.trim()) || isLoading}
                  isLoading={isLoading}
                  className={
                    isApprove
                      ? 'bg-emerald-600 hover:bg-emerald-700 focus:ring-emerald-500'
                      : ''
                  }
                >
                  <ActionIcon className="w-4 h-4 mr-2" />
                  {isApprove ? 'Approve' : 'Reject'}
                </Button>
              </div>
            </Dialog.Panel>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition>
  )
}

export default VerificationActionModal

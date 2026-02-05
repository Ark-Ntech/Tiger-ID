import { cn } from '../../utils/cn'
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronDoubleLeftIcon,
  ChevronDoubleRightIcon,
} from '@heroicons/react/24/outline'

interface VerificationPaginationProps {
  currentPage: number
  totalPages: number
  totalItems: number
  pageSize: number
  onPageChange: (page: number) => void
  onPageSizeChange?: (pageSize: number) => void
  className?: string
}

export const VerificationPagination = ({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  onPageSizeChange,
  className,
}: VerificationPaginationProps) => {
  const startItem = (currentPage - 1) * pageSize + 1
  const endItem = Math.min(currentPage * pageSize, totalItems)

  const canGoPrevious = currentPage > 1
  const canGoNext = currentPage < totalPages

  // Generate page numbers to show
  const getPageNumbers = () => {
    const pages: (number | 'ellipsis')[] = []
    const maxVisible = 5

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      // Always show first page
      pages.push(1)

      if (currentPage > 3) {
        pages.push('ellipsis')
      }

      // Show pages around current
      const start = Math.max(2, currentPage - 1)
      const end = Math.min(totalPages - 1, currentPage + 1)

      for (let i = start; i <= end; i++) {
        if (i !== 1 && i !== totalPages) {
          pages.push(i)
        }
      }

      if (currentPage < totalPages - 2) {
        pages.push('ellipsis')
      }

      // Always show last page
      if (totalPages > 1) {
        pages.push(totalPages)
      }
    }

    return pages
  }

  const pageNumbers = getPageNumbers()

  return (
    <div
      className={cn(
        'flex flex-col sm:flex-row items-center justify-between gap-4 py-4',
        className
      )}
    >
      {/* Results Info */}
      <div className="flex items-center gap-4">
        <p className="text-sm text-tactical-500 dark:text-tactical-400">
          Showing{' '}
          <span className="font-medium text-tactical-700 dark:text-tactical-200">
            {startItem}
          </span>
          {' - '}
          <span className="font-medium text-tactical-700 dark:text-tactical-200">
            {endItem}
          </span>
          {' of '}
          <span className="font-medium text-tactical-700 dark:text-tactical-200">
            {totalItems}
          </span>
          {' items'}
        </p>

        {/* Page Size Selector */}
        {onPageSizeChange && (
          <div className="flex items-center gap-2">
            <label
              htmlFor="page-size"
              className="text-sm text-tactical-500 dark:text-tactical-400"
            >
              Per page:
            </label>
            <select
              id="page-size"
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              className={cn(
                'h-8 px-2 pr-7 rounded-lg text-sm',
                'bg-white dark:bg-tactical-800',
                'border border-tactical-300 dark:border-tactical-600',
                'text-tactical-900 dark:text-tactical-100',
                'focus:outline-none focus:ring-2 focus:ring-tiger-orange/30 focus:border-tiger-orange',
                'cursor-pointer'
              )}
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        )}
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center gap-1">
        {/* First Page */}
        <button
          onClick={() => onPageChange(1)}
          disabled={!canGoPrevious}
          className={cn(
            'p-2 rounded-lg',
            'text-tactical-500 dark:text-tactical-400',
            'hover:bg-tactical-100 dark:hover:bg-tactical-700',
            'hover:text-tactical-700 dark:hover:text-tactical-200',
            'disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-transparent',
            'transition-colors duration-200'
          )}
          title="First Page"
        >
          <ChevronDoubleLeftIcon className="w-4 h-4" />
        </button>

        {/* Previous Page */}
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={!canGoPrevious}
          className={cn(
            'p-2 rounded-lg',
            'text-tactical-500 dark:text-tactical-400',
            'hover:bg-tactical-100 dark:hover:bg-tactical-700',
            'hover:text-tactical-700 dark:hover:text-tactical-200',
            'disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-transparent',
            'transition-colors duration-200'
          )}
          title="Previous Page"
        >
          <ChevronLeftIcon className="w-4 h-4" />
        </button>

        {/* Page Numbers */}
        <div className="flex items-center gap-1 mx-2">
          {pageNumbers.map((page, index) =>
            page === 'ellipsis' ? (
              <span
                key={`ellipsis-${index}`}
                className="w-8 text-center text-tactical-400 dark:text-tactical-500"
              >
                ...
              </span>
            ) : (
              <button
                key={page}
                onClick={() => onPageChange(page)}
                className={cn(
                  'min-w-[2rem] h-8 px-2 rounded-lg text-sm font-medium',
                  'transition-all duration-200',
                  page === currentPage
                    ? cn(
                        'bg-tiger-orange text-white',
                        'shadow-sm'
                      )
                    : cn(
                        'text-tactical-600 dark:text-tactical-300',
                        'hover:bg-tactical-100 dark:hover:bg-tactical-700',
                        'hover:text-tactical-900 dark:hover:text-tactical-100'
                      )
                )}
              >
                {page}
              </button>
            )
          )}
        </div>

        {/* Next Page */}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={!canGoNext}
          className={cn(
            'p-2 rounded-lg',
            'text-tactical-500 dark:text-tactical-400',
            'hover:bg-tactical-100 dark:hover:bg-tactical-700',
            'hover:text-tactical-700 dark:hover:text-tactical-200',
            'disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-transparent',
            'transition-colors duration-200'
          )}
          title="Next Page"
        >
          <ChevronRightIcon className="w-4 h-4" />
        </button>

        {/* Last Page */}
        <button
          onClick={() => onPageChange(totalPages)}
          disabled={!canGoNext}
          className={cn(
            'p-2 rounded-lg',
            'text-tactical-500 dark:text-tactical-400',
            'hover:bg-tactical-100 dark:hover:bg-tactical-700',
            'hover:text-tactical-700 dark:hover:text-tactical-200',
            'disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-transparent',
            'transition-colors duration-200'
          )}
          title="Last Page"
        >
          <ChevronDoubleRightIcon className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

export default VerificationPagination

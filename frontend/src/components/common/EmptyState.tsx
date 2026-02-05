import { ReactNode } from 'react'
import { cn } from '../../utils/cn'

export type EmptyStateSize = 'sm' | 'md' | 'lg'

export interface EmptyStateAction {
  label: string
  onClick: () => void
}

export interface EmptyStateProps {
  /** Optional icon to display */
  icon?: ReactNode
  /** Main heading text */
  title: string
  /** Optional secondary description text */
  description?: string
  /** Optional action button configuration */
  action?: EmptyStateAction
  /** Additional CSS classes */
  className?: string
  /** Size variant affecting padding and text sizes */
  size?: EmptyStateSize
}

const EmptyState = ({
  icon,
  title,
  description,
  action,
  className,
  size = 'md',
}: EmptyStateProps) => {
  const sizeClasses: Record<EmptyStateSize, {
    container: string
    iconWrapper: string
    title: string
    description: string
    button: string
  }> = {
    sm: {
      container: 'py-6 px-4',
      iconWrapper: 'w-10 h-10 mb-3',
      title: 'text-sm',
      description: 'text-xs mt-1',
      button: 'px-3 py-1.5 text-xs mt-3',
    },
    md: {
      container: 'py-10 px-6',
      iconWrapper: 'w-14 h-14 mb-4',
      title: 'text-base',
      description: 'text-sm mt-2',
      button: 'px-4 py-2 text-sm mt-4',
    },
    lg: {
      container: 'py-16 px-8',
      iconWrapper: 'w-18 h-18 mb-6',
      title: 'text-lg',
      description: 'text-base mt-3',
      button: 'px-5 py-2.5 text-base mt-6',
    },
  }

  const currentSize = sizeClasses[size]

  return (
    <div
      data-testid="empty-state"
      className={cn(
        'flex flex-col items-center justify-center text-center',
        currentSize.container,
        className
      )}
    >
      {icon && (
        <div
          data-testid="empty-state-icon"
          className={cn(
            'flex items-center justify-center rounded-full',
            'bg-tactical-100 text-tactical-500',
            'dark:bg-tactical-800 dark:text-tactical-400',
            currentSize.iconWrapper
          )}
        >
          {icon}
        </div>
      )}

      <h3
        data-testid="empty-state-title"
        className={cn(
          'font-medium',
          'text-tactical-900 dark:text-tactical-100',
          currentSize.title
        )}
      >
        {title}
      </h3>

      {description && (
        <p
          data-testid="empty-state-description"
          className={cn(
            'text-tactical-600 dark:text-tactical-400',
            'max-w-sm',
            currentSize.description
          )}
        >
          {description}
        </p>
      )}

      {action && (
        <button
          data-testid="empty-state-action"
          type="button"
          onClick={action.onClick}
          className={cn(
            'inline-flex items-center justify-center',
            'font-medium rounded-lg',
            'bg-tiger-orange text-white',
            'hover:bg-tiger-orange-dark',
            'focus:outline-none focus:ring-2 focus:ring-tiger-orange focus:ring-offset-2',
            'dark:focus:ring-offset-tactical-900',
            'transition-colors duration-200',
            currentSize.button
          )}
        >
          {action.label}
        </button>
      )}
    </div>
  )
}

export { EmptyState }
export default EmptyState

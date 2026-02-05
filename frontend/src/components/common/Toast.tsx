import { useState, useEffect, useCallback, createContext, useContext, ReactNode } from 'react'
import { cn } from '../../utils/cn'
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'

// Toast types
export type ToastType = 'success' | 'warning' | 'error' | 'info'

export interface Toast {
  id: string
  type: ToastType
  title: string
  message?: string
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
}

// Toast configuration
const TOAST_CONFIG = {
  success: {
    icon: CheckCircleIcon,
    bgClass: 'bg-emerald-50 dark:bg-emerald-900/30',
    borderClass: 'border-emerald-200 dark:border-emerald-700',
    iconClass: 'text-emerald-500 dark:text-emerald-400',
    titleClass: 'text-emerald-800 dark:text-emerald-200',
    messageClass: 'text-emerald-700 dark:text-emerald-300',
  },
  warning: {
    icon: ExclamationTriangleIcon,
    bgClass: 'bg-amber-50 dark:bg-amber-900/30',
    borderClass: 'border-amber-200 dark:border-amber-700',
    iconClass: 'text-amber-500 dark:text-amber-400',
    titleClass: 'text-amber-800 dark:text-amber-200',
    messageClass: 'text-amber-700 dark:text-amber-300',
  },
  error: {
    icon: XCircleIcon,
    bgClass: 'bg-red-50 dark:bg-red-900/30',
    borderClass: 'border-red-200 dark:border-red-700',
    iconClass: 'text-red-500 dark:text-red-400',
    titleClass: 'text-red-800 dark:text-red-200',
    messageClass: 'text-red-700 dark:text-red-300',
  },
  info: {
    icon: InformationCircleIcon,
    bgClass: 'bg-blue-50 dark:bg-blue-900/30',
    borderClass: 'border-blue-200 dark:border-blue-700',
    iconClass: 'text-blue-500 dark:text-blue-400',
    titleClass: 'text-blue-800 dark:text-blue-200',
    messageClass: 'text-blue-700 dark:text-blue-300',
  },
}

// Single toast item component
interface ToastItemProps {
  toast: Toast
  onDismiss: (id: string) => void
}

const ToastItem = ({ toast, onDismiss }: ToastItemProps) => {
  const [isExiting, setIsExiting] = useState(false)
  const config = TOAST_CONFIG[toast.type]
  const Icon = config.icon

  useEffect(() => {
    if (toast.duration !== 0) {
      const timeout = setTimeout(() => {
        setIsExiting(true)
        setTimeout(() => onDismiss(toast.id), 300)
      }, toast.duration || 5000)

      return () => clearTimeout(timeout)
    }
  }, [toast.id, toast.duration, onDismiss])

  const handleDismiss = () => {
    setIsExiting(true)
    setTimeout(() => onDismiss(toast.id), 300)
  }

  return (
    <div
      data-testid="toast"
      className={cn(
        'flex items-start gap-3 w-full max-w-sm p-4 rounded-xl border shadow-tactical-lg',
        'transition-all duration-300',
        config.bgClass,
        config.borderClass,
        isExiting ? 'opacity-0 translate-x-full' : 'opacity-100 translate-x-0 animate-slide-in-right'
      )}
      role="alert"
    >
      <Icon className={cn('w-5 h-5 flex-shrink-0 mt-0.5', config.iconClass)} />

      <div className="flex-1 min-w-0">
        <p className={cn('text-sm font-semibold', config.titleClass)}>
          {toast.title}
        </p>
        {toast.message && (
          <p className={cn('text-sm mt-1', config.messageClass)}>
            {toast.message}
          </p>
        )}
        {toast.action && (
          <button
            onClick={toast.action.onClick}
            className={cn(
              'mt-2 text-sm font-medium underline underline-offset-2',
              'hover:no-underline transition-all',
              config.titleClass
            )}
          >
            {toast.action.label}
          </button>
        )}
      </div>

      <button
        data-testid="toast-close"
        onClick={handleDismiss}
        className={cn(
          'flex-shrink-0 p-1 rounded-lg hover:bg-black/5 dark:hover:bg-white/5',
          'transition-colors',
          config.iconClass
        )}
        aria-label="Dismiss"
      >
        <XMarkIcon className="w-4 h-4" />
      </button>
    </div>
  )
}

// Progress toast for investigations
interface ProgressToastProps {
  title: string
  progress: number
  phase?: string
  onCancel?: () => void
}

export const ProgressToast = ({ title, progress, phase, onCancel }: ProgressToastProps) => {
  return (
    <div className={cn(
      'w-full max-w-sm p-4 rounded-xl border shadow-tactical-lg',
      'bg-white dark:bg-tactical-800 border-tactical-200 dark:border-tactical-700',
      'animate-slide-in-right'
    )}>
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-semibold text-tactical-900 dark:text-tactical-100">
          {title}
        </p>
        <span className="text-sm font-mono text-tactical-600 dark:text-tactical-400">
          {Math.round(progress)}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="progress-bar mb-2">
        <div
          className="progress-bar-fill bg-tiger-orange"
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        />
      </div>

      {phase && (
        <p className="text-xs text-tactical-500 dark:text-tactical-400 mb-2">
          {phase}
        </p>
      )}

      {onCancel && (
        <button
          onClick={onCancel}
          className="text-xs text-tactical-500 hover:text-tactical-700 dark:text-tactical-400 dark:hover:text-tactical-200"
        >
          Cancel
        </button>
      )}
    </div>
  )
}

// Toast context for global state management
interface ToastContextValue {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => string
  removeToast: (id: string) => void
  clearAll: () => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

// Toast provider component
interface ToastProviderProps {
  children: ReactNode
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center'
  maxToasts?: number
}

export const ToastProvider = ({
  children,
  position = 'top-right',
  maxToasts = 5,
}: ToastProviderProps) => {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`

    setToasts(prev => {
      const newToasts = [...prev, { ...toast, id }]
      // Remove oldest toasts if we exceed max
      if (newToasts.length > maxToasts) {
        return newToasts.slice(-maxToasts)
      }
      return newToasts
    })

    return id
  }, [maxToasts])

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const clearAll = useCallback(() => {
    setToasts([])
  }, [])

  const positionClasses = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-center': 'top-4 left-1/2 -translate-x-1/2',
    'bottom-center': 'bottom-4 left-1/2 -translate-x-1/2',
  }

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, clearAll }}>
      {children}

      {/* Toast container */}
      <div
        className={cn(
          'fixed z-50 flex flex-col gap-2',
          positionClasses[position]
        )}
        aria-live="polite"
        aria-label="Notifications"
      >
        {toasts.map(toast => (
          <ToastItem key={toast.id} toast={toast} onDismiss={removeToast} />
        ))}
      </div>
    </ToastContext.Provider>
  )
}

// Hook to use toast
export const useToast = () => {
  const context = useContext(ToastContext)

  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }

  return {
    ...context,
    // Convenience methods
    success: (title: string, message?: string, options?: Partial<Toast>) =>
      context.addToast({ type: 'success', title, message, ...options }),
    warning: (title: string, message?: string, options?: Partial<Toast>) =>
      context.addToast({ type: 'warning', title, message, ...options }),
    error: (title: string, message?: string, options?: Partial<Toast>) =>
      context.addToast({ type: 'error', title, message, ...options }),
    info: (title: string, message?: string, options?: Partial<Toast>) =>
      context.addToast({ type: 'info', title, message, ...options }),
  }
}

// Standalone toast component (can be used without provider)
interface StandaloneToastProps extends Omit<Toast, 'id'> {
  onDismiss?: () => void
  className?: string
}

export const StandaloneToast = ({
  type,
  title,
  message,
  action,
  onDismiss,
  className,
}: StandaloneToastProps) => {
  const config = TOAST_CONFIG[type]
  const Icon = config.icon

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-xl border shadow-tactical-lg',
        config.bgClass,
        config.borderClass,
        className
      )}
      role="alert"
    >
      <Icon className={cn('w-5 h-5 flex-shrink-0 mt-0.5', config.iconClass)} />

      <div className="flex-1 min-w-0">
        <p className={cn('text-sm font-semibold', config.titleClass)}>
          {title}
        </p>
        {message && (
          <p className={cn('text-sm mt-1', config.messageClass)}>
            {message}
          </p>
        )}
        {action && (
          <button
            onClick={action.onClick}
            className={cn(
              'mt-2 text-sm font-medium underline underline-offset-2',
              'hover:no-underline transition-all',
              config.titleClass
            )}
          >
            {action.label}
          </button>
        )}
      </div>

      {onDismiss && (
        <button
          onClick={onDismiss}
          className={cn(
            'flex-shrink-0 p-1 rounded-lg hover:bg-black/5 dark:hover:bg-white/5',
            'transition-colors',
            config.iconClass
          )}
          aria-label="Dismiss"
        >
          <XMarkIcon className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}

export default ToastProvider

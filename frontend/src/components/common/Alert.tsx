import { ReactNode } from 'react'
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline'
import { cn } from '../../utils/cn'

interface AlertProps {
  type?: 'info' | 'success' | 'warning' | 'error'
  title?: string
  children?: ReactNode
  /** Alias for children - the message to display */
  message?: string
  className?: string
  onClose?: () => void
}

const Alert = ({ type = 'info', title, children, message, className, onClose }: AlertProps) => {
  const content = children || message
  const styles = {
    info: {
      container: 'bg-blue-50 border-blue-200',
      icon: 'text-blue-400',
      title: 'text-blue-800',
      text: 'text-blue-700',
      Icon: InformationCircleIcon,
    },
    success: {
      container: 'bg-green-50 border-green-200',
      icon: 'text-green-400',
      title: 'text-green-800',
      text: 'text-green-700',
      Icon: CheckCircleIcon,
    },
    warning: {
      container: 'bg-yellow-50 border-yellow-200',
      icon: 'text-yellow-400',
      title: 'text-yellow-800',
      text: 'text-yellow-700',
      Icon: ExclamationTriangleIcon,
    },
    error: {
      container: 'bg-red-50 border-red-200',
      icon: 'text-red-400',
      title: 'text-red-800',
      text: 'text-red-700',
      Icon: XCircleIcon,
    },
  }

  const style = styles[type]
  const Icon = style.Icon

  return (
    <div data-testid="alert" className={cn('border rounded-lg p-4', style.container, className)}>
      <div className="flex">
        <div data-testid="alert-icon" className="flex-shrink-0">
          <Icon className={cn('h-5 w-5', style.icon)} />
        </div>
        <div className="ml-3 flex-1">
          {title && <h3 data-testid="alert-title" className={cn('text-sm font-medium', style.title)}>{title}</h3>}
          <div data-testid="alert-message" className={cn('text-sm', title ? 'mt-2' : '', style.text)}>{content}</div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className={cn('ml-3 flex-shrink-0', style.text, 'hover:opacity-75')}
          >
            <span className="sr-only">Dismiss</span>
            <XCircleIcon className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  )
}

export default Alert


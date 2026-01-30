import { ReactNode } from 'react'
import { cn } from '../../utils/cn'

interface BadgeProps {
  children: ReactNode
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'primary' | 'outline' | 'error'
  /** Alias for variant - supports color names like 'green', 'blue', 'yellow', 'red', 'gray', 'purple' */
  color?: 'green' | 'blue' | 'yellow' | 'red' | 'gray' | 'purple'
  size?: 'sm' | 'md'
  className?: string
}

const Badge = ({ children, variant, color, size = 'md', className }: BadgeProps) => {
  // Map color prop to variant if provided
  const colorToVariant: Record<string, string> = {
    green: 'success',
    blue: 'info',
    yellow: 'warning',
    red: 'danger',
    gray: 'default',
    purple: 'purple',
  }

  const variants: Record<string, string> = {
    default: 'bg-gray-100 text-gray-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    danger: 'bg-red-100 text-red-800',
    error: 'bg-red-100 text-red-800',
    info: 'bg-blue-100 text-blue-800',
    primary: 'bg-blue-600 text-white',
    outline: 'bg-transparent border border-gray-300 text-gray-700',
    purple: 'bg-purple-100 text-purple-800',
  }

  // Determine which variant to use: explicit variant > mapped color > default
  const effectiveVariant = variant || (color ? colorToVariant[color] : 'default') || 'default'

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded-full',
        variants[effectiveVariant],
        sizes[size],
        className
      )}
    >
      {children}
    </span>
  )
}

export default Badge


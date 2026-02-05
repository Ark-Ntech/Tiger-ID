import { ReactNode } from 'react'
import { cn } from '../../utils/cn'

export type CardVariant = 'default' | 'elevated' | 'evidence' | 'critical' | 'match' | 'dark' | 'ghost'

interface CardProps {
  children: ReactNode
  className?: string
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
  variant?: CardVariant
  onClick?: () => void
  as?: 'div' | 'article' | 'section'
  hoverable?: boolean
}

const Card = ({
  children,
  className,
  padding = 'md',
  variant = 'default',
  onClick,
  as: Component = 'div',
  hoverable = false,
}: CardProps) => {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
    xl: 'p-10',
  }

  const variantClasses: Record<CardVariant, string> = {
    default: cn(
      'bg-white border border-tactical-200/50 shadow-tactical',
      'dark:bg-tactical-800 dark:border-tactical-700/50'
    ),
    elevated: cn(
      'bg-white border border-tactical-200/30 shadow-tactical-lg',
      'dark:bg-tactical-800 dark:border-tactical-700/30'
    ),
    evidence: cn(
      'bg-white border border-emerald-200/50 shadow-evidence',
      'dark:bg-tactical-800 dark:border-emerald-700/50'
    ),
    critical: cn(
      'bg-white border-2 border-red-300 shadow-critical',
      'dark:bg-tactical-800 dark:border-red-700'
    ),
    match: cn(
      'bg-white border border-blue-200/50 shadow-match',
      'dark:bg-tactical-800 dark:border-blue-700/50'
    ),
    dark: cn(
      'bg-tactical-900 border border-tactical-700 text-tactical-100',
      'dark:bg-tactical-950 dark:border-tactical-800'
    ),
    ghost: cn(
      'bg-transparent border border-tactical-200',
      'dark:border-tactical-700'
    ),
  }

  const hoverClasses: Record<CardVariant, string> = {
    default: 'hover:shadow-tactical-lg hover:border-tactical-300 dark:hover:border-tactical-600',
    elevated: 'hover:shadow-xl',
    evidence: 'hover:shadow-evidence-hover hover:border-emerald-300 dark:hover:border-emerald-600',
    critical: 'hover:shadow-critical-hover hover:border-red-400 dark:hover:border-red-600',
    match: 'hover:shadow-match-hover hover:border-blue-300 dark:hover:border-blue-600',
    dark: 'hover:border-tactical-600 dark:hover:border-tactical-700',
    ghost: 'hover:bg-tactical-50 dark:hover:bg-tactical-800/50',
  }

  return (
    <Component
      data-testid="card"
      className={cn(
        'rounded-xl transition-all duration-200',
        variantClasses[variant],
        paddingClasses[padding],
        (onClick || hoverable) && cn(
          'cursor-pointer',
          hoverClasses[variant]
        ),
        className
      )}
      onClick={onClick}
    >
      {children}
    </Component>
  )
}

// Card Header subcomponent
interface CardHeaderProps {
  children: ReactNode
  className?: string
  action?: ReactNode
}

export const CardHeader = ({ children, className, action }: CardHeaderProps) => {
  return (
    <div className={cn(
      'flex items-center justify-between mb-4',
      className
    )}>
      <div className="flex-1 min-w-0">
        {children}
      </div>
      {action && (
        <div className="flex-shrink-0 ml-4">
          {action}
        </div>
      )}
    </div>
  )
}

// Card Title subcomponent
interface CardTitleProps {
  children: ReactNode
  className?: string
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'
}

export const CardTitle = ({ children, className, as: Component = 'h3' }: CardTitleProps) => {
  return (
    <Component className={cn(
      'text-lg font-semibold text-tactical-900 dark:text-tactical-100',
      className
    )}>
      {children}
    </Component>
  )
}

// Card Description subcomponent
interface CardDescriptionProps {
  children: ReactNode
  className?: string
}

export const CardDescription = ({ children, className }: CardDescriptionProps) => {
  return (
    <p className={cn(
      'text-sm text-tactical-600 dark:text-tactical-400 mt-1',
      className
    )}>
      {children}
    </p>
  )
}

// Card Content subcomponent
interface CardContentProps {
  children: ReactNode
  className?: string
}

export const CardContent = ({ children, className }: CardContentProps) => {
  return (
    <div className={cn('', className)}>
      {children}
    </div>
  )
}

// Card Footer subcomponent
interface CardFooterProps {
  children: ReactNode
  className?: string
  border?: boolean
}

export const CardFooter = ({ children, className, border = true }: CardFooterProps) => {
  return (
    <div className={cn(
      'mt-4 pt-4 flex items-center gap-3',
      border && 'border-t border-tactical-200 dark:border-tactical-700',
      className
    )}>
      {children}
    </div>
  )
}

// Stat Card - specialized card for statistics
interface StatCardProps {
  label: string
  value: string | number
  icon?: ReactNode
  trend?: {
    value: number
    isPositive: boolean
  }
  variant?: CardVariant
  className?: string
}

export const StatCard = ({
  label,
  value,
  icon,
  trend,
  variant = 'default',
  className,
}: StatCardProps) => {
  return (
    <Card variant={variant} padding="md" className={className}>
      <div data-testid="stat-card" className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-tactical-600 dark:text-tactical-400 mb-1">
            {label}
          </p>
          <p className="text-3xl font-bold text-tactical-900 dark:text-tactical-100">
            {value}
          </p>
          {trend && (
            <p className={cn(
              'text-sm font-medium mt-1',
              trend.isPositive
                ? 'text-emerald-600 dark:text-emerald-400'
                : 'text-red-600 dark:text-red-400'
            )}>
              {trend.isPositive ? '+' : ''}{trend.value}%
            </p>
          )}
        </div>
        {icon && (
          <div className="p-2 rounded-lg bg-tactical-100 dark:bg-tactical-700/50 text-tactical-600 dark:text-tactical-300">
            {icon}
          </div>
        )}
      </div>
    </Card>
  )
}

export default Card

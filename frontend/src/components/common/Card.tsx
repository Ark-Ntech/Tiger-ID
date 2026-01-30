import { ReactNode } from 'react'
import { cn } from '../../utils/cn'

interface CardProps {
  children: ReactNode
  className?: string
  padding?: 'sm' | 'md' | 'lg' | 'none'
  onClick?: () => void
}

const Card = ({ children, className, padding = 'md', onClick }: CardProps) => {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  }

  return (
    <div
      className={cn(
        'bg-white rounded-lg shadow-md',
        paddingClasses[padding],
        onClick && 'cursor-pointer hover:shadow-lg transition-shadow',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

export default Card


import Badge from '../common/Badge'

interface StatusBadgeProps {
  status: string
  phase?: string | null
  className?: string
}

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'primary' | 'outline' | 'error'

const StatusBadge = ({ status, phase, className = '' }: StatusBadgeProps) => {
  const getVariant = (): BadgeVariant => {
    switch (status) {
      case 'active':
      case 'in_progress':
        return 'primary'
      case 'completed':
        return 'success'
      case 'paused':
        return 'warning'
      case 'cancelled':
        return 'danger'
      case 'draft':
        return 'default'
      default:
        return 'default'
    }
  }

  const getLabel = () => {
    if (status === 'active' || status === 'in_progress') {
      if (phase) {
        return `${phase.charAt(0).toUpperCase() + phase.slice(1)} Phase`
      }
      return 'Active'
    }
    return status.charAt(0).toUpperCase() + status.slice(1)
  }

  const shouldAnimate = status === 'active' || status === 'in_progress'

  return (
    <Badge 
      variant={getVariant()} 
      className={`${shouldAnimate ? 'animate-pulse' : ''} ${className}`}
    >
      {getLabel()}
    </Badge>
  )
}

export default StatusBadge


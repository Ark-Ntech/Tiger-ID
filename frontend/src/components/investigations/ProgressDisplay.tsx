import { CheckCircleIcon, ArrowPathIcon, ClockIcon } from '@heroicons/react/24/outline'

interface ProgressDisplayProps {
  phase: string | null
  percentage: number
  timeElapsed?: number
  className?: string
}

const ProgressDisplay = ({ phase, percentage, timeElapsed, className = '' }: ProgressDisplayProps) => {
  const phases = [
    { name: 'Research', key: 'research' },
    { name: 'Analysis', key: 'analysis' },
    { name: 'Validation', key: 'validation' },
    { name: 'Reporting', key: 'reporting' }
  ]

  const getPhaseStatus = (phaseKey: string) => {
    if (!phase) return 'pending'
    const currentIndex = phases.findIndex(p => p.key === phase)
    const phaseIndex = phases.findIndex(p => p.key === phaseKey)
    
    if (phaseIndex < currentIndex) return 'completed'
    if (phaseIndex === currentIndex) return 'running'
    return 'pending'
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    if (mins > 0) {
      return `${mins}m ${secs}s`
    }
    return `${secs}s`
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Progress Bar */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-600 font-medium">Progress</span>
          <span className="text-gray-500">{percentage}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-primary-600 h-2 rounded-full transition-all duration-500"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {/* Phase Timeline */}
      <div className="flex items-center justify-between">
        {phases.map((p, idx) => {
          const status = getPhaseStatus(p.key)
          
          return (
            <div key={p.key} className="flex items-center">
              <div className="flex flex-col items-center">
                <div className={`flex items-center justify-center w-6 h-6 rounded-full ${
                  status === 'completed' ? 'bg-green-500' :
                  status === 'running' ? 'bg-blue-500' :
                  'bg-gray-300'
                }`}>
                  {status === 'completed' && (
                    <CheckCircleIcon className="h-4 w-4 text-white" />
                  )}
                  {status === 'running' && (
                    <ArrowPathIcon className="h-4 w-4 text-white animate-spin" />
                  )}
                  {status === 'pending' && (
                    <ClockIcon className="h-3 w-3 text-gray-500" />
                  )}
                </div>
                <span className={`text-xs mt-1 ${
                  status === 'completed' ? 'text-green-600 font-medium' :
                  status === 'running' ? 'text-blue-600 font-medium' :
                  'text-gray-400'
                }`}>
                  {p.name}
                </span>
              </div>
              
              {idx < phases.length - 1 && (
                <div className={`w-8 h-0.5 mx-1 ${
                  status === 'completed' ? 'bg-green-500' : 'bg-gray-300'
                }`} />
              )}
            </div>
          )
        })}
      </div>

      {/* Time Elapsed */}
      {timeElapsed !== undefined && timeElapsed > 0 && (
        <div className="text-xs text-gray-500">
          Time elapsed: {formatTime(timeElapsed)}
        </div>
      )}
    </div>
  )
}

export default ProgressDisplay


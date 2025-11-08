import { useEffect, useState } from 'react'
import Card from '../common/Card'
import Badge from '../common/Badge'
import { 
  MagnifyingGlassIcon, 
  LightBulbIcon, 
  CheckCircleIcon,
  ArrowPathIcon,
  ClockIcon
} from '@heroicons/react/24/outline'

interface AgentActivity {
  agent: string
  action: string
  status: 'running' | 'completed' | 'idle' | 'waiting'
  details: string
  timestamp: string
}

interface AgentActivityFeedProps {
  activities: AgentActivity[]
  maxItems?: number
}

const AgentActivityFeed = ({ activities, maxItems = 10 }: AgentActivityFeedProps) => {
  const [displayActivities, setDisplayActivities] = useState<AgentActivity[]>([])

  useEffect(() => {
    // Show most recent activities
    setDisplayActivities(activities.slice(-maxItems).reverse())
  }, [activities, maxItems])

  const getAgentIcon = (agent: string) => {
    if (agent.includes('research')) return MagnifyingGlassIcon
    if (agent.includes('analysis')) return LightBulbIcon
    if (agent.includes('validation')) return CheckCircleIcon
    return ClockIcon
  }

  const getAgentColor = (agent: string) => {
    if (agent.includes('research')) return 'text-blue-600'
    if (agent.includes('analysis')) return 'text-purple-600'
    if (agent.includes('validation')) return 'text-green-600'
    if (agent.includes('reporting')) return 'text-orange-600'
    return 'text-gray-600'
  }

  const getStatusIcon = (status: string) => {
    if (status === 'running') return <ArrowPathIcon className="h-4 w-4 text-blue-500 animate-spin" />
    if (status === 'completed') return <CheckCircleIcon className="h-4 w-4 text-green-500" />
    if (status === 'waiting') return <ClockIcon className="h-4 w-4 text-yellow-500" />
    return <div className="h-4 w-4 rounded-full border-2 border-gray-300" />
  }

  if (displayActivities.length === 0) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Activity</h3>
        <p className="text-sm text-gray-500 text-center py-4">
          No agent activity yet. Launch an investigation to see live updates.
        </p>
      </Card>
    )
  }

  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Live Agent Activity</h3>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {displayActivities.map((activity, index) => {
          const Icon = getAgentIcon(activity.agent)
          const colorClass = getAgentColor(activity.agent)
          
          return (
            <div key={index} className="flex items-start gap-3 p-2 rounded-lg hover:bg-gray-50">
              <div className={`mt-0.5 ${colorClass}`}>
                <Icon className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-sm font-medium ${colorClass}`}>
                    {activity.agent.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                  {getStatusIcon(activity.status)}
                </div>
                <p className="text-xs text-gray-600">
                  {activity.details}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(activity.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </Card>
  )
}

export default AgentActivityFeed


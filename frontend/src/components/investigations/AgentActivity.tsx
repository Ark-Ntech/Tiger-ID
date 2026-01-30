import { useState, useEffect } from 'react'
import { useWebSocket } from '../../hooks/useWebSocket'
import Card from '../common/Card'
import Badge from '../common/Badge'
import { formatDateTime } from '../../utils/formatters'
import { AgentActivity as AgentActivityType } from '../../types'

interface AgentActivityProps {
  investigationId: string
}

const AgentActivity = ({ investigationId }: AgentActivityProps) => {
  const [activities, setActivities] = useState<Record<string, AgentActivityType>>({})

  const { isConnected, joinInvestigation, leaveInvestigation } = useWebSocket({
    onMessage: (message) => {
      if (message.type === 'agent_update') {
        const data = message.data
        setActivities((prev) => ({
          ...prev,
          [data.agent_type]: {
            agent_type: data.agent_type,
            status: data.status,
            current_task: data.current_task,
            progress: data.progress,
            last_update: data.last_update,
          },
        }))
      } else if (message.type === 'investigation_update') {
        // Refresh when investigation is updated
        // Could trigger a refetch of investigation data here
      }
    },
    autoConnect: true,
  })

  useEffect(() => {
    if (isConnected && investigationId) {
      joinInvestigation(investigationId)
    }

    return () => {
      if (investigationId) {
        leaveInvestigation(investigationId)
      }
    }
  }, [isConnected, investigationId, joinInvestigation, leaveInvestigation])

  const agentTypes = ['research', 'analysis', 'validation', 'reporting', 'orchestrator']

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'working':
        return 'bg-blue-100 text-blue-800'
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      case 'idle':
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'working':
        return '⚙️'
      case 'completed':
        return '✅'
      case 'error':
        return '❌'
      case 'idle':
      default:
        return '😴'
    }
  }

  const getAgentIcon = (agentType: string) => {
    switch (agentType) {
      case 'research':
        return '🔍'
      case 'analysis':
        return '📊'
      case 'validation':
        return '✅'
      case 'reporting':
        return '📝'
      case 'orchestrator':
        return '🎯'
      default:
        return '🤖'
    }
  }

  return (
    <Card>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Agent Activity</h3>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-gray-500">
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
        </div>
      </div>

      {!isConnected && (
        <div className="text-center text-gray-500 py-4 mb-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <p className="text-sm">WebSocket disconnected. Real-time updates unavailable.</p>
        </div>
      )}

      <div className="space-y-4">
        {agentTypes.map((agentType) => {
          const activity = activities[agentType] || {
            agent_type: agentType,
            status: 'idle',
            last_update: new Date().toISOString(),
          }

          return (
            <div
              key={agentType}
              className="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{getAgentIcon(agentType)}</span>
                  <div>
                    <h4 className="font-medium text-gray-900 capitalize">
                      {agentType} Agent
                    </h4>
                    <p className="text-xs text-gray-500">
                      Last update: {formatDateTime(activity.last_update)}
                    </p>
                  </div>
                </div>
                <Badge variant="info" className={getStatusColor(activity.status)}>
                  {getStatusIcon(activity.status)} {activity.status}
                </Badge>
              </div>

              {activity.status === 'working' && (
                <div className="mt-3 space-y-2">
                  {activity.current_task && (
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">
                        <strong>Current Task:</strong> {activity.current_task}
                      </span>
                    </div>
                  )}
                  {activity.progress !== undefined && (
                    <div className="w-full">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-gray-600">Progress</span>
                        <span className="text-xs text-gray-600">
                          {Math.round(activity.progress)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${activity.progress}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activity.status === 'error' && (
                <div className="mt-3 text-sm text-red-600">
                  An error occurred. Please check the investigation logs.
                </div>
              )}

              {activity.status === 'completed' && (
                <div className="mt-3 text-sm text-green-600">
                  Task completed successfully.
                </div>
              )}
            </div>
          )
        })}
      </div>

      {Object.keys(activities).length === 0 && isConnected && (
        <div className="text-center text-gray-500 py-8">
          <p className="text-sm">No agent activity yet. Agents will appear here when active.</p>
        </div>
      )}
    </Card>
  )
}

export default AgentActivity


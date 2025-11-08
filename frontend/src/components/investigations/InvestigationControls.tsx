import { useState } from 'react'
import Button from '../common/Button'
import Badge from '../common/Badge'
import {
  PlayIcon,
  PauseIcon,
  StopIcon,
  ChatBubbleLeftRightIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline'

interface InvestigationControlsProps {
  investigationId: string
  status: 'running' | 'paused' | 'completed' | 'cancelled'
  currentPhase?: string
  timeElapsed?: number
  costSoFar?: number
  onPause?: () => void
  onResume?: () => void
  onStop?: () => void
  onChat?: () => void
  onSettings?: () => void
}

const InvestigationControls = ({
  investigationId,
  status,
  currentPhase,
  timeElapsed = 0,
  costSoFar = 0,
  onPause,
  onResume,
  onStop,
  onChat,
  onSettings
}: InvestigationControlsProps) => {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getStatusBadge = () => {
    if (status === 'running') return <Badge variant="primary" className="animate-pulse">Running</Badge>
    if (status === 'paused') return <Badge variant="warning">Paused</Badge>
    if (status === 'completed') return <Badge variant="success">Completed</Badge>
    if (status === 'cancelled') return <Badge variant="default">Cancelled</Badge>
    return <Badge variant="default">{status}</Badge>
  }

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-3 sticky top-0 z-10 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Investigation</h3>
            <p className="text-xs text-gray-600">ID: {investigationId.slice(0, 8)}</p>
          </div>
          
          {getStatusBadge()}
          
          {currentPhase && status === 'running' && (
            <div className="flex items-center gap-2 text-xs text-gray-600">
              <span className="inline-block w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
              {currentPhase}
            </div>
          )}
        </div>

        <div className="flex items-center gap-4">
          {/* Time & Cost */}
          <div className="flex items-center gap-4 text-xs text-gray-600">
            <div>
              <span className="font-medium">Time:</span> {formatTime(timeElapsed)}
            </div>
            <div>
              <span className="font-medium">Cost:</span> ${costSoFar.toFixed(2)}
            </div>
          </div>

          {/* Control Buttons */}
          <div className="flex items-center gap-2">
            {status === 'running' && onPause && (
              <Button
                variant="outline"
                size="sm"
                onClick={onPause}
                title="Pause investigation"
              >
                <PauseIcon className="h-4 w-4" />
              </Button>
            )}
            
            {status === 'paused' && onResume && (
              <Button
                variant="primary"
                size="sm"
                onClick={onResume}
                title="Resume investigation"
              >
                <PlayIcon className="h-4 w-4" />
              </Button>
            )}
            
            {(status === 'running' || status === 'paused') && onStop && (
              <Button
                variant="danger"
                size="sm"
                onClick={onStop}
                title="Stop investigation"
              >
                <StopIcon className="h-4 w-4" />
              </Button>
            )}
            
            {onChat && (
              <Button
                variant="outline"
                size="sm"
                onClick={onChat}
                title="Chat with agent"
              >
                <ChatBubbleLeftRightIcon className="h-4 w-4" />
              </Button>
            )}
            
            {onSettings && (
              <Button
                variant="outline"
                size="sm"
                onClick={onSettings}
                title="Settings"
              >
                <Cog6ToothIcon className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default InvestigationControls


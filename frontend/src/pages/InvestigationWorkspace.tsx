import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useGetInvestigationQuery, useGetInvestigationEventsQuery, useGetEvidenceQuery } from '../app/api'
import Card from '../components/common/Card'
import Badge from '../components/common/Badge'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Button from '../components/common/Button'
import TimelineView from '../components/investigations/TimelineView'
import EvidenceGallery from '../components/investigations/EvidenceGallery'
import AnnotationPanel from '../components/investigations/AnnotationPanel'
import ExportDialog from '../components/investigations/ExportDialog'
import ChatInterface from '../components/investigations/ChatInterface'
import AgentActivity from '../components/investigations/AgentActivity'
import RelationshipGraph from '../components/investigations/RelationshipGraph'
import { useWebSocket } from '../hooks/useWebSocket'
import { formatDate } from '../utils/formatters'
import {
  ArrowLeftIcon,
  DocumentArrowDownIcon,
  ClockIcon,
  FolderIcon,
  ChatBubbleLeftIcon,
} from '@heroicons/react/24/outline'
import { useNavigate } from 'react-router-dom'

const InvestigationWorkspace = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'timeline' | 'evidence' | 'annotations' | 'relationships' | 'chat'>('timeline')
  const [showExportDialog, setShowExportDialog] = useState(false)
  
  const { data, isLoading, error, refetch: refetchInvestigation } = useGetInvestigationQuery(id!)
  const { refetch: refetchEvents } = useGetInvestigationEventsQuery({
    investigation_id: id!,
    limit: 100,
  }, { skip: !id })
  const { refetch: refetchEvidence } = useGetEvidenceQuery(id!, { skip: !id })

  // WebSocket integration for real-time updates
  const { isConnected, joinInvestigation, leaveInvestigation } = useWebSocket({
    onMessage: (message) => {
      // Handle real-time updates
      if (message.type === 'investigation_update') {
        // Refetch investigation data when updated
        refetchInvestigation()
        
        // Refetch related data based on update type
        if (message.update_type === 'evidence_added' || message.update_type === 'evidence_updated') {
          refetchEvidence()
        }
        if (message.update_type === 'step_added' || message.update_type === 'event_added') {
          refetchEvents()
        }
      } else if (message.type === 'event') {
        // Refetch events when new event is received
        refetchEvents()
      }
    },
    autoConnect: true,
  })

  useEffect(() => {
    if (isConnected && id) {
      joinInvestigation(id)
    }

    return () => {
      if (id) {
        leaveInvestigation(id)
      }
    }
  }, [isConnected, id, joinInvestigation, leaveInvestigation])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-red-600">Failed to load investigation</p>
      </div>
    )
  }

  const investigation = data.data

  const tabs = [
    { id: 'timeline', name: 'Timeline', icon: ClockIcon },
    { id: 'evidence', name: 'Evidence', icon: FolderIcon },
    { id: 'annotations', name: 'Annotations', icon: DocumentArrowDownIcon },
    { id: 'relationships', name: 'Relationships', icon: ClockIcon }, // Using ClockIcon temporarily, should add ShareIcon
    { id: 'chat', name: 'AI Assistant', icon: ChatBubbleLeftIcon },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => navigate('/investigations')}
              >
                <ArrowLeftIcon className="h-4 w-4 mr-1" />
                Back
              </Button>
              <h1 className="text-3xl font-bold text-gray-900">{investigation.title}</h1>
              <span className="text-xs text-gray-500">
                {isConnected ? '🟢' : '🔴'}
              </span>
            </div>
            <p className="text-gray-600 mt-2">{investigation.description}</p>
            <div className="flex items-center space-x-3 mt-4">
              <Badge variant="info">{investigation.status}</Badge>
              <Badge variant="warning">{investigation.priority}</Badge>
              <span className="text-sm text-gray-500">
                Created {formatDate(investigation.created_at)}
              </span>
              {investigation.tags && investigation.tags.length > 0 && (
                <div className="flex items-center space-x-2">
                  {investigation.tags.map((tag, idx) => (
                    <Badge key={idx} variant="info" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div className="ml-4">
            <Button
              variant="primary"
              onClick={() => setShowExportDialog(true)}
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <Card>
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`
                    flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm
                    ${
                      isActive
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="h-5 w-5" />
                  <span>{tab.name}</span>
                </button>
              )
            })}
          </nav>
        </div>
      </Card>

      {/* Tab Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-6">
          {activeTab === 'timeline' && (
            <TimelineView investigationId={id!} />
          )}
          {activeTab === 'evidence' && (
            <EvidenceGallery investigationId={id!} />
          )}
          {activeTab === 'annotations' && (
            <AnnotationPanel investigationId={id!} />
          )}
          {activeTab === 'relationships' && (
            <RelationshipGraph investigationId={id!} />
          )}
          {activeTab === 'chat' && (
            <ChatInterface investigationId={id!} />
          )}
        </div>
        <div>
          <AgentActivity investigationId={id!} />
        </div>
      </div>

      {/* Export Dialog */}
      {showExportDialog && (
        <ExportDialog
          investigationId={id!}
          investigationTitle={investigation.title}
          onClose={() => setShowExportDialog(false)}
        />
      )}
    </div>
  )
}

export default InvestigationWorkspace


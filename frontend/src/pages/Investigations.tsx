import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { 
  useGetInvestigationsQuery,
  useGetInvestigationExtendedQuery,
  useResumeInvestigationMutation,
  usePauseInvestigationMutation,
  useBulkPauseInvestigationsMutation,
  useBulkArchiveInvestigationsMutation,
  useCreateInvestigationMutation,
  useLaunchInvestigationMutation,
  useGetMCPToolsQuery,
  useIdentifyTigerImageMutation,
  useRegisterTigerMutation
} from '../app/api'
import { useWebSocket } from '../hooks/useWebSocket'
import AgentActivityFeed from '../components/investigations/AgentActivityFeed'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Alert from '../components/common/Alert'
import Badge from '../components/common/Badge'
import InvestigationCard from '../components/investigations/InvestigationCard'
import BulkActions from '../components/investigations/BulkActions'
import ApprovalModal from '../components/investigations/ApprovalModal'
import { PlusIcon, Squares2X2Icon, ListBulletIcon, FolderOpenIcon, ChatBubbleLeftRightIcon, CpuChipIcon, GlobeAltIcon, PhotoIcon, NewspaperIcon, LightBulbIcon, ShareIcon, DocumentTextIcon, ServerIcon, DocumentArrowUpIcon, PaperAirplaneIcon, WrenchScrewdriverIcon, CheckCircleIcon, XCircleIcon, ArrowPathIcon } from '@heroicons/react/24/outline'
import WebSearchTab from '../components/investigations/WebSearchTab'
import ReverseImageSearchTab from '../components/investigations/ReverseImageSearchTab'
import NewsMonitorTab from '../components/investigations/NewsMonitorTab'
import LeadGenerationTab from '../components/investigations/LeadGenerationTab'
import RelationshipAnalysisTab from '../components/investigations/RelationshipAnalysisTab'
import EvidenceCompilationTab from '../components/investigations/EvidenceCompilationTab'
import CrawlSchedulerTab from '../components/investigations/CrawlSchedulerTab'
import ReferenceDataTab from '../components/investigations/ReferenceDataTab'
import ModelTestingTab from '../components/investigations/ModelTestingTab'

const Investigations = () => {
  // ========== ALL HOOKS MUST BE HERE (TOP) - NO CONDITIONALS BETWEEN ==========
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [page, setPage] = useState(1)
  const [activeTab, setActiveTab] = useState(() => parseInt(searchParams.get('tab') || '0'))
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [bulkMode, setBulkMode] = useState(false)
  const [pendingApproval, setPendingApproval] = useState<any>(null)
  const [extendedInfo, setExtendedInfo] = useState<Record<string, any>>({})

  const { data, isLoading, error, refetch } = useGetInvestigationsQuery({
    page,
    page_size: 10,
    status: statusFilter,
  })

  const [resumeInvestigation] = useResumeInvestigationMutation()
  const [pauseInvestigation] = usePauseInvestigationMutation()
  const [bulkPause] = useBulkPauseInvestigationsMutation()
  const [bulkArchive] = useBulkArchiveInvestigationsMutation()

  // Assistant Tab specific hooks
  const [createInvestigation] = useCreateInvestigationMutation()
  const [launchInvestigation] = useLaunchInvestigationMutation()
  const [identifyTigerImage] = useIdentifyTigerImageMutation()
  const [registerTiger] = useRegisterTigerMutation()
  const { data: mcpToolsData, isLoading: toolsLoading, error: toolsError } = useGetMCPToolsQuery()
  
  // Assistant Tab state
  const [assistantMessages, setAssistantMessages] = useState<any[]>([])
  const [assistantInput, setAssistantInput] = useState('')
  const [selectedTools, setSelectedTools] = useState<Set<string>>(new Set())
  const [showToolSelector, setShowToolSelector] = useState(false)
  const [showTigerUpload, setShowTigerUpload] = useState(false)
  const [assistantLoading, setAssistantLoading] = useState(false)
  const [assistantError, setAssistantError] = useState<string | null>(null)
  const [currentInvestigationId, setCurrentInvestigationId] = useState<string | null>(null)
  const [launchProgress, setLaunchProgress] = useState<any[]>([])
  const [agentActivities, setAgentActivities] = useState<any[]>([])
  const [uploadedTigerImages, setUploadedTigerImages] = useState<File[]>([])
  const [uploadedTigerId, setUploadedTigerId] = useState<string | null>(null)
  const [tigerMetadata, setTigerMetadata] = useState<{ name?: string | null; confidence?: number | null; isNew?: boolean } | null>(null)
  const [tigerUploadLoading, setTigerUploadLoading] = useState(false)
  const [tigerUploadError, setTigerUploadError] = useState<string | null>(null)
  const [tigerImagePreviews, setTigerImagePreviews] = useState<string[]>([])

  const tigerFileInputRef = useRef<HTMLInputElement | null>(null)

  // WebSocket for Assistant and live updates
  const { isConnected } = useWebSocket({
    onMessage: (message) => {
      if (message.type === 'agent_activity') {
        setAgentActivities(prev => [...prev, message.data])
        setLaunchProgress(prev => {
          const phaseMap: Record<string, string> = {
            'research_agent': 'Gathering evidence',
            'analysis_agent': 'Analyzing evidence',
            'validation_agent': 'Validating findings',
            'reporting_agent': 'Generating report'
          }
          const stepName = phaseMap[message.data.agent] || message.data.action
          const exists = prev.find(p => p.step === stepName)
          if (!exists && message.data.status === 'running') {
            return [...prev, { step: stepName, status: 'running' }]
          }
          return prev.map(p =>
            p.step.toLowerCase().includes(message.data.agent.split('_')[0]) && message.data.status === 'completed'
              ? { ...p, status: 'completed' }
              : p
          )
        })
      } else if (message.type === 'approval_required') {
        setPendingApproval(message.data)
      } else if (message.type === 'investigation_completed') {
        setAssistantLoading(false)
        setLaunchProgress([])
        const completionMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `Investigation completed! ${message.data.summary || 'View results in workspace.'}`,
          timestamp: new Date().toISOString()
        }
        setAssistantMessages(prev => [...prev, completionMessage])
        // Refetch investigations list
        refetch()
      } else if (message.type === 'investigation_created') {
        // Refetch when new investigation created
        refetch()
      } else if (message.type === 'tiger_identified') {
        const data = message.data || {}
        if (data.tiger_id) {
          setUploadedTigerId(data.tiger_id)
          setTigerMetadata({
            name: data.tiger_name,
            confidence: typeof data.confidence === 'number' ? data.confidence : null,
            isNew: !!data.is_new,
          })
          setTigerUploadError(null)
          setTigerUploadLoading(false)
          setShowTigerUpload(true)
        }
      }
    },
    autoConnect: true
  })

  // ========== DATA DERIVATION (AFTER HOOKS, BEFORE EFFECTS) ==========
  const investigations = data?.data?.data || []
  const pagination = data?.data

  const tabs = [
    { id: 0, name: 'All Investigations', icon: FolderOpenIcon, component: null },
    { id: 1, name: 'Launch Assistant', icon: ChatBubbleLeftRightIcon, component: null },
    { id: 2, name: 'Model Testing', icon: CpuChipIcon, component: ModelTestingTab },
    { id: 3, name: 'Web Search', icon: GlobeAltIcon, component: WebSearchTab },
    { id: 4, name: 'Reverse Image Search', icon: PhotoIcon, component: ReverseImageSearchTab },
    { id: 5, name: 'News Monitor', icon: NewspaperIcon, component: NewsMonitorTab },
    { id: 6, name: 'Lead Generation', icon: LightBulbIcon, component: LeadGenerationTab },
    { id: 7, name: 'Relationship Analysis', icon: ShareIcon, component: RelationshipAnalysisTab },
    { id: 8, name: 'Evidence Compilation', icon: DocumentTextIcon, component: EvidenceCompilationTab },
    { id: 9, name: 'Crawl Scheduler', icon: ServerIcon, component: CrawlSchedulerTab },
    { id: 10, name: 'Reference Data', icon: DocumentArrowUpIcon, component: ReferenceDataTab },
  ]

  // ========== DATA DERIVATION (CONTINUED) ==========
  const mcpServers = mcpToolsData?.data?.servers || {}

  const clearTigerSelection = useCallback(() => {
    setUploadedTigerImages([])
    setUploadedTigerId(null)
    setTigerMetadata(null)
    setTigerUploadError(null)
    setTigerUploadLoading(false)
    setTigerImagePreviews(prev => {
      prev.forEach(url => URL.revokeObjectURL(url))
      return []
    })
    if (tigerFileInputRef.current) {
      tigerFileInputRef.current.value = ''
    }
  }, [])

  const parseTigerError = (err: any): string => {
    if (!err) return 'Unknown error'
    if (err?.data?.detail) {
      if (Array.isArray(err.data.detail)) {
        return err.data.detail.map((item: any) => item.msg || JSON.stringify(item)).join(', ')
      }
      if (typeof err.data.detail === 'string') {
        return err.data.detail
      }
      return JSON.stringify(err.data.detail)
    }
    if (err?.data?.message) {
      return err.data.message
    }
    if (err?.message) {
      return err.message
    }
    return typeof err === 'string' ? err : 'Unknown error'
  }

  const processTigerFiles = useCallback(async (files: File[]) => {
    if (!files || files.length === 0) {
      clearTigerSelection()
      return
    }

    const imageFiles = files.filter(file => file.type.startsWith('image/'))
    if (imageFiles.length === 0) {
      setTigerUploadError('Only image files are supported.')
      clearTigerSelection()
      return
    }

    setTigerUploadLoading(true)
    setTigerUploadError(null)
    setUploadedTigerImages(imageFiles)
    setTigerMetadata(null)
    setUploadedTigerId(null)
    setTigerImagePreviews(prev => {
      prev.forEach(url => URL.revokeObjectURL(url))
      return imageFiles.map(file => URL.createObjectURL(file))
    })

    try {
      const primaryImage = imageFiles[0]
      const identifyResult = await identifyTigerImage({ image: primaryImage }).unwrap()
      const identifiedData = identifyResult?.data

      if (identifiedData?.identified && identifiedData?.tiger_id) {
        setUploadedTigerId(identifiedData.tiger_id)
        setTigerMetadata({
          name: identifiedData.tiger_name,
          confidence: identifiedData.confidence,
          isNew: false,
        })
        return
      }

      const defaultName = `Unidentified Tiger ${new Date().toISOString()}`
      const createResult = await registerTiger({
        name: defaultName,
        images: imageFiles,
        notes: 'Automatically registered from investigation assistant upload',
      }).unwrap()

      if (createResult?.data?.tiger_id) {
        setUploadedTigerId(createResult.data.tiger_id)
        setTigerMetadata({
          name: createResult.data.name || defaultName,
          confidence: null,
          isNew: true,
        })
      } else {
        throw new Error('Tiger created but ID was not returned.')
      }
    } catch (err: any) {
      setTigerUploadError(parseTigerError(err))
      clearTigerSelection()
    } finally {
      setTigerUploadLoading(false)
    }
  }, [clearTigerSelection, identifyTigerImage, registerTiger])

  const handleTigerFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files ? Array.from(event.target.files) : []
    processTigerFiles(files)
    if (tigerFileInputRef.current) {
      tigerFileInputRef.current.value = ''
    }
  }

  const handleTigerDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    const files = Array.from(event.dataTransfer.files)
    processTigerFiles(files)
  }

  const handleTigerDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    event.stopPropagation()
  }

  // ========== ALL useEffect CALLS (USING DERIVED DATA) ==========
  // Sync activeTab with URL
  useEffect(() => {
    const urlTab = parseInt(searchParams.get('tab') || '0')
    if (activeTab !== urlTab) {
      setSearchParams({ tab: activeTab.toString() }, { replace: true })
    }
  }, [activeTab, searchParams, setSearchParams])

  // Initialize Assistant welcome message
  useEffect(() => {
    if (assistantMessages.length === 0 && activeTab === 1) {
      setAssistantMessages([{
        id: Date.now().toString(),
        role: 'assistant',
        content: "Hello! I'm your investigation assistant. I can help you launch a new investigation. You can:\n\n1. Describe what you'd like to investigate\n2. Upload files or images\n3. Select specific tools to use\n\nWhat would you like to investigate?",
        timestamp: new Date().toISOString()
      }])
    }
  }, [activeTab, assistantMessages.length])

  useEffect(() => {
    return () => {
      tigerImagePreviews.forEach(url => URL.revokeObjectURL(url))
    }
  }, [tigerImagePreviews])

  // Fetch extended info for all investigations
  useEffect(() => {
    const fetchExtendedInfo = async () => {
      for (const inv of investigations) {
        try {
          const response = await fetch(`/api/v1/investigations/${inv.id}/extended`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          })
          const data = await response.json()
          if (data.success) {
            setExtendedInfo(prev => ({
              ...prev,
              [inv.id]: data.data
            }))
          }
        } catch (error) {
          console.error(`Failed to fetch extended info for ${inv.id}:`, error)
        }
      }
    }

    if (investigations.length > 0) {
      fetchExtendedInfo()
    }
  }, [investigations])

  // ========== CONDITIONAL RETURNS (AFTER ALL HOOKS AND EFFECTS) ==========
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-red-600">Failed to load investigations</p>
      </div>
    )
  }

  // ========== EVENT HANDLERS ==========

  const handleResume = async (id: string) => {
    try {
      await resumeInvestigation(id).unwrap()
      refetch()
      navigate(`/investigations/${id}`)
    } catch (error: any) {
      console.error('Failed to resume:', error)
      alert(error.data?.detail || 'Failed to resume investigation')
    }
  }

  const handlePause = async (id: string) => {
    try {
      await pauseInvestigation(id).unwrap()
      refetch()
    } catch (error: any) {
      console.error('Failed to pause:', error)
      alert(error.data?.detail || 'Failed to pause investigation')
    }
  }

  const handleBulkPause = async (ids: string[]) => {
    try {
      await bulkPause(ids).unwrap()
      setSelectedIds(new Set())
      refetch()
    } catch (error: any) {
      console.error('Failed to bulk pause:', error)
      alert(error.data?.detail || 'Failed to pause investigations')
    }
  }

  const handleBulkArchive = async (ids: string[]) => {
    try {
      await bulkArchive(ids).unwrap()
      setSelectedIds(new Set())
      refetch()
    } catch (error: any) {
      console.error('Failed to bulk archive:', error)
      alert(error.data?.detail || 'Failed to archive investigations')
    }
  }

  const handleSelect = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const isListTab = activeTab === 0
  const assistantSendDisabled = ((!assistantInput.trim() && selectedTools.size === 0) || assistantLoading || tigerUploadLoading)
  const ActiveTabComponent = tabs[activeTab]?.component

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Investigations</h1>
          <p className="text-gray-600 mt-2">Manage and track all investigations</p>
        </div>
        <div className="flex items-center gap-2">
          {isListTab && (
            <Button
              variant={bulkMode ? 'primary' : 'outline'}
              onClick={() => {
                setBulkMode(!bulkMode)
                setSelectedIds(new Set())
              }}
            >
              <Squares2X2Icon className="h-5 w-5 mr-2" />
              Bulk Select
            </Button>
          )}
          <Button
            variant="primary"
            onClick={() => setActiveTab(1)}
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            New Investigation
          </Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <Card padding="none">
        <div className="border-b border-gray-200">
          <nav className="flex overflow-x-auto -mb-px" aria-label="Tabs">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center gap-2 whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm
                    transition-colors
                    ${
                      activeTab === tab.id
                        ? 'border-primary-600 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="h-5 w-5" />
                  {tab.name}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* LIST TAB CONTENT */}
          {isListTab ? (
            <>
              {error && <Alert type="error">Failed to load investigations</Alert>}

      {/* Bulk Actions Bar */}
      {bulkMode && (
        <BulkActions
          selectedIds={selectedIds}
          onPause={handleBulkPause}
          onArchive={handleBulkArchive}
          onDelete={(ids) => console.log('Delete:', ids)}
          onClearSelection={() => setSelectedIds(new Set())}
        />
      )}

      {/* Approval Modal */}
      {pendingApproval && (
        <ApprovalModal
          isOpen={true}
          onClose={() => setPendingApproval(null)}
          approvalId={pendingApproval.approval_id}
          approvalType={pendingApproval.approval_type}
          data={pendingApproval.data}
          onApprove={() => {
            fetch(`/api/v1/approvals/${pendingApproval.approval_id}/submit`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ approved: true })
            })
            setPendingApproval(null)
            refetch()
          }}
          onReject={(reason) => {
            fetch(`/api/v1/approvals/${pendingApproval.approval_id}/submit`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ approved: false, message: reason })
            })
            setPendingApproval(null)
          }}
        />
      )}

      {/* Filters */}
      <Card>
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium text-gray-700">Filter by Status:</label>
          <select
            value={statusFilter || ''}
            onChange={(e) => setStatusFilter(e.target.value || undefined)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All</option>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="in_progress">In Progress</option>
            <option value="paused">Paused</option>
            <option value="completed">Completed</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </Card>

      {/* Investigations List */}
      <div className="space-y-4">
        {investigations.length > 0 ? (
          investigations.map((investigation: any) => (
            <InvestigationCard
              key={investigation.id}
              investigation={investigation}
              extended={extendedInfo[investigation.id]}
              onResume={handleResume}
              onPause={handlePause}
              onView={(id) => navigate(`/investigations/${id}`)}
              onApprove={(id) => {
                const ext = extendedInfo[id]
                if (ext?.pending_approval) {
                  setPendingApproval(ext.pending_approval)
                }
              }}
              onSelect={handleSelect}
              selected={selectedIds.has(investigation.id)}
              showCheckbox={bulkMode}
            />
          ))
        ) : (
          <Card className="text-center py-12">
            <ListBulletIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No investigations found</p>
            <Button
              variant="primary"
              className="mt-4"
              onClick={() => setActiveTab(1)}
            >
              Create Your First Investigation
            </Button>
          </Card>
        )}
      </div>

      {/* Pagination */}
      {pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-gray-600">
            Page {page} of {pagination.total_pages}
          </span>
          <Button
            variant="outline"
            disabled={page >= pagination.total_pages}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
            </>
          ) : activeTab === 1 ? (
            /* LAUNCH ASSISTANT TAB */
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Agent Activity (if active) */}
              {agentActivities.length > 0 && (
                <div className="lg:col-span-1">
                  <AgentActivityFeed activities={agentActivities} maxItems={10} />
                </div>
              )}
              
              {/* Chat Interface */}
              <div className={agentActivities.length > 0 ? 'lg:col-span-2' : 'lg:col-span-3'}>
                <Card className="h-[calc(100vh-16rem)] flex flex-col">
                  <div className="border-b pb-4 mb-4 flex items-center justify-between gap-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">Investigation Assistant</h3>
                      <p className="text-sm text-gray-500">Select tools, upload tiger images, and describe your investigation</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        onClick={() => setShowTigerUpload(!showTigerUpload)}
                        className="flex items-center gap-2"
                      >
                        <PhotoIcon className="h-5 w-5" />
                        {showTigerUpload ? 'Hide' : 'Upload'} Tiger ({uploadedTigerImages.length})
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => setShowToolSelector(!showToolSelector)}
                        className="flex items-center gap-2"
                      >
                        <WrenchScrewdriverIcon className="h-5 w-5" />
                        {showToolSelector ? 'Hide' : 'Select'} Tools ({selectedTools.size})
                      </Button>
                    </div>
                  </div>

                  {/* Tool Selector */}
                  {showToolSelector && (
                    <div className="border-b pb-4 mb-4 max-h-48 overflow-y-auto">
                      {toolsLoading ? (
                        <LoadingSpinner size="sm" />
                      ) : toolsError ? (
                        <Alert type="error"><span className="text-sm">Failed to load tools</span></Alert>
                      ) : Object.keys(mcpServers).length === 0 ? (
                        <Alert type="info"><span className="text-sm">No tools available</span></Alert>
                      ) : (
                        <div className="space-y-4">
                          {Object.entries(mcpServers).map(([serverKey, server]: [string, any]) => (
                            <div key={serverKey}>
                              <h4 className="text-sm font-semibold text-gray-700 mb-2">{server.name}</h4>
                              <div className="flex flex-wrap gap-2">
                                {server.tools && server.tools.map((tool: any) => (
                                  <div
                                    key={tool.name}
                                    className="cursor-pointer inline-block"
                                    onClick={() => {
                                      setSelectedTools(prev => {
                                        const next = new Set(prev)
                                        next.has(tool.name) ? next.delete(tool.name) : next.add(tool.name)
                                        return next
                                      })
                                    }}
                                  >
                                    <Badge variant={selectedTools.has(tool.name) ? 'success' : 'default'}>
                                      {tool.name}
                                    </Badge>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Tiger Upload */}
                  {showTigerUpload && (
                    <div className="border-b pb-4 mb-4">
                      <div
                        className={`mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-lg transition-colors ${
                          tigerUploadLoading ? 'border-primary-500' : 'border-gray-300 hover:border-primary-500'
                        }`}
                        onDragOver={handleTigerDragOver}
                        onDrop={handleTigerDrop}
                      >
                        <div className="space-y-1 text-center">
                          <PhotoIcon className="mx-auto h-12 w-12 text-gray-400" />
                          <div className="flex text-sm text-gray-600 items-center justify-center gap-1">
                            <label
                              htmlFor="assistant-tiger-file-upload"
                              className="relative cursor-pointer bg-white rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
                            >
                              <span>Select images</span>
                              <input
                                id="assistant-tiger-file-upload"
                                name="assistant-tiger-file-upload"
                                type="file"
                                accept="image/*"
                                multiple
                                className="sr-only"
                                onChange={handleTigerFileSelect}
                                ref={tigerFileInputRef}
                              />
                            </label>
                            <p>or drag and drop</p>
                          </div>
                          <p className="text-xs text-gray-500">PNG, JPG, GIF up to 10MB each (max 5 images recommended)</p>
                        </div>
                      </div>

                      {tigerUploadLoading && (
                        <div className="mt-4 flex items-center gap-2 text-sm text-primary-600">
                          <LoadingSpinner size="sm" />
                          <span>Processing tiger images...</span>
                        </div>
                      )}

                      {tigerUploadError && (
                        <div className="mt-4">
                          <Alert type="error">
                            <span className="text-sm">{tigerUploadError}</span>
                          </Alert>
                        </div>
                      )}

                      {uploadedTigerImages.length > 0 && (
                        <div className="mt-4 space-y-3">
                          <div className="flex items-center justify-between">
                            <h4 className="text-sm font-semibold text-gray-700">Uploaded Images</h4>
                            <Button variant="outline" size="sm" onClick={clearTigerSelection}>
                              Clear
                            </Button>
                          </div>
                          <div className="flex flex-wrap gap-4">
                            {tigerImagePreviews.map((src, index) => (
                              <div key={index} className="w-24 h-24 rounded-md overflow-hidden border border-gray-200 shadow-sm">
                                <img
                                  src={src}
                                  alt={`Uploaded tiger ${index + 1}`}
                                  className="object-cover w-full h-full"
                                />
                              </div>
                            ))}
                          </div>
                          {tigerMetadata && (
                            <div className="rounded-md border border-primary-200 bg-primary-50 p-3 text-sm text-primary-900">
                              <p className="font-semibold">
                                {tigerMetadata.isNew ? 'New tiger registered' : 'Tiger identified'}
                              </p>
                              <p className="mt-1">
                                <span className="font-medium">Name:</span>{' '}
                                {tigerMetadata.name || 'Unknown'}
                              </p>
                              {typeof tigerMetadata.confidence === 'number' && (
                                <p>
                                  <span className="font-medium">Confidence:</span>{' '}
                                  {(tigerMetadata.confidence * 100).toFixed(1)}%
                                </p>
                              )}
                              {uploadedTigerId && (
                                <p className="mt-1 text-xs text-primary-700 break-all">
                                  <span className="font-medium">Tiger ID:</span> {uploadedTigerId}
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Progress Indicator */}
                  {launchProgress.length > 0 && (
                    <div className="border-b pb-4 mb-4 space-y-2">
                      <h4 className="text-sm font-semibold text-gray-700">Progress</h4>
                      {launchProgress.map((progress: any, idx: number) => (
                        <div key={idx} className="flex items-center gap-2 text-sm">
                          {progress.status === 'completed' && <CheckCircleIcon className="h-4 w-4 text-green-500" />}
                          {progress.status === 'running' && <ArrowPathIcon className="h-4 w-4 text-blue-500 animate-spin" />}
                          {progress.status === 'error' && <XCircleIcon className="h-4 w-4 text-red-500" />}
                          <span className={progress.status === 'completed' ? 'text-gray-600' : progress.status === 'running' ? 'text-blue-600' : 'text-red-600'}>
                            {progress.step}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                    {assistantMessages.map((message: any) => (
                      <div
                        key={message.id}
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[80%] rounded-lg p-3 ${
                            message.role === 'user'
                              ? 'bg-primary-600 text-white'
                              : message.role === 'system'
                              ? 'bg-gray-100 text-gray-800'
                              : 'bg-blue-50 text-blue-900 border border-blue-200'
                          }`}
                        >
                          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                        </div>
                      </div>
                    ))}
                    {assistantLoading && (
                      <div className="flex justify-start">
                        <div className="bg-gray-100 rounded-lg p-3">
                          <div className="flex space-x-2">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Input */}
                  <form 
                    onSubmit={async (e) => {
                      e.preventDefault()
                      if (!assistantInput.trim() && selectedTools.size === 0) return
                      if (tigerUploadLoading) return

                      const userMessage = {
                        id: Date.now().toString(),
                        role: 'user',
                        content: assistantInput || 'Launch investigation',
                        timestamp: new Date().toISOString()
                      }

                      setAssistantMessages(prev => [...prev, userMessage])
                      setAssistantInput('')
                      setAssistantLoading(true)
                      setAssistantError(null)

                      try {
                        if (!currentInvestigationId) {
                          // Create new investigation
                          const title = assistantInput || 'New Investigation'
                          const createResult = await createInvestigation({
                            title,
                            description: assistantInput || 'Investigation from Assistant',
                            priority: 'medium'
                          }).unwrap()
                          const newId = createResult.data.id
                          setCurrentInvestigationId(newId)

                          setAssistantMessages(prev => [...prev, {
                            id: (Date.now() + 1).toString(),
                            role: 'system',
                            content: `Investigation created: ${title}`,
                            timestamp: new Date().toISOString()
                          }])

                          setLaunchProgress([{ step: 'Starting investigation', status: 'running' }])

                          // Launch investigation
                          const launchResult = await launchInvestigation({
                            investigation_id: newId,
                            user_input: assistantInput || 'Launch investigation',
                            selected_tools: selectedTools.size > 0 ? Array.from(selectedTools) : undefined,
                            tiger_id: uploadedTigerId || undefined
                          }).unwrap()

                          const resultData = (launchResult.data as any) || {}
                          if (resultData?.tiger_id) {
                            setUploadedTigerId(resultData.tiger_id)
                            if (resultData.tiger_metadata) {
                              setTigerMetadata({
                                name: resultData.tiger_metadata.tiger_name ?? tigerMetadata?.name ?? null,
                                confidence: resultData.tiger_metadata.confidence ?? tigerMetadata?.confidence ?? null,
                                isNew: resultData.tiger_metadata.is_new ?? tigerMetadata?.isNew ?? false,
                              })
                              setShowTigerUpload(true)
                            }
                          }

                          setAssistantMessages(prev => [...prev, {
                            id: (Date.now() + 2).toString(),
                            role: 'assistant',
                            content: (launchResult.data as any)?.response || 'Investigation launched!',
                            timestamp: new Date().toISOString()
                          }])
                          setAssistantLoading(false)
                          refetch() // Refresh list
                        } else {
                          // Continue with existing investigation
                          const launchResult = await launchInvestigation({
                            investigation_id: currentInvestigationId,
                            user_input: assistantInput || 'Launch investigation',
                            selected_tools: selectedTools.size > 0 ? Array.from(selectedTools) : undefined,
                            tiger_id: uploadedTigerId || undefined
                          }).unwrap()

                          const resultData = (launchResult.data as any) || {}
                          if (resultData?.tiger_id) {
                            setUploadedTigerId(resultData.tiger_id)
                            if (resultData.tiger_metadata) {
                              setTigerMetadata({
                                name: resultData.tiger_metadata.tiger_name ?? tigerMetadata?.name ?? null,
                                confidence: resultData.tiger_metadata.confidence ?? tigerMetadata?.confidence ?? null,
                                isNew: resultData.tiger_metadata.is_new ?? tigerMetadata?.isNew ?? false,
                              })
                              setShowTigerUpload(true)
                            }
                          }

                          setAssistantMessages(prev => [...prev, {
                            id: (Date.now() + 2).toString(),
                            role: 'assistant',
                            content: (launchResult.data as any)?.response || 'Processed!',
                            timestamp: new Date().toISOString()
                          }])
                          setAssistantLoading(false)
                        }
                      } catch (error: any) {
                        console.error('Assistant error:', error)
                        const errorMsg = error.data?.detail || error.message || 'Error occurred'
                        setAssistantMessages(prev => [...prev, {
                          id: (Date.now() + 2).toString(),
                          role: 'assistant',
                          content: `Error: ${errorMsg}`,
                          timestamp: new Date().toISOString()
                        }])
                        setAssistantLoading(false)
                      }
                    }}
                    className="flex items-center space-x-2"
                  >
                    <input
                      type="text"
                      value={assistantInput}
                      onChange={(e) => setAssistantInput(e.target.value)}
                      placeholder="Describe what you'd like to investigate..."
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      disabled={assistantLoading || tigerUploadLoading}
                    />
                    <Button type="submit" variant="primary" disabled={assistantSendDisabled}>
                      <PaperAirplaneIcon className="h-5 w-5" />
                    </Button>
                  </form>
                </Card>
              </div>
            </div>
          ) : ActiveTabComponent ? (
            /* TOOL TABS */
            <ActiveTabComponent />
          ) : null}
        </div>
      </Card>
    </div>
  )
}

export default Investigations


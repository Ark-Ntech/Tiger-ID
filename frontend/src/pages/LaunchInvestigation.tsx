import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  useCreateInvestigationMutation, 
  useLaunchInvestigationMutation,
  useGetMCPToolsQuery,
  useIdentifyTigerImageMutation,
  useRegisterTigerMutation
} from '../app/api'
import { useWebSocket } from '../hooks/useWebSocket'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import Badge from '../components/common/Badge'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Alert from '../components/common/Alert'
import { PaperAirplaneIcon, WrenchScrewdriverIcon, CheckCircleIcon, XCircleIcon, ArrowPathIcon, ChatBubbleLeftRightIcon, GlobeAltIcon, PhotoIcon, NewspaperIcon, LightBulbIcon, ShareIcon, DocumentTextIcon, ServerIcon, DocumentArrowUpIcon, CpuChipIcon } from '@heroicons/react/24/outline'
import WebSearchTab from '../components/investigations/WebSearchTab'
import ReverseImageSearchTab from '../components/investigations/ReverseImageSearchTab'
import NewsMonitorTab from '../components/investigations/NewsMonitorTab'
import LeadGenerationTab from '../components/investigations/LeadGenerationTab'
import RelationshipAnalysisTab from '../components/investigations/RelationshipAnalysisTab'
import EvidenceCompilationTab from '../components/investigations/EvidenceCompilationTab'
import CrawlSchedulerTab from '../components/investigations/CrawlSchedulerTab'
import ReferenceDataTab from '../components/investigations/ReferenceDataTab'
import ModelTestingTab from '../components/investigations/ModelTestingTab'
import AgentActivityFeed from '../components/investigations/AgentActivityFeed'
import ApprovalModal from '../components/investigations/ApprovalModal'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  tool_used?: string
  tool_result?: any
}

interface Tool {
  name: string
  description: string
  server?: string
}

interface MCPServer {
  name: string
  description: string
  tools: Tool[]
}

const LaunchInvestigation = () => {
  const navigate = useNavigate()
  const [createInvestigation] = useCreateInvestigationMutation()
  const [launchInvestigation] = useLaunchInvestigationMutation()
  const [identifyTigerImage] = useIdentifyTigerImageMutation()
  const [registerTiger] = useRegisterTigerMutation()
  const { data: mcpToolsData, isLoading: toolsLoading, error: toolsError } = useGetMCPToolsQuery()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const [activeTab, setActiveTab] = useState(0)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [selectedTools, setSelectedTools] = useState<Set<string>>(new Set())
  const [showToolSelector, setShowToolSelector] = useState(false)
  const [showTigerUpload, setShowTigerUpload] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [investigationId, setInvestigationId] = useState<string | null>(null)
  const [launchProgress, setLaunchProgress] = useState<{ step: string; status: 'pending' | 'running' | 'completed' | 'error' }[]>([])
  const [agentActivities, setAgentActivities] = useState<any[]>([])
  const [pendingApproval, setPendingApproval] = useState<any>(null)
  const [uploadedTigerImages, setUploadedTigerImages] = useState<File[]>([])
  const [uploadedTigerId, setUploadedTigerId] = useState<string | null>(null)
  const [tigerMetadata, setTigerMetadata] = useState<{ name?: string | null; confidence?: number | null; isNew?: boolean } | null>(null)
  const [tigerUploadLoading, setTigerUploadLoading] = useState(false)
  const [tigerUploadError, setTigerUploadError] = useState<string | null>(null)
  const [tigerImagePreviews, setTigerImagePreviews] = useState<string[]>([])

  const tigerFileInputRef = useRef<HTMLInputElement | null>(null)

  const tabs = [
    { name: 'Assistant', icon: ChatBubbleLeftRightIcon, component: null },
    { name: 'Model Testing', icon: CpuChipIcon, component: ModelTestingTab },
    { name: 'Web Search', icon: GlobeAltIcon, component: WebSearchTab },
    { name: 'Reverse Image Search', icon: PhotoIcon, component: ReverseImageSearchTab },
    { name: 'News Monitor', icon: NewspaperIcon, component: NewsMonitorTab },
    { name: 'Lead Generation', icon: LightBulbIcon, component: LeadGenerationTab },
    { name: 'Relationship Analysis', icon: ShareIcon, component: RelationshipAnalysisTab },
    { name: 'Evidence Compilation', icon: DocumentTextIcon, component: EvidenceCompilationTab },
    { name: 'Crawl Scheduler', icon: ServerIcon, component: CrawlSchedulerTab },
    { name: 'Reference Data', icon: DocumentArrowUpIcon, component: ReferenceDataTab },
  ]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    return () => {
      tigerImagePreviews.forEach(url => URL.revokeObjectURL(url))
    }
  }, [tigerImagePreviews])

  // Initialize with welcome message
  useEffect(() => {
    if (messages.length === 0) {
      const welcomeMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: "Hello! I'm your investigation assistant. I can help you launch a new investigation. You can:\n\n1. Describe what you'd like to investigate (e.g., 'Check if Facility XYZ has proper permits')\n2. Upload files or images\n3. Select specific tools to use\n\nWhat would you like to investigate?",
        timestamp: new Date().toISOString(),
      }
      setMessages([welcomeMessage])
    }
  }, [])

  // WebSocket connection for real-time updates
  const { isConnected } = useWebSocket({
    onMessage: (message) => {
      if (message.type === 'agent_activity') {
        // Add agent activity to feed
        setAgentActivities(prev => [...prev, message.data])
        
        // Update progress if phase changed
        if (message.data.status === 'running') {
          const phaseMap: Record<string, string> = {
            'research_agent': 'Gathering evidence',
            'analysis_agent': 'Analyzing evidence',
            'validation_agent': 'Validating findings',
            'reporting_agent': 'Generating report'
          }
          const stepName = phaseMap[message.data.agent] || message.data.action
          setLaunchProgress(prev => {
            const exists = prev.find(p => p.step === stepName)
            if (!exists) {
              return [...prev, { step: stepName, status: 'running' }]
            }
            return prev
          })
        } else if (message.data.status === 'completed') {
          setLaunchProgress(prev => prev.map(p => 
            p.step.toLowerCase().includes(message.data.agent.split('_')[0]) 
              ? { ...p, status: 'completed' as const } 
              : p
          ))
        }
      } else if (message.type === 'approval_required') {
        // Show approval modal
        setPendingApproval(message.data)
      } else if (message.type === 'investigation_completed') {
        // Investigation finished
        setIsLoading(false)
        setLaunchProgress([])
        const completionMessage: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `Investigation completed! ${message.data.summary || 'View results in the investigation workspace.'}`,
          timestamp: new Date().toISOString()
        }
        setMessages(prev => [...prev, completionMessage])
        
        // Navigate to workspace after short delay
        setTimeout(() => {
          if (investigationId) {
            navigate(`/investigations/${investigationId}`)
          }
        }, 2000)
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

  const mcpServers: Record<string, MCPServer> = mcpToolsData?.data?.servers || {}
  
  // Log tools loading state for debugging
  useEffect(() => {
    if (toolsError) {
      console.error('Error loading MCP tools:', toolsError)
    }
    if (mcpToolsData) {
      console.log('MCP Tools loaded:', Object.keys(mcpToolsData.data?.servers || {}))
    }
  }, [toolsError, mcpToolsData])

  const toggleTool = (toolName: string) => {
    setSelectedTools(prev => {
      const next = new Set(prev)
      if (next.has(toolName)) {
        next.delete(toolName)
      } else {
        next.add(toolName)
      }
      return next
    })
  }

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

  const handleSendMessage = async () => {
    if (!input.trim() && selectedTools.size === 0) return
    if (tigerUploadLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input || 'Launch investigation',
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setError(null)

    try {
      // If no investigation exists yet, create one
      if (!investigationId) {
        const investigationTitle = input || 'New Investigation'
        const investigationData = {
          title: investigationTitle,
          description: input || 'Investigation launched from chatbot',
          priority: 'medium' as const
        }

        const createResult = await createInvestigation(investigationData).unwrap()
        const newInvestigationId = createResult.data.id
        setInvestigationId(newInvestigationId)

        // Add system message
        const systemMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'system',
          content: `Investigation created: ${investigationTitle}`,
          timestamp: new Date().toISOString(),
        }
        setMessages(prev => [...prev, systemMessage])

        // Launch investigation
        const selectedToolsArray = Array.from(selectedTools)
        
        // Initialize progress (will be updated by WebSocket events)
        setLaunchProgress([
          { step: 'Starting investigation', status: 'running' as const }
        ])

        try{
          const launchResult = await launchInvestigation({
            investigation_id: newInvestigationId,
            user_input: input || 'Launch investigation',
            selected_tools: selectedToolsArray.length > 0 ? selectedToolsArray : undefined,
            tiger_id: uploadedTigerId || undefined,
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

          const assistantMessage: Message = {
            id: (Date.now() + 2).toString(),
            role: 'assistant',
            content: (launchResult.data as any)?.response || 'Investigation launched successfully!',
            timestamp: new Date().toISOString(),
          }
          setMessages(prev => [...prev, assistantMessage])
        } catch (launchError: any) {
          console.error('Launch error:', launchError)
          let launchErrorMsg = 'Failed to launch investigation'
          if (launchError.data?.detail) {
            if (Array.isArray(launchError.data.detail)) {
              launchErrorMsg = launchError.data.detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
            } else if (typeof launchError.data.detail === 'string') {
              launchErrorMsg = launchError.data.detail
            } else {
              launchErrorMsg = JSON.stringify(launchError.data.detail)
            }
          } else if (launchError.data?.message) {
            launchErrorMsg = launchError.data.message
          } else if (launchError.message) {
            launchErrorMsg = launchError.message
          }
          setError(launchErrorMsg)
          setLaunchProgress(prev => prev.map(step => 
            step.status === 'running' ? { ...step, status: 'error' as const } : step
          ))
        }
      } else {
        // Continue conversation with existing investigation
        const selectedToolsArray = Array.from(selectedTools)
        
        try {
          const launchResult = await launchInvestigation({
            investigation_id: investigationId,
            user_input: input,
            selected_tools: selectedToolsArray.length > 0 ? selectedToolsArray : undefined,
            tiger_id: uploadedTigerId || undefined,
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

          const assistantMessage: Message = {
            id: (Date.now() + 2).toString(),
            role: 'assistant',
            content: (launchResult.data as any)?.response || 'Request processed successfully.',
            timestamp: new Date().toISOString(),
          }
          setMessages(prev => [...prev, assistantMessage])
        } catch (continueError: any) {
          console.error('Continue conversation error:', continueError)
          let continueErrorMsg = 'Failed to process message'
          if (continueError.data?.detail) {
            if (Array.isArray(continueError.data.detail)) {
              continueErrorMsg = continueError.data.detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
            } else if (typeof continueError.data.detail === 'string') {
              continueErrorMsg = continueError.data.detail
            } else {
              continueErrorMsg = JSON.stringify(continueError.data.detail)
            }
          } else if (continueError.data?.message) {
            continueErrorMsg = continueError.data.message
          } else if (continueError.message) {
            continueErrorMsg = continueError.message
          }
          setError(continueErrorMsg)
        }
      }
    } catch (err: any) {
      console.group('🚨 Investigation Error Details')
      console.error('Full error object:', err)
      console.error('Error type:', typeof err)
      console.error('Error keys:', Object.keys(err || {}))
      console.error('err.message:', err.message)
      console.error('err.data:', err.data)
      console.error('err.data.detail:', err.data?.detail)
      console.error('err.status:', err.status)
      console.error('err.error:', err.error)
      console.groupEnd()
      
      // Extract error message from RTK Query error structure
      let errorMessage = 'Unknown error'
      
      if (err.data?.detail) {
        // FastAPI validation errors come as array of objects
        if (Array.isArray(err.data.detail)) {
          errorMessage = err.data.detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
        } else if (typeof err.data.detail === 'string') {
          errorMessage = err.data.detail
        } else {
          errorMessage = JSON.stringify(err.data.detail)
        }
      } else if (err.data?.message) {
        errorMessage = err.data.message
      } else if (err.message) {
        errorMessage = err.message
      } else if (err.error) {
        errorMessage = err.error
      } else if (typeof err === 'string') {
        errorMessage = err
      }
      
      setError(errorMessage)
      const errorMsg: Message = {
        id: (Date.now() + 2).toString(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${errorMessage}. Please try again.`,
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }

  const handleViewWorkspace = () => {
    if (investigationId) {
      navigate(`/investigations/${investigationId}`)
    }
  }

  const allTools: Tool[] = []
  Object.values(mcpServers).forEach(server => {
    server.tools.forEach(tool => {
      allTools.push({ ...tool, server: server.name })
    })
  })

  const ActiveComponent = tabs[activeTab].component
  const isAssistantTab = activeTab === 0
  const isSendDisabled = ((!input.trim() && selectedTools.size === 0) || isLoading || tigerUploadLoading)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Launch Investigation</h1>
          <p className="text-gray-600 mt-2">Configure and launch investigations with AI assistance</p>
        </div>
        {investigationId && (
          <Button variant="primary" onClick={handleViewWorkspace}>
            View Workspace
          </Button>
        )}
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {/* Approval Modal */}
      {pendingApproval && (
        <ApprovalModal
          isOpen={true}
          onClose={() => setPendingApproval(null)}
          approvalId={pendingApproval.approval_id}
          approvalType={pendingApproval.approval_type}
          data={pendingApproval.data}
          onApprove={() => {
            // Call approval API
            fetch(`/api/v1/approvals/${pendingApproval.approval_id}/submit`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ approved: true })
            })
            setPendingApproval(null)
          }}
          onReject={(reason) => {
            // Call approval API with rejection
            fetch(`/api/v1/approvals/${pendingApproval.approval_id}/submit`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ approved: false, message: reason })
            })
            setPendingApproval(null)
          }}
        />
      )}

      {/* Tab Navigation */}
      <Card padding="none">
        <div className="border-b border-gray-200">
          <nav className="flex overflow-x-auto -mb-px" aria-label="Tabs">
            {tabs.map((tab, index) => {
              const Icon = tab.icon
              return (
                <button
                  key={index}
                  onClick={() => setActiveTab(index)}
                  className={`
                    flex items-center gap-2 whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm
                    transition-colors
                    ${
                      activeTab === index
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
          {isAssistantTab ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column - Agent Activity (if investigation active) */}
              {agentActivities.length > 0 && (
                <div className="lg:col-span-1">
                  <AgentActivityFeed activities={agentActivities} maxItems={10} />
                </div>
              )}
              
              {/* Main Column - Chat */}
              <div className={agentActivities.length > 0 ? 'lg:col-span-2' : 'lg:col-span-3'}>
          <Card className="h-[calc(100vh-16rem)] flex flex-col">
            {/* Tool Selector Toggle */}
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
              <Alert type="error">
                <span className="text-sm">Failed to load tools. Please check your authentication and try again.</span>
              </Alert>
            ) : Object.keys(mcpServers).length === 0 ? (
              <Alert type="info">
                <span className="text-sm">No tools available. Make sure you're authenticated and the MCP servers are running.</span>
              </Alert>
                ) : (
                  <div className="space-y-4">
                    {Object.entries(mcpServers).map(([serverKey, server]) => (
                      <div key={serverKey}>
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">{server.name}</h4>
                        <p className="text-xs text-gray-500 mb-2">{server.description}</p>
                        <div className="flex flex-wrap gap-2">
                          {server.tools && server.tools.length > 0 ? (
                            server.tools.map((tool: Tool) => (
                              <div
                                key={tool.name}
                                className="cursor-pointer inline-block"
                                onClick={() => toggleTool(tool.name)}
                              >
                                <Badge
                                  variant={selectedTools.has(tool.name) ? 'success' : 'default'}
                                >
                                  {tool.name}
                                </Badge>
                              </div>
                            ))
                          ) : (
                            <p className="text-xs text-gray-500">No tools available for this server</p>
                          )}
                        </div>
                      </div>
                    ))}
                    {selectedTools.size > 0 && (
                      <div className="mt-2 pt-2 border-t">
                        <p className="text-xs text-gray-600">
                          Selected: {Array.from(selectedTools).join(', ')}
                        </p>
                      </div>
                    )}
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
                        htmlFor="tiger-file-upload"
                        className="relative cursor-pointer bg-white rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
                      >
                        <span>Select images</span>
                        <input
                          id="tiger-file-upload"
                          name="tiger-file-upload"
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
                {launchProgress.map((progress, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    {progress.status === 'completed' && (
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                    )}
                    {progress.status === 'running' && (
                      <ArrowPathIcon className="h-4 w-4 text-blue-500 animate-spin" />
                    )}
                    {progress.status === 'error' && (
                      <XCircleIcon className="h-4 w-4 text-red-500" />
                    )}
                    {progress.status === 'pending' && (
                      <div className="h-4 w-4 rounded-full border-2 border-gray-300" />
                    )}
                    <span className={progress.status === 'completed' ? 'text-gray-600' : progress.status === 'running' ? 'text-blue-600' : progress.status === 'error' ? 'text-red-600' : 'text-gray-400'}>
                      {progress.step}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Messages */}
            <div className="flex-1 overflow-y-auto space-y-4 mb-4">
              {messages.map((message) => (
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
                    {message.tool_used && (
                      <p className="text-xs opacity-75 mb-1">
                        🔧 Used: {message.tool_used}
                      </p>
                    )}
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    {message.tool_result && (
                      <div className="mt-2 pt-2 border-t border-opacity-20">
                        <p className="text-xs font-semibold mb-1">Result:</p>
                        <pre className="text-xs overflow-auto">
                          {JSON.stringify(message.tool_result, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
              {isLoading && (
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
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form 
              onSubmit={(e) => {
                e.preventDefault()
                handleSendMessage()
              }} 
              className="flex items-center space-x-2"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Describe what you'd like to investigate..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={isLoading}
              />
              <Button
                type="submit"
                variant="primary"
                disabled={isSendDisabled}
                isLoading={isLoading}
              >
                <PaperAirplaneIcon className="h-5 w-5" />
              </Button>
            </form>
          </Card>
        </div>

        {/* Tools Sidebar */}
        <div className="space-y-4">
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Tools</h3>
            {toolsLoading ? (
              <LoadingSpinner size="sm" />
            ) : toolsError ? (
              <Alert type="error">
                <span className="text-sm">Failed to load tools. Please check authentication.</span>
              </Alert>
            ) : Object.keys(mcpServers).length === 0 ? (
              <Alert type="info">
                <span className="text-sm">No tools available. Make sure you're authenticated.</span>
              </Alert>
            ) : (
              <div className="space-y-4 max-h-[calc(100vh-20rem)] overflow-y-auto">
                {Object.entries(mcpServers).map(([serverKey, server]) => (
                  <div key={serverKey}>
                    <h4 className="text-sm font-semibold text-gray-700 mb-1">{server.name}</h4>
                    <p className="text-xs text-gray-500 mb-2">{server.description}</p>
                    <div className="space-y-1">
                      {server.tools && server.tools.length > 0 ? (
                        server.tools.map((tool: Tool) => (
                          <div
                            key={tool.name}
                            className={`text-xs p-2 rounded cursor-pointer transition-colors ${
                              selectedTools.has(tool.name)
                                ? 'bg-primary-100 text-primary-900 border border-primary-300'
                                : 'bg-gray-50 hover:bg-gray-100'
                            }`}
                            onClick={() => toggleTool(tool.name)}
                          >
                            <div className="font-medium">{tool.name}</div>
                            <div className="text-gray-600 mt-1">{tool.description}</div>
                          </div>
                        ))
                      ) : (
                        <p className="text-xs text-gray-500">No tools available</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {selectedTools.size > 0 && (
            <Card>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Selected Tools</h3>
              <div className="flex flex-wrap gap-1">
                {Array.from(selectedTools).map(tool => (
                  <Badge key={tool} variant="success" className="text-xs">
                    {tool}
                  </Badge>
                ))}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedTools(new Set())}
                className="mt-2 w-full"
              >
                Clear Selection
              </Button>
            </Card>
          )}
        </div>
      </div>
          ) : ActiveComponent ? (
            <ActiveComponent />
          ) : null}
        </div>
      </Card>
    </div>
  )
}

export default LaunchInvestigation

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useMemo,
  type ReactNode,
} from 'react'
import {
  useLaunchInvestigation2Mutation,
  useGetInvestigation2Query,
  useRegenerateInvestigation2ReportMutation,
} from '../app/api'
import { useWebSocket } from '../hooks/useWebSocket'
import type {
  Investigation2Response,
  Investigation2Context as InvestigationContextType,
  ProgressStep,
  Investigation2Phase,
  StepStatus,
  ReportAudience,
} from '../types/investigation2'

/**
 * Initial progress steps for a new investigation.
 */
const INITIAL_PROGRESS_STEPS: ProgressStep[] = [
  { phase: 'upload_and_parse', status: 'pending' },
  { phase: 'reverse_image_search', status: 'pending' },
  { phase: 'tiger_detection', status: 'pending' },
  { phase: 'stripe_analysis', status: 'pending' },
  { phase: 'report_generation', status: 'pending' },
  { phase: 'complete', status: 'pending' },
]

/**
 * The 6-model ReID ensemble for stripe analysis.
 */
const REID_MODELS = [
  'wildlife_tools',
  'cvwc2019_reid',
  'transreid',
  'megadescriptor_b',
  'tiger_reid',
  'rapid_reid',
] as const

/**
 * Subagent information for tracking parallel processing tasks.
 */
interface SubagentInfo {
  id: string
  type: string
  phase: string
  status: 'running' | 'completed' | 'error'
  progress: number
  startedAt: string
  completedAt?: string
  result?: any
  error?: string
}

/**
 * Model progress tracking for the 6-model ensemble.
 */
interface ModelProgressInfo {
  model: string
  progress: number
  status: 'pending' | 'running' | 'completed' | 'error'
  startedAt?: string
  completedAt?: string
  matchesFound?: number
  topScore?: number
}

/**
 * Activity event for the investigation timeline.
 */
interface ActivityEvent {
  id: string
  timestamp: string
  type:
    | 'phase_started'
    | 'phase_completed'
    | 'model_started'
    | 'model_completed'
    | 'subagent_spawned'
    | 'subagent_completed'
    | 'match_found'
    | 'error'
    | 'info'
  message: string
  phase?: string
  model?: string
  metadata?: Record<string, any>
}

/**
 * Context value interface for Investigation 2.0 state management.
 */
interface Investigation2ContextValue {
  // State
  investigationId: string | null
  investigation: Investigation2Response | null
  progressSteps: ProgressStep[]
  isLaunching: boolean
  uploadedImage: File | null
  imagePreview: string | null
  context: InvestigationContextType
  error: string | null

  // WebSocket state
  wsConnected: boolean
  wsError: string | null

  // Subagent and model progress state
  activeSubagents: Map<string, SubagentInfo>
  modelProgress: ModelProgressInfo[]
  activityEvents: ActivityEvent[]

  // Computed state
  isCompleted: boolean
  isInProgress: boolean
  completedModelsCount: number
  totalModelsCount: number
  isStripeAnalysisRunning: boolean

  // Actions
  setInvestigationId: (id: string | null) => void
  setUploadedImage: (file: File | null) => void
  setImagePreview: (preview: string | null) => void
  setContext: (context: InvestigationContextType) => void
  updateContext: (field: keyof InvestigationContextType, value: string) => void
  setError: (error: string | null) => void
  launchInvestigation: () => Promise<void>
  resetInvestigation: () => void
  regenerateReport: (audience: ReportAudience) => Promise<void>
}

const Investigation2Context = createContext<Investigation2ContextValue | null>(null)

/**
 * Custom hook to access Investigation 2.0 context.
 * Must be used within an Investigation2Provider.
 */
export const useInvestigation2 = (): Investigation2ContextValue => {
  const context = useContext(Investigation2Context)
  if (!context) {
    throw new Error('useInvestigation2 must be used within an Investigation2Provider')
  }
  return context
}

interface Investigation2ProviderProps {
  children: ReactNode
}

/**
 * Provider component for Investigation 2.0 state management.
 * Handles WebSocket connections, API calls, and state synchronization.
 */
export const Investigation2Provider = ({ children }: Investigation2ProviderProps) => {
  // Core state
  const [investigationId, setInvestigationId] = useState<string | null>(null)
  const [uploadedImage, setUploadedImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [context, setContext] = useState<InvestigationContextType>({
    location: '',
    date: '',
    notes: '',
  })
  const [progressSteps, setProgressSteps] = useState<ProgressStep[]>([])
  const [error, setError] = useState<string | null>(null)

  // Subagent and model progress state
  const [activeSubagents, setActiveSubagents] = useState<Map<string, SubagentInfo>>(new Map())
  const [modelProgress, setModelProgress] = useState<ModelProgressInfo[]>([])
  const [activityEvents, setActivityEvents] = useState<ActivityEvent[]>([])

  // API mutations
  const [launchMutation, { isLoading: isLaunching }] = useLaunchInvestigation2Mutation()
  const [regenerateMutation] = useRegenerateInvestigation2ReportMutation()

  // API query for investigation data (with polling for updates)
  const { data: investigationResponse } = useGetInvestigation2Query(
    investigationId || '',
    {
      skip: !investigationId,
      pollingInterval: 2000, // Poll every 2 seconds for faster updates
    }
  )

  // Extract investigation data from API response
  const investigation = investigationResponse?.data || null

  /**
   * Update model progress for a specific model.
   */
  const updateModelProgress = useCallback(
    (
      model: string,
      progress: number,
      status: 'pending' | 'running' | 'completed' | 'error',
      extras?: Partial<ModelProgressInfo>
    ) => {
      setModelProgress((prev) => {
        const existing = prev.find((m) => m.model === model)
        if (existing) {
          return prev.map((m) =>
            m.model === model
              ? {
                  ...m,
                  progress,
                  status,
                  ...(status === 'running' && !m.startedAt
                    ? { startedAt: new Date().toISOString() }
                    : {}),
                  ...(status === 'completed'
                    ? { completedAt: new Date().toISOString() }
                    : {}),
                  ...extras,
                }
              : m
          )
        }
        return [
          ...prev,
          {
            model,
            progress,
            status,
            ...(status === 'running' ? { startedAt: new Date().toISOString() } : {}),
            ...(status === 'completed' ? { completedAt: new Date().toISOString() } : {}),
            ...extras,
          },
        ]
      })
    },
    []
  )

  /**
   * Add an activity event to the timeline.
   */
  const addActivityEvent = useCallback(
    (
      type: ActivityEvent['type'],
      message: string,
      metadata?: { phase?: string; model?: string; [key: string]: any }
    ) => {
      const event: ActivityEvent = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date().toISOString(),
        type,
        message,
        phase: metadata?.phase,
        model: metadata?.model,
        metadata,
      }
      setActivityEvents((prev) => [...prev.slice(-99), event]) // Keep last 100
    },
    []
  )

  /**
   * Initialize model progress with all 6 models as pending.
   */
  const initializeModelProgress = useCallback(() => {
    setModelProgress(
      REID_MODELS.map((model) => ({
        model,
        progress: 0,
        status: 'pending' as const,
      }))
    )
  }, [])

  // WebSocket handler for real-time updates
  const handleWebSocketMessage = useCallback(
    (message: any) => {
      console.log('WebSocket message received:', message)

      // Handle phase events
      if (message.event === 'phase_started') {
        updateProgressStep(message.data.phase, 'running', message.data)
        addActivityEvent('phase_started', `Phase ${message.data.phase} started`, {
          phase: message.data.phase,
        })

        // Initialize model progress when stripe_analysis starts
        if (message.data.phase === 'stripe_analysis') {
          initializeModelProgress()
        }
      } else if (message.event === 'phase_completed') {
        updateProgressStep(message.data.phase, 'completed', message.data)
        addActivityEvent('phase_completed', `Phase ${message.data.phase} completed`, {
          phase: message.data.phase,
        })
      } else if (message.event === 'investigation_completed') {
        updateProgressStep('complete', 'completed', message.data)
        addActivityEvent('phase_completed', 'Investigation completed', {
          phase: 'complete',
        })
      } else if (message.event === 'error') {
        setError(message.data.error || 'An error occurred during the investigation')
        addActivityEvent('error', message.data.error || 'An error occurred', {
          phase: message.data.phase,
        })
      }

      // Handle subagent events
      if (message.event === 'subagent_spawned') {
        const info: SubagentInfo = {
          id: message.data.subagent_id,
          type: message.data.subagent_type,
          phase: message.data.phase,
          status: 'running',
          progress: 0,
          startedAt: message.data.timestamp || new Date().toISOString(),
        }
        setActiveSubagents((prev) => new Map(prev).set(info.id, info))
        addActivityEvent('subagent_spawned', `Subagent ${info.type} started`, {
          phase: info.phase,
        })
      }

      if (message.event === 'subagent_progress') {
        const { subagent_id, progress, result } = message.data
        setActiveSubagents((prev) => {
          const newMap = new Map(prev)
          const existing = newMap.get(subagent_id)
          if (existing) {
            newMap.set(subagent_id, { ...existing, progress, result })
          }
          return newMap
        })
      }

      if (message.event === 'subagent_completed') {
        const { subagent_id, result, error: subagentError } = message.data
        setActiveSubagents((prev) => {
          const newMap = new Map(prev)
          const existing = newMap.get(subagent_id)
          if (existing) {
            newMap.set(subagent_id, {
              ...existing,
              status: subagentError ? 'error' : 'completed',
              progress: 100,
              completedAt: new Date().toISOString(),
              result,
              error: subagentError,
            })
          }
          return newMap
        })
        const existing = activeSubagents.get(subagent_id)
        addActivityEvent(
          'subagent_completed',
          `Subagent ${existing?.type || subagent_id} completed`,
          { phase: existing?.phase }
        )
      }

      // Handle model progress events
      if (message.event === 'model_progress') {
        const { model, progress, status, matches_found, top_score } = message.data
        updateModelProgress(model, progress, status, {
          matchesFound: matches_found,
          topScore: top_score,
        })

        if (status === 'running' && progress <= 10) {
          addActivityEvent('model_started', `Model ${model} processing...`, { model })
        }
        if (status === 'completed') {
          addActivityEvent('model_completed', `Model ${model} complete`, {
            model,
            matchesFound: matches_found,
            topScore: top_score,
          })
        }
        if (status === 'error') {
          addActivityEvent('error', `Model ${model} failed`, { model })
        }
      }

      // Handle match found events
      if (message.event === 'match_found') {
        const { tiger_id, confidence, model } = message.data
        addActivityEvent(
          'match_found',
          `Match found: Tiger ${tiger_id} (${(confidence * 100).toFixed(1)}%)`,
          { model, tigerId: tiger_id, confidence }
        )
      }
    },
    [addActivityEvent, initializeModelProgress, updateModelProgress, activeSubagents]
  )

  // Use the existing WebSocket hook
  const {
    isConnected: wsConnected,
    error: wsError,
    joinInvestigation,
    leaveInvestigation,
  } = useWebSocket({
    onMessage: handleWebSocketMessage,
    autoConnect: !!investigationId,
  })

  // Join/leave investigation WebSocket room when ID changes
  useEffect(() => {
    if (investigationId && wsConnected) {
      joinInvestigation(investigationId)
      return () => {
        leaveInvestigation(investigationId)
      }
    }
  }, [investigationId, wsConnected, joinInvestigation, leaveInvestigation])

  // Sync progress steps from polling data (backup for WebSocket)
  useEffect(() => {
    if (investigation?.steps) {
      console.log('Syncing progress from investigation data:', investigation)

      const stepsMap = new Map(
        investigation.steps.map((s) => [s.step_type, s])
      )

      setProgressSteps((prev) =>
        prev.map((step) => {
          const backendStep = stepsMap.get(step.phase as Investigation2Phase)
          if (backendStep) {
            const status: StepStatus =
              backendStep.status === 'completed' ? 'completed' :
              backendStep.status === 'running' ? 'running' :
              backendStep.status === 'error' ? 'error' :
              step.status

            return {
              ...step,
              status,
              data: backendStep.result,
              timestamp: backendStep.timestamp,
            }
          }
          return step
        })
      )
    }
  }, [investigation])

  // Update a single progress step
  const updateProgressStep = (
    phase: Investigation2Phase | string,
    status: StepStatus,
    data?: any
  ) => {
    setProgressSteps((prev) =>
      prev.map((step) =>
        step.phase === phase
          ? { ...step, status, timestamp: new Date().toISOString(), data }
          : step
      )
    )
  }

  // Update a single context field
  const updateContext = useCallback(
    (field: keyof InvestigationContextType, value: string) => {
      setContext((prev) => ({
        ...prev,
        [field]: value,
      }))
    },
    []
  )

  // Launch a new investigation
  const launchInvestigation = useCallback(async () => {
    if (!uploadedImage) {
      setError('Please upload a tiger image')
      return
    }

    setError(null)
    setProgressSteps([...INITIAL_PROGRESS_STEPS])
    setActiveSubagents(new Map())
    setModelProgress([])
    setActivityEvents([])

    try {
      const formData = new FormData()
      formData.append('image', uploadedImage)
      if (context.location) formData.append('location', context.location)
      if (context.date) formData.append('date', context.date)
      if (context.notes) formData.append('notes', context.notes)

      const result = await launchMutation(formData).unwrap()

      if (result.success) {
        setInvestigationId(result.investigation_id)
        addActivityEvent('info', 'Investigation launched', {
          investigationId: result.investigation_id,
        })
      } else {
        setError('Failed to launch investigation')
      }
    } catch (err: any) {
      setError(err.data?.detail || 'Failed to launch investigation')
      console.error('Launch error:', err)
    }
  }, [uploadedImage, context, launchMutation, addActivityEvent])

  // Reset investigation state
  const resetInvestigation = useCallback(() => {
    setInvestigationId(null)
    setUploadedImage(null)
    setImagePreview(null)
    setContext({ location: '', date: '', notes: '' })
    setProgressSteps([])
    setError(null)
    setActiveSubagents(new Map())
    setModelProgress([])
    setActivityEvents([])
  }, [])

  // Regenerate report with a different audience
  const regenerateReport = useCallback(
    async (audience: ReportAudience) => {
      if (!investigationId) {
        setError('No investigation ID available')
        return
      }

      try {
        await regenerateMutation({
          investigation_id: investigationId,
          audience,
        }).unwrap()
      } catch (err: any) {
        setError(err.data?.detail || 'Failed to regenerate report')
        console.error('Regenerate error:', err)
      }
    },
    [investigationId, regenerateMutation]
  )

  // Computed state
  const isCompleted =
    investigation?.status === 'completed' ||
    investigation?.steps?.some(
      (s) => s.step_type === 'complete' && s.status === 'completed'
    ) ||
    false

  const isInProgress =
    !!investigationId &&
    !!investigation?.status &&
    !isCompleted

  const completedModelsCount = useMemo(
    () => modelProgress.filter((m) => m.status === 'completed').length,
    [modelProgress]
  )

  const totalModelsCount = useMemo(() => modelProgress.length, [modelProgress])

  const isStripeAnalysisRunning = useMemo(
    () => progressSteps.find((s) => s.phase === 'stripe_analysis')?.status === 'running',
    [progressSteps]
  )

  const value: Investigation2ContextValue = {
    // State
    investigationId,
    investigation,
    progressSteps,
    isLaunching,
    uploadedImage,
    imagePreview,
    context,
    error,

    // WebSocket state
    wsConnected,
    wsError,

    // Subagent and model progress state
    activeSubagents,
    modelProgress,
    activityEvents,

    // Computed state
    isCompleted,
    isInProgress,
    completedModelsCount,
    totalModelsCount,
    isStripeAnalysisRunning,

    // Actions
    setInvestigationId,
    setUploadedImage,
    setImagePreview,
    setContext,
    updateContext,
    setError,
    launchInvestigation,
    resetInvestigation,
    regenerateReport,
  }

  return (
    <Investigation2Context.Provider value={value}>
      {children}
    </Investigation2Context.Provider>
  )
}

export default Investigation2Context

// Export types for use in other components
export type { SubagentInfo, ModelProgressInfo, ActivityEvent }

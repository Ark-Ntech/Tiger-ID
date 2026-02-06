import { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import { useAppSelector } from '../app/hooks'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

/**
 * Information about a running subagent.
 */
export interface SubagentInfo {
  id: string
  type: string
  phase: string
  status: 'running' | 'completed' | 'error'
  progress: number
  startedAt: string
  completedAt?: string
  result?: unknown
  error?: string
}

/**
 * Progress information for a single model in the ensemble.
 */
export interface ModelProgress {
  model: string
  progress: number
  status: 'pending' | 'running' | 'completed' | 'error'
  embeddings?: number
  processingTime?: number
  startedAt?: string
  completedAt?: string
  matchesFound?: number
  topScore?: number
  error?: string
}

/**
 * Return type for the useSubagentProgress hook.
 */
export interface UseSubagentProgressReturn {
  activeSubagents: Map<string, SubagentInfo>
  modelProgress: Record<string, ModelProgress>
  isConnected: boolean
  error: string | null
  // Computed values
  runningSubagentsCount: number
  completedSubagentsCount: number
  errorSubagentsCount: number
  completedModelsCount: number
  totalModelsCount: number
  overallModelProgress: number
  // Actions
  clearSubagents: () => void
  clearModelProgress: () => void
  resetAll: () => void
}

/**
 * Options for the useSubagentProgress hook.
 */
interface UseSubagentProgressOptions {
  /** Investigation ID to subscribe to. Required for WebSocket connection. */
  investigationId?: string | null
  /** Whether to auto-connect when investigationId is available. Default: true */
  autoConnect?: boolean
  /** Callback when a subagent spawns */
  onSubagentSpawned?: (info: SubagentInfo) => void
  /** Callback when a subagent completes */
  onSubagentCompleted?: (info: SubagentInfo) => void
  /** Callback when a subagent errors */
  onSubagentError?: (info: SubagentInfo) => void
  /** Callback when model progress updates */
  onModelProgress?: (progress: ModelProgress) => void
  /** Maximum reconnect attempts. Default: 5 */
  maxReconnectAttempts?: number
}

/**
 * The 6-model ReID ensemble for tiger re-identification.
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
 * Hook for subscribing to subagent WebSocket events and tracking model progress.
 *
 * This hook manages WebSocket connections for real-time updates during
 * Investigation 2.0 workflows, tracking both subagent execution and
 * individual model progress in the 6-model ReID ensemble.
 *
 * @example
 * ```tsx
 * const {
 *   activeSubagents,
 *   modelProgress,
 *   isConnected,
 *   completedModelsCount,
 *   overallModelProgress,
 * } = useSubagentProgress({
 *   investigationId: 'inv_123',
 *   onSubagentCompleted: (info) => console.log('Subagent done:', info.type),
 * })
 * ```
 */
export const useSubagentProgress = (
  options: UseSubagentProgressOptions = {}
): UseSubagentProgressReturn => {
  const {
    investigationId,
    autoConnect = true,
    onSubagentSpawned,
    onSubagentCompleted,
    onSubagentError,
    onModelProgress,
    maxReconnectAttempts = 5,
  } = options

  // Get auth token from Redux store
  const token = useAppSelector((state) => state.auth.token)

  // WebSocket ref and connection state
  const wsRef = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectAttemptsRef = useRef(0)

  // Subagent tracking state
  const [activeSubagents, setActiveSubagents] = useState<Map<string, SubagentInfo>>(new Map())

  // Model progress tracking state (using Record for easier lookup)
  const [modelProgress, setModelProgress] = useState<Record<string, ModelProgress>>({})

  // Store callbacks in refs to avoid recreating the WebSocket handler
  const callbacksRef = useRef({
    onSubagentSpawned,
    onSubagentCompleted,
    onSubagentError,
    onModelProgress,
  })

  // Update callbacks ref when they change
  useEffect(() => {
    callbacksRef.current = {
      onSubagentSpawned,
      onSubagentCompleted,
      onSubagentError,
      onModelProgress,
    }
  }, [onSubagentSpawned, onSubagentCompleted, onSubagentError, onModelProgress])

  /**
   * Initialize model progress with all 6 models as pending.
   */
  const initializeModelProgress = useCallback(() => {
    const initial: Record<string, ModelProgress> = {}
    for (const model of REID_MODELS) {
      initial[model] = {
        model,
        progress: 0,
        status: 'pending',
      }
    }
    setModelProgress(initial)
  }, [])

  /**
   * Update progress for a specific model.
   */
  const updateModelProgressState = useCallback(
    (
      model: string,
      progress: number,
      status: ModelProgress['status'],
      extras?: Partial<ModelProgress>
    ) => {
      setModelProgress((prev) => {
        const existing = prev[model]
        const now = new Date().toISOString()

        const updated: ModelProgress = {
          ...(existing || {}),
          model,
          progress,
          status,
          ...(status === 'running' && !existing?.startedAt ? { startedAt: now } : {}),
          ...(status === 'completed' ? { completedAt: now } : {}),
          ...extras,
        }

        // Trigger callback if provided
        if (callbacksRef.current.onModelProgress) {
          callbacksRef.current.onModelProgress(updated)
        }

        return {
          ...prev,
          [model]: updated,
        }
      })
    },
    []
  )

  /**
   * Handle incoming WebSocket messages.
   */
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data)
        console.log('[useSubagentProgress] WebSocket message:', message)

        // Handle subagent_spawned event
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

          if (callbacksRef.current.onSubagentSpawned) {
            callbacksRef.current.onSubagentSpawned(info)
          }
        }

        // Handle subagent_progress event
        if (message.event === 'subagent_progress') {
          const { subagent_id, progress, result } = message.data

          setActiveSubagents((prev) => {
            const newMap = new Map(prev)
            const existing = newMap.get(subagent_id)
            if (existing) {
              newMap.set(subagent_id, {
                ...existing,
                progress,
                ...(result !== undefined ? { result } : {}),
              })
            }
            return newMap
          })
        }

        // Handle subagent_completed event
        if (message.event === 'subagent_completed') {
          const { subagent_id, result, error: subagentError } = message.data
          const now = new Date().toISOString()

          setActiveSubagents((prev) => {
            const newMap = new Map(prev)
            const existing = newMap.get(subagent_id)
            if (existing) {
              const updated: SubagentInfo = {
                ...existing,
                status: subagentError ? 'error' : 'completed',
                progress: 100,
                completedAt: now,
                result,
                error: subagentError,
              }
              newMap.set(subagent_id, updated)

              // Trigger appropriate callback
              if (subagentError && callbacksRef.current.onSubagentError) {
                callbacksRef.current.onSubagentError(updated)
              } else if (!subagentError && callbacksRef.current.onSubagentCompleted) {
                callbacksRef.current.onSubagentCompleted(updated)
              }
            }
            return newMap
          })
        }

        // Handle subagent_error event (separate from completed with error)
        if (message.event === 'subagent_error') {
          const { subagent_id, error: subagentError } = message.data
          const now = new Date().toISOString()

          setActiveSubagents((prev) => {
            const newMap = new Map(prev)
            const existing = newMap.get(subagent_id)
            if (existing) {
              const updated: SubagentInfo = {
                ...existing,
                status: 'error',
                completedAt: now,
                error: subagentError,
              }
              newMap.set(subagent_id, updated)

              if (callbacksRef.current.onSubagentError) {
                callbacksRef.current.onSubagentError(updated)
              }
            }
            return newMap
          })
        }

        // Handle model_progress event
        if (message.event === 'model_progress') {
          const {
            model,
            progress,
            status,
            embeddings,
            processing_time,
            matches_found,
            top_score,
            error: modelError,
          } = message.data

          updateModelProgressState(model, progress, status, {
            embeddings,
            processingTime: processing_time,
            matchesFound: matches_found,
            topScore: top_score,
            error: modelError,
          })
        }

        // Handle phase events that might trigger model progress initialization
        if (message.event === 'phase_started' && message.data.phase === 'stripe_analysis') {
          initializeModelProgress()
        }
      } catch (err) {
        console.error('[useSubagentProgress] Error parsing WebSocket message:', err)
      }
    },
    [initializeModelProgress, updateModelProgressState]
  )

  /**
   * Connect to the WebSocket server.
   */
  const connect = useCallback(() => {
    if (!token) {
      setError('No authentication token available')
      return
    }

    if (!investigationId) {
      return
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      const ws = new WebSocket(`${WS_URL}/ws?token=${token}`)

      ws.onopen = () => {
        console.log('[useSubagentProgress] WebSocket connected')
        setIsConnected(true)
        setError(null)
        reconnectAttemptsRef.current = 0

        // Join the investigation room
        ws.send(
          JSON.stringify({
            type: 'join_investigation',
            investigation_id: investigationId,
          })
        )
      }

      ws.onmessage = handleMessage

      ws.onerror = (event) => {
        console.error('[useSubagentProgress] WebSocket error:', event)
        setError('WebSocket connection error')
      }

      ws.onclose = () => {
        console.log('[useSubagentProgress] WebSocket disconnected')
        setIsConnected(false)

        // Attempt to reconnect with exponential backoff
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000)
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current += 1
            connect()
          }, delay)
        } else {
          setError(`Failed to reconnect after ${maxReconnectAttempts} attempts`)
        }
      }

      wsRef.current = ws
    } catch (err) {
      console.error('[useSubagentProgress] Error creating WebSocket:', err)
      setError('Failed to create WebSocket connection')
    }
  }, [token, investigationId, handleMessage, maxReconnectAttempts])

  /**
   * Disconnect from the WebSocket server.
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      // Leave the investigation room before closing
      if (investigationId && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            type: 'leave_investigation',
            investigation_id: investigationId,
          })
        )
      }

      wsRef.current.close()
      wsRef.current = null
    }

    setIsConnected(false)
  }, [investigationId])

  /**
   * Clear all subagent tracking state.
   */
  const clearSubagents = useCallback(() => {
    setActiveSubagents(new Map())
  }, [])

  /**
   * Clear all model progress state.
   */
  const clearModelProgress = useCallback(() => {
    setModelProgress({})
  }, [])

  /**
   * Reset all state (subagents, model progress, error).
   */
  const resetAll = useCallback(() => {
    clearSubagents()
    clearModelProgress()
    setError(null)
  }, [clearSubagents, clearModelProgress])

  // Auto-connect effect
  useEffect(() => {
    if (autoConnect && token && investigationId) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [autoConnect, token, investigationId, connect, disconnect])

  // Computed values
  const runningSubagentsCount = useMemo(() => {
    let count = 0
    activeSubagents.forEach((info) => {
      if (info.status === 'running') count++
    })
    return count
  }, [activeSubagents])

  const completedSubagentsCount = useMemo(() => {
    let count = 0
    activeSubagents.forEach((info) => {
      if (info.status === 'completed') count++
    })
    return count
  }, [activeSubagents])

  const errorSubagentsCount = useMemo(() => {
    let count = 0
    activeSubagents.forEach((info) => {
      if (info.status === 'error') count++
    })
    return count
  }, [activeSubagents])

  const completedModelsCount = useMemo(() => {
    return Object.values(modelProgress).filter((m) => m.status === 'completed').length
  }, [modelProgress])

  const totalModelsCount = useMemo(() => {
    return Object.keys(modelProgress).length
  }, [modelProgress])

  const overallModelProgress = useMemo(() => {
    const models = Object.values(modelProgress)
    if (models.length === 0) return 0
    const totalProgress = models.reduce((sum, m) => sum + m.progress, 0)
    return Math.round(totalProgress / models.length)
  }, [modelProgress])

  return {
    activeSubagents,
    modelProgress,
    isConnected,
    error,
    // Computed values
    runningSubagentsCount,
    completedSubagentsCount,
    errorSubagentsCount,
    completedModelsCount,
    totalModelsCount,
    overallModelProgress,
    // Actions
    clearSubagents,
    clearModelProgress,
    resetAll,
  }
}

export default useSubagentProgress

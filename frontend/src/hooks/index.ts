/**
 * Custom React hooks for the Tiger ID application
 */

// Authentication hook
export { useAuth } from './useAuth'

// Count-up animation hook
export {
  useCountUp,
  type UseCountUpOptions,
  type UseCountUpReturn,
  type EasingType,
} from './useCountUp'

// Debounce hook for input handling
export { useDebounce } from './useDebounce'

// WebSocket hook for real-time updates
export { useWebSocket } from './useWebSocket'

// Subagent progress tracking hook
export {
  useSubagentProgress,
  type SubagentInfo,
  type ModelProgress,
  type UseSubagentProgressReturn,
} from './useSubagentProgress'

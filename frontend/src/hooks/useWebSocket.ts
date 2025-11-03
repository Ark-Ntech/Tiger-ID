import { useEffect, useRef, useState, useCallback } from 'react'
import { useAppDispatch, useAppSelector } from '../app/hooks'
import { addNotification } from '../features/notifications/notificationsSlice'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

interface UseWebSocketOptions {
  onMessage?: (message: any) => void
  onConnect?: () => void
  onDisconnect?: () => void
  autoConnect?: boolean
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    autoConnect = true,
  } = options

  const dispatch = useAppDispatch()
  const token = useAppSelector((state) => state.auth.token)
  
  const wsRef = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)

  const connect = useCallback(() => {
    if (!token) {
      setError('No authentication token available')
      return
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      const ws = new WebSocket(`${WS_URL}/ws?token=${token}`)

      ws.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        setError(null)
        setReconnectAttempts(0)
        onConnect?.()
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          
          // Handle different message types
          if (message.type === 'notification') {
            dispatch(addNotification({
              id: Date.now().toString(),
              ...message.data,
            }))
          }

          onMessage?.(message)
        } catch (err) {
          console.error('Error parsing WebSocket message:', err)
        }
      }

      ws.onerror = (event) => {
        console.error('WebSocket error:', event)
        setError('WebSocket connection error')
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
        onDisconnect?.()

        // Attempt to reconnect with exponential backoff
        if (reconnectAttempts < 5) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts((prev) => prev + 1)
            connect()
          }, delay)
        }
      }

      wsRef.current = ws
    } catch (err) {
      console.error('Error creating WebSocket:', err)
      setError('Failed to create WebSocket connection')
    }
  }, [token, onMessage, onConnect, onDisconnect, dispatch, reconnectAttempts])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setIsConnected(false)
  }, [])

  const send = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.error('WebSocket is not connected')
    }
  }, [])

  const joinInvestigation = useCallback((investigationId: string) => {
    send({
      type: 'join_investigation',
      investigation_id: investigationId,
    })
  }, [send])

  const leaveInvestigation = useCallback((investigationId: string) => {
    send({
      type: 'leave_investigation',
      investigation_id: investigationId,
    })
  }, [send])

  useEffect(() => {
    if (autoConnect && token) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [autoConnect, token])

  return {
    isConnected,
    error,
    connect,
    disconnect,
    send,
    joinInvestigation,
    leaveInvestigation,
  }
}


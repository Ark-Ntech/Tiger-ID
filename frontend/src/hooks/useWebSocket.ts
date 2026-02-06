import { useEffect, useRef, useState, useCallback } from 'react'
import { useAppDispatch, useAppSelector } from '../app/hooks'
import { addNotification } from '../features/notifications/notificationsSlice'

const WS_URL = import.meta.env.VITE_WS_URL || (import.meta.env.PROD ? `ws://${window.location.host}` : `ws://${window.location.host}`)

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
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const intentionalCloseRef = useRef(false)

  // Store callbacks in refs to avoid re-creating connect on every render
  const onMessageRef = useRef(onMessage)
  const onConnectRef = useRef(onConnect)
  const onDisconnectRef = useRef(onDisconnect)
  onMessageRef.current = onMessage
  onConnectRef.current = onConnect
  onDisconnectRef.current = onDisconnect

  const connect = useCallback(() => {
    if (!token) {
      setError('No authentication token available')
      return
    }

    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return
    }

    intentionalCloseRef.current = false

    try {
      const ws = new WebSocket(`${WS_URL}/ws?token=${token}`)

      ws.onopen = () => {
        // Ignore if this WebSocket was superseded by a newer one
        if (wsRef.current !== ws) return
        console.log('WebSocket connected')
        setIsConnected(true)
        setError(null)
        reconnectAttemptsRef.current = 0
        onConnectRef.current?.()
      }

      ws.onmessage = (event) => {
        // Ignore messages from a superseded WebSocket
        if (wsRef.current !== ws) return
        try {
          const message = JSON.parse(event.data)

          // Handle different message types
          if (message.type === 'notification') {
            dispatch(addNotification({
              id: Date.now().toString(),
              ...message.data,
            }))
          }

          onMessageRef.current?.(message)
        } catch (err) {
          console.error('Error parsing WebSocket message:', err)
        }
      }

      ws.onerror = () => {
        // Ignore errors from a superseded WebSocket
        if (wsRef.current !== ws) return
        console.error('WebSocket error')
        setError('WebSocket connection error')
      }

      ws.onclose = () => {
        // Only handle close for the CURRENT WebSocket instance.
        // If wsRef.current has already moved on to a newer WebSocket,
        // this is a stale close event (e.g., from React StrictMode
        // unmount/remount) and must be ignored to prevent orphaned
        // reconnect loops.
        if (wsRef.current !== ws) return

        console.log('WebSocket disconnected')
        setIsConnected(false)
        wsRef.current = null
        onDisconnectRef.current?.()

        // Only reconnect if the close was NOT intentional
        if (!intentionalCloseRef.current && reconnectAttemptsRef.current < 5) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000)
          reconnectAttemptsRef.current += 1
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, delay)
        }
      }

      wsRef.current = ws
    } catch (err) {
      console.error('Error creating WebSocket:', err)
      setError('Failed to create WebSocket connection')
    }
  }, [token, dispatch])

  const disconnect = useCallback(() => {
    intentionalCloseRef.current = true

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setIsConnected(false)
    reconnectAttemptsRef.current = 0
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
  }, [autoConnect, token, connect, disconnect])

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

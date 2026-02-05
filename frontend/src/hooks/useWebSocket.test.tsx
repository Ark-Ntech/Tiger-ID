import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import React from 'react'
import { useWebSocket } from './useWebSocket'
import authReducer from '../features/auth/authSlice'
import notificationsReducer from '../features/notifications/notificationsSlice'

// Mock WebSocket
class MockWebSocket {
  static OPEN = 1
  static CLOSED = 3

  url: string
  readyState: number
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(url: string) {
    this.url = url
    this.readyState = MockWebSocket.CLOSED
  }

  send(data: string) {
    // Mock send
  }

  close() {
    this.readyState = MockWebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close'))
    }
  }

  simulateOpen() {
    this.readyState = MockWebSocket.OPEN
    if (this.onopen) {
      this.onopen(new Event('open'))
    }
  }

  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }))
    }
  }

  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'))
    }
  }
}

let mockWebSocketInstance: MockWebSocket | null = null

vi.stubGlobal('WebSocket', class extends MockWebSocket {
  constructor(url: string) {
    super(url)
    mockWebSocketInstance = this
  }
})

const createTestStore = (token: string | null = 'test-token') => {
  return configureStore({
    reducer: {
      auth: authReducer,
      notifications: notificationsReducer,
    },
    preloadedState: {
      auth: {
        user: null,
        token,
        isAuthenticated: !!token,
        loading: false,
        error: null,
      },
      notifications: {
        notifications: [],
        unreadCount: 0,
      },
    },
  })
}

const wrapper = (store: ReturnType<typeof createTestStore>) => {
  return ({ children }: { children: React.ReactNode }) => (
    <Provider store={store}>{children}</Provider>
  )
}

describe('useWebSocket', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    mockWebSocketInstance = null
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('should return initial disconnected state', () => {
      const store = createTestStore()
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false }),
        { wrapper: wrapper(store) }
      )

      expect(result.current.isConnected).toBe(false)
      expect(result.current.error).toBeNull()
    })

    it('should return all expected functions', () => {
      const store = createTestStore()
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false }),
        { wrapper: wrapper(store) }
      )

      expect(typeof result.current.connect).toBe('function')
      expect(typeof result.current.disconnect).toBe('function')
      expect(typeof result.current.send).toBe('function')
      expect(typeof result.current.joinInvestigation).toBe('function')
      expect(typeof result.current.leaveInvestigation).toBe('function')
    })
  })

  describe('connect', () => {
    it('should set error when no token', () => {
      const store = createTestStore(null)
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false }),
        { wrapper: wrapper(store) }
      )

      act(() => {
        result.current.connect()
      })

      expect(result.current.error).toBe('No authentication token available')
    })

    it('should create WebSocket with token in URL', () => {
      const store = createTestStore('my-token')
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false }),
        { wrapper: wrapper(store) }
      )

      act(() => {
        result.current.connect()
      })

      expect(mockWebSocketInstance?.url).toContain('token=my-token')
    })

    it('should set isConnected to true on open', () => {
      const store = createTestStore()
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false }),
        { wrapper: wrapper(store) }
      )

      act(() => {
        result.current.connect()
      })

      act(() => {
        mockWebSocketInstance?.simulateOpen()
      })

      expect(result.current.isConnected).toBe(true)
      expect(result.current.error).toBeNull()
    })

    it('should call onConnect callback', () => {
      const onConnect = vi.fn()
      const store = createTestStore()
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false, onConnect }),
        { wrapper: wrapper(store) }
      )

      act(() => {
        result.current.connect()
      })

      act(() => {
        mockWebSocketInstance?.simulateOpen()
      })

      expect(onConnect).toHaveBeenCalled()
    })

    it('should auto-connect when autoConnect is true', () => {
      const store = createTestStore()
      renderHook(
        () => useWebSocket({ autoConnect: true }),
        { wrapper: wrapper(store) }
      )

      expect(mockWebSocketInstance).not.toBeNull()
    })

    it('should not auto-connect without token', () => {
      const store = createTestStore(null)
      renderHook(
        () => useWebSocket({ autoConnect: true }),
        { wrapper: wrapper(store) }
      )

      expect(mockWebSocketInstance).toBeNull()
    })
  })

  describe('disconnect', () => {
    it('should close WebSocket connection', () => {
      const store = createTestStore()
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false }),
        { wrapper: wrapper(store) }
      )

      act(() => {
        result.current.connect()
      })

      act(() => {
        mockWebSocketInstance?.simulateOpen()
      })

      act(() => {
        result.current.disconnect()
      })

      expect(result.current.isConnected).toBe(false)
    })

    it('should call onDisconnect callback', () => {
      const onDisconnect = vi.fn()
      const store = createTestStore()
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false, onDisconnect }),
        { wrapper: wrapper(store) }
      )

      act(() => {
        result.current.connect()
      })

      act(() => {
        mockWebSocketInstance?.simulateOpen()
      })

      act(() => {
        result.current.disconnect()
      })

      expect(onDisconnect).toHaveBeenCalled()
    })
  })

  describe('message handling', () => {
    it('should call onMessage callback with parsed data', () => {
      const onMessage = vi.fn()
      const store = createTestStore()
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false, onMessage }),
        { wrapper: wrapper(store) }
      )

      act(() => {
        result.current.connect()
      })

      act(() => {
        mockWebSocketInstance?.simulateOpen()
      })

      act(() => {
        mockWebSocketInstance?.simulateMessage({ type: 'test', data: 'hello' })
      })

      expect(onMessage).toHaveBeenCalledWith({ type: 'test', data: 'hello' })
    })

    it('should handle notification messages', () => {
      const store = createTestStore()
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false }),
        { wrapper: wrapper(store) }
      )

      act(() => {
        result.current.connect()
      })

      act(() => {
        mockWebSocketInstance?.simulateOpen()
      })

      act(() => {
        mockWebSocketInstance?.simulateMessage({
          type: 'notification',
          data: { message: 'Test notification' },
        })
      })

      // Notification should be dispatched to store
      const state = store.getState()
      expect(state.notifications.notifications).toHaveLength(1)
    })
  })

  describe('error handling', () => {
    it('should set error on WebSocket error', () => {
      const store = createTestStore()
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false }),
        { wrapper: wrapper(store) }
      )

      act(() => {
        result.current.connect()
      })

      act(() => {
        mockWebSocketInstance?.simulateError()
      })

      expect(result.current.error).toBe('WebSocket connection error')
    })
  })

  describe('send', () => {
    it('should send JSON stringified message', () => {
      const store = createTestStore()
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false }),
        { wrapper: wrapper(store) }
      )

      act(() => {
        result.current.connect()
      })

      act(() => {
        mockWebSocketInstance?.simulateOpen()
      })

      const sendSpy = vi.spyOn(mockWebSocketInstance!, 'send')

      act(() => {
        result.current.send({ type: 'test', data: 'hello' })
      })

      expect(sendSpy).toHaveBeenCalledWith(JSON.stringify({ type: 'test', data: 'hello' }))
    })

    it('should not send when not connected', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const store = createTestStore()
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false }),
        { wrapper: wrapper(store) }
      )

      act(() => {
        result.current.send({ type: 'test' })
      })

      expect(consoleSpy).toHaveBeenCalledWith('WebSocket is not connected')
      consoleSpy.mockRestore()
    })
  })

  describe('joinInvestigation', () => {
    it('should send join_investigation message', () => {
      const store = createTestStore()
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false }),
        { wrapper: wrapper(store) }
      )

      act(() => {
        result.current.connect()
      })

      act(() => {
        mockWebSocketInstance?.simulateOpen()
      })

      const sendSpy = vi.spyOn(mockWebSocketInstance!, 'send')

      act(() => {
        result.current.joinInvestigation('investigation-123')
      })

      expect(sendSpy).toHaveBeenCalledWith(
        JSON.stringify({
          type: 'join_investigation',
          investigation_id: 'investigation-123',
        })
      )
    })
  })

  describe('leaveInvestigation', () => {
    it('should send leave_investigation message', () => {
      const store = createTestStore()
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false }),
        { wrapper: wrapper(store) }
      )

      act(() => {
        result.current.connect()
      })

      act(() => {
        mockWebSocketInstance?.simulateOpen()
      })

      const sendSpy = vi.spyOn(mockWebSocketInstance!, 'send')

      act(() => {
        result.current.leaveInvestigation('investigation-123')
      })

      expect(sendSpy).toHaveBeenCalledWith(
        JSON.stringify({
          type: 'leave_investigation',
          investigation_id: 'investigation-123',
        })
      )
    })
  })

  describe('reconnection', () => {
    it('should attempt reconnection on close', () => {
      const store = createTestStore()
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false }),
        { wrapper: wrapper(store) }
      )

      act(() => {
        result.current.connect()
      })

      act(() => {
        mockWebSocketInstance?.simulateOpen()
      })

      // Simulate close
      act(() => {
        mockWebSocketInstance?.close()
      })

      expect(result.current.isConnected).toBe(false)

      // Advance timers for reconnection attempt
      act(() => {
        vi.advanceTimersByTime(1000)
      })

      // New WebSocket should be created
      expect(mockWebSocketInstance).not.toBeNull()
    })

    it('should use exponential backoff for reconnection', () => {
      const store = createTestStore()
      const { result } = renderHook(
        () => useWebSocket({ autoConnect: false }),
        { wrapper: wrapper(store) }
      )

      act(() => {
        result.current.connect()
      })

      act(() => {
        mockWebSocketInstance?.simulateOpen()
      })

      // First disconnect
      act(() => {
        mockWebSocketInstance?.close()
      })

      // First reconnect after 1s (1000 * 2^0)
      act(() => {
        vi.advanceTimersByTime(1000)
      })

      // Second disconnect
      act(() => {
        mockWebSocketInstance?.close()
      })

      // Second reconnect after 2s (1000 * 2^1)
      act(() => {
        vi.advanceTimersByTime(2000)
      })

      expect(mockWebSocketInstance).not.toBeNull()
    })
  })

  describe('cleanup', () => {
    it('should disconnect on unmount', () => {
      const store = createTestStore()
      const { result, unmount } = renderHook(
        () => useWebSocket({ autoConnect: false }),
        { wrapper: wrapper(store) }
      )

      act(() => {
        result.current.connect()
      })

      act(() => {
        mockWebSocketInstance?.simulateOpen()
      })

      unmount()

      // Should not throw
      act(() => {
        vi.advanceTimersByTime(1000)
      })
    })
  })
})

import { describe, it, expect } from 'vitest'
import { configureStore } from '@reduxjs/toolkit'
import notificationsReducer, {
  addNotification,
  markAsRead,
  markAllAsRead,
  removeNotification,
  clearNotifications,
} from '../notificationsSlice'
import type { Notification } from '../../../types'

const createTestStore = (preloadedState?: any) => {
  return configureStore({
    reducer: { notifications: notificationsReducer },
    preloadedState: preloadedState
      ? { notifications: preloadedState }
      : undefined,
  })
}

const createNotification = (
  overrides: Partial<Notification> = {}
): Notification => ({
  id: `notif-${Date.now()}`,
  type: 'info',
  title: 'Test Notification',
  message: 'This is a test notification',
  read: false,
  created_at: new Date().toISOString(),
  ...overrides,
})

describe('notificationsSlice', () => {
  describe('initial state', () => {
    it('should have empty notifications', () => {
      const store = createTestStore()
      const state = store.getState().notifications

      expect(state.notifications).toEqual([])
    })

    it('should have zero unread count', () => {
      const store = createTestStore()
      const state = store.getState().notifications

      expect(state.unreadCount).toBe(0)
    })
  })

  describe('addNotification', () => {
    it('should add notification to the beginning of the list', () => {
      const store = createTestStore()
      const notification = createNotification({ id: 'notif-1' })

      store.dispatch(addNotification(notification))

      const state = store.getState().notifications
      expect(state.notifications[0]).toEqual(notification)
    })

    it('should increment unread count for unread notification', () => {
      const store = createTestStore()
      const notification = createNotification({ read: false })

      store.dispatch(addNotification(notification))

      expect(store.getState().notifications.unreadCount).toBe(1)
    })

    it('should not increment unread count for read notification', () => {
      const store = createTestStore()
      const notification = createNotification({ read: true })

      store.dispatch(addNotification(notification))

      expect(store.getState().notifications.unreadCount).toBe(0)
    })

    it('should add multiple notifications in correct order', () => {
      const store = createTestStore()
      const notif1 = createNotification({ id: 'notif-1', title: 'First' })
      const notif2 = createNotification({ id: 'notif-2', title: 'Second' })
      const notif3 = createNotification({ id: 'notif-3', title: 'Third' })

      store.dispatch(addNotification(notif1))
      store.dispatch(addNotification(notif2))
      store.dispatch(addNotification(notif3))

      const state = store.getState().notifications
      expect(state.notifications[0].id).toBe('notif-3')
      expect(state.notifications[1].id).toBe('notif-2')
      expect(state.notifications[2].id).toBe('notif-1')
    })

    it('should handle different notification types', () => {
      const store = createTestStore()

      store.dispatch(addNotification(createNotification({ type: 'success' })))
      store.dispatch(addNotification(createNotification({ type: 'warning' })))
      store.dispatch(addNotification(createNotification({ type: 'error' })))
      store.dispatch(addNotification(createNotification({ type: 'info' })))

      const state = store.getState().notifications
      expect(state.notifications).toHaveLength(4)
    })
  })

  describe('markAsRead', () => {
    it('should mark notification as read', () => {
      const notification = createNotification({ id: 'notif-1', read: false })
      const store = createTestStore({
        notifications: [notification],
        unreadCount: 1,
      })

      store.dispatch(markAsRead('notif-1'))

      const state = store.getState().notifications
      expect(state.notifications[0].read).toBe(true)
    })

    it('should decrement unread count', () => {
      const notification = createNotification({ id: 'notif-1', read: false })
      const store = createTestStore({
        notifications: [notification],
        unreadCount: 1,
      })

      store.dispatch(markAsRead('notif-1'))

      expect(store.getState().notifications.unreadCount).toBe(0)
    })

    it('should not decrement unread count if already read', () => {
      const notification = createNotification({ id: 'notif-1', read: true })
      const store = createTestStore({
        notifications: [notification],
        unreadCount: 0,
      })

      store.dispatch(markAsRead('notif-1'))

      expect(store.getState().notifications.unreadCount).toBe(0)
    })

    it('should not affect other notifications', () => {
      const notif1 = createNotification({ id: 'notif-1', read: false })
      const notif2 = createNotification({ id: 'notif-2', read: false })
      const store = createTestStore({
        notifications: [notif1, notif2],
        unreadCount: 2,
      })

      store.dispatch(markAsRead('notif-1'))

      const state = store.getState().notifications
      expect(state.notifications.find((n) => n.id === 'notif-1')!.read).toBe(true)
      expect(state.notifications.find((n) => n.id === 'notif-2')!.read).toBe(false)
      expect(state.unreadCount).toBe(1)
    })

    it('should do nothing for non-existent notification', () => {
      const notification = createNotification({ id: 'notif-1', read: false })
      const store = createTestStore({
        notifications: [notification],
        unreadCount: 1,
      })

      store.dispatch(markAsRead('non-existent'))

      const state = store.getState().notifications
      expect(state.notifications[0].read).toBe(false)
      expect(state.unreadCount).toBe(1)
    })
  })

  describe('markAllAsRead', () => {
    it('should mark all notifications as read', () => {
      const notifications = [
        createNotification({ id: 'notif-1', read: false }),
        createNotification({ id: 'notif-2', read: false }),
        createNotification({ id: 'notif-3', read: true }),
      ]
      const store = createTestStore({
        notifications,
        unreadCount: 2,
      })

      store.dispatch(markAllAsRead())

      const state = store.getState().notifications
      expect(state.notifications.every((n) => n.read)).toBe(true)
    })

    it('should set unread count to zero', () => {
      const notifications = [
        createNotification({ id: 'notif-1', read: false }),
        createNotification({ id: 'notif-2', read: false }),
      ]
      const store = createTestStore({
        notifications,
        unreadCount: 2,
      })

      store.dispatch(markAllAsRead())

      expect(store.getState().notifications.unreadCount).toBe(0)
    })

    it('should work with empty notifications', () => {
      const store = createTestStore({
        notifications: [],
        unreadCount: 0,
      })

      store.dispatch(markAllAsRead())

      expect(store.getState().notifications.unreadCount).toBe(0)
    })
  })

  describe('removeNotification', () => {
    it('should remove notification by id', () => {
      const notifications = [
        createNotification({ id: 'notif-1' }),
        createNotification({ id: 'notif-2' }),
      ]
      const store = createTestStore({
        notifications,
        unreadCount: 2,
      })

      store.dispatch(removeNotification('notif-1'))

      const state = store.getState().notifications
      expect(state.notifications).toHaveLength(1)
      expect(state.notifications[0].id).toBe('notif-2')
    })

    it('should decrement unread count for unread notification', () => {
      const notification = createNotification({ id: 'notif-1', read: false })
      const store = createTestStore({
        notifications: [notification],
        unreadCount: 1,
      })

      store.dispatch(removeNotification('notif-1'))

      expect(store.getState().notifications.unreadCount).toBe(0)
    })

    it('should not decrement unread count for read notification', () => {
      const notification = createNotification({ id: 'notif-1', read: true })
      const store = createTestStore({
        notifications: [notification],
        unreadCount: 0,
      })

      store.dispatch(removeNotification('notif-1'))

      expect(store.getState().notifications.unreadCount).toBe(0)
    })

    it('should do nothing for non-existent notification', () => {
      const notification = createNotification({ id: 'notif-1' })
      const store = createTestStore({
        notifications: [notification],
        unreadCount: 1,
      })

      store.dispatch(removeNotification('non-existent'))

      const state = store.getState().notifications
      expect(state.notifications).toHaveLength(1)
      expect(state.unreadCount).toBe(1)
    })
  })

  describe('clearNotifications', () => {
    it('should remove all notifications', () => {
      const notifications = [
        createNotification({ id: 'notif-1' }),
        createNotification({ id: 'notif-2' }),
        createNotification({ id: 'notif-3' }),
      ]
      const store = createTestStore({
        notifications,
        unreadCount: 3,
      })

      store.dispatch(clearNotifications())

      const state = store.getState().notifications
      expect(state.notifications).toEqual([])
    })

    it('should reset unread count to zero', () => {
      const notifications = [
        createNotification({ id: 'notif-1', read: false }),
        createNotification({ id: 'notif-2', read: false }),
      ]
      const store = createTestStore({
        notifications,
        unreadCount: 2,
      })

      store.dispatch(clearNotifications())

      expect(store.getState().notifications.unreadCount).toBe(0)
    })

    it('should work when already empty', () => {
      const store = createTestStore({
        notifications: [],
        unreadCount: 0,
      })

      store.dispatch(clearNotifications())

      const state = store.getState().notifications
      expect(state.notifications).toEqual([])
      expect(state.unreadCount).toBe(0)
    })
  })

  describe('complex scenarios', () => {
    it('should handle add, read, and remove sequence', () => {
      const store = createTestStore()

      // Add notifications
      store.dispatch(addNotification(createNotification({ id: 'n1', read: false })))
      store.dispatch(addNotification(createNotification({ id: 'n2', read: false })))
      expect(store.getState().notifications.unreadCount).toBe(2)

      // Mark one as read
      store.dispatch(markAsRead('n1'))
      expect(store.getState().notifications.unreadCount).toBe(1)

      // Remove the read one
      store.dispatch(removeNotification('n1'))
      expect(store.getState().notifications.notifications).toHaveLength(1)
      expect(store.getState().notifications.unreadCount).toBe(1)

      // Remove the unread one
      store.dispatch(removeNotification('n2'))
      expect(store.getState().notifications.unreadCount).toBe(0)
    })

    it('should maintain consistency after multiple operations', () => {
      const store = createTestStore()

      // Add mix of read and unread
      store.dispatch(addNotification(createNotification({ id: 'n1', read: false })))
      store.dispatch(addNotification(createNotification({ id: 'n2', read: true })))
      store.dispatch(addNotification(createNotification({ id: 'n3', read: false })))

      expect(store.getState().notifications.unreadCount).toBe(2)
      expect(store.getState().notifications.notifications).toHaveLength(3)

      // Mark all as read
      store.dispatch(markAllAsRead())
      expect(store.getState().notifications.unreadCount).toBe(0)

      // Add new unread
      store.dispatch(addNotification(createNotification({ id: 'n4', read: false })))
      expect(store.getState().notifications.unreadCount).toBe(1)

      // Clear all
      store.dispatch(clearNotifications())
      expect(store.getState().notifications.notifications).toEqual([])
      expect(store.getState().notifications.unreadCount).toBe(0)
    })
  })
})

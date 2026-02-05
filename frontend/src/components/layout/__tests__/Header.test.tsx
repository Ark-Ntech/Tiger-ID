import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import { BrowserRouter } from 'react-router-dom'
import React from 'react'
import Header from '../Header'
import authReducer from '../../../features/auth/authSlice'
import notificationsReducer from '../../../features/notifications/notificationsSlice'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock useAuth hook
const mockLogout = vi.fn()
vi.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      user_id: '123',
      username: 'testuser',
      full_name: 'Test User',
      email: 'test@example.com',
      role: 'investigator',
    },
    isAuthenticated: true,
    loading: false,
    error: null,
    login: vi.fn(),
    logout: mockLogout,
    register: vi.fn(),
  }),
}))

// Mock icons
vi.mock('@heroicons/react/24/outline', () => ({
  BellIcon: () => <svg data-testid="bell-icon" />,
  MagnifyingGlassIcon: () => <svg data-testid="search-icon" />,
  UserCircleIcon: () => <svg data-testid="user-icon" />,
  Cog6ToothIcon: () => <svg data-testid="settings-icon" />,
  ArrowRightOnRectangleIcon: () => <svg data-testid="logout-icon" />,
  SunIcon: () => <svg data-testid="sun-icon" />,
  MoonIcon: () => <svg data-testid="moon-icon" />,
}))

// Mock headlessui
vi.mock('@headlessui/react', () => {
  const MockMenu = ({ children }: { children: React.ReactNode }) => (
    <div data-testid="menu">{children}</div>
  )

  MockMenu.Button = ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <button data-testid="menu-button" className={className}>{children}</button>
  )

  MockMenu.Items = ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="menu-items" className={className}>{children}</div>
  )

  MockMenu.Item = ({ children }: { children: (props: { active: boolean }) => React.ReactNode }) => (
    <div data-testid="menu-item">{children({ active: false })}</div>
  )

  const MockTransition = ({ children }: { children: React.ReactNode }) => (
    <div data-testid="transition">{children}</div>
  )

  MockTransition.Child = ({ children }: { children: React.ReactNode }) => (
    <div data-testid="transition-child">{children}</div>
  )

  return {
    Menu: MockMenu,
    Transition: MockTransition,
  }
})

const createTestStore = (notifications: any[] = []) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      notifications: notificationsReducer,
    },
    preloadedState: {
      auth: {
        user: {
          user_id: '123',
          username: 'testuser',
          email: 'test@example.com',
          role: 'investigator',
          is_active: true,
        },
        token: 'test-token',
        isAuthenticated: true,
        loading: false,
        error: null,
      },
      notifications: {
        notifications,
        unreadCount: notifications.filter((n: any) => !n.read).length,
      },
    },
  })
}

const renderHeader = (store = createTestStore()) => {
  return render(
    <Provider store={store}>
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    </Provider>
  )
}

describe('Header', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn(() => null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    }
    Object.defineProperty(window, 'localStorage', { value: localStorageMock })

    // Mock matchMedia
    Object.defineProperty(window, 'matchMedia', {
      value: vi.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    })
  })

  describe('rendering', () => {
    it('should render the header', () => {
      renderHeader()

      expect(screen.getByPlaceholderText(/Search investigations/)).toBeInTheDocument()
    })

    it('should display user information', () => {
      renderHeader()

      expect(screen.getByText('Test User')).toBeInTheDocument()
      expect(screen.getByText('investigator')).toBeInTheDocument()
    })
  })

  describe('search functionality', () => {
    it('should update search input value', () => {
      renderHeader()

      const searchInput = screen.getByPlaceholderText(/Search investigations/)
      fireEvent.change(searchInput, { target: { value: 'test search' } })

      expect(searchInput).toHaveValue('test search')
    })

    it('should navigate to search page on submit', () => {
      renderHeader()

      const searchInput = screen.getByPlaceholderText(/Search investigations/)
      fireEvent.change(searchInput, { target: { value: 'test query' } })
      fireEvent.submit(searchInput.closest('form')!)

      expect(mockNavigate).toHaveBeenCalledWith('/search?q=test%20query')
    })

    it('should not navigate for empty search', () => {
      renderHeader()

      const searchInput = screen.getByPlaceholderText(/Search investigations/)
      fireEvent.submit(searchInput.closest('form')!)

      expect(mockNavigate).not.toHaveBeenCalled()
    })

    it('should not navigate for search with only spaces', () => {
      renderHeader()

      const searchInput = screen.getByPlaceholderText(/Search investigations/)
      fireEvent.change(searchInput, { target: { value: '   ' } })
      fireEvent.submit(searchInput.closest('form')!)

      expect(mockNavigate).not.toHaveBeenCalled()
    })

    it('should not navigate for search with less than 2 characters', () => {
      renderHeader()

      const searchInput = screen.getByPlaceholderText(/Search investigations/)
      fireEvent.change(searchInput, { target: { value: 'a' } })
      fireEvent.submit(searchInput.closest('form')!)

      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })

  describe('dark mode toggle', () => {
    it('should render dark mode toggle button', () => {
      renderHeader()

      const toggleButton = screen.getByLabelText(/Switch to dark mode/)
      expect(toggleButton).toBeInTheDocument()
    })

    it('should toggle dark mode when clicked', () => {
      renderHeader()

      const toggleButton = screen.getByLabelText(/Switch to dark mode/)
      fireEvent.click(toggleButton)

      // Should update localStorage
      expect(localStorage.setItem).toHaveBeenCalled()
    })
  })

  describe('notifications', () => {
    it('should show notification count badge when there are unread notifications', () => {
      const notifications = [
        { id: '1', title: 'Test', message: 'Message', read: false },
        { id: '2', title: 'Test 2', message: 'Message 2', read: false },
      ]
      const store = createTestStore(notifications)

      renderHeader(store)

      expect(screen.getByText('2')).toBeInTheDocument()
    })

    it('should not show badge when no unread notifications', () => {
      const store = createTestStore([])
      renderHeader(store)

      // Badge should not be visible
      expect(screen.queryByText('9+')).not.toBeInTheDocument()
    })

    it('should display "9+" when more than 9 unread notifications', () => {
      const notifications = Array(10).fill(null).map((_, i) => ({
        id: `${i}`,
        title: `Test ${i}`,
        message: `Message ${i}`,
        read: false,
      }))
      const store = createTestStore(notifications)

      renderHeader(store)

      expect(screen.getByText('9+')).toBeInTheDocument()
    })

    it('should display "No notifications" when empty', () => {
      const store = createTestStore([])
      renderHeader(store)

      expect(screen.getByText('No notifications')).toBeInTheDocument()
    })

    it('should display notifications in dropdown', () => {
      const notifications = [
        { id: '1', title: 'Alert', message: 'New match found', read: false },
      ]
      const store = createTestStore(notifications)

      renderHeader(store)

      expect(screen.getByText('Alert')).toBeInTheDocument()
      expect(screen.getByText('New match found')).toBeInTheDocument()
    })
  })

  describe('user menu', () => {
    it('should display Settings option', () => {
      renderHeader()

      expect(screen.getByText('Settings')).toBeInTheDocument()
    })

    it('should display Logout option', () => {
      renderHeader()

      expect(screen.getByText('Logout')).toBeInTheDocument()
    })

    it('should call logout and navigate when Logout is clicked', async () => {
      renderHeader()

      const logoutButton = screen.getByText('Logout')
      fireEvent.click(logoutButton)

      expect(mockLogout).toHaveBeenCalled()
    })
  })

  describe('user display', () => {
    it('should show full name when available', () => {
      renderHeader()

      expect(screen.getByText('Test User')).toBeInTheDocument()
    })

    it('should show role', () => {
      renderHeader()

      expect(screen.getByText('investigator')).toBeInTheDocument()
    })
  })
})

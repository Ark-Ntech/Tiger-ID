import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import { BrowserRouter } from 'react-router-dom'
import PasswordReset from '../PasswordReset'
import authReducer from '../../features/auth/authSlice'
import { baseApi } from '../../app/api/baseApi'

// Mock react-router-dom
const mockNavigate = vi.fn()
const mockSearchParams = new URLSearchParams()
const mockSetSearchParams = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useSearchParams: () => [mockSearchParams, mockSetSearchParams],
  }
})

// Mock fetch for RTK Query
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

const createTestStore = (preloadedState?: any) => {
  return configureStore({
    reducer: {
      [baseApi.reducerPath]: baseApi.reducer,
      auth: authReducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(baseApi.middleware),
    preloadedState: preloadedState ? { auth: preloadedState } : undefined,
  })
}

const renderPasswordReset = (store = createTestStore()) => {
  return render(
    <Provider store={store}>
      <BrowserRouter>
        <PasswordReset />
      </BrowserRouter>
    </Provider>
  )
}

// Helper to mock successful fetch response
const mockFetchSuccess = (data: any = {}) => {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => data,
  })
}

// Helper to mock failed fetch response
const mockFetchError = (message: string, status = 400) => {
  mockFetch.mockResolvedValueOnce({
    ok: false,
    status,
    json: async () => ({ message, detail: message }),
  })
}

describe('PasswordReset', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSearchParams.delete('token')
    localStorageMock.getItem.mockReturnValue(null)
    mockFetch.mockReset()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.runOnlyPendingTimers()
    vi.useRealTimers()
  })

  describe('rendering - request password reset mode', () => {
    it('should render the request password reset form when no token', () => {
      renderPasswordReset()

      expect(screen.getByText('Forgot Password')).toBeInTheDocument()
      expect(screen.getByText('Enter your email to reset your password')).toBeInTheDocument()
    })

    it('should render email input field', () => {
      renderPasswordReset()

      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    })

    it('should render send reset link button', () => {
      renderPasswordReset()

      expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument()
    })

    it('should render back to login link', () => {
      renderPasswordReset()

      const loginLink = screen.getByText(/back to login/i)
      expect(loginLink).toBeInTheDocument()
      expect(loginLink.closest('a')).toHaveAttribute('href', '/login')
    })

    it('should render tiger emoji logo', () => {
      renderPasswordReset()

      expect(screen.getByText('🐅')).toBeInTheDocument()
    })
  })

  describe('rendering - confirm password reset mode', () => {
    beforeEach(() => {
      mockSearchParams.set('token', 'reset-token-123')
    })

    it('should render the confirm password reset form when token exists', () => {
      renderPasswordReset()

      expect(screen.getByRole('heading', { name: /reset password/i })).toBeInTheDocument()
      expect(screen.getByText('Enter your new password')).toBeInTheDocument()
    })

    it('should render new password input field', () => {
      renderPasswordReset()

      expect(screen.getByLabelText(/new password/i)).toBeInTheDocument()
    })

    it('should render confirm password input field', () => {
      renderPasswordReset()

      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    })

    it('should render reset password button', () => {
      renderPasswordReset()

      expect(screen.getByRole('button', { name: /^reset password$/i })).toBeInTheDocument()
    })

    it('should not render email field when token exists', () => {
      renderPasswordReset()

      expect(screen.queryByLabelText(/email address/i)).not.toBeInTheDocument()
    })
  })

  describe('form validation - request password reset', () => {
    it('should show error when submitting empty email', async () => {
      renderPasswordReset()

      const submitButton = screen.getByRole('button', { name: /send reset link/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument()
      })
    })

    it('should show error when email is invalid format', async () => {
      renderPasswordReset()

      const emailInput = screen.getByLabelText(/email address/i)
      fireEvent.change(emailInput, { target: { value: 'invalid-email' } })

      const submitButton = screen.getByRole('button', { name: /send reset link/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument()
      })
    })

    it('should not show error when email is valid', async () => {
      mockFetchSuccess({ message: 'Password reset email sent' })
      renderPasswordReset()

      const emailInput = screen.getByLabelText(/email address/i)
      fireEvent.change(emailInput, { target: { value: 'valid@example.com' } })

      const submitButton = screen.getByRole('button', { name: /send reset link/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.queryByText(/please enter a valid email address/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('form validation - confirm password reset', () => {
    beforeEach(() => {
      mockSearchParams.set('token', 'reset-token-123')
    })

    it('should show error when password is too short', async () => {
      renderPasswordReset()

      const newPasswordInput = screen.getByLabelText(/new password/i)
      fireEvent.change(newPasswordInput, { target: { value: 'short' } })

      const submitButton = screen.getByRole('button', { name: /^reset password$/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument()
      })
    })

    it('should show error when passwords do not match', async () => {
      renderPasswordReset()

      const newPasswordInput = screen.getByLabelText(/new password/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

      fireEvent.change(newPasswordInput, { target: { value: 'password123' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'different123' } })

      const submitButton = screen.getByRole('button', { name: /^reset password$/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/passwords don't match/i)).toBeInTheDocument()
      })
    })

    it('should not show error when passwords match and meet requirements', async () => {
      mockFetchSuccess({ message: 'Password reset successful' })
      renderPasswordReset()

      const newPasswordInput = screen.getByLabelText(/new password/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

      fireEvent.change(newPasswordInput, { target: { value: 'password123' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } })

      const submitButton = screen.getByRole('button', { name: /^reset password$/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.queryByText(/passwords don't match/i)).not.toBeInTheDocument()
        expect(screen.queryByText(/password must be at least 8 characters/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('request password reset flow', () => {
    it('should call API on valid submission', async () => {
      mockFetchSuccess({ message: 'Password reset email sent' })

      const store = createTestStore()
      render(
        <Provider store={store}>
          <BrowserRouter>
            <PasswordReset />
          </BrowserRouter>
        </Provider>
      )

      const emailInput = screen.getByLabelText(/email address/i)
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })

      const submitButton = screen.getByRole('button', { name: /send reset link/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/auth/password-reset/request'),
          expect.objectContaining({
            method: 'POST',
          })
        )
      })
    })

    it('should show success message after successful request', async () => {
      mockFetchSuccess({ message: 'Password reset email sent' })

      const store = createTestStore()
      renderPasswordReset(store)

      const emailInput = screen.getByLabelText(/email address/i)
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })

      const submitButton = screen.getByRole('button', { name: /send reset link/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/password reset email sent/i)).toBeInTheDocument()
      })
    })

    it('should hide form after successful request', async () => {
      mockFetchSuccess({ message: 'Password reset email sent' })

      const store = createTestStore()
      renderPasswordReset(store)

      const emailInput = screen.getByLabelText(/email address/i)
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })

      const submitButton = screen.getByRole('button', { name: /send reset link/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.queryByLabelText(/email address/i)).not.toBeInTheDocument()
      })
    })

    it('should show error message on failed request', async () => {
      mockFetchError('Email not found')

      const store = createTestStore()
      renderPasswordReset(store)

      const emailInput = screen.getByLabelText(/email address/i)
      fireEvent.change(emailInput, { target: { value: 'nonexistent@example.com' } })

      const submitButton = screen.getByRole('button', { name: /send reset link/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/email not found/i)).toBeInTheDocument()
      })
    })

    it('should show generic error message on network failure', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const store = createTestStore()
      renderPasswordReset(store)

      const emailInput = screen.getByLabelText(/email address/i)
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })

      const submitButton = screen.getByRole('button', { name: /send reset link/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/failed to send password reset email/i)).toBeInTheDocument()
      })
    })
  })

  describe('confirm password reset flow', () => {
    beforeEach(() => {
      mockSearchParams.set('token', 'reset-token-123')
    })

    it('should call API with token and password', async () => {
      mockFetchSuccess({ message: 'Password reset successful' })

      const store = createTestStore()
      render(
        <Provider store={store}>
          <BrowserRouter>
            <PasswordReset />
          </BrowserRouter>
        </Provider>
      )

      const newPasswordInput = screen.getByLabelText(/new password/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } })

      const submitButton = screen.getByRole('button', { name: /^reset password$/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/auth/password-reset/confirm'),
          expect.objectContaining({
            method: 'POST',
          })
        )
      })
    })

    it('should show success message after successful reset', async () => {
      mockFetchSuccess({ message: 'Password reset successful' })

      const store = createTestStore()
      renderPasswordReset(store)

      const newPasswordInput = screen.getByLabelText(/new password/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } })

      const submitButton = screen.getByRole('button', { name: /^reset password$/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/password reset successful/i)).toBeInTheDocument()
      })
    })

    it('should navigate to login after 3 seconds on success', async () => {
      mockFetchSuccess({ message: 'Password reset successful' })

      const store = createTestStore()
      renderPasswordReset(store)

      const newPasswordInput = screen.getByLabelText(/new password/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } })

      const submitButton = screen.getByRole('button', { name: /^reset password$/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/password reset successful/i)).toBeInTheDocument()
      })

      // Fast-forward time by 3 seconds
      vi.advanceTimersByTime(3000)

      expect(mockNavigate).toHaveBeenCalledWith('/login')
    })

    it('should hide form after successful reset', async () => {
      mockFetchSuccess({ message: 'Password reset successful' })

      const store = createTestStore()
      renderPasswordReset(store)

      const newPasswordInput = screen.getByLabelText(/new password/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } })

      const submitButton = screen.getByRole('button', { name: /^reset password$/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.queryByLabelText(/new password/i)).not.toBeInTheDocument()
      })
    })

    it('should show error message on failed reset', async () => {
      mockFetchError('Invalid or expired token')

      const store = createTestStore()
      renderPasswordReset(store)

      const newPasswordInput = screen.getByLabelText(/new password/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } })

      const submitButton = screen.getByRole('button', { name: /^reset password$/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/invalid or expired token/i)).toBeInTheDocument()
      })
    })

    it('should show generic error message on network failure', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const store = createTestStore()
      renderPasswordReset(store)

      const newPasswordInput = screen.getByLabelText(/new password/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } })

      const submitButton = screen.getByRole('button', { name: /^reset password$/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/failed to reset password/i)).toBeInTheDocument()
      })
    })

    it('should show error when token is missing', async () => {
      mockSearchParams.delete('token')

      const store = createTestStore()
      renderPasswordReset(store)

      // This should render the request form, not the confirm form
      expect(screen.queryByLabelText(/new password/i)).not.toBeInTheDocument()
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    })
  })

  describe('loading states', () => {
    it('should show loading state on request form submission', async () => {
      // Mock a delayed response
      mockFetch.mockImplementationOnce(() =>
        new Promise((resolve) =>
          setTimeout(() => resolve({
            ok: true,
            json: async () => ({ message: 'Success' }),
          }), 1000)
        )
      )

      const store = createTestStore()
      renderPasswordReset(store)

      const emailInput = screen.getByLabelText(/email address/i)
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })

      const submitButton = screen.getByRole('button', { name: /send reset link/i })
      fireEvent.click(submitButton)

      // Button should be disabled during loading
      await waitFor(() => {
        expect(submitButton).toBeDisabled()
      })
    })

    it('should show loading state on confirm form submission', async () => {
      mockSearchParams.set('token', 'reset-token-123')

      // Mock a delayed response
      mockFetch.mockImplementationOnce(() =>
        new Promise((resolve) =>
          setTimeout(() => resolve({
            ok: true,
            json: async () => ({ message: 'Success' }),
          }), 1000)
        )
      )

      const store = createTestStore()
      renderPasswordReset(store)

      const newPasswordInput = screen.getByLabelText(/new password/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } })

      const submitButton = screen.getByRole('button', { name: /^reset password$/i })
      fireEvent.click(submitButton)

      // Button should be disabled during loading
      await waitFor(() => {
        expect(submitButton).toBeDisabled()
      })
    })
  })

  describe('error clearing', () => {
    it('should clear error when submitting again', async () => {
      // First request fails
      mockFetchError('Email not found')

      const store = createTestStore()
      renderPasswordReset(store)

      const emailInput = screen.getByLabelText(/email address/i)
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })

      const submitButton = screen.getByRole('button', { name: /send reset link/i })

      // First submission - error
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/email not found/i)).toBeInTheDocument()
      })

      // Second request succeeds
      mockFetchSuccess({ message: 'Password reset email sent' })

      // Second submission - success
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.queryByText(/email not found/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('accessibility', () => {
    it('should have proper form labels for request form', () => {
      renderPasswordReset()

      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    })

    it('should have proper form labels for confirm form', () => {
      mockSearchParams.set('token', 'reset-token-123')
      renderPasswordReset()

      expect(screen.getByLabelText(/new password/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    })

    it('should have autocomplete attributes on email input', () => {
      renderPasswordReset()

      const emailInput = screen.getByLabelText(/email address/i)
      expect(emailInput).toHaveAttribute('autocomplete', 'email')
    })

    it('should have autocomplete attributes on password inputs', () => {
      mockSearchParams.set('token', 'reset-token-123')
      renderPasswordReset()

      const newPasswordInput = screen.getByLabelText(/new password/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

      expect(newPasswordInput).toHaveAttribute('autocomplete', 'new-password')
      expect(confirmPasswordInput).toHaveAttribute('autocomplete', 'new-password')
    })

    it('should have proper input types', () => {
      renderPasswordReset()

      const emailInput = screen.getByLabelText(/email address/i)
      expect(emailInput).toHaveAttribute('type', 'email')
    })

    it('should have password type for password inputs', () => {
      mockSearchParams.set('token', 'reset-token-123')
      renderPasswordReset()

      const newPasswordInput = screen.getByLabelText(/new password/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

      expect(newPasswordInput).toHaveAttribute('type', 'password')
      expect(confirmPasswordInput).toHaveAttribute('type', 'password')
    })
  })

  describe('UI elements', () => {
    it('should display correct heading based on mode', () => {
      const { rerender } = renderPasswordReset()
      expect(screen.getByRole('heading', { name: /forgot password/i })).toBeInTheDocument()

      mockSearchParams.set('token', 'reset-token-123')

      rerender(
        <Provider store={createTestStore()}>
          <BrowserRouter>
            <PasswordReset />
          </BrowserRouter>
        </Provider>
      )

      expect(screen.getByRole('heading', { name: /reset password/i })).toBeInTheDocument()
    })

    it('should display correct subheading based on mode', () => {
      const { rerender } = renderPasswordReset()
      expect(screen.getByText('Enter your email to reset your password')).toBeInTheDocument()

      mockSearchParams.set('token', 'reset-token-123')

      rerender(
        <Provider store={createTestStore()}>
          <BrowserRouter>
            <PasswordReset />
          </BrowserRouter>
        </Provider>
      )

      expect(screen.getByText('Enter your new password')).toBeInTheDocument()
    })

    it('should display correct success message based on mode', async () => {
      mockFetchSuccess({ message: 'Password reset email sent' })

      const store = createTestStore()
      renderPasswordReset(store)

      const emailInput = screen.getByLabelText(/email address/i)
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })

      const submitButton = screen.getByRole('button', { name: /send reset link/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/password reset email sent/i)).toBeInTheDocument()
      })
    })

    it('should display redirect message in confirm mode success', async () => {
      mockSearchParams.set('token', 'reset-token-123')
      mockFetchSuccess({ message: 'Password reset successful' })

      const store = createTestStore()
      renderPasswordReset(store)

      const newPasswordInput = screen.getByLabelText(/new password/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } })

      const submitButton = screen.getByRole('button', { name: /^reset password$/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/redirecting to login/i)).toBeInTheDocument()
      })
    })
  })
})

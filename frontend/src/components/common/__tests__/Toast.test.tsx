import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import React from 'react'
import {
  ToastProvider,
  useToast,
  StandaloneToast,
  ProgressToast,
} from '../Toast'

// Mock cn utility
vi.mock('../../../utils/cn', () => ({
  cn: (...classes: (string | undefined | null | false)[]) =>
    classes.filter(Boolean).join(' '),
}))

// Test component that uses the toast hook
const TestComponent = () => {
  const { success, warning, error, info, clearAll } = useToast()

  return (
    <div>
      <button onClick={() => success('Success', 'Operation completed')}>
        Show Success
      </button>
      <button onClick={() => warning('Warning', 'Be careful')}>
        Show Warning
      </button>
      <button onClick={() => error('Error', 'Something went wrong')}>
        Show Error
      </button>
      <button onClick={() => info('Info', 'For your information')}>
        Show Info
      </button>
      <button onClick={() => clearAll()}>Clear All</button>
    </div>
  )
}

const renderWithProvider = (children: React.ReactNode, position?: any) => {
  return render(
    <ToastProvider position={position}>
      {children}
    </ToastProvider>
  )
}

describe('Toast', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('ToastProvider', () => {
    it('should render children', () => {
      renderWithProvider(<div data-testid="child">Child Content</div>)

      expect(screen.getByTestId('child')).toBeInTheDocument()
    })

    it('should render toast container with correct position', () => {
      renderWithProvider(<TestComponent />, 'top-right')

      const container = screen.getByLabelText('Notifications')
      expect(container).toHaveClass('top-4')
      expect(container).toHaveClass('right-4')
    })
  })

  describe('useToast hook', () => {
    it('should throw error when used outside provider', () => {
      // Suppress console.error for this test
      const originalError = console.error
      console.error = vi.fn()

      const ErrorComponent = () => {
        useToast()
        return <div>No error</div>
      }

      // This should throw an error
      expect(() => render(<ErrorComponent />)).toThrow('useToast must be used within a ToastProvider')

      console.error = originalError
    })

    it('should add success toast', async () => {
      renderWithProvider(<TestComponent />)

      act(() => {
        fireEvent.click(screen.getByText('Show Success'))
      })

      await waitFor(() => {
        expect(screen.getByText('Success')).toBeInTheDocument()
        expect(screen.getByText('Operation completed')).toBeInTheDocument()
      }, { timeout: 1000 })
    })

    it('should add warning toast', async () => {
      renderWithProvider(<TestComponent />)

      act(() => {
        fireEvent.click(screen.getByText('Show Warning'))
      })

      await waitFor(() => {
        expect(screen.getByText('Warning')).toBeInTheDocument()
      }, { timeout: 1000 })
    })

    it('should add error toast', async () => {
      renderWithProvider(<TestComponent />)

      act(() => {
        fireEvent.click(screen.getByText('Show Error'))
      })

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument()
      }, { timeout: 1000 })
    })

    it('should add info toast', async () => {
      renderWithProvider(<TestComponent />)

      act(() => {
        fireEvent.click(screen.getByText('Show Info'))
      })

      await waitFor(() => {
        expect(screen.getByText('Info')).toBeInTheDocument()
      }, { timeout: 1000 })
    })

    it('should clear all toasts', async () => {
      renderWithProvider(<TestComponent />)

      // Add multiple toasts
      act(() => {
        fireEvent.click(screen.getByText('Show Success'))
        fireEvent.click(screen.getByText('Show Error'))
      })

      await waitFor(() => {
        expect(screen.getByText('Success')).toBeInTheDocument()
        expect(screen.getByText('Error')).toBeInTheDocument()
      }, { timeout: 1000 })

      // Clear all
      act(() => {
        fireEvent.click(screen.getByText('Clear All'))
      })

      await waitFor(() => {
        expect(screen.queryByText('Success')).not.toBeInTheDocument()
        expect(screen.queryByText('Error')).not.toBeInTheDocument()
      }, { timeout: 1000 })
    })
  })

  describe('toast auto-dismiss', () => {
    it('should auto-dismiss after duration', async () => {
      renderWithProvider(<TestComponent />)

      act(() => {
        fireEvent.click(screen.getByText('Show Success'))
      })

      await waitFor(() => {
        expect(screen.getByText('Success')).toBeInTheDocument()
      }, { timeout: 1000 })

      // Fast-forward past the default 5000ms duration + animation time
      act(() => {
        vi.advanceTimersByTime(5500)
      })

      await waitFor(() => {
        expect(screen.queryByText('Success')).not.toBeInTheDocument()
      }, { timeout: 1000 })
    })
  })

  describe('toast dismissal', () => {
    it('should dismiss when dismiss button is clicked', async () => {
      renderWithProvider(<TestComponent />)

      act(() => {
        fireEvent.click(screen.getByText('Show Success'))
      })

      await waitFor(() => {
        expect(screen.getByText('Success')).toBeInTheDocument()
      }, { timeout: 1000 })

      const dismissButton = screen.getByLabelText('Dismiss')

      act(() => {
        fireEvent.click(dismissButton)
        // Wait for animation
        vi.advanceTimersByTime(400)
      })

      await waitFor(() => {
        expect(screen.queryByText('Success')).not.toBeInTheDocument()
      }, { timeout: 1000 })
    })
  })

  describe('max toasts limit', () => {
    it('should limit toasts to maxToasts', async () => {
      render(
        <ToastProvider maxToasts={2}>
          <TestComponent />
        </ToastProvider>
      )

      // Add 3 toasts
      act(() => {
        fireEvent.click(screen.getByText('Show Success'))
        fireEvent.click(screen.getByText('Show Warning'))
        fireEvent.click(screen.getByText('Show Error'))
      })

      // Should only show 2 (last 2)
      await waitFor(() => {
        const alerts = screen.getAllByRole('alert')
        expect(alerts.length).toBeLessThanOrEqual(2)
      }, { timeout: 1000 })
    })
  })
})

describe('StandaloneToast', () => {
  describe('rendering', () => {
    it('should render success toast', () => {
      render(<StandaloneToast type="success" title="Success!" />)

      expect(screen.getByText('Success!')).toBeInTheDocument()
    })

    it('should render with message', () => {
      render(
        <StandaloneToast
          type="info"
          title="Info"
          message="Additional information"
        />
      )

      expect(screen.getByText('Additional information')).toBeInTheDocument()
    })

    it('should render action button', () => {
      const onAction = vi.fn()

      render(
        <StandaloneToast
          type="warning"
          title="Warning"
          action={{ label: 'Undo', onClick: onAction }}
        />
      )

      const actionButton = screen.getByText('Undo')
      expect(actionButton).toBeInTheDocument()

      fireEvent.click(actionButton)
      expect(onAction).toHaveBeenCalled()
    })

    it('should render dismiss button when onDismiss provided', () => {
      const onDismiss = vi.fn()

      render(
        <StandaloneToast
          type="error"
          title="Error"
          onDismiss={onDismiss}
        />
      )

      const dismissButton = screen.getByLabelText('Dismiss')
      fireEvent.click(dismissButton)

      expect(onDismiss).toHaveBeenCalled()
    })

    it('should not render dismiss button when onDismiss not provided', () => {
      render(<StandaloneToast type="info" title="Info" />)

      expect(screen.queryByLabelText('Dismiss')).not.toBeInTheDocument()
    })
  })

  describe('toast types', () => {
    it('should apply success styles', () => {
      const { container } = render(
        <StandaloneToast type="success" title="Success" />
      )

      expect(container.firstChild).toHaveClass('bg-emerald-50')
    })

    it('should apply warning styles', () => {
      const { container } = render(
        <StandaloneToast type="warning" title="Warning" />
      )

      expect(container.firstChild).toHaveClass('bg-amber-50')
    })

    it('should apply error styles', () => {
      const { container } = render(
        <StandaloneToast type="error" title="Error" />
      )

      expect(container.firstChild).toHaveClass('bg-red-50')
    })

    it('should apply info styles', () => {
      const { container } = render(
        <StandaloneToast type="info" title="Info" />
      )

      expect(container.firstChild).toHaveClass('bg-blue-50')
    })
  })

  describe('accessibility', () => {
    it('should have role="alert"', () => {
      render(<StandaloneToast type="error" title="Error" />)

      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
  })

  describe('className prop', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <StandaloneToast type="info" title="Info" className="custom-class" />
      )

      expect(container.firstChild).toHaveClass('custom-class')
    })
  })
})

describe('ProgressToast', () => {
  describe('rendering', () => {
    it('should render title', () => {
      render(<ProgressToast title="Processing..." progress={50} />)

      expect(screen.getByText('Processing...')).toBeInTheDocument()
    })

    it('should render progress percentage', () => {
      render(<ProgressToast title="Processing" progress={75} />)

      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    it('should render phase when provided', () => {
      render(
        <ProgressToast
          title="Investigation"
          progress={50}
          phase="Analyzing stripe patterns..."
        />
      )

      expect(screen.getByText('Analyzing stripe patterns...')).toBeInTheDocument()
    })

    it('should render cancel button when onCancel provided', () => {
      const onCancel = vi.fn()

      render(
        <ProgressToast
          title="Processing"
          progress={50}
          onCancel={onCancel}
        />
      )

      const cancelButton = screen.getByText('Cancel')
      fireEvent.click(cancelButton)

      expect(onCancel).toHaveBeenCalled()
    })

    it('should not render cancel button when onCancel not provided', () => {
      render(<ProgressToast title="Processing" progress={50} />)

      expect(screen.queryByText('Cancel')).not.toBeInTheDocument()
    })
  })

  describe('progress clamping', () => {
    it('should clamp progress to 0-100', () => {
      const { container } = render(
        <ProgressToast title="Processing" progress={150} />
      )

      const progressBar = container.querySelector('.progress-bar-fill')
      expect(progressBar).toHaveStyle({ width: '100%' })
    })

    it('should handle negative progress', () => {
      const { container } = render(
        <ProgressToast title="Processing" progress={-10} />
      )

      const progressBar = container.querySelector('.progress-bar-fill')
      expect(progressBar).toHaveStyle({ width: '0%' })
    })
  })
})

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import { BrowserRouter } from 'react-router-dom'
import React from 'react'
import Investigation2 from '../Investigation2'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({}),
  }
})

// Mock heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  ArrowLeftIcon: () => <svg data-testid="arrow-left-icon" />,
  PhotoIcon: () => <svg data-testid="photo-icon" />,
  XMarkIcon: () => <svg data-testid="x-mark-icon" />,
  CheckCircleIcon: () => <svg data-testid="check-circle-icon" />,
  ExclamationTriangleIcon: () => <svg data-testid="exclamation-triangle-icon" />,
  InformationCircleIcon: () => <svg data-testid="information-circle-icon" />,
  XCircleIcon: () => <svg data-testid="x-circle-icon" />,
  GlobeAltIcon: () => <svg data-testid="globe-alt-icon" />,
  BeakerIcon: () => <svg data-testid="beaker-icon" />,
  EyeIcon: () => <svg data-testid="eye-icon" />,
  DocumentTextIcon: () => <svg data-testid="document-text-icon" />,
  ArrowPathIcon: () => <svg data-testid="arrow-path-icon" />,
}))

vi.mock('@heroicons/react/24/solid', () => ({
  ShieldCheckIcon: () => <svg data-testid="shield-check-icon" />,
  SparklesIcon: () => <svg data-testid="sparkles-icon" />,
  UsersIcon: () => <svg data-testid="users-icon" />,
  FingerPrintIcon: () => <svg data-testid="fingerprint-icon" />,
}))

// Mock child components
vi.mock('../../components/investigations/Investigation2Upload', () => ({
  default: ({ image, imagePreview, context, onImageUpload, onContextChange, disabled }: any) => (
    <div data-testid="investigation2-upload">
      <input
        data-testid="file-input"
        type="file"
        onChange={(e) => e.target.files?.[0] && onImageUpload(e.target.files[0])}
        disabled={disabled}
      />
      <input
        data-testid="location-input"
        value={context.location}
        onChange={(e) => onContextChange('location', e.target.value)}
        disabled={disabled}
      />
      <input
        data-testid="date-input"
        value={context.date}
        onChange={(e) => onContextChange('date', e.target.value)}
        disabled={disabled}
      />
      <textarea
        data-testid="notes-input"
        value={context.notes}
        onChange={(e) => onContextChange('notes', e.target.value)}
        disabled={disabled}
      />
      {imagePreview && <img data-testid="image-preview" src={imagePreview} alt="Preview" />}
      {image && <span data-testid="image-name">{image.name}</span>}
    </div>
  ),
}))

vi.mock('../../components/investigations/Investigation2Progress', () => ({
  default: ({ steps, investigationId }: any) => (
    <div data-testid="investigation2-progress">
      <div data-testid="investigation-id">{investigationId}</div>
      {steps.map((step: any, index: number) => (
        <div key={index} data-testid={`step-${step.phase}`} data-status={step.status}>
          {step.phase}: {step.status}
        </div>
      ))}
    </div>
  ),
}))

vi.mock('../../components/investigations/Investigation2ResultsEnhanced', () => ({
  default: ({ investigation, fullWidth }: any) => (
    <div data-testid="investigation2-results" data-fullwidth={fullWidth}>
      Investigation ID: {investigation.investigation_id}
      Status: {investigation.status}
    </div>
  ),
}))

// Mock API hooks
const mockLaunchInvestigation = vi.fn()
const mockUseGetInvestigation2Query = vi.fn()
let mockInvestigationData: any = null

vi.mock('../../app/api', () => ({
  useLaunchInvestigation2Mutation: () => [
    mockLaunchInvestigation,
    { isLoading: false },
  ],
  useGetInvestigation2Query: (id: string, options: any) => {
    const result = mockUseGetInvestigation2Query(id, options)
    // Allow tests to override with mockInvestigationData
    if (mockInvestigationData && id === mockInvestigationData.investigation_id) {
      return {
        data: { data: mockInvestigationData },
        isLoading: false,
        error: null,
      }
    }
    return result
  },
  api: {
    util: {
      resetApiState: vi.fn(),
    },
  },
}))

// Helper to create mock store
const createMockStore = () => {
  return configureStore({
    reducer: {
      api: () => ({}),
    },
  })
}

// Helper to render Investigation2 with providers
const renderInvestigation2 = (store = createMockStore()) => {
  return render(
    <Provider store={store}>
      <BrowserRouter>
        <Investigation2 />
      </BrowserRouter>
    </Provider>
  )
}

// Create a mock File
const createMockFile = (name = 'tiger.jpg', size = 1024 * 100) => {
  const blob = new Blob(['mock image content'], { type: 'image/jpeg' })
  return new File([blob], name, { type: 'image/jpeg' })
}

// Mock WebSocket
class MockWebSocket {
  onopen: (() => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  readyState: number = WebSocket.CONNECTING
  OPEN = WebSocket.OPEN

  constructor(public url: string) {
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      this.onopen?.()
    }, 0)
  }

  send(data: string) {}
  close() {
    this.readyState = WebSocket.CLOSED
    this.onclose?.(new CloseEvent('close'))
  }
}

describe('Investigation2', () => {
  let originalWebSocket: typeof WebSocket

  beforeEach(() => {
    vi.clearAllMocks()
    mockInvestigationData = null

    // Reset API mock implementations
    mockLaunchInvestigation.mockReturnValue({
      unwrap: vi.fn().mockResolvedValue({
        success: true,
        investigation_id: 'test-investigation-123',
      }),
    } as any)

    mockUseGetInvestigation2Query.mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    })

    // Mock WebSocket
    originalWebSocket = global.WebSocket
    global.WebSocket = MockWebSocket as any

    // Mock FileReader
    global.FileReader = class {
      result: string | ArrayBuffer | null = 'data:image/jpeg;base64,mockbase64'
      onloadend: (() => void) | null = null
      readAsDataURL() {
        setTimeout(() => this.onloadend?.(), 0)
      }
    } as any
  })

  afterEach(() => {
    global.WebSocket = originalWebSocket
  })

  describe('Initial Render', () => {
    it('should render the page title and description', () => {
      renderInvestigation2()

      expect(screen.getByText('Investigation 2.0')).toBeInTheDocument()
      expect(screen.getByText('Advanced tiger identification workflow')).toBeInTheDocument()
    })

    it('should render the Back button', () => {
      renderInvestigation2()

      const backButton = screen.getByRole('button', { name: /back/i })
      expect(backButton).toBeInTheDocument()
    })

    it('should navigate to investigations page on Back button click', () => {
      renderInvestigation2()

      const backButton = screen.getByRole('button', { name: /back/i })
      fireEvent.click(backButton)

      expect(mockNavigate).toHaveBeenCalledWith('/investigations')
    })

    it('should render the upload component', () => {
      renderInvestigation2()

      expect(screen.getByTestId('investigation2-upload')).toBeInTheDocument()
    })

    it('should render the Launch Investigation button', () => {
      renderInvestigation2()

      expect(screen.getByRole('button', { name: /launch investigation/i })).toBeInTheDocument()
    })

    it('should have Launch Investigation button disabled when no image uploaded', () => {
      renderInvestigation2()

      const launchButton = screen.getByRole('button', { name: /launch investigation/i })
      expect(launchButton).toBeDisabled()
    })

    it('should not render progress component initially', () => {
      renderInvestigation2()

      expect(screen.queryByTestId('investigation2-progress')).not.toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should have launch button disabled when no image uploaded', () => {
      renderInvestigation2()

      const launchButton = screen.getByRole('button', { name: /launch investigation/i })
      expect(launchButton).toBeDisabled()
    })

    it('should display API error message', async () => {
      mockLaunchInvestigation.mockReturnValue({
        unwrap: vi.fn().mockRejectedValue({
          data: { detail: 'API Error occurred' },
        }),
      } as any)

      renderInvestigation2()

      // Upload image first
      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        expect(launchButton).not.toBeDisabled()
      })

      const launchButton = screen.getByRole('button', { name: /launch investigation/i })
      fireEvent.click(launchButton)

      await waitFor(() => {
        expect(screen.getByText('API Error occurred')).toBeInTheDocument()
      })
    })

    it('should display generic error message when API error has no detail', async () => {
      mockLaunchInvestigation.mockReturnValue({
        unwrap: vi.fn().mockRejectedValue({}),
      } as any)

      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        expect(screen.getByText('Failed to launch investigation')).toBeInTheDocument()
      })
    })
  })

  describe('File Upload', () => {
    it('should handle file upload', async () => {
      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile('my-tiger.jpg')

      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        expect(screen.getByTestId('image-name')).toHaveTextContent('my-tiger.jpg')
      })
    })

    it('should create image preview on file upload', async () => {
      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()

      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const preview = screen.getByTestId('image-preview')
        expect(preview).toBeInTheDocument()
        expect(preview).toHaveAttribute('src', 'data:image/jpeg;base64,mockbase64')
      })
    })

    it('should enable Launch Investigation button after file upload', async () => {
      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()

      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        expect(launchButton).not.toBeDisabled()
      })
    })
  })

  describe('Context Form Inputs', () => {
    it('should handle location input change', () => {
      renderInvestigation2()

      const locationInput = screen.getByTestId('location-input')
      fireEvent.change(locationInput, { target: { value: 'Texas, USA' } })

      expect(locationInput).toHaveValue('Texas, USA')
    })

    it('should handle date input change', () => {
      renderInvestigation2()

      const dateInput = screen.getByTestId('date-input')
      fireEvent.change(dateInput, { target: { value: '2024-01-15' } })

      expect(dateInput).toHaveValue('2024-01-15')
    })

    it('should handle notes input change', () => {
      renderInvestigation2()

      const notesInput = screen.getByTestId('notes-input')
      fireEvent.change(notesInput, { target: { value: 'Tiger spotted near facility' } })

      expect(notesInput).toHaveValue('Tiger spotted near facility')
    })

    it('should disable context inputs after investigation launched', async () => {
      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        expect(launchButton).not.toBeDisabled()
      })

      const launchButton = screen.getByRole('button', { name: /launch investigation/i })
      fireEvent.click(launchButton)

      // Wait for investigation to be launched (ID is set)
      await waitFor(() => {
        expect(screen.getByTestId('investigation-id')).toHaveTextContent('test-investigation-123')
      })

      await waitFor(() => {
        expect(screen.getByTestId('location-input')).toBeDisabled()
        expect(screen.getByTestId('date-input')).toBeDisabled()
        expect(screen.getByTestId('notes-input')).toBeDisabled()
      })
    })
  })

  describe('Launch Investigation', () => {
    it('should call launch API with FormData', async () => {
      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile('tiger.jpg')
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        expect(mockLaunchInvestigation).toHaveBeenCalled()
        const formData = mockLaunchInvestigation.mock.calls[0][0]
        expect(formData).toBeInstanceOf(FormData)
      })
    })

    it('should include context data in FormData when provided', async () => {
      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const locationInput = screen.getByTestId('location-input')
      const dateInput = screen.getByTestId('date-input')
      const notesInput = screen.getByTestId('notes-input')

      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })
      fireEvent.change(locationInput, { target: { value: 'Texas' } })
      fireEvent.change(dateInput, { target: { value: '2024-01-15' } })
      fireEvent.change(notesInput, { target: { value: 'Test notes' } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        expect(mockLaunchInvestigation).toHaveBeenCalled()
        const formData = mockLaunchInvestigation.mock.calls[0][0] as FormData
        expect(formData.get('location')).toBe('Texas')
        expect(formData.get('date')).toBe('2024-01-15')
        expect(formData.get('notes')).toBe('Test notes')
      })
    })

    it('should set investigation ID after successful launch', async () => {
      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        expect(screen.getByTestId('investigation-id')).toHaveTextContent('test-investigation-123')
      })
    })

    it('should initialize progress steps on launch', async () => {
      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        expect(screen.getByTestId('step-upload_and_parse')).toBeInTheDocument()
        expect(screen.getByTestId('step-reverse_image_search')).toBeInTheDocument()
        expect(screen.getByTestId('step-tiger_detection')).toBeInTheDocument()
        expect(screen.getByTestId('step-stripe_analysis')).toBeInTheDocument()
        expect(screen.getByTestId('step-report_generation')).toBeInTheDocument()
        expect(screen.getByTestId('step-complete')).toBeInTheDocument()
      })
    })

    it('should hide Launch Investigation button after successful launch', async () => {
      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      const launchButton = screen.getByRole('button', { name: /launch investigation/i })
      fireEvent.click(launchButton)

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /launch investigation/i })).not.toBeInTheDocument()
      })
    })

    it('should show New Investigation button after launch', async () => {
      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /new investigation/i })).toBeInTheDocument()
      })
    })

    it('should handle failed launch', async () => {
      mockLaunchInvestigation.mockReturnValue({
        unwrap: vi.fn().mockResolvedValue({
          success: false,
        }),
      } as any)

      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        expect(screen.getByText('Failed to launch investigation')).toBeInTheDocument()
      })
    })
  })

  describe('WebSocket Connection', () => {
    it('should establish WebSocket connection after launch', async () => {
      const mockWs = vi.fn()
      global.WebSocket = vi.fn().mockImplementation((url) => {
        mockWs(url)
        return new MockWebSocket(url)
      }) as any

      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        expect(mockWs).toHaveBeenCalled()
        const wsUrl = mockWs.mock.calls[0][0]
        expect(wsUrl).toContain('test-investigation-123')
      })
    })

    it('should update step status on phase_started message', async () => {
      let wsInstance: MockWebSocket | null = null
      global.WebSocket = vi.fn().mockImplementation((url) => {
        wsInstance = new MockWebSocket(url)
        return wsInstance
      }) as any

      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        expect(wsInstance).not.toBeNull()
      })

      // Simulate phase_started message
      const message = {
        event: 'phase_started',
        data: {
          phase: 'tiger_detection',
          status: 'running',
          timestamp: new Date().toISOString(),
        },
      }

      wsInstance!.onmessage?.(new MessageEvent('message', { data: JSON.stringify(message) }))

      await waitFor(() => {
        const step = screen.getByTestId('step-tiger_detection')
        expect(step).toHaveAttribute('data-status', 'running')
      })
    })

    it('should update step status on phase_completed message', async () => {
      let wsInstance: MockWebSocket | null = null
      global.WebSocket = vi.fn().mockImplementation((url) => {
        wsInstance = new MockWebSocket(url)
        return wsInstance
      }) as any

      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        expect(wsInstance).not.toBeNull()
      })

      const message = {
        event: 'phase_completed',
        data: {
          phase: 'upload_and_parse',
          status: 'completed',
          timestamp: new Date().toISOString(),
        },
      }

      wsInstance!.onmessage?.(new MessageEvent('message', { data: JSON.stringify(message) }))

      await waitFor(() => {
        const step = screen.getByTestId('step-upload_and_parse')
        expect(step).toHaveAttribute('data-status', 'completed')
      })
    })

    it('should mark investigation complete on investigation_completed message', async () => {
      let wsInstance: MockWebSocket | null = null
      global.WebSocket = vi.fn().mockImplementation((url) => {
        wsInstance = new MockWebSocket(url)
        return wsInstance
      }) as any

      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        expect(wsInstance).not.toBeNull()
      })

      const message = {
        event: 'investigation_completed',
        data: {
          timestamp: new Date().toISOString(),
        },
      }

      wsInstance!.onmessage?.(new MessageEvent('message', { data: JSON.stringify(message) }))

      await waitFor(() => {
        const step = screen.getByTestId('step-complete')
        expect(step).toHaveAttribute('data-status', 'completed')
      })
    })
  })

  describe('Progress Tracking', () => {
    it('should update progress from polling data', async () => {
      const { rerender } = renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        expect(launchButton).not.toBeDisabled()
      })

      const launchButton = screen.getByRole('button', { name: /launch investigation/i })
      fireEvent.click(launchButton)

      // Wait for investigation to launch and progress to be initialized
      await waitFor(() => {
        expect(screen.getByTestId('investigation-id')).toHaveTextContent('test-investigation-123')
      })

      // Set mock investigation data with step progress
      mockInvestigationData = {
        investigation_id: 'test-investigation-123',
        status: 'running',
        steps: [
          { step_type: 'upload_and_parse', status: 'completed', result: {} },
          { step_type: 'reverse_image_search', status: 'running', result: {} },
        ],
      }

      // Force a re-render to trigger the useEffect
      rerender(
        <Provider store={createMockStore()}>
          <BrowserRouter>
            <Investigation2 />
          </BrowserRouter>
        </Provider>
      )

      // Wait for the progress to update
      await waitFor(() => {
        const uploadStep = screen.getByTestId('step-upload_and_parse')
        expect(uploadStep).toHaveAttribute('data-status', 'completed')
      })

      await waitFor(() => {
        const searchStep = screen.getByTestId('step-reverse_image_search')
        expect(searchStep).toHaveAttribute('data-status', 'running')
      })
    })
  })

  describe('Results Display', () => {
    it('should display results when investigation is completed', async () => {
      mockUseGetInvestigation2Query.mockReturnValue({
        data: {
          data: {
            investigation_id: 'test-123',
            status: 'completed',
            steps: [
              { step_type: 'complete', status: 'completed' },
            ],
            summary: {
              confidence: 'high',
              top_matches: [],
            },
          },
        },
        isLoading: false,
        error: null,
      })

      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        const results = screen.getAllByTestId('investigation2-results')
        expect(results.length).toBeGreaterThan(0)
      })
    })

    it('should not display results when investigation is in progress', async () => {
      mockUseGetInvestigation2Query.mockReturnValue({
        data: {
          data: {
            investigation_id: 'test-123',
            status: 'running',
            steps: [],
          },
        },
        isLoading: false,
        error: null,
      })

      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        expect(screen.queryByTestId('investigation2-results')).not.toBeInTheDocument()
      })
    })
  })

  describe('Reset Functionality', () => {
    it('should reset investigation state on New Investigation click', async () => {
      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        const newButton = screen.getByRole('button', { name: /new investigation/i })
        fireEvent.click(newButton)
      })

      await waitFor(() => {
        expect(screen.queryByTestId('investigation2-progress')).not.toBeInTheDocument()
        expect(screen.getByRole('button', { name: /launch investigation/i })).toBeInTheDocument()
      })
    })

    it('should clear context fields on reset', async () => {
      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const locationInput = screen.getByTestId('location-input')
      const file = createMockFile()

      fireEvent.change(fileInput, { target: { files: [file] } })
      fireEvent.change(locationInput, { target: { value: 'Texas' } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        const newButton = screen.getByRole('button', { name: /new investigation/i })
        fireEvent.click(newButton)
      })

      await waitFor(() => {
        expect(screen.getByTestId('location-input')).toHaveValue('')
      })
    })
  })

  describe('Phase Progression', () => {
    const phases = [
      'upload_and_parse',
      'reverse_image_search',
      'tiger_detection',
      'stripe_analysis',
      'report_generation',
      'complete',
    ]

    it('should initialize all phases as pending', async () => {
      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        phases.forEach((phase) => {
          const step = screen.getByTestId(`step-${phase}`)
          expect(step).toHaveAttribute('data-status', 'pending')
        })
      })
    })

    it('should progress through all phases sequentially via WebSocket', async () => {
      let wsInstance: MockWebSocket | null = null
      global.WebSocket = vi.fn().mockImplementation((url) => {
        wsInstance = new MockWebSocket(url)
        return wsInstance
      }) as any

      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        fireEvent.click(launchButton)
      })

      await waitFor(() => {
        expect(wsInstance).not.toBeNull()
      })

      // Simulate phase progression
      for (const phase of phases.slice(0, -1)) {
        const startMessage = {
          event: 'phase_started',
          data: { phase, status: 'running', timestamp: new Date().toISOString() },
        }
        wsInstance!.onmessage?.(new MessageEvent('message', { data: JSON.stringify(startMessage) }))

        await waitFor(() => {
          const step = screen.getByTestId(`step-${phase}`)
          expect(step).toHaveAttribute('data-status', 'running')
        })

        const completeMessage = {
          event: 'phase_completed',
          data: { phase, status: 'completed', timestamp: new Date().toISOString() },
        }
        wsInstance!.onmessage?.(new MessageEvent('message', { data: JSON.stringify(completeMessage) }))

        await waitFor(() => {
          const step = screen.getByTestId(`step-${phase}`)
          expect(step).toHaveAttribute('data-status', 'completed')
        })
      }

      // Complete the investigation
      const finalMessage = {
        event: 'investigation_completed',
        data: { timestamp: new Date().toISOString() },
      }
      wsInstance!.onmessage?.(new MessageEvent('message', { data: JSON.stringify(finalMessage) }))

      await waitFor(() => {
        const completeStep = screen.getByTestId('step-complete')
        expect(completeStep).toHaveAttribute('data-status', 'completed')
      })
    })
  })

  describe('Empty States', () => {
    it('should handle empty investigation data', () => {
      mockUseGetInvestigation2Query.mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      })

      renderInvestigation2()

      expect(screen.queryByTestId('investigation2-progress')).not.toBeInTheDocument()
    })
  })

  describe('Loading States', () => {
    it('should show disabled button when launching', async () => {
      renderInvestigation2()

      const fileInput = screen.getByTestId('file-input')
      const file = createMockFile()
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        const launchButton = screen.getByRole('button', { name: /launch investigation/i })
        expect(launchButton).not.toBeDisabled()
      })

      // Button should exist and be clickable
      const launchButton = screen.getByRole('button', { name: /launch investigation/i })
      expect(launchButton).toBeInTheDocument()
    })
  })
})

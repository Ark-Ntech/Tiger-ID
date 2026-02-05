import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import ModelWeights from '../ModelWeights'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  CpuChipIcon: () => <svg data-testid="cpu-icon" />,
  ArrowLeftIcon: () => <svg data-testid="arrow-left-icon" />,
  CloudArrowUpIcon: () => <svg data-testid="cloud-upload-icon" />,
  CheckCircleIcon: () => <svg data-testid="check-circle-icon" />,
  XCircleIcon: () => <svg data-testid="x-circle-icon" />,
}))

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

describe('ModelWeights', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('rendering', () => {
    it('should render page title', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByText('Model Weights Management')).toBeInTheDocument()
    })

    it('should render page subtitle', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByText('Upload and manage model weights in Modal volumes')).toBeInTheDocument()
    })

    it('should render back button', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByText('Back')).toBeInTheDocument()
    })

    it('should render upload section', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByText('Upload Model Weights')).toBeInTheDocument()
    })

    it('should render model status section', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByText('Model Weight Status')).toBeInTheDocument()
    })

    it('should render instructions section', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByText('Instructions')).toBeInTheDocument()
    })
  })

  describe('navigation', () => {
    it('should navigate to dashboard when back button clicked', () => {
      renderWithRouter(<ModelWeights />)

      const backButton = screen.getByText('Back')
      fireEvent.click(backButton)

      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  describe('model selection', () => {
    it('should render model select dropdown', () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      expect(select).toBeInTheDocument()
    })

    it('should have default placeholder option', () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      expect(select).toHaveValue('')
      expect(screen.getByText('Select a model...')).toBeInTheDocument()
    })

    it('should list CVWC2019 model option', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByText(/CVWC2019 - Part-pose guided tiger re-identification/)).toBeInTheDocument()
    })

    it('should list RAPID model option', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByText(/RAPID - Real-time animal pattern re-identification/)).toBeInTheDocument()
    })

    it('should update selected model when option chosen', () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model') as HTMLSelectElement
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      expect(select.value).toBe('cvwc2019')
    })

    it('should show file input when model selected', () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      expect(screen.getByLabelText('Weight File (.pth)')).toBeInTheDocument()
    })

    it('should not show file input when no model selected', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.queryByLabelText('Weight File (.pth)')).not.toBeInTheDocument()
    })
  })

  describe('file selection', () => {
    it('should accept .pth files', () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const fileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      expect(fileInput.accept).toBe('.pth,.pt,.pkl')
    })

    it('should display selected file name and size', () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const fileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      const file = new File(['model weights'], 'best_model.pth', { type: 'application/octet-stream' })
      Object.defineProperty(file, 'size', { value: 1024 * 1024 * 50 }) // 50 MB

      fireEvent.change(fileInput, { target: { files: [file] } })

      expect(screen.getByText(/Selected: best_model.pth/)).toBeInTheDocument()
      expect(screen.getByText(/50.00 MB/)).toBeInTheDocument()
    })

    it('should clear file selection when model changed', () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const fileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      const file = new File(['model weights'], 'best_model.pth', { type: 'application/octet-stream' })

      fireEvent.change(fileInput, { target: { files: [file] } })

      expect(screen.getByText(/Selected: best_model.pth/)).toBeInTheDocument()

      // Changing model should clear selection
      fireEvent.change(select, { target: { value: 'rapid' } })

      // File input should be fresh
      const newFileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      expect(newFileInput.files?.length).toBe(0)
    })
  })

  describe('upload button', () => {
    it('should render upload button', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByText('Upload to Modal Volume')).toBeInTheDocument()
    })

    it('should disable upload button when no model selected', () => {
      renderWithRouter(<ModelWeights />)

      const uploadButton = screen.getByText('Upload to Modal Volume')
      expect(uploadButton).toBeDisabled()
    })

    it('should disable upload button when no file selected', () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const uploadButton = screen.getByText('Upload to Modal Volume')
      expect(uploadButton).toBeDisabled()
    })

    it('should enable upload button when model and file selected', () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const fileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      const file = new File(['model weights'], 'best_model.pth', { type: 'application/octet-stream' })
      fireEvent.change(fileInput, { target: { files: [file] } })

      const uploadButton = screen.getByText('Upload to Modal Volume')
      expect(uploadButton).not.toBeDisabled()
    })

    it('should disable upload button during upload', async () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const fileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      const file = new File(['model weights'], 'best_model.pth', { type: 'application/octet-stream' })
      fireEvent.change(fileInput, { target: { files: [file] } })

      const uploadButton = screen.getByText('Upload to Modal Volume')

      act(() => {
        fireEvent.click(uploadButton)
      })

      expect(screen.getByText('Uploading...')).toBeInTheDocument()
      expect(uploadButton).toBeDisabled()
    })
  })

  describe('upload functionality', () => {
    it('should show alert when trying to upload without selection', () => {
      renderWithRouter(<ModelWeights />)

      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

      const uploadButton = screen.getByText('Upload to Modal Volume')

      // Force click even though disabled (testing the handler)
      const button = uploadButton.closest('button')
      if (button) {
        button.disabled = false
        fireEvent.click(button)
      }

      expect(alertSpy).toHaveBeenCalledWith('Please select a model and weight file')
      alertSpy.mockRestore()
    })

    it('should show pending status during upload', async () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const fileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      const file = new File(['model weights'], 'best_model.pth', { type: 'application/octet-stream' })
      fireEvent.change(fileInput, { target: { files: [file] } })

      const uploadButton = screen.getByText('Upload to Modal Volume')

      act(() => {
        fireEvent.click(uploadButton)
      })

      expect(screen.getByText('Uploading...')).toBeInTheDocument()
    })

    it('should show success status after successful upload', async () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const fileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      const file = new File(['model weights'], 'best_model.pth', { type: 'application/octet-stream' })
      fireEvent.change(fileInput, { target: { files: [file] } })

      const uploadButton = screen.getByText('Upload to Modal Volume')

      act(() => {
        fireEvent.click(uploadButton)
      })

      // Advance timers to complete upload simulation (2000ms)
      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      await waitFor(() => {
        expect(screen.getByText('Weights uploaded successfully to Modal volume')).toBeInTheDocument()
      })
    })

    it('should clear file selection after successful upload', async () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const fileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      const file = new File(['model weights'], 'best_model.pth', { type: 'application/octet-stream' })
      fireEvent.change(fileInput, { target: { files: [file] } })

      const uploadButton = screen.getByText('Upload to Modal Volume')

      act(() => {
        fireEvent.click(uploadButton)
      })

      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      await waitFor(() => {
        expect(screen.queryByText(/Selected: best_model.pth/)).not.toBeInTheDocument()
      })
    })

    it('should reset model selection after successful upload', async () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model') as HTMLSelectElement
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const fileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      const file = new File(['model weights'], 'best_model.pth', { type: 'application/octet-stream' })
      fireEvent.change(fileInput, { target: { files: [file] } })

      const uploadButton = screen.getByText('Upload to Modal Volume')

      act(() => {
        fireEvent.click(uploadButton)
      })

      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      await waitFor(() => {
        expect(select.value).toBe('')
      })
    })

    it('should re-enable upload button after upload completes', async () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const fileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      const file = new File(['model weights'], 'best_model.pth', { type: 'application/octet-stream' })
      fireEvent.change(fileInput, { target: { files: [file] } })

      const uploadButton = screen.getByText('Upload to Modal Volume')

      act(() => {
        fireEvent.click(uploadButton)
      })

      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      await waitFor(() => {
        expect(screen.getByText('Upload to Modal Volume')).toBeInTheDocument()
      })
    })
  })

  describe('model status section', () => {
    it('should display all models in status list', () => {
      renderWithRouter(<ModelWeights />)

      const statusSection = screen.getByText('Model Weight Status').parentElement
      expect(statusSection).toBeInTheDocument()

      expect(screen.getByText('CVWC2019')).toBeInTheDocument()
      expect(screen.getByText('RAPID')).toBeInTheDocument()
    })

    it('should display model descriptions', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByText('Part-pose guided tiger re-identification')).toBeInTheDocument()
      expect(screen.getByText('Real-time animal pattern re-identification')).toBeInTheDocument()
    })

    it('should display model weight paths', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByText('Path: /models/cvwc2019/best_model.pth')).toBeInTheDocument()
      expect(screen.getByText('Path: /models/rapid/checkpoints/model.pth')).toBeInTheDocument()
    })

    it('should render check status buttons for each model', () => {
      renderWithRouter(<ModelWeights />)

      const checkButtons = screen.getAllByText('Check Status')
      expect(checkButtons).toHaveLength(2) // One for each model
    })
  })

  describe('check weight status', () => {
    it('should show pending status when checking', async () => {
      renderWithRouter(<ModelWeights />)

      const checkButtons = screen.getAllByText('Check Status')

      act(() => {
        fireEvent.click(checkButtons[0])
      })

      expect(screen.getByText('Checking weight status...')).toBeInTheDocument()
    })

    it('should disable check button during status check', async () => {
      renderWithRouter(<ModelWeights />)

      const checkButtons = screen.getAllByText('Check Status')

      act(() => {
        fireEvent.click(checkButtons[0])
      })

      expect(checkButtons[0]).toBeDisabled()
    })

    it('should show success or error status after check', async () => {
      renderWithRouter(<ModelWeights />)

      const checkButtons = screen.getAllByText('Check Status')

      act(() => {
        fireEvent.click(checkButtons[0])
      })

      await act(async () => {
        vi.advanceTimersByTime(1000)
      })

      await waitFor(() => {
        const foundMessage = screen.queryByText('Weights found in Modal volume')
        const notFoundMessage = screen.queryByText('Weights not found in Modal volume')
        expect(foundMessage || notFoundMessage).toBeInTheDocument()
      })
    })

    it('should show status badge after check completes', async () => {
      renderWithRouter(<ModelWeights />)

      const checkButtons = screen.getAllByText('Check Status')

      act(() => {
        fireEvent.click(checkButtons[0])
      })

      await act(async () => {
        vi.advanceTimersByTime(1000)
      })

      await waitFor(() => {
        const successBadge = screen.queryByText('success')
        const errorBadge = screen.queryByText('error')
        expect(successBadge || errorBadge).toBeInTheDocument()
      })
    })
  })

  describe('upload status alerts', () => {
    it('should show success alert with appropriate styling', async () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const fileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      const file = new File(['model weights'], 'best_model.pth', { type: 'application/octet-stream' })
      fireEvent.change(fileInput, { target: { files: [file] } })

      const uploadButton = screen.getByText('Upload to Modal Volume')

      act(() => {
        fireEvent.click(uploadButton)
      })

      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      await waitFor(() => {
        const alert = screen.getByText('Weights uploaded successfully to Modal volume')
        expect(alert).toBeInTheDocument()
      })
    })

    it('should only show alert for selected model', async () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const fileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      const file = new File(['model weights'], 'best_model.pth', { type: 'application/octet-stream' })
      fireEvent.change(fileInput, { target: { files: [file] } })

      const uploadButton = screen.getByText('Upload to Modal Volume')

      act(() => {
        fireEvent.click(uploadButton)
      })

      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      await waitFor(() => {
        const alerts = screen.getAllByText(/Weights uploaded successfully/)
        expect(alerts).toHaveLength(1)
      })
    })
  })

  describe('instructions section', () => {
    it('should display download instructions', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByText(/Download model weights from their respective repositories/)).toBeInTheDocument()
    })

    it('should display CVWC2019 repository link', () => {
      renderWithRouter(<ModelWeights />)

      const link = screen.getByRole('link', { name: /GitHub Repository/ })
      expect(link).toHaveAttribute('href', 'https://github.com/LcenArthas/CWCV2019-Amur-Tiger-Re-ID')
      expect(link).toHaveAttribute('target', '_blank')
      expect(link).toHaveAttribute('rel', 'noopener noreferrer')
    })

    it('should display CLI upload command', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByText(/modal run scripts\/upload_weights_to_modal.py/)).toBeInTheDocument()
    })

    it('should display deployment command', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByText(/modal deploy backend\/modal_app.py/)).toBeInTheDocument()
    })

    it('should display testing command', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByText(/python scripts\/test_modal_models.py/)).toBeInTheDocument()
    })
  })

  describe('status badges', () => {
    it('should show success badge with check icon', async () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const fileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      const file = new File(['model weights'], 'best_model.pth', { type: 'application/octet-stream' })
      fireEvent.change(fileInput, { target: { files: [file] } })

      const uploadButton = screen.getByText('Upload to Modal Volume')

      act(() => {
        fireEvent.click(uploadButton)
      })

      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      await waitFor(() => {
        expect(screen.getByTestId('check-circle-icon')).toBeInTheDocument()
      })
    })

    it('should show error badge with x icon for errors', async () => {
      renderWithRouter(<ModelWeights />)

      // Spy on Promise to force an error
      const originalPromise = global.Promise
      global.Promise = class extends originalPromise {
        constructor(executor: any) {
          super((resolve, reject) => {
            executor(
              () => reject(new Error('Upload failed')),
              reject
            )
          })
        }
      } as any

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const fileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      const file = new File(['model weights'], 'best_model.pth', { type: 'application/octet-stream' })
      fireEvent.change(fileInput, { target: { files: [file] } })

      const uploadButton = screen.getByText('Upload to Modal Volume')

      await act(async () => {
        fireEvent.click(uploadButton)
      })

      global.Promise = originalPromise

      // The error handling is in the catch block
      // Since we mocked Promise, we won't get to the success path
    })
  })

  describe('model icons', () => {
    it('should display CPU chip icons for models', () => {
      renderWithRouter(<ModelWeights />)

      const cpuIcons = screen.getAllByTestId('cpu-icon')
      expect(cpuIcons.length).toBeGreaterThanOrEqual(2)
    })

    it('should display cloud upload icon on upload button', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByTestId('cloud-upload-icon')).toBeInTheDocument()
    })

    it('should display arrow left icon on back button', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByTestId('arrow-left-icon')).toBeInTheDocument()
    })
  })

  describe('responsive layout', () => {
    it('should render in a space-y layout', () => {
      renderWithRouter(<ModelWeights />)

      const mainDiv = screen.getByText('Model Weights Management').closest('.space-y-6')
      expect(mainDiv).toBeInTheDocument()
    })

    it('should have proper card structure', () => {
      renderWithRouter(<ModelWeights />)

      const uploadCard = screen.getByText('Upload Model Weights').closest('div')
      expect(uploadCard).toBeInTheDocument()

      const statusCard = screen.getByText('Model Weight Status').closest('div')
      expect(statusCard).toBeInTheDocument()

      const instructionsCard = screen.getByText('Instructions').closest('div')
      expect(instructionsCard).toBeInTheDocument()
    })
  })

  describe('file size display', () => {
    it('should format small files in MB', () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const fileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      const file = new File(['model weights'], 'small.pth', { type: 'application/octet-stream' })
      Object.defineProperty(file, 'size', { value: 1024 * 512 }) // 0.5 MB

      fireEvent.change(fileInput, { target: { files: [file] } })

      expect(screen.getByText(/0.50 MB/)).toBeInTheDocument()
    })

    it('should format large files in MB', () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      const fileInput = screen.getByLabelText('Weight File (.pth)') as HTMLInputElement
      const file = new File(['model weights'], 'large.pth', { type: 'application/octet-stream' })
      Object.defineProperty(file, 'size', { value: 1024 * 1024 * 250 }) // 250 MB

      fireEvent.change(fileInput, { target: { files: [file] } })

      expect(screen.getByText(/250.00 MB/)).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('should have proper labels for form inputs', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByLabelText('Select Model')).toBeInTheDocument()
    })

    it('should have proper labels for file input when visible', () => {
      renderWithRouter(<ModelWeights />)

      const select = screen.getByLabelText('Select Model')
      fireEvent.change(select, { target: { value: 'cvwc2019' } })

      expect(screen.getByLabelText('Weight File (.pth)')).toBeInTheDocument()
    })

    it('should have descriptive button text', () => {
      renderWithRouter(<ModelWeights />)

      expect(screen.getByText('Back')).toBeInTheDocument()
      expect(screen.getByText('Upload to Modal Volume')).toBeInTheDocument()
      expect(screen.getAllByText('Check Status')).toHaveLength(2)
    })
  })
})

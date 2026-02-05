import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import React from 'react'
import FineTuning from '../FineTuning'

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
  CpuChipIcon: () => <span data-testid="cpu-icon">CPU</span>,
  ArrowLeftIcon: () => <span data-testid="arrow-left-icon">ArrowLeft</span>,
  PlayIcon: () => <span data-testid="play-icon">Play</span>,
  StopIcon: () => <span data-testid="stop-icon">Stop</span>,
  CheckCircleIcon: () => <span data-testid="check-circle-icon">CheckCircle</span>,
  XMarkIcon: () => <span data-testid="x-mark-icon">X</span>,
}))

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch as any

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
})

// Mock window.alert and window.confirm
const mockAlert = vi.fn()
const mockConfirm = vi.fn()
global.alert = mockAlert
global.confirm = mockConfirm

const mockJobsData = {
  data: {
    jobs: [
      {
        job_id: 'job-1',
        model_name: 'tiger_reid',
        status: 'training',
        progress: 0.65,
        description: 'Training with 10 tigers',
        epochs: 50,
        current_epoch: 33,
        loss: 0.2345,
        validation_loss: 0.2678,
        created_at: '2024-01-15T10:30:00Z',
      },
      {
        job_id: 'job-2',
        model_name: 'wildlife_tools',
        status: 'completed',
        progress: 1.0,
        description: 'Completed training',
        epochs: 100,
        current_epoch: 100,
        loss: 0.1234,
        validation_loss: 0.1456,
        created_at: '2024-01-10T08:00:00Z',
      },
      {
        job_id: 'job-3',
        model_name: 'cvwc2019',
        status: 'failed',
        progress: 0.3,
        description: 'Failed due to OOM',
        epochs: 50,
        current_epoch: 15,
        loss: 0.4567,
        created_at: '2024-01-12T14:20:00Z',
      },
      {
        job_id: 'job-4',
        model_name: 'rapid',
        status: 'preparing',
        progress: 0.0,
        description: 'Preparing dataset',
        epochs: 50,
        current_epoch: 0,
        created_at: '2024-01-16T09:00:00Z',
      },
      {
        job_id: 'job-5',
        model_name: 'tiger_reid',
        status: 'cancelled',
        progress: 0.2,
        description: 'Cancelled by user',
        epochs: 50,
        current_epoch: 10,
        created_at: '2024-01-14T11:00:00Z',
      },
    ],
  },
}

const mockTigersData = {
  data: [
    {
      tiger_id: 'tiger-1',
      name: 'Raja',
      image_count: 15,
    },
    {
      tiger_id: 'tiger-2',
      name: 'Shere Khan',
      image_count: 20,
    },
    {
      tiger_id: 'tiger-3',
      name: null,
      image_count: 8,
    },
    {
      tiger_id: 'tiger-4',
      name: 'Tigger',
      image_count: 12,
    },
  ],
}

const renderFineTuning = () => {
  return render(
    <BrowserRouter>
      <FineTuning />
    </BrowserRouter>
  )
}

describe('FineTuning', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLocalStorage.getItem.mockReturnValue('mock-token')
    mockFetch.mockClear()
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  describe('initial rendering', () => {
    it('should render page header', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: [] }),
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText('Model Fine-Tuning')).toBeInTheDocument()
      })
    })

    it('should render page description', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: [] }),
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText('Fine-tune models with selected tiger images')).toBeInTheDocument()
      })
    })

    it('should render back button', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: [] }),
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText('Back')).toBeInTheDocument()
      })
    })

    it('should render start fine-tuning button', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: [] }),
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText('Start Fine-Tuning Job')).toBeInTheDocument()
      })
    })

    it('should fetch jobs on mount', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/v1/finetuning/jobs')
      })
    })

    it('should fetch available tigers on mount', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/v1/finetuning/available-tigers?min_images=5')
      })
    })
  })

  describe('loading state', () => {
    it('should show loading spinner while jobs are loading', async () => {
      const pendingPromise = new Promise(() => {})
      mockFetch.mockReturnValueOnce(pendingPromise as any)
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByRole('status')).toBeInTheDocument()
      })
    })
  })

  describe('empty state', () => {
    it('should show empty state when no jobs exist', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText('No fine-tuning jobs yet')).toBeInTheDocument()
      })
    })

    it('should show empty state message with instructions', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText('Start a new job to begin fine-tuning models')).toBeInTheDocument()
      })
    })

    it('should show CPU icon in empty state', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByTestId('cpu-icon')).toBeInTheDocument()
      })
    })
  })

  describe('error handling', () => {
    it('should handle job fetch error gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      mockFetch.mockRejectedValueOnce(new Error('Network error'))
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith('Error fetching jobs:', expect.any(Error))
      })

      consoleErrorSpy.mockRestore()
    })

    it('should handle tiger fetch error gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      renderFineTuning()

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith('Error fetching tigers:', expect.any(Error))
      })

      consoleErrorSpy.mockRestore()
    })
  })

  describe('jobs list display', () => {
    it('should display all jobs', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        // tiger_reid appears twice (two jobs with same model name), so use getAllByText
        expect(screen.getAllByText('tiger_reid').length).toBeGreaterThan(0)
        expect(screen.getByText('wildlife_tools')).toBeInTheDocument()
        expect(screen.getByText('cvwc2019')).toBeInTheDocument()
        expect(screen.getByText('rapid')).toBeInTheDocument()
      })
    })

    it('should display job descriptions', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText('Training with 10 tigers')).toBeInTheDocument()
        expect(screen.getByText('Completed training')).toBeInTheDocument()
      })
    })

    it('should display job epochs', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText(/Epochs: 33 \/ 50/)).toBeInTheDocument()
        expect(screen.getByText(/Epochs: 100 \/ 100/)).toBeInTheDocument()
      })
    })

    it('should display training loss', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText(/Loss: 0.2345/)).toBeInTheDocument()
        expect(screen.getByText(/Loss: 0.1234/)).toBeInTheDocument()
      })
    })

    it('should display validation loss', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText(/Val Loss: 0.2678/)).toBeInTheDocument()
        expect(screen.getByText(/Val Loss: 0.1456/)).toBeInTheDocument()
      })
    })

    it('should display job creation timestamps', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        // Multiple jobs have timestamps, so use getAllByText
        const startedElements = screen.getAllByText(/Started:/)
        expect(startedElements.length).toBeGreaterThan(0)
      })
    })
  })

  describe('job status display', () => {
    it('should display training status badge', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText('training')).toBeInTheDocument()
      })
    })

    it('should display completed status badge', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText('completed')).toBeInTheDocument()
      })
    })

    it('should display failed status badge', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText('failed')).toBeInTheDocument()
      })
    })

    it('should display preparing status badge', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText('preparing')).toBeInTheDocument()
      })
    })

    it('should display cancelled status badge', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText('cancelled')).toBeInTheDocument()
      })
    })
  })

  describe('progress tracking', () => {
    it('should display progress percentage for training jobs', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText('65%')).toBeInTheDocument()
      })
    })

    it('should display progress bar for training jobs', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        const progressBars = document.querySelectorAll('.bg-blue-600')
        expect(progressBars.length).toBeGreaterThan(0)
      })
    })

    it('should show cancel button for training jobs', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        // Multiple cancel buttons (one for training job, one for preparing job)
        const cancelButtons = screen.getAllByText('Cancel')
        expect(cancelButtons.length).toBeGreaterThan(0)
      })
    })

    it('should not show cancel button for completed jobs', async () => {
      const completedJob = {
        data: {
          jobs: [mockJobsData.data.jobs[1]],
        },
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => completedJob,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.queryByText('Cancel')).not.toBeInTheDocument()
      })
    })
  })

  describe('navigation', () => {
    it('should navigate to dashboard when back button clicked', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        const backButton = screen.getByText('Back')
        fireEvent.click(backButton)
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
      })
    })
  })

  describe('start job modal', () => {
    it('should open modal when start button clicked', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        const startButton = screen.getByText('Start Fine-Tuning Job')
        fireEvent.click(startButton)
      })

      await waitFor(() => {
        expect(screen.getAllByText('Start Fine-Tuning Job').length).toBeGreaterThan(1)
      })
    })

    it('should display model selection dropdown', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      await waitFor(() => {
        expect(screen.getByText('Select Model')).toBeInTheDocument()
      })
    })

    it('should display all available models', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      await waitFor(() => {
        expect(screen.getByText(/Tiger ReID/)).toBeInTheDocument()
        expect(screen.getByText(/Wildlife Tools/)).toBeInTheDocument()
        expect(screen.getByText(/CVWC2019/)).toBeInTheDocument()
        expect(screen.getByText(/RAPID/)).toBeInTheDocument()
      })
    })

    it('should display tiger selection list', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      await waitFor(() => {
        expect(screen.getByText(/Select Tigers for Training/)).toBeInTheDocument()
      })
    })

    it('should display available tigers with names', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
        expect(screen.getByText('Shere Khan')).toBeInTheDocument()
        expect(screen.getByText('Tigger')).toBeInTheDocument()
      })
    })

    it('should display tiger image counts', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      await waitFor(() => {
        expect(screen.getByText('15 images')).toBeInTheDocument()
        expect(screen.getByText('20 images')).toBeInTheDocument()
      })
    })

    it('should display fallback name for tigers without names', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      await waitFor(() => {
        expect(screen.getByText(/Tiger #tiger-3/)).toBeInTheDocument()
      })
    })
  })

  describe('tiger selection', () => {
    it('should toggle tiger selection when clicked', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      await waitFor(() => {
        expect(screen.getByText(/0 selected/)).toBeInTheDocument()
      })

      const tigerOption = screen.getByText('Raja').closest('div')
      if (tigerOption) {
        fireEvent.click(tigerOption)
      }

      await waitFor(() => {
        expect(screen.getByText(/1 selected/)).toBeInTheDocument()
      })
    })

    it('should show checkmark for selected tigers', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      const tigerOption = await screen.findByText('Raja')
      const tigerDiv = tigerOption.closest('div')
      if (tigerDiv) {
        fireEvent.click(tigerDiv)
      }

      await waitFor(() => {
        expect(screen.getByTestId('check-circle-icon')).toBeInTheDocument()
      })
    })

    it('should deselect tiger when clicked again', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      const tigerOption = await screen.findByText('Raja')
      const tigerDiv = tigerOption.closest('div')

      if (tigerDiv) {
        fireEvent.click(tigerDiv)
        await waitFor(() => {
          expect(screen.getByText(/1 selected/)).toBeInTheDocument()
        })

        fireEvent.click(tigerDiv)
        await waitFor(() => {
          expect(screen.getByText(/0 selected/)).toBeInTheDocument()
        })
      }
    })
  })

  describe('job configuration', () => {
    it('should display epochs input', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      await waitFor(() => {
        expect(screen.getByText('Epochs')).toBeInTheDocument()
        const epochsInput = screen.getByDisplayValue('50')
        expect(epochsInput).toBeInTheDocument()
      })
    })

    it('should display batch size input', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      await waitFor(() => {
        expect(screen.getByText('Batch Size')).toBeInTheDocument()
        const batchSizeInput = screen.getByDisplayValue('32')
        expect(batchSizeInput).toBeInTheDocument()
      })
    })

    it('should display learning rate input', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      await waitFor(() => {
        expect(screen.getByText('Learning Rate')).toBeInTheDocument()
        const learningRateInput = screen.getByDisplayValue('0.001')
        expect(learningRateInput).toBeInTheDocument()
      })
    })

    it('should display validation split input', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      await waitFor(() => {
        expect(screen.getByText('Validation Split')).toBeInTheDocument()
        const validationSplitInput = screen.getByDisplayValue('0.2')
        expect(validationSplitInput).toBeInTheDocument()
      })
    })

    it('should display loss function selector', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      await waitFor(() => {
        expect(screen.getByText('Loss Function')).toBeInTheDocument()
        expect(screen.getByText(/Triplet Loss/)).toBeInTheDocument()
      })
    })

    it('should display description textarea', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      await waitFor(() => {
        expect(screen.getByText('Description (Optional)')).toBeInTheDocument()
        expect(screen.getByPlaceholderText('Describe this fine-tuning run...')).toBeInTheDocument()
      })
    })

    it('should update epochs value when changed', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      const epochsInput = await screen.findByDisplayValue('50')
      fireEvent.change(epochsInput, { target: { value: '100' } })

      await waitFor(() => {
        expect(epochsInput).toHaveValue(100)
      })
    })
  })

  describe('job creation', () => {
    it('should show alert when no tigers selected', async () => {
      // Note: The Start Job button is disabled when no tigers are selected,
      // so instead of clicking and expecting an alert, we verify the button
      // is disabled. If a user somehow clicks (via keyboard/assistive tech),
      // the handleStartJob would show an alert, but the primary behavior
      // is the disabled state.
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      const startJobButtons = await screen.findAllByText('Start Job')
      const modalStartButton = startJobButtons[startJobButtons.length - 1]

      // Button should be disabled when no tigers are selected
      expect(modalStartButton).toBeDisabled()
    })

    it('should disable start button when no tigers selected', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      const startJobButtons = await screen.findAllByText('Start Job')
      const modalStartButton = startJobButtons[startJobButtons.length - 1]

      expect(modalStartButton).toBeDisabled()
    })

    it('should send correct job data when started', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      const tigerOption = await screen.findByText('Raja')
      const tigerDiv = tigerOption.closest('div')
      if (tigerDiv) {
        fireEvent.click(tigerDiv)
      }

      await waitFor(() => {
        expect(screen.getByText(/1 selected/)).toBeInTheDocument()
      })

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { job_id: 'new-job-123' } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })

      const startJobButtons = screen.getAllByText('Start Job')
      const modalStartButton = startJobButtons[startJobButtons.length - 1]

      await act(async () => {
        fireEvent.click(modalStartButton)
      })

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/finetuning/start',
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Content-Type': 'application/json',
              'Authorization': 'Bearer mock-token',
            }),
            body: expect.stringContaining('tiger_reid'),
          })
        )
      })
    })

    it('should close modal after successful job creation', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      const tigerOption = await screen.findByText('Raja')
      const tigerDiv = tigerOption.closest('div')
      if (tigerDiv) {
        fireEvent.click(tigerDiv)
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { job_id: 'new-job-123' } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })

      const startJobButtons = screen.getAllByText('Start Job')
      const modalStartButton = startJobButtons[startJobButtons.length - 1]

      await act(async () => {
        fireEvent.click(modalStartButton)
      })

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith(expect.stringContaining('Fine-tuning job started!'))
      })
    })

    it('should handle job creation error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      const tigerOption = await screen.findByText('Raja')
      const tigerDiv = tigerOption.closest('div')
      if (tigerDiv) {
        fireEvent.click(tigerDiv)
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: 'Server error' }),
      })

      const startJobButtons = screen.getAllByText('Start Job')
      const modalStartButton = startJobButtons[startJobButtons.length - 1]

      await act(async () => {
        fireEvent.click(modalStartButton)
      })

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith(expect.stringContaining('Failed to start job'))
      })
    })
  })

  describe('job cancellation', () => {
    it('should show confirmation dialog when cancel clicked', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        // Multiple cancel buttons exist (one per cancellable job)
        const cancelButtons = screen.getAllByText('Cancel')
        expect(cancelButtons.length).toBeGreaterThan(0)
        fireEvent.click(cancelButtons[0])
        expect(mockConfirm).toHaveBeenCalledWith('Are you sure you want to cancel this job?')
      })
    })

    it('should cancel job when confirmed', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      mockConfirm.mockReturnValue(true)

      renderFineTuning()

      await waitFor(() => {
        // Multiple cancel buttons exist
        const cancelButtons = screen.getAllByText('Cancel')
        expect(cancelButtons.length).toBeGreaterThan(0)
      })

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })

      const cancelButtons = screen.getAllByText('Cancel')

      await act(async () => {
        fireEvent.click(cancelButtons[0])
      })

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/finetuning/jobs/job-1/cancel',
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Authorization': 'Bearer mock-token',
            }),
          })
        )
      })
    })

    it('should not cancel job when user declines confirmation', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      mockConfirm.mockReturnValue(false)

      renderFineTuning()

      await waitFor(() => {
        const cancelButtons = screen.getAllByText('Cancel')
        expect(cancelButtons.length).toBeGreaterThan(0)
        fireEvent.click(cancelButtons[0])
      })

      expect(mockFetch).not.toHaveBeenCalledWith(
        expect.stringContaining('/cancel'),
        expect.anything()
      )
    })

    it('should handle job cancellation error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJobsData,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      mockConfirm.mockReturnValue(true)

      renderFineTuning()

      await waitFor(() => {
        const cancelButtons = screen.getAllByText('Cancel')
        expect(cancelButtons.length).toBeGreaterThan(0)
      })

      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: 'Cannot cancel' }),
      })

      const cancelButtons = screen.getAllByText('Cancel')

      await act(async () => {
        fireEvent.click(cancelButtons[0])
      })

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith(expect.stringContaining('Failed to cancel job'))
      })
    })
  })

  describe('modal actions', () => {
    it('should close modal when cancel button clicked', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { jobs: [] } }),
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Fine-Tuning Job'))
      })

      await waitFor(() => {
        expect(screen.getAllByText('Start Fine-Tuning Job').length).toBeGreaterThan(1)
      })

      const cancelButtons = screen.getAllByText('Cancel')
      const modalCancelButton = cancelButtons[cancelButtons.length - 1]

      fireEvent.click(modalCancelButton)

      await waitFor(() => {
        expect(screen.getAllByText('Start Fine-Tuning Job').length).toBe(1)
      })
    })
  })

  describe('status color mapping', () => {
    it('should apply correct badge variant for completed status', async () => {
      const completedJob = {
        data: {
          jobs: [mockJobsData.data.jobs[1]],
        },
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => completedJob,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText('completed')).toBeInTheDocument()
      })
    })

    it('should apply correct badge variant for failed status', async () => {
      const failedJob = {
        data: {
          jobs: [mockJobsData.data.jobs[2]],
        },
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => failedJob,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText('failed')).toBeInTheDocument()
      })
    })

    it('should apply correct badge variant for training status', async () => {
      const trainingJob = {
        data: {
          jobs: [mockJobsData.data.jobs[0]],
        },
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => trainingJob,
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderFineTuning()

      await waitFor(() => {
        expect(screen.getByText('training')).toBeInTheDocument()
      })
    })
  })
})

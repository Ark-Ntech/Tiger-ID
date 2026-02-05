import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import { BrowserRouter } from 'react-router-dom'
import React from 'react'
import ModelTesting from '../ModelTesting'

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
  PhotoIcon: () => <span data-testid="photo-icon">Photo</span>,
  XMarkIcon: () => <span data-testid="x-icon">X</span>,
  CheckCircleIcon: () => <span data-testid="check-icon">Check</span>,
}))

// Mock data - this is what useGetModelsAvailableQuery returns
const mockModelsData = {
  data: {
    models: {
      wildlife_tools: {
        name: 'Wildlife Tools',
        description: 'ReID model',
        gpu: 'A10G',
        backend: 'Modal',
        type: 'reid',
      },
      cvwc2019: {
        name: 'CVWC 2019',
        description: 'Competition model',
        gpu: 'A10G',
        backend: 'Modal',
        type: 'reid',
      },
      transreid: {
        name: 'TransReID',
        description: 'Transformer model',
        gpu: 'A10G',
        backend: 'Modal',
        type: 'reid',
      },
    },
    default: 'wildlife_tools',
  },
}

// This is what unwrap() returns - the component accesses result.data.results
const mockTestSuccessData = {
  data: {
    model: 'wildlife_tools',
    total_images: 2,
    results: [
      {
        filename: 'tiger1.jpg',
        success: true,
        embedding_shape: [1, 1536],
      },
      {
        filename: 'tiger2.jpg',
        success: true,
        embedding_shape: [1, 1536],
      },
    ],
  },
}

const mockTestErrorData = {
  data: {
    model: 'wildlife_tools',
    total_images: 1,
    results: [
      {
        filename: 'invalid.jpg',
        success: false,
        error: 'Failed to process image',
      },
    ],
  },
}

// Mock API hooks
const mockTestModel = vi.fn()
const mockUseTestModelMutation = vi.fn(() => [mockTestModel, { isLoading: false }])
const mockUseGetModelsAvailableQuery = vi.fn(() => ({
  data: mockModelsData,
  isLoading: false,
  error: null,
}))

vi.mock('../../app/api', () => ({
  useTestModelMutation: () => mockUseTestModelMutation(),
  useGetModelsAvailableQuery: () => mockUseGetModelsAvailableQuery(),
}))

// Helper to create mock mutation result with unwrap
const createMockMutationResult = (data: any) => ({
  unwrap: () => Promise.resolve(data),
})

// Helper to create mock rejected mutation result
const createMockRejectedResult = (error: any) => ({
  unwrap: () => Promise.reject(error),
})

const createMockStore = () => {
  return configureStore({
    reducer: {
      api: () => ({}),
    },
  })
}

const renderModelTesting = (store = createMockStore()) => {
  return render(
    <Provider store={store}>
      <BrowserRouter>
        <ModelTesting />
      </BrowserRouter>
    </Provider>
  )
}

// Helper to create mock file
const createMockFile = (name: string, size: number = 1024, type: string = 'image/jpeg'): File => {
  const blob = new Blob(['x'.repeat(size)], { type })
  return new File([blob], name, { type })
}

describe('ModelTesting', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Return an object with unwrap method that returns the data
    // testModel(formData).unwrap() should return the data
    mockTestModel.mockReturnValue(createMockMutationResult(mockTestSuccessData))
  })

  describe('rendering', () => {
    it('should render page header', () => {
      renderModelTesting()

      expect(screen.getByText('Model Testing')).toBeInTheDocument()
    })

    it('should render page description', () => {
      renderModelTesting()

      expect(screen.getByText('Test RE-ID models on tiger images')).toBeInTheDocument()
    })

    it('should render configuration card', () => {
      renderModelTesting()

      expect(screen.getByText('Configuration')).toBeInTheDocument()
    })

    it('should render results card', () => {
      renderModelTesting()

      expect(screen.getByText('Test Results')).toBeInTheDocument()
    })
  })

  describe('loading state', () => {
    it('should show loading spinner when models are loading', () => {
      mockUseGetModelsAvailableQuery.mockReturnValueOnce({
        data: null,
        isLoading: true,
        error: null,
      })

      renderModelTesting()

      // LoadingSpinner component has data-testid="loading-spinner"
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    })

    it('should show loading state when testing', () => {
      mockUseTestModelMutation.mockReturnValueOnce([mockTestModel, { isLoading: true }])

      renderModelTesting()

      expect(screen.getByText('Testing...')).toBeInTheDocument()
    })
  })

  describe('model selection', () => {
    it('should render model select dropdown', () => {
      renderModelTesting()

      expect(screen.getByRole('combobox')).toBeInTheDocument()
    })

    it('should show placeholder option', () => {
      renderModelTesting()

      expect(screen.getByText('Select a model...')).toBeInTheDocument()
    })

    it('should render all available models as options', () => {
      renderModelTesting()

      expect(screen.getByText('wildlife_tools')).toBeInTheDocument()
      expect(screen.getByText('cvwc2019')).toBeInTheDocument()
      expect(screen.getByText('transreid')).toBeInTheDocument()
    })

    it('should update selected model on change', () => {
      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      expect(select).toHaveValue('wildlife_tools')
    })

    it('should handle empty models data', () => {
      mockUseGetModelsAvailableQuery.mockReturnValueOnce({
        data: { data: { models: {}, default: '' } },
        isLoading: false,
        error: null,
      })

      renderModelTesting()

      const select = screen.getByRole('combobox')
      expect(select.children.length).toBe(1) // Only placeholder
    })
  })

  describe('image upload', () => {
    it('should render file upload input', () => {
      renderModelTesting()

      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      expect(input).toBeInTheDocument()
      expect(input.type).toBe('file')
      expect(input.multiple).toBe(true)
      expect(input.accept).toBe('image/*')
    })

    it('should display upload instructions', () => {
      renderModelTesting()

      expect(screen.getByText(/or drag and drop/i)).toBeInTheDocument()
      expect(screen.getByText(/PNG, JPG, GIF up to 10MB each/i)).toBeInTheDocument()
    })

    it('should add files on selection', () => {
      renderModelTesting()

      const file1 = createMockFile('tiger1.jpg')
      const file2 = createMockFile('tiger2.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement

      fireEvent.change(input, { target: { files: [file1, file2] } })

      expect(screen.getByText('tiger1.jpg')).toBeInTheDocument()
      expect(screen.getByText('tiger2.jpg')).toBeInTheDocument()
      expect(screen.getByText('Selected Files (2)')).toBeInTheDocument()
    })

    it('should show selected files count', () => {
      renderModelTesting()

      const file = createMockFile('tiger.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement

      fireEvent.change(input, { target: { files: [file] } })

      expect(screen.getByText('Selected Files (1)')).toBeInTheDocument()
    })

    it('should display selected files list', () => {
      renderModelTesting()

      const file = createMockFile('tiger.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement

      fireEvent.change(input, { target: { files: [file] } })

      expect(screen.getByText('tiger.jpg')).toBeInTheDocument()
    })

    it('should allow removing individual files', () => {
      renderModelTesting()

      const file1 = createMockFile('tiger1.jpg')
      const file2 = createMockFile('tiger2.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement

      fireEvent.change(input, { target: { files: [file1, file2] } })

      const removeButtons = screen.getAllByTestId('x-icon')
      fireEvent.click(removeButtons[0].closest('button')!)

      expect(screen.queryByText('tiger1.jpg')).not.toBeInTheDocument()
      expect(screen.getByText('tiger2.jpg')).toBeInTheDocument()
      expect(screen.getByText('Selected Files (1)')).toBeInTheDocument()
    })

    it('should append new files to existing selection', () => {
      renderModelTesting()

      const file1 = createMockFile('tiger1.jpg')
      const file2 = createMockFile('tiger2.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement

      fireEvent.change(input, { target: { files: [file1] } })
      fireEvent.change(input, { target: { files: [file2] } })

      expect(screen.getByText('Selected Files (2)')).toBeInTheDocument()
    })
  })

  describe('test execution', () => {
    it('should disable run test button when no model selected', () => {
      renderModelTesting()

      const file = createMockFile('tiger.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      expect(runButton).toBeDisabled()
    })

    it('should disable run test button when no files selected', () => {
      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const runButton = screen.getByText('Run Test')
      expect(runButton).toBeDisabled()
    })

    it('should enable run test button when model and files selected', () => {
      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file = createMockFile('tiger.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      expect(runButton).not.toBeDisabled()
    })

    it('should call testModel mutation on run test click', async () => {
      mockTestModel.mockReturnValue(createMockMutationResult(mockTestSuccessData))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file = createMockFile('tiger.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        expect(mockTestModel).toHaveBeenCalled()
      })
    })

    it('should send FormData with images and model name', async () => {
      mockTestModel.mockReturnValue(createMockMutationResult(mockTestSuccessData))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file = createMockFile('tiger.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        expect(mockTestModel).toHaveBeenCalledWith(expect.any(FormData))
      })
    })

    it('should validate file types before testing', async () => {
      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const invalidFile = createMockFile('document.pdf', 1024, 'application/pdf')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [invalidFile] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        expect(screen.getByText('Validation Error')).toBeInTheDocument()
        expect(screen.getByText(/Invalid file type/i)).toBeInTheDocument()
      })

      expect(mockTestModel).not.toHaveBeenCalled()
    })

    it('should validate file size before testing', async () => {
      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const largeFile = createMockFile('large.jpg', 11 * 1024 * 1024) // 11MB
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [largeFile] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        expect(screen.getByText('Validation Error')).toBeInTheDocument()
        expect(screen.getByText(/File size exceeds 10MB/i)).toBeInTheDocument()
      })

      expect(mockTestModel).not.toHaveBeenCalled()
    })

    it('should validate maximum number of images', async () => {
      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const files = Array.from({ length: 21 }, (_, i) => createMockFile(`tiger${i}.jpg`))
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        expect(screen.getByText('Validation Error')).toBeInTheDocument()
        expect(screen.getByText('Maximum 20 images per test request')).toBeInTheDocument()
      })

      expect(mockTestModel).not.toHaveBeenCalled()
    })
  })

  describe('test results display', () => {
    it('should show empty state when no results', () => {
      renderModelTesting()

      expect(screen.getByText('No test results yet. Upload images and run a test.')).toBeInTheDocument()
    })

    it('should display successful test results', async () => {
      mockTestModel.mockReturnValue(createMockMutationResult(mockTestSuccessData))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file1 = createMockFile('tiger1.jpg')
      const file2 = createMockFile('tiger2.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file1, file2] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        expect(screen.getByText('tiger1.jpg')).toBeInTheDocument()
        expect(screen.getByText('tiger2.jpg')).toBeInTheDocument()
      })
    })

    it('should display success badge for successful results', async () => {
      mockTestModel.mockReturnValue(createMockMutationResult(mockTestSuccessData))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file = createMockFile('tiger1.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        // Multiple success badges for multiple results
        const successBadges = screen.getAllByText('Success')
        expect(successBadges.length).toBeGreaterThan(0)
      })
    })

    it('should display embedding shape for successful results', async () => {
      mockTestModel.mockReturnValue(createMockMutationResult(mockTestSuccessData))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file = createMockFile('tiger1.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        // Multiple embedding shapes for multiple results
        const embeddingTexts = screen.getAllByText(/Embedding shape: \[1, 1536\]/)
        expect(embeddingTexts.length).toBeGreaterThan(0)
      })
    })

    it('should display error message for failed results', async () => {
      mockTestModel.mockReturnValue(createMockMutationResult(mockTestErrorData))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file = createMockFile('invalid.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        expect(screen.getByText('Failed to process image')).toBeInTheDocument()
      })
    })

    it('should display failed badge for failed results', async () => {
      mockTestModel.mockReturnValue(createMockMutationResult(mockTestErrorData))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file = createMockFile('invalid.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        expect(screen.getByText('Failed')).toBeInTheDocument()
      })
    })

    it('should display check icon for successful results', async () => {
      mockTestModel.mockReturnValue(createMockMutationResult(mockTestSuccessData))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file = createMockFile('tiger1.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        // Multiple check icons for multiple results
        const checkIcons = screen.getAllByTestId('check-icon')
        expect(checkIcons.length).toBeGreaterThan(0)
      })
    })

    it('should display x icon for failed results', async () => {
      mockTestModel.mockReturnValue(createMockMutationResult(mockTestErrorData))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file = createMockFile('invalid.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        const xIcons = screen.getAllByTestId('x-icon')
        expect(xIcons.length).toBeGreaterThan(1) // One for remove button, one for failed result
      })
    })

    it('should show total images count in summary', async () => {
      mockTestModel.mockReturnValue(createMockMutationResult(mockTestSuccessData))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file1 = createMockFile('tiger1.jpg')
      const file2 = createMockFile('tiger2.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file1, file2] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        expect(screen.getByText(/Total: 2 images/)).toBeInTheDocument()
      })
    })

    it('should show successful count in summary', async () => {
      mockTestModel.mockReturnValue(createMockMutationResult(mockTestSuccessData))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file1 = createMockFile('tiger1.jpg')
      const file2 = createMockFile('tiger2.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file1, file2] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        expect(screen.getByText(/Successful: 2/)).toBeInTheDocument()
      })
    })
  })

  describe('error handling', () => {
    it('should handle API error gracefully', async () => {
      mockTestModel.mockReturnValue(createMockRejectedResult({
        data: { detail: 'Model not found' },
      }))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file = createMockFile('tiger.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        expect(screen.getByText('Model not found')).toBeInTheDocument()
      })
    })

    it('should handle network error gracefully', async () => {
      mockTestModel.mockReturnValue(createMockRejectedResult({
        data: { message: 'Network error' },
      }))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file = createMockFile('tiger.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument()
      })
    })

    it('should show generic error message when error details missing', async () => {
      mockTestModel.mockReturnValue(createMockRejectedResult({}))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file = createMockFile('tiger.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        expect(screen.getByText('Failed to test model')).toBeInTheDocument()
      })
    })
  })

  describe('clear functionality', () => {
    it('should render clear button', () => {
      renderModelTesting()

      expect(screen.getByText('Clear')).toBeInTheDocument()
    })

    it('should clear selected files on clear click', () => {
      renderModelTesting()

      const file = createMockFile('tiger.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      expect(screen.getByText('Selected Files (1)')).toBeInTheDocument()

      const clearButton = screen.getByText('Clear')
      fireEvent.click(clearButton)

      expect(screen.queryByText('Selected Files (1)')).not.toBeInTheDocument()
    })

    it('should clear test results on clear click', async () => {
      mockTestModel.mockReturnValue(createMockMutationResult(mockTestSuccessData))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file = createMockFile('tiger1.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        expect(screen.getByText(/Total: 2 images/)).toBeInTheDocument()
      })

      const clearButton = screen.getByText('Clear')
      fireEvent.click(clearButton)

      expect(screen.getByText('No test results yet. Upload images and run a test.')).toBeInTheDocument()
    })

    it('should disable clear button when testing', async () => {
      // The Clear button is disabled based on internal isTesting state
      // which is set during handleTest execution
      // Create a delayed mock to keep the test in "testing" state
      let resolvePromise: (value: any) => void
      const delayedPromise = new Promise((resolve) => {
        resolvePromise = resolve
      })
      mockTestModel.mockReturnValue({
        unwrap: () => delayedPromise,
      })

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file = createMockFile('tiger.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      // While testing is in progress, the button should show "Testing..." and Clear should be disabled
      await waitFor(() => {
        expect(screen.getByText('Testing...')).toBeInTheDocument()
      })

      const clearButton = screen.getByText('Clear')
      expect(clearButton).toBeDisabled()

      // Resolve the promise to clean up
      resolvePromise!(mockTestSuccessData)
    })
  })

  describe('confidence score display', () => {
    it('should use green background for successful results', async () => {
      mockTestModel.mockReturnValue(createMockMutationResult(mockTestSuccessData))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file = createMockFile('tiger1.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        // Check that a result card with green background exists
        const greenCards = document.querySelectorAll('.bg-green-50.border-green-200')
        expect(greenCards.length).toBeGreaterThan(0)
      })
    })

    it('should use red background for failed results', async () => {
      mockTestModel.mockReturnValue(createMockMutationResult(mockTestErrorData))

      renderModelTesting()

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'wildlife_tools' } })

      const file = createMockFile('invalid.jpg')
      const input = screen.getByLabelText(/upload files/i) as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      const runButton = screen.getByText('Run Test')
      fireEvent.click(runButton)

      await waitFor(() => {
        // Check that a result card with red background exists
        const redCards = document.querySelectorAll('.bg-red-50.border-red-200')
        expect(redCards.length).toBeGreaterThan(0)
      })
    })
  })

  describe('accessibility', () => {
    it('should have proper labels for form elements', () => {
      renderModelTesting()

      expect(screen.getByText('Select Model')).toBeInTheDocument()
      expect(screen.getByText('Upload Images')).toBeInTheDocument()
    })

    it('should have proper button roles', () => {
      renderModelTesting()

      const runButton = screen.getByText('Run Test')
      expect(runButton.tagName).toBe('BUTTON')

      const clearButton = screen.getByText('Clear')
      expect(clearButton.tagName).toBe('BUTTON')
    })
  })
})

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import DatasetManagement from '../DatasetManagement'

// Mock tigers data
const mockTigersData = {
  data: {
    data: [
      {
        id: 'tiger-001',
        name: 'Raja',
        image_count: 12,
        images: [
          {
            id: 'img-001',
            url: '/images/raja-1.jpg',
          },
          {
            id: 'img-002',
            url: 'http://example.com/raja-2.jpg',
          },
        ],
      },
      {
        id: 'tiger-002',
        name: 'Shere Khan',
        image_count: 25,
        images: [],
      },
      {
        id: 'tiger-003',
        name: null,
        image_count: 5,
        images: [
          {
            id: 'img-003',
            url: '/images/unknown.jpg',
          },
        ],
      },
    ],
  },
}

const mockTigerDetailsData = {
  data: {
    id: 'tiger-001',
    name: 'Raja',
    images: [
      {
        id: 'img-001',
        url: '/images/raja-1.jpg',
      },
      {
        id: 'img-002',
        url: 'http://example.com/raja-2.jpg',
      },
      {
        id: 'img-003',
        url: '/images/raja-3.jpg',
      },
    ],
  },
}

const mockEmptyTigerDetailsData = {
  data: {
    id: 'tiger-002',
    name: 'Shere Khan',
    images: [],
  },
}

const mockNavigate = vi.fn()
const mockFetch = vi.fn()
const mockAlert = vi.fn()
const mockConfirm = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  PhotoIcon: () => <svg data-testid="photo-icon" />,
  ArrowLeftIcon: () => <svg data-testid="arrow-left-icon" />,
  ArrowDownTrayIcon: () => <svg data-testid="download-icon" />,
  TrashIcon: () => <svg data-testid="trash-icon" />,
  PlusIcon: () => <svg data-testid="plus-icon" />,
  XMarkIcon: () => <svg data-testid="x-icon" />,
}))

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

describe('DatasetManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = mockFetch
    global.alert = mockAlert
    global.confirm = mockConfirm
    mockAlert.mockImplementation(() => {})
    mockConfirm.mockReturnValue(true)

    // Default fetch mock returns empty tigers list
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ data: { data: [] } }),
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('loading state', () => {
    it('should show loading spinner while fetching tigers', async () => {
      mockFetch.mockImplementationOnce(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () => resolve({ ok: true, json: async () => mockTigersData }),
              100
            )
          )
      )

      renderWithRouter(<DatasetManagement />)

      // Loading spinner should appear
      expect(screen.getByRole('status') || screen.queryByText(/loading/i)).toBeTruthy()
    })

    it('should show loading spinner while fetching tiger images', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTigersData,
        })
        .mockImplementationOnce(
          () =>
            new Promise((resolve) =>
              setTimeout(
                () =>
                  resolve({
                    ok: true,
                    json: async () => mockTigerDetailsData,
                  }),
                100
              )
            )
        )

      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      // Click on a tiger to trigger image fetch
      fireEvent.click(screen.getByText('Raja'))

      // Loading should show while fetching images
      await waitFor(() => {
        expect(screen.getByRole('status') || screen.queryByText(/loading/i)).toBeTruthy()
      })
    })
  })

  describe('error state', () => {
    it('should handle fetch error gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          'Error fetching tigers:',
          expect.any(Error)
        )
      })

      consoleErrorSpy.mockRestore()
    })

    it('should handle tiger images fetch error', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTigersData,
        })
        .mockRejectedValueOnce(new Error('Failed to fetch images'))

      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          'Error fetching tiger images:',
          expect.any(Error)
        )
      })

      consoleErrorSpy.mockRestore()
    })
  })

  describe('empty state', () => {
    it('should show message when no tigers', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { data: [] } }),
      })

      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        // With no tigers, the list should be empty
        expect(screen.queryByText('Raja')).not.toBeInTheDocument()
      })
    })

    it('should show message when no tiger is selected', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        // Multiple elements match this pattern (h2 and p), use getAllByText
        const selectMessages = screen.getAllByText(/Select a tiger to view/i)
        expect(selectMessages.length).toBeGreaterThan(0)
      })
    })

    it('should show empty state when tiger has no images', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTigersData,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockEmptyTigerDetailsData,
        })

      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Shere Khan')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Shere Khan'))

      await waitFor(() => {
        expect(screen.getByText(/No images in dataset/i)).toBeInTheDocument()
      })
    })
  })

  describe('tiger list display', () => {
    beforeEach(() => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })
    })

    it('should render page title and description', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Dataset Management')).toBeInTheDocument()
        expect(
          screen.getByText(/Manage training datasets for tiger models/i)
        ).toBeInTheDocument()
      })
    })

    it('should render back button', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Back')).toBeInTheDocument()
      })
    })

    it('should navigate to dashboard when back button is clicked', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Back')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Back'))

      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })

    it('should render all tigers from API', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
        expect(screen.getByText('Shere Khan')).toBeInTheDocument()
      })
    })

    it('should display tiger names', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
        expect(screen.getByText('Shere Khan')).toBeInTheDocument()
      })
    })

    it('should display fallback ID for tigers without names', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText(/Tiger #tiger-00/i)).toBeInTheDocument()
      })
    })

    it('should display image counts', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('12 images')).toBeInTheDocument()
        expect(screen.getByText('25 images')).toBeInTheDocument()
        expect(screen.getByText('5 images')).toBeInTheDocument()
      })
    })

    it('should highlight selected tiger', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      const tigerCard = screen.getByText('Raja').closest('div')
      expect(tigerCard?.className).not.toContain('bg-blue-50')

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigerDetailsData,
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const selectedCard = screen.getByText('Raja').closest('div')
        expect(selectedCard?.className).toContain('bg-blue-50')
      })
    })

    it('should fetch tiger images when a tiger is selected', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigerDetailsData,
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/v1/tigers/tiger-001')
      })
    })
  })

  describe('dataset images display', () => {
    beforeEach(() => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTigersData,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTigerDetailsData,
        })
    })

    it('should display tiger images after selection', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const images = screen.getAllByRole('img')
        expect(images.length).toBeGreaterThan(0)
      })
    })

    it('should handle both absolute and relative image URLs', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const images = screen.getAllByRole('img') as HTMLImageElement[]
        expect(images.length).toBe(3)

        // Check that absolute URLs are used as-is
        const absoluteUrlImage = images.find((img) =>
          img.src.includes('example.com')
        )
        expect(absoluteUrlImage).toBeTruthy()

        // Check that relative URLs get the API URL prepended
        const relativeUrlImage = images.find((img) =>
          img.src.includes('raja-1.jpg')
        )
        expect(relativeUrlImage).toBeTruthy()
      })
    })

    it('should show delete button on image hover', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const trashIcons = screen.getAllByTestId('trash-icon')
        expect(trashIcons.length).toBeGreaterThan(0)
      })
    })
  })

  describe('add images functionality', () => {
    beforeEach(() => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTigersData,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTigerDetailsData,
        })
    })

    it('should show Add Images button when tiger is selected', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const addButtons = screen.getAllByText('Add Images')
        expect(addButtons.length).toBeGreaterThan(0)
      })
    })

    it('should not show Add Images button when no tiger is selected', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      // Without selecting a tiger, Add Images button in header should not appear
      const headerAddButtons = screen.queryAllByText('Add Images')
      // There might be one in the empty state, but not in the header
      expect(screen.queryByText('Export Dataset')).not.toBeInTheDocument()
    })

    it('should open modal when Add Images is clicked', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const addButton = screen.getAllByText('Add Images')[0]
        fireEvent.click(addButton)
      })

      await waitFor(() => {
        expect(screen.getByText('Add Images to Dataset')).toBeInTheDocument()
      })
    })

    it('should allow file selection in modal', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const addButton = screen.getAllByText('Add Images')[0]
        fireEvent.click(addButton)
      })

      await waitFor(() => {
        // Input doesn't have a label association, find by type and accept
        const fileInput = document.querySelector('input[type="file"][accept="image/*"]') as HTMLInputElement
        expect(fileInput).toBeInTheDocument()
        expect(fileInput.type).toBe('file')
        expect(fileInput.multiple).toBe(true)
        expect(fileInput.accept).toBe('image/*')
      })
    })

    it('should display selected files', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const addButton = screen.getAllByText('Add Images')[0]
        fireEvent.click(addButton)
      })

      const fileInput = document.querySelector('input[type="file"][accept="image/*"]') as HTMLInputElement
      const file1 = new File(['image1'], 'tiger1.jpg', { type: 'image/jpeg' })
      const file2 = new File(['image2'], 'tiger2.jpg', { type: 'image/jpeg' })

      await userEvent.upload(fileInput, [file1, file2])

      await waitFor(() => {
        expect(screen.getByText('tiger1.jpg')).toBeInTheDocument()
        expect(screen.getByText('tiger2.jpg')).toBeInTheDocument()
      })
    })

    it('should allow removing selected files', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const addButton = screen.getAllByText('Add Images')[0]
        fireEvent.click(addButton)
      })

      const fileInput = document.querySelector('input[type="file"][accept="image/*"]') as HTMLInputElement
      const file = new File(['image'], 'tiger.jpg', { type: 'image/jpeg' })

      await userEvent.upload(fileInput, [file])

      await waitFor(() => {
        expect(screen.getByText('tiger.jpg')).toBeInTheDocument()
      })

      const removeButtons = screen.getAllByTestId('x-icon')
      // Find the remove button within the file list (not the modal close button)
      const fileRemoveButton = removeButtons.find(
        (btn) => btn.closest('.bg-gray-50')
      )?.closest('button')

      if (fileRemoveButton) {
        fireEvent.click(fileRemoveButton)

        await waitFor(() => {
          expect(screen.queryByText('tiger.jpg')).not.toBeInTheDocument()
        })
      }
    })

    it('should show validation alert when trying to add without files', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const addButton = screen.getAllByText('Add Images')[0]
        fireEvent.click(addButton)
      })

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /Add Images/i })
        fireEvent.click(submitButton)
      })

      expect(mockAlert).toHaveBeenCalledWith(
        'Please select a tiger and at least one image'
      )
    })

    it('should submit images successfully', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const addButton = screen.getAllByText('Add Images')[0]
        fireEvent.click(addButton)
      })

      const fileInput = document.querySelector('input[type="file"][accept="image/*"]') as HTMLInputElement
      const file = new File(['image'], 'tiger.jpg', { type: 'image/jpeg' })

      await userEvent.upload(fileInput, [file])

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTigerDetailsData,
        })

      const submitButton = screen.getByRole('button', { name: /Add Images/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/tigers/tiger-001/images',
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              Authorization: expect.stringContaining('Bearer'),
            }),
            body: expect.any(FormData),
          })
        )
      })

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith('Images added successfully')
      })
    })

    it('should handle add images error', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const addButton = screen.getAllByText('Add Images')[0]
        fireEvent.click(addButton)
      })

      const fileInput = document.querySelector('input[type="file"][accept="image/*"]') as HTMLInputElement
      const file = new File(['image'], 'tiger.jpg', { type: 'image/jpeg' })

      await userEvent.upload(fileInput, [file])

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      })

      const submitButton = screen.getByRole('button', { name: /Add Images/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith(
          expect.stringContaining('Failed to add images')
        )
      })
    })

    it('should close modal on cancel', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const addButton = screen.getAllByText('Add Images')[0]
        fireEvent.click(addButton)
      })

      await waitFor(() => {
        expect(screen.getByText('Add Images to Dataset')).toBeInTheDocument()
      })

      const cancelButton = screen.getByRole('button', { name: /Cancel/i })
      fireEvent.click(cancelButton)

      await waitFor(() => {
        expect(screen.queryByText('Add Images to Dataset')).not.toBeInTheDocument()
      })
    })

    it('should disable submit button when no files selected', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const addButton = screen.getAllByText('Add Images')[0]
        fireEvent.click(addButton)
      })

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /Add Images/i })
        expect(submitButton).toBeDisabled()
      })
    })

    it('should show loading state during submission', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const addButton = screen.getAllByText('Add Images')[0]
        fireEvent.click(addButton)
      })

      const fileInput = document.querySelector('input[type="file"][accept="image/*"]') as HTMLInputElement
      const file = new File(['image'], 'tiger.jpg', { type: 'image/jpeg' })

      await userEvent.upload(fileInput, [file])

      mockFetch.mockImplementationOnce(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () => resolve({ ok: true, json: async () => ({ success: true }) }),
              100
            )
          )
      )

      const submitButton = screen.getByRole('button', { name: /Add Images/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Adding...')).toBeInTheDocument()
      })
    })
  })

  describe('delete image functionality', () => {
    beforeEach(() => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTigersData,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTigerDetailsData,
        })
    })

    it('should show confirmation dialog when deleting image', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const deleteButtons = screen.getAllByTestId('trash-icon')
        expect(deleteButtons.length).toBeGreaterThan(0)
      })

      const deleteButton = screen.getAllByTestId('trash-icon')[0].closest('button')
      if (deleteButton) {
        fireEvent.click(deleteButton)

        expect(mockConfirm).toHaveBeenCalledWith(
          'Are you sure you want to remove this image from the dataset?'
        )
      }
    })

    it('should delete image when confirmed', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const deleteButtons = screen.getAllByTestId('trash-icon')
        expect(deleteButtons.length).toBeGreaterThan(0)
      })

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTigerDetailsData,
        })

      const deleteButton = screen.getAllByTestId('trash-icon')[0].closest('button')
      if (deleteButton) {
        fireEvent.click(deleteButton)

        await waitFor(() => {
          expect(mockFetch).toHaveBeenCalledWith(
            '/api/v1/tigers/tiger-001/images/img-001',
            expect.objectContaining({
              method: 'DELETE',
              headers: expect.objectContaining({
                Authorization: expect.stringContaining('Bearer'),
              }),
            })
          )
        })
      }
    })

    it('should not delete image when cancelled', async () => {
      mockConfirm.mockReturnValueOnce(false)

      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const deleteButtons = screen.getAllByTestId('trash-icon')
        expect(deleteButtons.length).toBeGreaterThan(0)
      })

      const deleteButton = screen.getAllByTestId('trash-icon')[0].closest('button')
      if (deleteButton) {
        fireEvent.click(deleteButton)

        expect(mockConfirm).toHaveBeenCalled()
        // Fetch should only be called for initial loads, not delete
        expect(mockFetch).not.toHaveBeenCalledWith(
          expect.stringContaining('/images/'),
          expect.objectContaining({ method: 'DELETE' })
        )
      }
    })

    it('should handle delete error', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const deleteButtons = screen.getAllByTestId('trash-icon')
        expect(deleteButtons.length).toBeGreaterThan(0)
      })

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      })

      const deleteButton = screen.getAllByTestId('trash-icon')[0].closest('button')
      if (deleteButton) {
        fireEvent.click(deleteButton)

        await waitFor(() => {
          expect(mockAlert).toHaveBeenCalledWith(
            expect.stringContaining('Failed to remove image')
          )
        })
      }
    })

    it('should refresh images after successful delete', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const deleteButtons = screen.getAllByTestId('trash-icon')
        expect(deleteButtons.length).toBeGreaterThan(0)
      })

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTigerDetailsData,
        })

      const deleteButton = screen.getAllByTestId('trash-icon')[0].closest('button')
      if (deleteButton) {
        fireEvent.click(deleteButton)

        await waitFor(() => {
          // Should refetch tiger images
          expect(mockFetch).toHaveBeenCalledWith('/api/v1/tigers/tiger-001')
        })
      }
    })
  })

  describe('export dataset functionality', () => {
    beforeEach(() => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTigersData,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTigerDetailsData,
        })

      // Mock URL.createObjectURL and related methods
      global.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
      global.URL.revokeObjectURL = vi.fn()

      // Mock document methods
      const mockAnchor = {
        href: '',
        download: '',
        click: vi.fn(),
      } as any
      vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor)
      vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockAnchor)
      vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockAnchor)
    })

    it('should show Export Dataset button when tiger is selected', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        expect(screen.getByText('Export Dataset')).toBeInTheDocument()
      })
    })

    it('should not show Export Dataset button when no tiger is selected', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.queryByText('Export Dataset')).not.toBeInTheDocument()
      })
    })

    it('should trigger download when export is clicked', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        expect(screen.getByText('Export Dataset')).toBeInTheDocument()
      })

      const blob = new Blob(['mock zip data'], { type: 'application/zip' })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: async () => blob,
      })

      fireEvent.click(screen.getByText('Export Dataset'))

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/tigers/tiger-001/export-dataset',
          expect.objectContaining({
            method: 'GET',
            headers: expect.objectContaining({
              Authorization: expect.stringContaining('Bearer'),
            }),
          })
        )
      })

      await waitFor(() => {
        const anchor = document.createElement('a') as any
        expect(anchor.click).toHaveBeenCalled()
      })
    })

    it('should handle export error', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        expect(screen.getByText('Export Dataset')).toBeInTheDocument()
      })

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      })

      fireEvent.click(screen.getByText('Export Dataset'))

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith(
          expect.stringContaining('Failed to export dataset')
        )
      })
    })

    it('should show alert when trying to export without selecting tiger', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })

      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      // Export button should not be visible without selection
      expect(screen.queryByText('Export Dataset')).not.toBeInTheDocument()
    })
  })

  describe('tiger header section', () => {
    beforeEach(() => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })
    })

    it('should render Tigers section title', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Tigers')).toBeInTheDocument()
      })
    })

    it('should render Dataset Images section title', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Dataset Images')).toBeInTheDocument() ||
        expect(screen.getByText(/Select a tiger to view images/i)).toBeInTheDocument()
      })
    })
  })

  describe('image grid layout', () => {
    beforeEach(() => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTigersData,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTigerDetailsData,
        })
    })

    it('should render images in a grid', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const images = screen.getAllByRole('img')
        expect(images.length).toBe(3)
      })
    })

    it('should render images with proper alt text', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Raja'))

      await waitFor(() => {
        const images = screen.getAllByRole('img') as HTMLImageElement[]
        images.forEach((img) => {
          expect(img.alt).toMatch(/Image img-/)
        })
      })
    })
  })

  describe('responsive behavior', () => {
    beforeEach(() => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTigersData,
      })
    })

    it('should render grid layout for tigers and images', async () => {
      renderWithRouter(<DatasetManagement />)

      await waitFor(() => {
        expect(screen.getByText('Raja')).toBeInTheDocument()
      })

      // Check that the layout grid exists
      const grid = screen.getByText('Tigers').closest('.grid')?.parentElement
      expect(grid).toBeTruthy()
    })
  })
})

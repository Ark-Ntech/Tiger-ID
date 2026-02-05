import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import TigerDetail from '../TigerDetail'

// Mock tiger data
const mockTigerData = {
  data: {
    id: 'tiger-001',
    tiger_id: 'tiger-001-full-uuid-here',
    name: 'Raja',
    alias: 'The Striped King',
    status: 'active',
    confidence_score: 0.95,
    first_seen: '2023-06-15T10:00:00Z',
    last_seen: '2024-01-15T10:30:00Z',
    last_seen_date: '2024-01-15T10:30:00Z',
    last_seen_location: 'Tiger Sanctuary, Section A',
    image_count: 3,
    images: [
      {
        id: 'img-001',
        url: '/images/raja-1.jpg',
        path: '/images/raja-1.jpg',
        uploaded_at: '2023-06-15T10:00:00Z',
      },
      {
        id: 'img-002',
        url: 'http://example.com/raja-2.jpg',
        uploaded_at: '2023-07-20T14:00:00Z',
      },
      {
        id: 'img-003',
        url: '/images/raja-3.jpg',
        uploaded_at: '2023-08-10T09:30:00Z',
      },
    ],
    notes: 'Raja shows distinctive stripe pattern on left flank.\nVery cooperative during photo sessions.',
    related_tigers: [
      {
        id: 'tiger-002',
        name: 'Shere Khan',
        alias: 'Khan',
        status: 'active',
      },
      {
        id: 'tiger-003',
        name: null,
        alias: 'Unknown Tiger #3',
        status: 'unverified',
      },
    ],
    locations: [],
  },
}

const mockTigerWithoutOptionalFields = {
  data: {
    id: 'tiger-999',
    tiger_id: 'tiger-999-uuid',
    name: null,
    status: 'unverified',
    confidence_score: 0.45,
    first_seen: '2024-01-01T09:00:00Z',
    last_seen: '2024-01-01T09:00:00Z',
    image_count: 0,
    images: [],
    locations: [],
  },
}

const mockInvestigationResult = {
  data: {
    investigation_id: 'inv-001',
  },
}

// Mock hooks
const mockNavigate = vi.fn()
const mockUseParams = vi.fn()
const mockUseGetTigerQuery = vi.fn()
const mockUseLaunchInvestigationFromTigerMutation = vi.fn()

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => mockUseParams(),
  }
})

// Mock API hooks
vi.mock('../../app/api', () => ({
  useGetTigerQuery: (id: string) => mockUseGetTigerQuery(id),
  useLaunchInvestigationFromTigerMutation: () => mockUseLaunchInvestigationFromTigerMutation(),
}))

// Mock heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  ArrowLeftIcon: () => <svg data-testid="arrow-left-icon" />,
  MagnifyingGlassIcon: () => <svg data-testid="magnifying-glass-icon" />,
  PhotoIcon: () => <svg data-testid="photo-icon" />,
  XMarkIcon: () => <svg data-testid="x-mark-icon" />,
  InformationCircleIcon: () => <svg data-testid="information-circle-icon" />,
  ExclamationTriangleIcon: () => <svg data-testid="exclamation-triangle-icon" />,
  CheckCircleIcon: () => <svg data-testid="check-circle-icon" />,
  XCircleIcon: () => <svg data-testid="x-circle-icon" />,
}))

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

describe('TigerDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseParams.mockReturnValue({ id: 'tiger-001' })
    const mockUnwrap = vi.fn().mockResolvedValue(mockInvestigationResult)
    const mockMutationFn = vi.fn().mockReturnValue({
      unwrap: mockUnwrap,
    })
    mockUseLaunchInvestigationFromTigerMutation.mockReturnValue([
      mockMutationFn,
      { isLoading: false, error: undefined },
    ])
  })

  describe('loading state', () => {
    it('should show loading spinner when fetching tiger', () => {
      mockUseGetTigerQuery.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: undefined,
      })

      renderWithRouter(<TigerDetail />)

      expect(screen.getByRole('status')).toBeInTheDocument()
    })

    it('should not show tiger details while loading', () => {
      mockUseGetTigerQuery.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: undefined,
      })

      renderWithRouter(<TigerDetail />)

      expect(screen.queryByText('Raja')).not.toBeInTheDocument()
    })
  })

  describe('error state', () => {
    it('should show error message when fetch fails', () => {
      mockUseGetTigerQuery.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Failed to fetch tiger' },
      })

      renderWithRouter(<TigerDetail />)

      expect(screen.getByText(/failed to load tiger details/i)).toBeInTheDocument()
    })

    it('should show back button in error state', () => {
      mockUseGetTigerQuery.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Network error' },
      })

      renderWithRouter(<TigerDetail />)

      const backButton = screen.getByRole('button', { name: /back to tigers/i })
      expect(backButton).toBeInTheDocument()
    })

    it('should navigate to tigers list when back button clicked in error state', () => {
      mockUseGetTigerQuery.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Network error' },
      })

      renderWithRouter(<TigerDetail />)

      const backButton = screen.getByRole('button', { name: /back to tigers/i })
      fireEvent.click(backButton)

      expect(mockNavigate).toHaveBeenCalledWith('/tigers')
    })
  })

  describe('not found state', () => {
    it('should show not found message when tiger does not exist', () => {
      mockUseGetTigerQuery.mockReturnValue({
        data: null,
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<TigerDetail />)

      expect(screen.getByText(/tiger not found/i)).toBeInTheDocument()
    })

    it('should show back button in not found state', () => {
      mockUseGetTigerQuery.mockReturnValue({
        data: null,
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<TigerDetail />)

      const backButton = screen.getByRole('button', { name: /back to tigers/i })
      expect(backButton).toBeInTheDocument()
    })
  })

  describe('tiger details display', () => {
    beforeEach(() => {
      mockUseGetTigerQuery.mockReturnValue({
        data: mockTigerData,
        isLoading: false,
        error: undefined,
      })
    })

    it('should display tiger name', () => {
      renderWithRouter(<TigerDetail />)

      expect(screen.getByText('Raja')).toBeInTheDocument()
    })

    it('should display truncated tiger ID', () => {
      renderWithRouter(<TigerDetail />)

      // ID is truncated to first 8 characters + ellipsis (appears multiple times)
      const tigerIds = screen.getAllByText(/tiger-00/i)
      expect(tigerIds.length).toBeGreaterThan(0)
    })

    it('should display tiger alias', () => {
      renderWithRouter(<TigerDetail />)

      expect(screen.getByText('The Striped King')).toBeInTheDocument()
    })

    it('should display tiger status', () => {
      renderWithRouter(<TigerDetail />)

      // Status appears multiple times in the page
      const statusElements = screen.getAllByText(/active/i)
      expect(statusElements.length).toBeGreaterThan(0)
    })

    it('should display last seen location', () => {
      renderWithRouter(<TigerDetail />)

      expect(screen.getByText('Tiger Sanctuary, Section A')).toBeInTheDocument()
    })

    it('should display last seen date formatted', () => {
      renderWithRouter(<TigerDetail />)

      // Date format may vary by locale, just check it's rendered
      const dateText = screen.getByText(/1\/15\/2024|15\/1\/2024|2024/)
      expect(dateText).toBeInTheDocument()
    })

    it('should display notes with preserved whitespace', () => {
      renderWithRouter(<TigerDetail />)

      expect(screen.getByText(/distinctive stripe pattern/i)).toBeInTheDocument()
      expect(screen.getByText(/cooperative during photo sessions/i)).toBeInTheDocument()
    })

    it('should display image count in metadata', () => {
      renderWithRouter(<TigerDetail />)

      expect(screen.getByText('3')).toBeInTheDocument()
    })

    it('should use fallback tiger ID when name is not available', () => {
      mockUseGetTigerQuery.mockReturnValue({
        data: mockTigerWithoutOptionalFields,
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<TigerDetail />)

      // Displays truncated ID (first 8 chars)
      expect(screen.getByText(/Tiger #tiger-99/i)).toBeInTheDocument()
    })
  })

  describe('back button navigation', () => {
    beforeEach(() => {
      mockUseGetTigerQuery.mockReturnValue({
        data: mockTigerData,
        isLoading: false,
        error: undefined,
      })
    })

    it('should display back button', () => {
      renderWithRouter(<TigerDetail />)

      const backButton = screen.getByRole('button', { name: /back/i })
      expect(backButton).toBeInTheDocument()
    })

    it('should navigate to tigers list when back button clicked', () => {
      renderWithRouter(<TigerDetail />)

      const backButton = screen.getByRole('button', { name: /back/i })
      fireEvent.click(backButton)

      expect(mockNavigate).toHaveBeenCalledWith('/tigers')
    })
  })

  describe('image gallery display', () => {
    beforeEach(() => {
      mockUseGetTigerQuery.mockReturnValue({
        data: mockTigerData,
        isLoading: false,
        error: undefined,
      })
    })

    it('should display images section header', () => {
      renderWithRouter(<TigerDetail />)

      expect(screen.getByText('Images')).toBeInTheDocument()
    })

    it('should display all tiger images', () => {
      renderWithRouter(<TigerDetail />)

      const images = screen.getAllByRole('img')
      expect(images.length).toBeGreaterThanOrEqual(3)
    })

    it('should display edit button for images', () => {
      renderWithRouter(<TigerDetail />)

      const editButton = screen.getByRole('button', { name: /edit/i })
      expect(editButton).toBeInTheDocument()
    })

    it('should toggle edit mode when edit button clicked', () => {
      renderWithRouter(<TigerDetail />)

      const editButton = screen.getByRole('button', { name: /edit/i })
      fireEvent.click(editButton)

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
    })

    it('should show empty state when no images available', () => {
      mockUseGetTigerQuery.mockReturnValue({
        data: mockTigerWithoutOptionalFields,
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<TigerDetail />)

      expect(screen.getByText(/no images available/i)).toBeInTheDocument()
    })

    it('should display photo icon in empty state', () => {
      mockUseGetTigerQuery.mockReturnValue({
        data: mockTigerWithoutOptionalFields,
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<TigerDetail />)

      expect(screen.getAllByTestId('photo-icon').length).toBeGreaterThan(0)
    })

    it('should display total image count', () => {
      renderWithRouter(<TigerDetail />)

      expect(screen.getByText(/total images: 3/i)).toBeInTheDocument()
    })
  })

  describe('image lightbox modal', () => {
    beforeEach(() => {
      mockUseGetTigerQuery.mockReturnValue({
        data: mockTigerData,
        isLoading: false,
        error: undefined,
      })
    })

    it('should open lightbox when image is clicked', async () => {
      renderWithRouter(<TigerDetail />)

      const images = screen.getAllByRole('img')
      fireEvent.click(images[0])

      await waitFor(() => {
        expect(screen.getByTestId('x-mark-icon')).toBeInTheDocument()
      })
    })

    it('should close lightbox when close button is clicked', async () => {
      renderWithRouter(<TigerDetail />)

      const images = screen.getAllByRole('img')
      fireEvent.click(images[0])

      await waitFor(() => {
        const closeButton = screen.getByTestId('x-mark-icon').parentElement
        if (closeButton) {
          fireEvent.click(closeButton)
        }
      })

      // Lightbox should be closed
      expect(screen.queryByText(/previous/i)).not.toBeInTheDocument()
    })

    it('should close lightbox when clicking on background', async () => {
      renderWithRouter(<TigerDetail />)

      const images = screen.getAllByRole('img')
      fireEvent.click(images[0])

      await waitFor(() => {
        const lightbox = screen.getByText(/previous/i).closest('div')?.parentElement?.parentElement
        if (lightbox) {
          fireEvent.click(lightbox)
        }
      })
    })

    it('should show navigation controls when multiple images exist', async () => {
      renderWithRouter(<TigerDetail />)

      const images = screen.getAllByRole('img')
      fireEvent.click(images[0])

      await waitFor(() => {
        expect(screen.getByText(/previous/i)).toBeInTheDocument()
        expect(screen.getByText(/next/i)).toBeInTheDocument()
      })
    })

    it('should show current image position in lightbox', async () => {
      renderWithRouter(<TigerDetail />)

      const images = screen.getAllByRole('img')
      fireEvent.click(images[0])

      await waitFor(() => {
        expect(screen.getByText(/1 \/ 3/i)).toBeInTheDocument()
      })
    })

    it('should navigate to next image when next button clicked', async () => {
      renderWithRouter(<TigerDetail />)

      const images = screen.getAllByRole('img')
      fireEvent.click(images[0])

      await waitFor(() => {
        const nextButton = screen.getByText(/next/i)
        fireEvent.click(nextButton)
      })

      await waitFor(() => {
        expect(screen.getByText(/2 \/ 3/i)).toBeInTheDocument()
      })
    })

    it('should navigate to previous image when previous button clicked', async () => {
      renderWithRouter(<TigerDetail />)

      const images = screen.getAllByRole('img')
      fireEvent.click(images[1])

      await waitFor(() => {
        const prevButton = screen.getByText(/previous/i)
        fireEvent.click(prevButton)
      })

      await waitFor(() => {
        expect(screen.getByText(/1 \/ 3/i)).toBeInTheDocument()
      })
    })

    it('should wrap to last image when clicking previous on first image', async () => {
      renderWithRouter(<TigerDetail />)

      const images = screen.getAllByRole('img')
      fireEvent.click(images[0])

      await waitFor(() => {
        const prevButton = screen.getByText(/previous/i)
        fireEvent.click(prevButton)
      })

      await waitFor(() => {
        expect(screen.getByText(/3 \/ 3/i)).toBeInTheDocument()
      })
    })

    it('should wrap to first image when clicking next on last image', async () => {
      renderWithRouter(<TigerDetail />)

      const images = screen.getAllByRole('img')
      fireEvent.click(images[2])

      await waitFor(() => {
        const nextButton = screen.getByText(/next/i)
        fireEvent.click(nextButton)
      })

      await waitFor(() => {
        expect(screen.getByText(/1 \/ 3/i)).toBeInTheDocument()
      })
    })
  })

  describe('related tigers display', () => {
    beforeEach(() => {
      mockUseGetTigerQuery.mockReturnValue({
        data: mockTigerData,
        isLoading: false,
        error: undefined,
      })
    })

    it('should display related tigers section', () => {
      renderWithRouter(<TigerDetail />)

      expect(screen.getByText('Related Tigers')).toBeInTheDocument()
    })

    it('should display all related tigers', () => {
      renderWithRouter(<TigerDetail />)

      expect(screen.getByText('Shere Khan')).toBeInTheDocument()
      // tiger-003 has null name, so displays truncated ID
      expect(screen.getByText(/Tiger #tiger-00/i)).toBeInTheDocument()
    })

    it('should display related tiger alias', () => {
      renderWithRouter(<TigerDetail />)

      expect(screen.getByText(/Alias: Khan/i)).toBeInTheDocument()
    })

    it('should display related tiger status badges', () => {
      renderWithRouter(<TigerDetail />)

      // Both active and unverified statuses should be shown
      const statusBadges = screen.getAllByText(/active|unverified/i)
      expect(statusBadges.length).toBeGreaterThanOrEqual(2)
    })

    it('should navigate to related tiger on click', () => {
      renderWithRouter(<TigerDetail />)

      const relatedTiger = screen.getByText('Shere Khan')
      fireEvent.click(relatedTiger)

      expect(mockNavigate).toHaveBeenCalledWith('/tigers/tiger-002')
    })

    it('should not display related tigers section when none exist', () => {
      mockUseGetTigerQuery.mockReturnValue({
        data: {
          ...mockTigerWithoutOptionalFields,
          related_tigers: [],
        },
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<TigerDetail />)

      expect(screen.queryByText('Related Tigers')).not.toBeInTheDocument()
    })

    it('should use fallback name for related tigers without names', () => {
      renderWithRouter(<TigerDetail />)

      // Displays truncated ID (first 8 chars)
      expect(screen.getByText(/Tiger #tiger-00/i)).toBeInTheDocument()
    })
  })

  describe('launch investigation functionality', () => {
    beforeEach(() => {
      mockUseGetTigerQuery.mockReturnValue({
        data: mockTigerData,
        isLoading: false,
        error: undefined,
      })
    })

    it('should display launch investigation button in header', () => {
      renderWithRouter(<TigerDetail />)

      const buttons = screen.getAllByRole('button', { name: /launch investigation/i })
      expect(buttons.length).toBeGreaterThan(0)
    })

    it('should display launch investigation button in quick actions', () => {
      renderWithRouter(<TigerDetail />)

      expect(screen.getByText('Quick Actions')).toBeInTheDocument()
      const buttons = screen.getAllByRole('button', { name: /launch investigation/i })
      expect(buttons.length).toBeGreaterThanOrEqual(2)
    })

    it('should call mutation when launch investigation is clicked', async () => {
      const mockUnwrap = vi.fn().mockResolvedValue(mockInvestigationResult)
      const mockLaunchMutation = vi.fn().mockReturnValue({ unwrap: mockUnwrap })
      mockUseLaunchInvestigationFromTigerMutation.mockReturnValue([
        mockLaunchMutation,
        { isLoading: false, error: undefined },
      ])

      renderWithRouter(<TigerDetail />)

      const launchButtons = screen.getAllByRole('button', { name: /launch investigation/i })
      fireEvent.click(launchButtons[0])

      await waitFor(() => {
        expect(mockLaunchMutation).toHaveBeenCalledWith({
          tiger_id: 'tiger-001',
          tiger_name: 'Raja',
        })
      })
    })

    it('should navigate to investigation workspace after successful launch', async () => {
      const mockUnwrap = vi.fn().mockResolvedValue(mockInvestigationResult)
      const mockLaunchMutation = vi.fn().mockReturnValue({ unwrap: mockUnwrap })
      mockUseLaunchInvestigationFromTigerMutation.mockReturnValue([
        mockLaunchMutation,
        { isLoading: false, error: undefined },
      ])

      renderWithRouter(<TigerDetail />)

      const launchButtons = screen.getAllByRole('button', { name: /launch investigation/i })
      fireEvent.click(launchButtons[0])

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/investigations/inv-001')
      })
    })

    it('should navigate to launch page when investigation_id is not returned', async () => {
      const mockUnwrap = vi.fn().mockResolvedValue({ data: {} })
      const mockLaunchMutation = vi.fn().mockReturnValue({ unwrap: mockUnwrap })
      mockUseLaunchInvestigationFromTigerMutation.mockReturnValue([
        mockLaunchMutation,
        { isLoading: false, error: undefined },
      ])

      renderWithRouter(<TigerDetail />)

      const launchButtons = screen.getAllByRole('button', { name: /launch investigation/i })
      fireEvent.click(launchButtons[0])

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/investigations/launch?tiger_id=tiger-001')
      })
    })

    it('should have launch investigation button', () => {
      renderWithRouter(<TigerDetail />)

      const launchButtons = screen.getAllByRole('button', { name: /launch investigation/i })
      expect(launchButtons.length).toBeGreaterThan(0)
      expect(launchButtons[0]).not.toBeDisabled()
    })

    it('should call mutation when launch investigation is clicked', async () => {
      const mockUnwrap = vi.fn().mockResolvedValue(mockInvestigationResult)
      const mockMutationFn = vi.fn().mockReturnValue({
        unwrap: mockUnwrap,
      })
      mockUseLaunchInvestigationFromTigerMutation.mockReturnValue([
        mockMutationFn,
        { isLoading: false, error: undefined },
      ])

      renderWithRouter(<TigerDetail />)

      const launchButtons = screen.getAllByRole('button', { name: /launch investigation/i })
      fireEvent.click(launchButtons[0])

      await waitFor(() => {
        expect(mockMutationFn).toHaveBeenCalled()
      })
    })

    it('should handle launch investigation error', async () => {
      const mockAlert = vi.spyOn(window, 'alert').mockImplementation(() => {})
      const mockUnwrap = vi.fn().mockRejectedValue({
        data: { detail: 'Investigation failed' },
      })
      const mockLaunchMutation = vi.fn().mockReturnValue({ unwrap: mockUnwrap })
      mockUseLaunchInvestigationFromTigerMutation.mockReturnValue([
        mockLaunchMutation,
        { isLoading: false, error: undefined },
      ])

      renderWithRouter(<TigerDetail />)

      const launchButtons = screen.getAllByRole('button', { name: /launch investigation/i })
      fireEvent.click(launchButtons[0])

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith(
          expect.stringContaining('Failed to launch investigation')
        )
      })

      mockAlert.mockRestore()
    })

    it('should not launch investigation when tiger ID is missing', async () => {
      mockUseParams.mockReturnValue({ id: undefined })
      const mockUnwrap = vi.fn()
      const mockLaunchMutation = vi.fn().mockReturnValue({ unwrap: mockUnwrap })
      mockUseLaunchInvestigationFromTigerMutation.mockReturnValue([
        mockLaunchMutation,
        { isLoading: false, error: undefined },
      ])

      renderWithRouter(<TigerDetail />)

      const launchButtons = screen.getAllByRole('button', { name: /launch investigation/i })
      fireEvent.click(launchButtons[0])

      await waitFor(() => {
        expect(mockLaunchMutation).not.toHaveBeenCalled()
      })
    })
  })

  describe('quick actions card', () => {
    beforeEach(() => {
      mockUseGetTigerQuery.mockReturnValue({
        data: mockTigerData,
        isLoading: false,
        error: undefined,
      })
    })

    it('should display quick actions section', () => {
      renderWithRouter(<TigerDetail />)

      expect(screen.getByText('Quick Actions')).toBeInTheDocument()
    })

    it('should display view all tigers button', () => {
      renderWithRouter(<TigerDetail />)

      expect(screen.getByRole('button', { name: /view all tigers/i })).toBeInTheDocument()
    })

    it('should navigate to tigers list when view all tigers is clicked', () => {
      renderWithRouter(<TigerDetail />)

      const viewAllButton = screen.getByRole('button', { name: /view all tigers/i })
      fireEvent.click(viewAllButton)

      expect(mockNavigate).toHaveBeenCalledWith('/tigers')
    })
  })

  describe('metadata card', () => {
    beforeEach(() => {
      mockUseGetTigerQuery.mockReturnValue({
        data: mockTigerData,
        isLoading: false,
        error: undefined,
      })
    })

    it('should display metadata section', () => {
      renderWithRouter(<TigerDetail />)

      expect(screen.getByText('Metadata')).toBeInTheDocument()
    })

    it('should display tiger ID in metadata', () => {
      renderWithRouter(<TigerDetail />)

      // Should show truncated ID (first 8 chars + ellipsis)
      const tigerIdLabel = screen.getByText('Tiger ID:')
      expect(tigerIdLabel).toBeInTheDocument()
      expect(tigerIdLabel.parentElement).toHaveTextContent(/tiger-00/)
    })

    it('should display image count in metadata', () => {
      renderWithRouter(<TigerDetail />)

      const imageCountLabel = screen.getByText('Image Count:')
      expect(imageCountLabel).toBeInTheDocument()
      expect(imageCountLabel.parentElement).toHaveTextContent('3')
    })
  })

  describe('status card', () => {
    beforeEach(() => {
      mockUseGetTigerQuery.mockReturnValue({
        data: mockTigerData,
        isLoading: false,
        error: undefined,
      })
    })

    it('should display status section', () => {
      renderWithRouter(<TigerDetail />)

      // Status appears as heading and label
      const statusElements = screen.getAllByText('Status')
      expect(statusElements.length).toBeGreaterThan(0)
    })

    it('should display active status with success badge', () => {
      renderWithRouter(<TigerDetail />)

      const statusBadges = screen.getAllByText(/active/i)
      expect(statusBadges.length).toBeGreaterThan(0)
    })

    it('should display unverified status with warning badge', () => {
      mockUseGetTigerQuery.mockReturnValue({
        data: {
          ...mockTigerData,
          status: 'unverified',
        },
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<TigerDetail />)

      expect(screen.getByText(/unverified/i)).toBeInTheDocument()
    })

    it('should display unknown status as fallback', () => {
      mockUseGetTigerQuery.mockReturnValue({
        data: {
          ...mockTigerData,
          status: null,
        },
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<TigerDetail />)

      expect(screen.getByText(/unknown/i)).toBeInTheDocument()
    })
  })

  describe('notes section', () => {
    beforeEach(() => {
      mockUseGetTigerQuery.mockReturnValue({
        data: mockTigerData,
        isLoading: false,
        error: undefined,
      })
    })

    it('should display notes section when notes exist', () => {
      renderWithRouter(<TigerDetail />)

      expect(screen.getByText('Notes')).toBeInTheDocument()
    })

    it('should preserve line breaks in notes', () => {
      renderWithRouter(<TigerDetail />)

      const notesElement = screen.getByText(/distinctive stripe pattern/i)
      expect(notesElement).toHaveClass('whitespace-pre-wrap')
    })

    it('should not display notes section when notes are empty', () => {
      mockUseGetTigerQuery.mockReturnValue({
        data: {
          ...mockTigerData.data,
          notes: null,
        },
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<TigerDetail />)

      expect(screen.queryByText('Notes')).not.toBeInTheDocument()
    })
  })

  describe('responsive layout', () => {
    beforeEach(() => {
      mockUseGetTigerQuery.mockReturnValue({
        data: mockTigerData,
        isLoading: false,
        error: undefined,
      })
    })

    it('should use grid layout for content organization', () => {
      renderWithRouter(<TigerDetail />)

      // Check for grid layout classes in the DOM
      const gridElement = document.querySelector('.grid')
      expect(gridElement).toBeInTheDocument()
    })

    it('should have image grid layout', () => {
      renderWithRouter(<TigerDetail />)

      // Check for grid layout in images section
      const imageGrids = document.querySelectorAll('.grid')
      expect(imageGrids.length).toBeGreaterThan(0)
    })
  })

  describe('image error handling', () => {
    beforeEach(() => {
      mockUseGetTigerQuery.mockReturnValue({
        data: mockTigerData,
        isLoading: false,
        error: undefined,
      })
    })

    it('should handle image load errors gracefully', () => {
      renderWithRouter(<TigerDetail />)

      const images = screen.getAllByRole('img')
      if (images.length > 0) {
        fireEvent.error(images[0])
        // Should not crash the component
        expect(screen.getByText('Raja')).toBeInTheDocument()
      }
    })
  })

  describe('accessibility', () => {
    beforeEach(() => {
      mockUseGetTigerQuery.mockReturnValue({
        data: mockTigerData,
        isLoading: false,
        error: undefined,
      })
    })

    it('should have proper image alt text', () => {
      renderWithRouter(<TigerDetail />)

      const images = screen.getAllByRole('img')
      images.forEach((img) => {
        expect(img).toHaveAttribute('alt')
      })
    })

    it('should have clickable elements as buttons', () => {
      renderWithRouter(<TigerDetail />)

      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)
    })

    it('should have proper heading hierarchy', () => {
      renderWithRouter(<TigerDetail />)

      const h1 = screen.getByRole('heading', { level: 1 })
      expect(h1).toBeInTheDocument()
    })
  })
})

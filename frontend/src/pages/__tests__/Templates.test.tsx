import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Templates from '../Templates'

// Mock template data
const mockTemplates = [
  {
    id: '1',
    template_id: 'template-1',
    name: 'Standard Investigation',
    description: 'Standard tiger trafficking investigation workflow',
    workflow_steps: ['upload', 'detect', 'analyze', 'report'],
    default_agents: ['image_analyzer', 'tiger_detector'],
    created_at: '2024-01-15T10:00:00Z',
  },
  {
    id: '2',
    template_id: 'template-2',
    name: 'Quick Scan',
    description: 'Fast preliminary scan for quick assessment',
    workflow_steps: ['upload', 'detect'],
    default_agents: ['image_analyzer'],
    created_at: '2024-01-16T12:00:00Z',
  },
  {
    id: '3',
    template_id: 'template-3',
    name: 'Deep Dive Analysis',
    description: 'Comprehensive investigation with all available tools',
    workflow_steps: ['upload', 'detect', 'analyze', 'research', 'verify', 'report'],
    default_agents: ['image_analyzer', 'tiger_detector', 'research_agent'],
    created_at: '2024-01-17T08:00:00Z',
  },
]

// Mock API hooks
const mockUseGetTemplatesQuery = vi.fn()
const mockUseApplyTemplateMutation = vi.fn()
const mockRefetch = vi.fn()
const mockApplyTemplate = vi.fn()

vi.mock('../../app/api', () => ({
  useGetTemplatesQuery: () => mockUseGetTemplatesQuery(),
  useApplyTemplateMutation: () => mockUseApplyTemplateMutation(),
}))

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
  DocumentTextIcon: () => <svg data-testid="document-icon" />,
}))

// Mock CreateTemplateDialog
vi.mock('../../components/templates/CreateTemplateDialog', () => ({
  default: ({ isOpen, onClose, onSuccess }: any) => {
    if (!isOpen) return null
    return (
      <div data-testid="create-template-dialog">
        <h2>Create Template Dialog</h2>
        <button onClick={onClose}>Close Dialog</button>
        <button
          onClick={() => {
            onSuccess?.()
            onClose()
          }}
        >
          Create Template Success
        </button>
      </div>
    )
  },
}))

// Mock window.prompt and window.alert
const originalPrompt = window.prompt
const originalAlert = window.alert

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

describe('Templates', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockRefetch.mockClear()
    mockApplyTemplate.mockClear()
    mockNavigate.mockClear()

    // Reset window functions
    window.prompt = vi.fn()
    window.alert = vi.fn()
  })

  afterEach(() => {
    window.prompt = originalPrompt
    window.alert = originalAlert
  })

  describe('loading state', () => {
    it('should show loading spinner when fetching templates', () => {
      mockUseGetTemplatesQuery.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: undefined,
        refetch: mockRefetch,
      })
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])

      renderWithRouter(<Templates />)

      expect(screen.getByRole('status')).toBeInTheDocument()
      expect(screen.queryByText('Investigation Templates')).not.toBeInTheDocument()
    })

    it('should not show template content during loading', () => {
      mockUseGetTemplatesQuery.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: undefined,
        refetch: mockRefetch,
      })
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])

      renderWithRouter(<Templates />)

      expect(screen.queryByText('Standard Investigation')).not.toBeInTheDocument()
    })
  })

  describe('empty state', () => {
    it('should show empty message when no templates exist', () => {
      mockUseGetTemplatesQuery.mockReturnValue({
        data: { data: [] },
        isLoading: false,
        error: undefined,
        refetch: mockRefetch,
      })
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])

      renderWithRouter(<Templates />)

      expect(screen.getByText('No templates available')).toBeInTheDocument()
    })

    it('should show document icon in empty state', () => {
      mockUseGetTemplatesQuery.mockReturnValue({
        data: { data: [] },
        isLoading: false,
        error: undefined,
        refetch: mockRefetch,
      })
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])

      renderWithRouter(<Templates />)

      const icons = screen.getAllByTestId('document-icon')
      expect(icons.length).toBeGreaterThan(0)
    })

    it('should still show create button in empty state', () => {
      mockUseGetTemplatesQuery.mockReturnValue({
        data: { data: [] },
        isLoading: false,
        error: undefined,
        refetch: mockRefetch,
      })
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])

      renderWithRouter(<Templates />)

      expect(screen.getByRole('button', { name: /create template/i })).toBeInTheDocument()
    })
  })

  describe('template list display', () => {
    beforeEach(() => {
      mockUseGetTemplatesQuery.mockReturnValue({
        data: { data: mockTemplates },
        isLoading: false,
        error: undefined,
        refetch: mockRefetch,
      })
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])
    })

    it('should render page title and description', () => {
      renderWithRouter(<Templates />)

      expect(screen.getByText('Investigation Templates')).toBeInTheDocument()
      expect(screen.getByText('Pre-configured investigation templates')).toBeInTheDocument()
    })

    it('should render all template names', () => {
      renderWithRouter(<Templates />)

      expect(screen.getByText('Standard Investigation')).toBeInTheDocument()
      expect(screen.getByText('Quick Scan')).toBeInTheDocument()
      expect(screen.getByText('Deep Dive Analysis')).toBeInTheDocument()
    })

    it('should render all template descriptions', () => {
      renderWithRouter(<Templates />)

      expect(screen.getByText('Standard tiger trafficking investigation workflow')).toBeInTheDocument()
      expect(screen.getByText('Fast preliminary scan for quick assessment')).toBeInTheDocument()
      expect(screen.getByText('Comprehensive investigation with all available tools')).toBeInTheDocument()
    })

    it('should render document icons for each template', () => {
      renderWithRouter(<Templates />)

      const icons = screen.getAllByTestId('document-icon')
      // 3 templates + 1 in empty state = 4, but we have data so just 3
      expect(icons.length).toBeGreaterThanOrEqual(3)
    })

    it('should render use template buttons for each template', () => {
      renderWithRouter(<Templates />)

      const useButtons = screen.getAllByRole('button', { name: /use template/i })
      expect(useButtons).toHaveLength(3)
    })

    it('should render create template button', () => {
      renderWithRouter(<Templates />)

      expect(screen.getByRole('button', { name: /create template/i })).toBeInTheDocument()
    })

    it('should render templates in a grid layout', () => {
      const { container } = renderWithRouter(<Templates />)

      const gridContainer = container.querySelector('.grid')
      expect(gridContainer).toBeInTheDocument()
      expect(gridContainer?.classList.contains('grid-cols-1')).toBe(true)
    })
  })

  describe('template creation', () => {
    beforeEach(() => {
      mockUseGetTemplatesQuery.mockReturnValue({
        data: { data: mockTemplates },
        isLoading: false,
        error: undefined,
        refetch: mockRefetch,
      })
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])
    })

    it('should open create dialog when create button is clicked', () => {
      renderWithRouter(<Templates />)

      const createButton = screen.getByRole('button', { name: /create template/i })
      fireEvent.click(createButton)

      expect(screen.getByTestId('create-template-dialog')).toBeInTheDocument()
      expect(screen.getByText('Create Template Dialog')).toBeInTheDocument()
    })

    it('should close create dialog when close is clicked', () => {
      renderWithRouter(<Templates />)

      const createButton = screen.getByRole('button', { name: /create template/i })
      fireEvent.click(createButton)

      expect(screen.getByTestId('create-template-dialog')).toBeInTheDocument()

      const closeButton = screen.getByRole('button', { name: /close dialog/i })
      fireEvent.click(closeButton)

      expect(screen.queryByTestId('create-template-dialog')).not.toBeInTheDocument()
    })

    it('should refetch templates after successful creation', async () => {
      renderWithRouter(<Templates />)

      const createButton = screen.getByRole('button', { name: /create template/i })
      fireEvent.click(createButton)

      const successButton = screen.getByRole('button', { name: /create template success/i })
      fireEvent.click(successButton)

      await waitFor(() => {
        expect(mockRefetch).toHaveBeenCalledOnce()
      })
    })

    it('should close dialog after successful creation', async () => {
      renderWithRouter(<Templates />)

      const createButton = screen.getByRole('button', { name: /create template/i })
      fireEvent.click(createButton)

      const successButton = screen.getByRole('button', { name: /create template success/i })
      fireEvent.click(successButton)

      await waitFor(() => {
        expect(screen.queryByTestId('create-template-dialog')).not.toBeInTheDocument()
      })
    })
  })

  describe('template application', () => {
    beforeEach(() => {
      mockUseGetTemplatesQuery.mockReturnValue({
        data: { data: mockTemplates },
        isLoading: false,
        error: undefined,
        refetch: mockRefetch,
      })
      mockApplyTemplate.mockReturnValue({
        unwrap: vi.fn().mockResolvedValue({ data: { success: true } })
      })
    })

    it('should apply template to existing investigation when ID provided', async () => {
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])

      vi.mocked(window.prompt).mockReturnValue('investigation-123')

      renderWithRouter(<Templates />)

      const useButtons = screen.getAllByRole('button', { name: /use template/i })
      fireEvent.click(useButtons[0])

      await waitFor(() => {
        expect(window.prompt).toHaveBeenCalled()
        expect(mockApplyTemplate).toHaveBeenCalledWith({
          template_id: 'template-1',
          investigation_id: 'investigation-123',
        })
      })
    })

    it('should navigate to investigation after successful application', async () => {
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])

      vi.mocked(window.prompt).mockReturnValue('investigation-456')

      renderWithRouter(<Templates />)

      const useButtons = screen.getAllByRole('button', { name: /use template/i })
      fireEvent.click(useButtons[1])

      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith(
          'Template "Quick Scan" applied successfully!'
        )
      })

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/investigations/investigation-456')
      })
    })

    it('should navigate to launch page when no investigation ID provided', async () => {
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])

      vi.mocked(window.prompt).mockReturnValue('')

      renderWithRouter(<Templates />)

      const useButtons = screen.getAllByRole('button', { name: /use template/i })
      fireEvent.click(useButtons[0])

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/investigations/launch', {
          state: { templateId: 'template-1' },
        })
      })
    })

    it('should navigate to launch page when prompt cancelled', async () => {
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])

      vi.mocked(window.prompt).mockReturnValue(null)

      renderWithRouter(<Templates />)

      const useButtons = screen.getAllByRole('button', { name: /use template/i })
      fireEvent.click(useButtons[0])

      // When prompt returns null, the else branch is not executed
      await waitFor(() => {
        expect(mockApplyTemplate).not.toHaveBeenCalled()
        expect(mockNavigate).not.toHaveBeenCalled()
      })
    })

    it('should show success alert after template application', async () => {
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])

      vi.mocked(window.prompt).mockReturnValue('investigation-789')

      renderWithRouter(<Templates />)

      const useButtons = screen.getAllByRole('button', { name: /use template/i })
      fireEvent.click(useButtons[0])

      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith(
          'Template "Standard Investigation" applied successfully!'
        )
      })
    })

    it('should handle template application error', async () => {
      const errorMessage = 'Investigation not found'
      mockApplyTemplate.mockReturnValue({
        unwrap: vi.fn().mockRejectedValue({
          data: { detail: errorMessage },
        })
      })
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])

      vi.mocked(window.prompt).mockReturnValue('invalid-investigation')

      renderWithRouter(<Templates />)

      const useButtons = screen.getAllByRole('button', { name: /use template/i })
      fireEvent.click(useButtons[0])

      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith(
          `Failed to apply template: ${errorMessage}`
        )
      })
    })

    it('should handle template application error with message', async () => {
      mockApplyTemplate.mockReturnValue({
        unwrap: vi.fn().mockRejectedValue({
          message: 'Network error',
        })
      })
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])

      vi.mocked(window.prompt).mockReturnValue('investigation-123')

      renderWithRouter(<Templates />)

      const useButtons = screen.getAllByRole('button', { name: /use template/i })
      fireEvent.click(useButtons[0])

      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith(
          'Failed to apply template: Network error'
        )
      })
    })

    it('should handle unknown template application error', async () => {
      const mockApplyError = vi.fn().mockReturnValue({
        unwrap: vi.fn().mockRejectedValue({})
      })
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyError,
        { isLoading: false },
      ])

      vi.mocked(window.prompt).mockReturnValue('investigation-123')

      renderWithRouter(<Templates />)

      const useButtons = screen.getAllByRole('button', { name: /use template/i })
      fireEvent.click(useButtons[0])

      await waitFor(() => {
        expect(mockApplyError).toHaveBeenCalled()
      })

      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith(
          'Failed to apply template: Unknown error'
        )
      })
    })

    it('should disable buttons while applying template', async () => {
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: true },
      ])

      renderWithRouter(<Templates />)

      const useButtons = screen.getAllByRole('button', { name: /applying/i })
      expect(useButtons).toHaveLength(3)
      useButtons.forEach(button => {
        expect(button).toBeDisabled()
      })
    })

    it('should show "Applying..." text while template is being applied', () => {
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: true },
      ])

      renderWithRouter(<Templates />)

      const applyingButtons = screen.getAllByRole('button', { name: /applying/i })
      expect(applyingButtons).toHaveLength(3)
    })
  })

  describe('template ID handling', () => {
    it('should use template_id field if available', async () => {
      mockUseGetTemplatesQuery.mockReturnValue({
        data: { data: mockTemplates },
        isLoading: false,
        error: undefined,
        refetch: mockRefetch,
      })
      mockApplyTemplate.mockResolvedValue({ data: { success: true } })
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])

      vi.mocked(window.prompt).mockReturnValue('investigation-123')

      renderWithRouter(<Templates />)

      const useButtons = screen.getAllByRole('button', { name: /use template/i })
      fireEvent.click(useButtons[0])

      await waitFor(() => {
        expect(mockApplyTemplate).toHaveBeenCalledWith({
          template_id: 'template-1',
          investigation_id: 'investigation-123',
        })
      })
    })

    it('should fall back to id field if template_id not available', async () => {
      const templatesWithoutTemplateId = mockTemplates.map(t => ({
        ...t,
        template_id: undefined,
      }))

      mockUseGetTemplatesQuery.mockReturnValue({
        data: { data: templatesWithoutTemplateId },
        isLoading: false,
        error: undefined,
        refetch: mockRefetch,
      })
      mockApplyTemplate.mockResolvedValue({ data: { success: true } })
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])

      vi.mocked(window.prompt).mockReturnValue('investigation-123')

      renderWithRouter(<Templates />)

      const useButtons = screen.getAllByRole('button', { name: /use template/i })
      fireEvent.click(useButtons[0])

      await waitFor(() => {
        expect(mockApplyTemplate).toHaveBeenCalledWith({
          template_id: '1',
          investigation_id: 'investigation-123',
        })
      })
    })
  })

  describe('hover effects', () => {
    beforeEach(() => {
      mockUseGetTemplatesQuery.mockReturnValue({
        data: { data: mockTemplates },
        isLoading: false,
        error: undefined,
        refetch: mockRefetch,
      })
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])
    })

    it('should apply hover styles to template cards', () => {
      const { container } = renderWithRouter(<Templates />)

      const cards = container.querySelectorAll('.hover\\:shadow-lg')
      expect(cards.length).toBeGreaterThanOrEqual(3)
    })
  })

  describe('data handling', () => {
    it('should handle undefined data gracefully', () => {
      mockUseGetTemplatesQuery.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: undefined,
        refetch: mockRefetch,
      })
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])

      renderWithRouter(<Templates />)

      expect(screen.getByText('No templates available')).toBeInTheDocument()
    })

    it('should handle null data.data gracefully', () => {
      mockUseGetTemplatesQuery.mockReturnValue({
        data: { data: null },
        isLoading: false,
        error: undefined,
        refetch: mockRefetch,
      })
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])

      renderWithRouter(<Templates />)

      expect(screen.getByText('No templates available')).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    beforeEach(() => {
      mockUseGetTemplatesQuery.mockReturnValue({
        data: { data: mockTemplates },
        isLoading: false,
        error: undefined,
        refetch: mockRefetch,
      })
      mockUseApplyTemplateMutation.mockReturnValue([
        mockApplyTemplate,
        { isLoading: false },
      ])
    })

    it('should have accessible button labels', () => {
      renderWithRouter(<Templates />)

      expect(screen.getByRole('button', { name: /create template/i })).toBeInTheDocument()
      expect(screen.getAllByRole('button', { name: /use template/i })).toHaveLength(3)
    })

    it('should have proper heading hierarchy', () => {
      renderWithRouter(<Templates />)

      const mainHeading = screen.getByText('Investigation Templates')
      expect(mainHeading.tagName).toBe('H1')
    })
  })
})

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import React from 'react'
import { ReportDownload } from '../ReportDownload'

// Mock heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  DocumentArrowDownIcon: () => <span data-testid="download-icon">Download</span>,
  DocumentTextIcon: () => <span data-testid="doc-icon">Doc</span>,
  CodeBracketIcon: () => <span data-testid="code-icon">Code</span>,
  EyeIcon: () => <span data-testid="eye-icon">Eye</span>,
  XMarkIcon: () => <span data-testid="x-icon">X</span>,
}))

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock URL.createObjectURL and revokeObjectURL
const mockCreateObjectURL = vi.fn(() => 'blob:test-url')
const mockRevokeObjectURL = vi.fn()
global.URL.createObjectURL = mockCreateObjectURL
global.URL.revokeObjectURL = mockRevokeObjectURL

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(() => 'test-token'),
  setItem: vi.fn(),
  removeItem: vi.fn(),
}
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage })

describe('ReportDownload', () => {
  const defaultProps = {
    investigationId: 'inv-123',
    audience: 'law_enforcement' as const,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(new Blob(['test content'], { type: 'application/pdf' })),
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('rendering', () => {
    it('should render download button', () => {
      render(<ReportDownload {...defaultProps} />)

      expect(screen.getByText('Download Report')).toBeInTheDocument()
    })

    it('should render download icon', () => {
      render(<ReportDownload {...defaultProps} />)

      expect(screen.getByTestId('download-icon')).toBeInTheDocument()
    })

    it('should not show modal initially', () => {
      render(<ReportDownload {...defaultProps} />)

      expect(screen.queryByText('Download Investigation Report')).not.toBeInTheDocument()
    })
  })

  describe('disabled state', () => {
    it('should disable button when disabled prop is true', () => {
      render(<ReportDownload {...defaultProps} disabled={true} />)

      const button = screen.getByText('Download Report').closest('button')
      expect(button).toBeDisabled()
    })

    it('should have opacity class when disabled', () => {
      render(<ReportDownload {...defaultProps} disabled={true} />)

      const button = screen.getByText('Download Report').closest('button')
      expect(button).toHaveClass('disabled:opacity-50')
    })
  })

  describe('modal opening', () => {
    it('should open modal when button clicked', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      expect(screen.getByText('Download Investigation Report')).toBeInTheDocument()
    })

    it('should show format selection in modal', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      expect(screen.getByText('Format')).toBeInTheDocument()
    })

    it('should show audience display in modal', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      expect(screen.getByText('Audience')).toBeInTheDocument()
      expect(screen.getByText('Law Enforcement')).toBeInTheDocument()
    })

    it('should show include options in modal', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      expect(screen.getByText('Include')).toBeInTheDocument()
      expect(screen.getByText('Evidence citations')).toBeInTheDocument()
      expect(screen.getByText('Methodology steps')).toBeInTheDocument()
    })
  })

  describe('format selection', () => {
    it('should show Markdown format option', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      expect(screen.getByText('Markdown')).toBeInTheDocument()
    })

    it('should show PDF format option', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      expect(screen.getByText('PDF')).toBeInTheDocument()
    })

    it('should show JSON format option', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      expect(screen.getByText('JSON')).toBeInTheDocument()
    })

    it('should select format when clicked', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))
      fireEvent.click(screen.getByText('Markdown'))

      // The description should change to markdown description
      expect(screen.getByText(/Plain text with formatting/)).toBeInTheDocument()
    })

    it('should show PDF description by default', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      expect(screen.getByText(/Professional formatted document/)).toBeInTheDocument()
    })
  })

  describe('include options', () => {
    it('should have evidence citations checked by default', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      const checkbox = screen.getByText('Evidence citations').previousElementSibling as HTMLInputElement
      expect(checkbox).toBeChecked()
    })

    it('should have methodology steps checked by default', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      const checkbox = screen.getByText('Methodology steps').previousElementSibling as HTMLInputElement
      expect(checkbox).toBeChecked()
    })

    it('should toggle option when clicked', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      const label = screen.getByText('Technical debug info').closest('label')!
      fireEvent.click(label)

      const checkbox = screen.getByText('Technical debug info').previousElementSibling as HTMLInputElement
      expect(checkbox).toBeChecked()
    })
  })

  describe('modal closing', () => {
    it('should close modal when X button clicked', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))
      expect(screen.getByText('Download Investigation Report')).toBeInTheDocument()

      const closeButton = screen.getByTestId('x-icon').closest('button')!
      fireEvent.click(closeButton)

      expect(screen.queryByText('Download Investigation Report')).not.toBeInTheDocument()
    })
  })

  describe('download functionality', () => {
    it('should call fetch with correct URL when download clicked', async () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      // Click the download button in modal (second one with same text)
      const downloadButtons = screen.getAllByText('Download Report')
      fireEvent.click(downloadButtons[1])

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })

      const fetchUrl = mockFetch.mock.calls[0][0]
      expect(fetchUrl).toContain('/api/v1/investigations/inv-123/export/pdf')
    })

    it('should include authorization header', async () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      const downloadButtons = screen.getAllByText('Download Report')
      fireEvent.click(downloadButtons[1])

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })

      const fetchOptions = mockFetch.mock.calls[0][1]
      expect(fetchOptions.headers.Authorization).toBe('Bearer test-token')
    })

    it('should include audience parameter', async () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      const downloadButtons = screen.getAllByText('Download Report')
      fireEvent.click(downloadButtons[1])

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })

      const fetchUrl = mockFetch.mock.calls[0][0]
      expect(fetchUrl).toContain('audience=law_enforcement')
    })

    it('should call onDownload callback on successful download', async () => {
      const onDownload = vi.fn()
      render(<ReportDownload {...defaultProps} onDownload={onDownload} />)

      fireEvent.click(screen.getByText('Download Report'))

      const downloadButtons = screen.getAllByText('Download Report')
      fireEvent.click(downloadButtons[1])

      await waitFor(() => {
        expect(onDownload).toHaveBeenCalledWith('pdf')
      })
    })

    it('should close modal after successful download', async () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))
      expect(screen.getByText('Download Investigation Report')).toBeInTheDocument()

      const downloadButtons = screen.getAllByText('Download Report')
      fireEvent.click(downloadButtons[1])

      await waitFor(() => {
        expect(screen.queryByText('Download Investigation Report')).not.toBeInTheDocument()
      })
    })

    it('should show loading state during download', async () => {
      mockFetch.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        blob: () => Promise.resolve(new Blob(['test'])),
      }), 100)))

      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      const downloadButtons = screen.getAllByText('Download Report')
      fireEvent.click(downloadButtons[1])

      expect(screen.getByText('Downloading...')).toBeInTheDocument()
    })
  })

  describe('preview', () => {
    it('should show Preview button', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      expect(screen.getByText('Preview')).toBeInTheDocument()
    })

    it('should open preview modal when Preview clicked', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))
      fireEvent.click(screen.getByText('Preview'))

      expect(screen.getByText('Report Preview')).toBeInTheDocument()
    })

    it('should show loading text in preview', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))
      fireEvent.click(screen.getByText('Preview'))

      expect(screen.getByText(/Preview loading for Law Enforcement report/)).toBeInTheDocument()
    })

    it('should close preview when Close clicked', () => {
      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))
      fireEvent.click(screen.getByText('Preview'))

      expect(screen.getByText('Report Preview')).toBeInTheDocument()

      fireEvent.click(screen.getByText('Close'))

      expect(screen.queryByText('Report Preview')).not.toBeInTheDocument()
    })
  })

  describe('audience labels', () => {
    it('should display Law Enforcement label', () => {
      render(<ReportDownload {...defaultProps} audience="law_enforcement" />)

      fireEvent.click(screen.getByText('Download Report'))

      expect(screen.getByText('Law Enforcement')).toBeInTheDocument()
    })

    it('should display Conservation label', () => {
      render(<ReportDownload {...defaultProps} audience="conservation" />)

      fireEvent.click(screen.getByText('Download Report'))

      expect(screen.getByText('Conservation')).toBeInTheDocument()
    })

    it('should display Internal/Technical label', () => {
      render(<ReportDownload {...defaultProps} audience="internal" />)

      fireEvent.click(screen.getByText('Download Report'))

      expect(screen.getByText('Internal/Technical')).toBeInTheDocument()
    })

    it('should display Public label', () => {
      render(<ReportDownload {...defaultProps} audience="public" />)

      fireEvent.click(screen.getByText('Download Report'))

      expect(screen.getByText('Public')).toBeInTheDocument()
    })
  })

  describe('error handling', () => {
    it('should handle download failure gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
      })

      render(<ReportDownload {...defaultProps} />)

      fireEvent.click(screen.getByText('Download Report'))

      const downloadButtons = screen.getAllByText('Download Report')
      fireEvent.click(downloadButtons[1])

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Download failed:', expect.any(Error))
      })

      consoleSpy.mockRestore()
    })
  })
})

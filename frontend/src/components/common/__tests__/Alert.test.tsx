import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import Alert from '../Alert'

describe('Alert', () => {
  it('renders with children', () => {
    render(<Alert>Alert message</Alert>)
    expect(screen.getByText('Alert message')).toBeInTheDocument()
  })

  it('renders with message prop', () => {
    render(<Alert message="Message via prop" />)
    expect(screen.getByText('Message via prop')).toBeInTheDocument()
  })

  it('prefers children over message prop', () => {
    render(<Alert message="Message prop">Children content</Alert>)
    expect(screen.getByText('Children content')).toBeInTheDocument()
    expect(screen.queryByText('Message prop')).not.toBeInTheDocument()
  })

  it('renders title when provided', () => {
    render(<Alert title="Alert Title">Content</Alert>)
    expect(screen.getByText('Alert Title')).toBeInTheDocument()
  })

  it('applies info type styles by default', () => {
    const { container } = render(<Alert>Info alert</Alert>)
    const alertDiv = container.firstChild as HTMLElement
    expect(alertDiv.className).toContain('bg-blue-50')
    expect(alertDiv.className).toContain('border-blue-200')
  })

  it('applies success type styles', () => {
    const { container } = render(<Alert type="success">Success alert</Alert>)
    const alertDiv = container.firstChild as HTMLElement
    expect(alertDiv.className).toContain('bg-green-50')
    expect(alertDiv.className).toContain('border-green-200')
  })

  it('applies warning type styles', () => {
    const { container } = render(<Alert type="warning">Warning alert</Alert>)
    const alertDiv = container.firstChild as HTMLElement
    expect(alertDiv.className).toContain('bg-yellow-50')
    expect(alertDiv.className).toContain('border-yellow-200')
  })

  it('applies error type styles', () => {
    const { container } = render(<Alert type="error">Error alert</Alert>)
    const alertDiv = container.firstChild as HTMLElement
    expect(alertDiv.className).toContain('bg-red-50')
    expect(alertDiv.className).toContain('border-red-200')
  })

  it('renders appropriate icon for info type', () => {
    const { container } = render(<Alert type="info">Info</Alert>)
    const iconWrapper = container.querySelector('.flex-shrink-0')
    expect(iconWrapper).toBeInTheDocument()
    expect(iconWrapper?.querySelector('svg')).toBeInTheDocument()
    expect(iconWrapper?.className).toContain('flex-shrink-0')
  })

  it('renders appropriate icon for success type', () => {
    const { container } = render(<Alert type="success">Success</Alert>)
    const iconWrapper = container.querySelector('.flex-shrink-0')
    expect(iconWrapper).toBeInTheDocument()
  })

  it('renders appropriate icon for warning type', () => {
    const { container } = render(<Alert type="warning">Warning</Alert>)
    const iconWrapper = container.querySelector('.flex-shrink-0')
    expect(iconWrapper).toBeInTheDocument()
  })

  it('renders appropriate icon for error type', () => {
    const { container } = render(<Alert type="error">Error</Alert>)
    const iconWrapper = container.querySelector('.flex-shrink-0')
    expect(iconWrapper).toBeInTheDocument()
  })

  it('renders close button when onClose is provided', () => {
    const handleClose = vi.fn()
    render(<Alert onClose={handleClose}>Dismissible</Alert>)

    const closeButton = screen.getByRole('button')
    expect(closeButton).toBeInTheDocument()
  })

  it('does not render close button when onClose is not provided', () => {
    render(<Alert>Not dismissible</Alert>)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    const handleClose = vi.fn()
    render(<Alert onClose={handleClose}>Dismissible</Alert>)

    fireEvent.click(screen.getByRole('button'))
    expect(handleClose).toHaveBeenCalledOnce()
  })

  it('has accessible dismiss button', () => {
    const handleClose = vi.fn()
    render(<Alert onClose={handleClose}>Dismissible</Alert>)

    expect(screen.getByText('Dismiss')).toBeInTheDocument()
    // The text should be screen-reader only
    expect(screen.getByText('Dismiss').className).toContain('sr-only')
  })

  it('applies custom className', () => {
    const { container } = render(<Alert className="custom-alert">Custom</Alert>)
    const alertDiv = container.firstChild as HTMLElement
    expect(alertDiv.className).toContain('custom-alert')
  })

  it('applies title styling', () => {
    render(<Alert type="info" title="Info Title">Content</Alert>)
    const title = screen.getByText('Info Title')
    expect(title.className).toContain('text-blue-800')
    expect(title.className).toContain('font-medium')
  })

  it('applies spacing between title and content', () => {
    render(<Alert title="Title">Content with title</Alert>)
    const content = screen.getByText('Content with title')
    expect(content.className).toContain('mt-2')
  })

  it('does not apply spacing when no title', () => {
    render(<Alert>Content without title</Alert>)
    const content = screen.getByText('Content without title')
    expect(content.className).not.toContain('mt-2')
  })
})

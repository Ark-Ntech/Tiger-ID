import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import Badge, { ConfidenceBadge, StatusBadge } from '../Badge'

describe('Badge', () => {
  it('renders children correctly', () => {
    render(<Badge>Badge text</Badge>)
    expect(screen.getByText('Badge text')).toBeInTheDocument()
  })

  it('applies default variant styles', () => {
    render(<Badge>Default</Badge>)
    const badge = screen.getByText('Default')
    expect(badge.className).toContain('bg-tactical-100')
    expect(badge.className).toContain('dark:bg-tactical-700')
  })

  it('applies variant styles correctly', () => {
    const { rerender } = render(<Badge variant="success">Success</Badge>)
    let badge = screen.getByText('Success')
    expect(badge.className).toContain('bg-emerald-100')
    expect(badge.className).toContain('text-emerald-800')

    rerender(<Badge variant="warning">Warning</Badge>)
    badge = screen.getByText('Warning')
    expect(badge.className).toContain('bg-amber-100')
    expect(badge.className).toContain('text-amber-800')

    rerender(<Badge variant="danger">Danger</Badge>)
    badge = screen.getByText('Danger')
    expect(badge.className).toContain('bg-red-100')
    expect(badge.className).toContain('text-red-800')

    rerender(<Badge variant="info">Info</Badge>)
    badge = screen.getByText('Info')
    expect(badge.className).toContain('bg-blue-100')
    expect(badge.className).toContain('text-blue-800')

    rerender(<Badge variant="primary">Primary</Badge>)
    badge = screen.getByText('Primary')
    expect(badge.className).toContain('bg-tiger-orange')

    rerender(<Badge variant="outline">Outline</Badge>)
    badge = screen.getByText('Outline')
    expect(badge.className).toContain('bg-transparent')
    expect(badge.className).toContain('border')
  })

  it('maps color prop to variant', () => {
    const { rerender } = render(<Badge color="green">Green</Badge>)
    let badge = screen.getByText('Green')
    expect(badge.className).toContain('bg-emerald-100')

    rerender(<Badge color="blue">Blue</Badge>)
    badge = screen.getByText('Blue')
    expect(badge.className).toContain('bg-blue-100')

    rerender(<Badge color="yellow">Yellow</Badge>)
    badge = screen.getByText('Yellow')
    expect(badge.className).toContain('bg-amber-100')

    rerender(<Badge color="red">Red</Badge>)
    badge = screen.getByText('Red')
    expect(badge.className).toContain('bg-red-100')

    rerender(<Badge color="gray">Gray</Badge>)
    badge = screen.getByText('Gray')
    expect(badge.className).toContain('bg-tactical-100')

    rerender(<Badge color="purple">Purple</Badge>)
    badge = screen.getByText('Purple')
    expect(badge.className).toContain('bg-purple-100')
  })

  it('prefers variant over color prop', () => {
    render(<Badge variant="danger" color="green">Priority</Badge>)
    const badge = screen.getByText('Priority')
    expect(badge.className).toContain('bg-red-100')
    expect(badge.className).not.toContain('bg-emerald-100')
  })

  it('applies size styles correctly', () => {
    const { rerender } = render(<Badge size="xs">XS</Badge>)
    let badge = screen.getByText('XS')
    expect(badge.className).toContain('px-1.5')
    expect(badge.className).toContain('text-2xs')

    rerender(<Badge size="sm">SM</Badge>)
    badge = screen.getByText('SM')
    expect(badge.className).toContain('px-2')
    expect(badge.className).toContain('text-xs')

    rerender(<Badge size="md">MD</Badge>)
    badge = screen.getByText('MD')
    expect(badge.className).toContain('px-2.5')
    expect(badge.className).toContain('text-sm')

    rerender(<Badge size="lg">LG</Badge>)
    badge = screen.getByText('LG')
    expect(badge.className).toContain('px-3')
  })

  it('renders dot when dot prop is true', () => {
    render(<Badge dot>With dot</Badge>)
    const badge = screen.getByText('With dot')
    const dot = badge.querySelector('span.rounded-full')
    expect(dot).toBeInTheDocument()
    expect(dot?.className).toContain('w-1.5')
    expect(dot?.className).toContain('h-1.5')
  })

  it('does not render dot by default', () => {
    render(<Badge>No dot</Badge>)
    const badge = screen.getByText('No dot')
    const dot = badge.querySelector('span.rounded-full.w-1\\.5')
    expect(dot).not.toBeInTheDocument()
  })

  it('renders remove button when removable and onRemove provided', () => {
    const handleRemove = vi.fn()
    render(<Badge removable onRemove={handleRemove}>Removable</Badge>)

    const removeButton = screen.getByRole('button')
    expect(removeButton).toBeInTheDocument()
  })

  it('does not render remove button when only removable prop is true', () => {
    render(<Badge removable>Not removable</Badge>)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('calls onRemove when remove button is clicked', () => {
    const handleRemove = vi.fn()
    render(<Badge removable onRemove={handleRemove}>Removable</Badge>)

    fireEvent.click(screen.getByRole('button'))
    expect(handleRemove).toHaveBeenCalledOnce()
  })

  it('stops propagation when remove button is clicked', () => {
    const handleRemove = vi.fn()
    const handleBadgeClick = vi.fn()

    render(
      <div onClick={handleBadgeClick}>
        <Badge removable onRemove={handleRemove}>Removable</Badge>
      </div>
    )

    fireEvent.click(screen.getByRole('button'))
    expect(handleRemove).toHaveBeenCalledOnce()
    expect(handleBadgeClick).not.toHaveBeenCalled()
  })

  it('applies custom className', () => {
    render(<Badge className="custom-badge">Custom</Badge>)
    expect(screen.getByText('Custom').className).toContain('custom-badge')
  })

  it('applies tiger variant styles', () => {
    render(<Badge variant="tiger">Tiger</Badge>)
    const badge = screen.getByText('Tiger')
    expect(badge.className).toContain('bg-tiger-orange/20')
    expect(badge.className).toContain('text-tiger-orange')
  })
})

describe('ConfidenceBadge', () => {
  it('renders high confidence correctly', () => {
    render(<ConfidenceBadge score={0.90} />)
    expect(screen.getByText(/High/)).toBeInTheDocument()
    expect(screen.getByText(/90%/)).toBeInTheDocument()
  })

  it('renders medium confidence correctly', () => {
    render(<ConfidenceBadge score={0.75} />)
    expect(screen.getByText(/Medium/)).toBeInTheDocument()
    expect(screen.getByText(/75%/)).toBeInTheDocument()
  })

  it('renders low confidence correctly', () => {
    render(<ConfidenceBadge score={0.50} />)
    expect(screen.getByText(/Low/)).toBeInTheDocument()
    expect(screen.getByText(/50%/)).toBeInTheDocument()
  })

  it('renders critical confidence correctly', () => {
    render(<ConfidenceBadge score={0.30} />)
    expect(screen.getByText(/Critical/)).toBeInTheDocument()
    expect(screen.getByText(/30%/)).toBeInTheDocument()
  })

  it('normalizes scores greater than 1', () => {
    render(<ConfidenceBadge score={85} />)
    expect(screen.getByText(/High/)).toBeInTheDocument()
    expect(screen.getByText(/85%/)).toBeInTheDocument()
  })

  it('hides label when showLabel is false', () => {
    render(<ConfidenceBadge score={0.90} showLabel={false} />)
    expect(screen.queryByText('High')).not.toBeInTheDocument()
    expect(screen.getByText('90%')).toBeInTheDocument()
  })

  it('applies size prop', () => {
    render(<ConfidenceBadge score={0.90} size="lg" />)
    const badge = screen.getByText(/90%/)
    expect(badge.className).toContain('px-3')
  })

  it('applies custom className', () => {
    render(<ConfidenceBadge score={0.90} className="custom-confidence" />)
    const badge = screen.getByText(/90%/)
    expect(badge.className).toContain('custom-confidence')
  })

  it('applies correct variant for each level', () => {
    const { rerender } = render(<ConfidenceBadge score={0.90} />)
    let badge = screen.getByText(/90%/)
    expect(badge.className).toContain('bg-emerald-100') // success

    rerender(<ConfidenceBadge score={0.70} />)
    badge = screen.getByText(/70%/)
    expect(badge.className).toContain('bg-amber-100') // warning

    rerender(<ConfidenceBadge score={0.50} />)
    badge = screen.getByText(/50%/)
    expect(badge.className).toContain('bg-orange-100') // orange

    rerender(<ConfidenceBadge score={0.20} />)
    badge = screen.getByText(/20%/)
    expect(badge.className).toContain('bg-red-100') // danger
  })
})

describe('StatusBadge', () => {
  it('renders active status correctly', () => {
    render(<StatusBadge status="active" />)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('renders pending status correctly', () => {
    render(<StatusBadge status="pending" />)
    expect(screen.getByText('Pending')).toBeInTheDocument()
  })

  it('renders completed status correctly', () => {
    render(<StatusBadge status="completed" />)
    expect(screen.getByText('Completed')).toBeInTheDocument()
  })

  it('renders failed status correctly', () => {
    render(<StatusBadge status="failed" />)
    expect(screen.getByText('Failed')).toBeInTheDocument()
  })

  it('renders cancelled status correctly', () => {
    render(<StatusBadge status="cancelled" />)
    expect(screen.getByText('Cancelled')).toBeInTheDocument()
  })

  it('renders processing status correctly', () => {
    render(<StatusBadge status="processing" />)
    expect(screen.getByText('Processing')).toBeInTheDocument()
  })

  it('shows dot by default', () => {
    render(<StatusBadge status="active" />)
    const badge = screen.getByText('Active')
    const dot = badge.querySelector('span.rounded-full')
    expect(dot).toBeInTheDocument()
  })

  it('hides dot when showDot is false', () => {
    render(<StatusBadge status="active" showDot={false} />)
    const badge = screen.getByText('Active')
    const dot = badge.querySelector('span.rounded-full.w-1\\.5')
    expect(dot).not.toBeInTheDocument()
  })

  it('applies size prop', () => {
    render(<StatusBadge status="active" size="lg" />)
    const badge = screen.getByText('Active')
    expect(badge.className).toContain('px-3')
  })

  it('applies custom className', () => {
    render(<StatusBadge status="active" className="custom-status" />)
    const badge = screen.getByText('Active')
    expect(badge.className).toContain('custom-status')
  })

  it('applies correct variant for each status', () => {
    const { rerender } = render(<StatusBadge status="active" />)
    let badge = screen.getByText('Active')
    expect(badge.className).toContain('bg-emerald-100') // success

    rerender(<StatusBadge status="pending" />)
    badge = screen.getByText('Pending')
    expect(badge.className).toContain('bg-amber-100') // warning

    rerender(<StatusBadge status="failed" />)
    badge = screen.getByText('Failed')
    expect(badge.className).toContain('bg-red-100') // danger

    rerender(<StatusBadge status="processing" />)
    badge = screen.getByText('Processing')
    expect(badge.className).toContain('bg-blue-100') // info

    rerender(<StatusBadge status="cancelled" />)
    badge = screen.getByText('Cancelled')
    expect(badge.className).toContain('bg-tactical-100') // default
  })
})

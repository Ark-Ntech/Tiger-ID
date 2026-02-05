import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import Card, { CardHeader, CardTitle, CardDescription, CardContent, CardFooter, StatCard } from '../Card'

describe('Card', () => {
  it('renders children correctly', () => {
    render(<Card>Card content</Card>)
    expect(screen.getByText('Card content')).toBeInTheDocument()
  })

  it('applies default variant styles', () => {
    render(<Card data-testid="card">Content</Card>)
    const card = screen.getByText('Content').closest('div')
    expect(card?.className).toContain('bg-white')
    expect(card?.className).toContain('dark:bg-tactical-800')
  })

  it('applies variant styles correctly', () => {
    const { rerender } = render(<Card variant="elevated">Elevated</Card>)
    let card = screen.getByText('Elevated').closest('div')
    expect(card?.className).toContain('shadow-tactical-lg')

    rerender(<Card variant="critical">Critical</Card>)
    card = screen.getByText('Critical').closest('div')
    expect(card?.className).toContain('border-red-300')

    rerender(<Card variant="evidence">Evidence</Card>)
    card = screen.getByText('Evidence').closest('div')
    expect(card?.className).toContain('border-emerald-200/50')

    rerender(<Card variant="ghost">Ghost</Card>)
    card = screen.getByText('Ghost').closest('div')
    expect(card?.className).toContain('bg-transparent')
  })

  it('applies padding correctly', () => {
    const { rerender } = render(<Card padding="none">No padding</Card>)
    let card = screen.getByText('No padding').closest('div')
    expect(card?.className).not.toContain('p-4')
    expect(card?.className).not.toContain('p-6')

    rerender(<Card padding="sm">Small padding</Card>)
    card = screen.getByText('Small padding').closest('div')
    expect(card?.className).toContain('p-4')

    rerender(<Card padding="lg">Large padding</Card>)
    card = screen.getByText('Large padding').closest('div')
    expect(card?.className).toContain('p-8')
  })

  it('handles click events', () => {
    const handleClick = vi.fn()
    render(<Card onClick={handleClick}>Clickable</Card>)

    fireEvent.click(screen.getByText('Clickable'))
    expect(handleClick).toHaveBeenCalledOnce()
  })

  it('applies hover styles when clickable', () => {
    const handleClick = vi.fn()
    render(<Card onClick={handleClick}>Clickable</Card>)

    const card = screen.getByText('Clickable').closest('div')
    expect(card?.className).toContain('cursor-pointer')
  })

  it('applies hover styles when hoverable prop is true', () => {
    render(<Card hoverable>Hoverable</Card>)

    const card = screen.getByText('Hoverable').closest('div')
    expect(card?.className).toContain('cursor-pointer')
  })

  it('renders as different HTML elements using as prop', () => {
    const { rerender } = render(<Card as="article">Article</Card>)
    expect(screen.getByText('Article').closest('article')).toBeInTheDocument()

    rerender(<Card as="section">Section</Card>)
    expect(screen.getByText('Section').closest('section')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<Card className="custom-class">Custom</Card>)
    const card = screen.getByText('Custom').closest('div')
    expect(card?.className).toContain('custom-class')
  })
})

describe('CardHeader', () => {
  it('renders children correctly', () => {
    render(<CardHeader>Header content</CardHeader>)
    expect(screen.getByText('Header content')).toBeInTheDocument()
  })

  it('renders action when provided', () => {
    render(
      <CardHeader action={<button>Action</button>}>
        Header
      </CardHeader>
    )
    expect(screen.getByText('Action')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<CardHeader className="custom-header">Header</CardHeader>)
    const header = screen.getByText('Header').closest('div')?.parentElement
    expect(header?.className).toContain('custom-header')
  })
})

describe('CardTitle', () => {
  it('renders as h3 by default', () => {
    render(<CardTitle>Title</CardTitle>)
    expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('Title')
  })

  it('renders as different heading levels', () => {
    const { rerender } = render(<CardTitle as="h1">Title</CardTitle>)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Title')

    rerender(<CardTitle as="h2">Title</CardTitle>)
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Title')
  })

  it('applies custom className', () => {
    render(<CardTitle className="custom-title">Title</CardTitle>)
    expect(screen.getByText('Title').className).toContain('custom-title')
  })
})

describe('CardDescription', () => {
  it('renders children correctly', () => {
    render(<CardDescription>Description text</CardDescription>)
    expect(screen.getByText('Description text')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<CardDescription className="custom-desc">Description</CardDescription>)
    expect(screen.getByText('Description').className).toContain('custom-desc')
  })
})

describe('CardContent', () => {
  it('renders children correctly', () => {
    render(<CardContent>Content here</CardContent>)
    expect(screen.getByText('Content here')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<CardContent className="custom-content">Content</CardContent>)
    expect(screen.getByText('Content').className).toContain('custom-content')
  })
})

describe('CardFooter', () => {
  it('renders children correctly', () => {
    render(<CardFooter>Footer content</CardFooter>)
    expect(screen.getByText('Footer content')).toBeInTheDocument()
  })

  it('renders with border by default', () => {
    render(<CardFooter>Footer</CardFooter>)
    const footer = screen.getByText('Footer').closest('div')
    expect(footer?.className).toContain('border-t')
  })

  it('renders without border when border prop is false', () => {
    render(<CardFooter border={false}>Footer</CardFooter>)
    const footer = screen.getByText('Footer').closest('div')
    expect(footer?.className).not.toContain('border-t')
  })

  it('applies custom className', () => {
    render(<CardFooter className="custom-footer">Footer</CardFooter>)
    expect(screen.getByText('Footer').closest('div')?.className).toContain('custom-footer')
  })
})

describe('StatCard', () => {
  it('renders label and value', () => {
    render(<StatCard label="Total Tigers" value={42} />)
    expect(screen.getByText('Total Tigers')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
  })

  it('renders string value', () => {
    render(<StatCard label="Status" value="Active" />)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('renders icon when provided', () => {
    render(
      <StatCard
        label="Tigers"
        value={10}
        icon={<span data-testid="icon">Icon</span>}
      />
    )
    expect(screen.getByTestId('icon')).toBeInTheDocument()
  })

  it('renders positive trend', () => {
    render(
      <StatCard
        label="Growth"
        value={100}
        trend={{ value: 15, isPositive: true }}
      />
    )
    expect(screen.getByText('+15%')).toBeInTheDocument()
  })

  it('renders negative trend', () => {
    render(
      <StatCard
        label="Decline"
        value={100}
        trend={{ value: -10, isPositive: false }}
      />
    )
    expect(screen.getByText('-10%')).toBeInTheDocument()
  })

  it('applies variant to Card', () => {
    render(<StatCard label="Test" value={1} variant="critical" />)
    const card = screen.getByText('Test').closest('div')?.parentElement?.parentElement
    expect(card?.className).toContain('border-red-300')
  })

  it('applies custom className', () => {
    render(<StatCard label="Test" value={1} className="custom-stat" />)
    const card = screen.getByText('Test').closest('div')?.parentElement?.parentElement
    expect(card?.className).toContain('custom-stat')
  })
})

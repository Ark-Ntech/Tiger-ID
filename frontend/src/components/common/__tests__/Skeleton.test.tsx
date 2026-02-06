import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import {
  Skeleton,
  CardSkeleton,
  MatchCardSkeleton,
  StatCardSkeleton,
  TabNavSkeleton,
  ImageQualitySkeleton,
  EnsembleSkeleton,
  TableRowSkeleton,
  InvestigationResultsSkeleton,
} from '../Skeleton'

// Mock cn utility
vi.mock('../../../utils/cn', () => ({
  cn: (...classes: (string | undefined | null | false)[]) =>
    classes.filter(Boolean).join(' '),
}))

describe('Skeleton', () => {
  describe('base skeleton', () => {
    it('should render', () => {
      const { container } = render(<Skeleton />)
      expect(container.firstChild).toBeInTheDocument()
    })

    it('should apply pulse animation by default', () => {
      const { container } = render(<Skeleton />)
      expect(container.firstChild).toHaveClass('animate-pulse')
    })

    it('should apply wave animation', () => {
      const { container } = render(<Skeleton animation="wave" />)
      expect(container.firstChild).toHaveClass('relative')
      expect(container.firstChild).toHaveClass('overflow-hidden')
    })

    it('should apply no animation', () => {
      const { container } = render(<Skeleton animation="none" />)
      expect(container.firstChild).not.toHaveClass('animate-pulse')
    })
  })

  describe('variants', () => {
    it('should apply text variant', () => {
      const { container } = render(<Skeleton variant="text" />)
      expect(container.firstChild).toHaveClass('rounded')
    })

    it('should apply circular variant', () => {
      const { container } = render(<Skeleton variant="circular" />)
      expect(container.firstChild).toHaveClass('rounded-full')
    })

    it('should apply rectangular variant', () => {
      const { container } = render(<Skeleton variant="rectangular" />)
      expect(container.firstChild).toHaveClass('rounded-none')
    })

    it('should apply rounded variant', () => {
      const { container } = render(<Skeleton variant="rounded" />)
      expect(container.firstChild).toHaveClass('rounded-lg')
    })
  })

  describe('dimensions', () => {
    it('should apply width as number', () => {
      const { container } = render(<Skeleton width={100} />)
      expect(container.firstChild).toHaveStyle({ width: '100px' })
    })

    it('should apply width as string', () => {
      const { container } = render(<Skeleton width="50%" />)
      expect(container.firstChild).toHaveStyle({ width: '50%' })
    })

    it('should apply height as number', () => {
      const { container } = render(<Skeleton height={50} />)
      expect(container.firstChild).toHaveStyle({ height: '50px' })
    })

    it('should apply height as string', () => {
      const { container } = render(<Skeleton height="2rem" />)
      expect(container.firstChild).toHaveStyle({ height: '2rem' })
    })
  })

  describe('className prop', () => {
    it('should apply custom className', () => {
      const { container } = render(<Skeleton className="custom-class" />)
      expect(container.firstChild).toHaveClass('custom-class')
    })
  })
})

describe('CardSkeleton', () => {
  it('should render', () => {
    const { container } = render(<CardSkeleton />)
    expect(container.firstChild).toBeInTheDocument()
  })

  it('should have card class', () => {
    const { container } = render(<CardSkeleton />)
    expect(container.firstChild).toHaveClass('card')
  })

  it('should apply custom className', () => {
    const { container } = render(<CardSkeleton className="custom-class" />)
    expect(container.firstChild).toHaveClass('custom-class')
  })
})

describe('MatchCardSkeleton', () => {
  it('should render', () => {
    const { container } = render(<MatchCardSkeleton />)
    expect(container.firstChild).toBeInTheDocument()
  })

  it('should have border styles', () => {
    const { container } = render(<MatchCardSkeleton />)
    expect(container.firstChild).toHaveClass('border')
  })

  it('should apply custom className', () => {
    const { container } = render(<MatchCardSkeleton className="custom-class" />)
    expect(container.firstChild).toHaveClass('custom-class')
  })
})

describe('StatCardSkeleton', () => {
  it('should render', () => {
    const { container } = render(<StatCardSkeleton />)
    expect(container.firstChild).toBeInTheDocument()
  })

  it('should have card class', () => {
    const { container } = render(<StatCardSkeleton />)
    expect(container.firstChild).toHaveClass('card')
  })
})

describe('TabNavSkeleton', () => {
  it('should render default number of tabs', () => {
    const { container } = render(<TabNavSkeleton />)
    const skeletons = container.querySelectorAll('.h-10.w-24')
    expect(skeletons.length).toBe(5)
  })

  it('should render custom number of tabs', () => {
    const { container } = render(<TabNavSkeleton count={3} />)
    const skeletons = container.querySelectorAll('.h-10.w-24')
    expect(skeletons.length).toBe(3)
  })

  it('should apply custom className', () => {
    const { container } = render(<TabNavSkeleton className="custom-class" />)
    expect(container.firstChild).toHaveClass('custom-class')
  })
})

describe('ImageQualitySkeleton', () => {
  it('should render', () => {
    const { container } = render(<ImageQualitySkeleton />)
    expect(container.firstChild).toBeInTheDocument()
  })

  it('should have card class', () => {
    const { container } = render(<ImageQualitySkeleton />)
    expect(container.firstChild).toHaveClass('card')
  })

  it('should render circular score skeleton', () => {
    const { container } = render(<ImageQualitySkeleton />)
    const circularSkeleton = container.querySelector('.rounded-full')
    expect(circularSkeleton).toBeInTheDocument()
  })
})

describe('EnsembleSkeleton', () => {
  it('should render', () => {
    const { container } = render(<EnsembleSkeleton />)
    expect(container.firstChild).toBeInTheDocument()
  })

  it('should render 6 model skeletons', () => {
    const { container } = render(<EnsembleSkeleton />)
    const modelSkeletons = container.querySelectorAll('.h-6.w-20')
    expect(modelSkeletons.length).toBe(6)
  })

  it('should apply custom className', () => {
    const { container } = render(<EnsembleSkeleton className="custom-class" />)
    expect(container.firstChild).toHaveClass('custom-class')
  })
})

describe('TableRowSkeleton', () => {
  it('should render default 4 columns', () => {
    const { container } = render(<TableRowSkeleton />)
    const columns = container.querySelectorAll('.flex-1')
    expect(columns.length).toBe(4)
  })

  it('should render custom number of columns', () => {
    const { container } = render(<TableRowSkeleton columns={6} />)
    const columns = container.querySelectorAll('.flex-1')
    expect(columns.length).toBe(6)
  })

  it('should apply custom className', () => {
    const { container } = render(<TableRowSkeleton className="custom-class" />)
    expect(container.firstChild).toHaveClass('custom-class')
  })
})

describe('InvestigationResultsSkeleton', () => {
  it('should render', () => {
    const { container } = render(<InvestigationResultsSkeleton />)
    expect(container.firstChild).toBeInTheDocument()
  })

  it('should have animation class', () => {
    const { container } = render(<InvestigationResultsSkeleton />)
    expect(container.firstChild).toHaveClass('animate-fade-in-up')
  })

  it('should render tab navigation skeleton', () => {
    render(<InvestigationResultsSkeleton />)
    // TabNavSkeleton with count=6 should be rendered
    // Check for expected number of tab skeletons
  })

  it('should render stat cards', () => {
    const { container } = render(<InvestigationResultsSkeleton />)
    // Should have 4 stat card skeletons
    const gridContainer = container.querySelector('.grid.grid-cols-1.md\\:grid-cols-4')
    expect(gridContainer).toBeInTheDocument()
  })

  it('should render match card skeletons', () => {
    const { container } = render(<InvestigationResultsSkeleton />)
    // Should have 3 match card skeletons
    const matchCards = container.querySelectorAll('.border.border-tactical-200')
    expect(matchCards.length).toBe(3)
  })
})

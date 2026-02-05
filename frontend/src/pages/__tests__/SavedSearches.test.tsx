import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import { BrowserRouter } from 'react-router-dom'
import React from 'react'
import SavedSearches from '../SavedSearches'

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
  BookmarkIcon: ({ className }: { className?: string }) => (
    <span data-testid="bookmark-icon" className={className}>
      Bookmark
    </span>
  ),
}))

// Mock API hooks
const mockSavedSearchesData = {
  data: [
    {
      id: '1',
      name: 'High Priority Investigations',
      description: 'All investigations with high or critical priority',
      query: { priority: ['high', 'critical'] },
      filters: { status: 'active' },
      created_by: 'user123',
      created_at: '2024-01-01T12:00:00Z',
      updated_at: '2024-01-01T12:00:00Z',
    },
    {
      id: '2',
      name: 'Recent Tiger Sightings',
      description: 'Tigers identified in the last 30 days',
      query: { date_range: '30days' },
      filters: { identified: true },
      created_by: 'user123',
      created_at: '2024-01-02T10:00:00Z',
      updated_at: '2024-01-02T10:00:00Z',
    },
  ],
}

const mockEmptyData = {
  data: [],
}

const mockDeleteMutate = vi.fn()
const mockRefetch = vi.fn().mockResolvedValue({})

vi.mock('../../app/api', () => ({
  useGetSavedSearchesQuery: vi.fn(() => ({
    data: mockSavedSearchesData,
    isLoading: false,
    error: null,
    refetch: mockRefetch,
  })),
  useDeleteSavedSearchMutation: vi.fn(() => [
    mockDeleteMutate,
    { isLoading: false },
  ]),
  useCreateSavedSearchMutation: vi.fn(() => [vi.fn(), { isLoading: false }]),
  useUpdateSavedSearchMutation: vi.fn(() => [vi.fn(), { isLoading: false }]),
}))

const createMockStore = () => {
  return configureStore({
    reducer: {
      api: () => ({}),
    },
  })
}

const renderSavedSearches = (store = createMockStore()) => {
  return render(
    <Provider store={store}>
      <BrowserRouter>
        <SavedSearches />
      </BrowserRouter>
    </Provider>
  )
}

describe('SavedSearches', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    // Reset mock to default successful state
    const api = await import('../../app/api')
    vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
      data: mockSavedSearchesData,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    } as any)
  })

  describe('rendering', () => {
    it('should render page header', () => {
      renderSavedSearches()

      expect(screen.getByText('Saved Searches')).toBeInTheDocument()
    })

    it('should render page description', () => {
      renderSavedSearches()

      expect(screen.getByText('Your saved search queries')).toBeInTheDocument()
    })

    it('should render save new search button', () => {
      renderSavedSearches()

      expect(screen.getByRole('button', { name: /save new search/i })).toBeInTheDocument()
    })

    it('should apply correct heading styles', () => {
      renderSavedSearches()

      const heading = screen.getByText('Saved Searches')
      expect(heading.className).toContain('text-3xl')
      expect(heading.className).toContain('font-bold')
    })
  })

  describe('loading state', () => {
    it('should show loading spinner when isLoading is true', async () => {
      const api = await import('../../app/api')
      vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
        refetch: mockRefetch,
      } as any)

      renderSavedSearches()

      // Check for loading spinner
      const spinner = screen.getByTestId('loading-spinner')
      expect(spinner.className).toContain('animate-spin')
    })

    it('should center loading spinner', async () => {
      const api = await import('../../app/api')
      vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
        refetch: mockRefetch,
      } as any)

      renderSavedSearches()

      const container = document.querySelector('.flex.items-center.justify-center.h-full')
      expect(container).toBeInTheDocument()
    })

    it('should use xl size for loading spinner', async () => {
      const api = await import('../../app/api')
      vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
        refetch: mockRefetch,
      } as any)

      renderSavedSearches()

      const spinner = screen.getByTestId('loading-spinner')
      expect(spinner.className).toContain('h-16')
      expect(spinner.className).toContain('w-16')
    })
  })

  describe('empty state', () => {
    it('should show empty state when no searches exist', async () => {
      const api = await import('../../app/api')
      vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
        data: mockEmptyData,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as any)

      renderSavedSearches()

      expect(screen.getByText('No saved searches yet')).toBeInTheDocument()
    })

    it('should show bookmark icon in empty state', async () => {
      const api = await import('../../app/api')
      vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
        data: mockEmptyData,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as any)

      renderSavedSearches()

      const icons = screen.getAllByTestId('bookmark-icon')
      expect(icons.length).toBeGreaterThan(0)
      // At least one should have gray color classes
      const grayIcon = icons.find(icon => icon.className?.includes('text-gray-400'))
      expect(grayIcon).toBeTruthy()
    })

    it('should center empty state content', async () => {
      const api = await import('../../app/api')
      vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
        data: mockEmptyData,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as any)

      renderSavedSearches()

      const card = screen.getByText('No saved searches yet').closest('div')
      expect(card?.className).toContain('text-center')
    })
  })

  describe('saved searches list', () => {
    it('should render all saved searches', () => {
      renderSavedSearches()

      expect(screen.getByText('High Priority Investigations')).toBeInTheDocument()
      expect(screen.getByText('Recent Tiger Sightings')).toBeInTheDocument()
    })

    it('should display search names', () => {
      renderSavedSearches()

      const name1 = screen.getByText('High Priority Investigations')
      const name2 = screen.getByText('Recent Tiger Sightings')

      expect(name1.tagName).toBe('H3')
      expect(name2.tagName).toBe('H3')
    })

    it('should display search descriptions', () => {
      renderSavedSearches()

      expect(screen.getByText('All investigations with high or critical priority')).toBeInTheDocument()
      expect(screen.getByText('Tigers identified in the last 30 days')).toBeInTheDocument()
    })

    it('should show bookmark icon for each search', () => {
      renderSavedSearches()

      const icons = screen.getAllByTestId('bookmark-icon')
      // Should have at least 2 icons for the saved searches
      expect(icons.length).toBeGreaterThanOrEqual(2)
    })

    it('should apply correct styles to search cards', () => {
      const { container } = renderSavedSearches()

      const cards = container.querySelectorAll('.hover\\:shadow-lg')
      expect(cards.length).toBeGreaterThan(0)

      const transitionCards = container.querySelectorAll('.transition-shadow')
      expect(transitionCards.length).toBeGreaterThan(0)
    })

    it('should render run search button for each search', () => {
      renderSavedSearches()

      const buttons = screen.getAllByRole('button', { name: /run search/i })
      expect(buttons).toHaveLength(2)
    })

    it('should use outline variant for run search buttons', () => {
      renderSavedSearches()

      const buttons = screen.getAllByRole('button', { name: /run search/i })
      buttons.forEach(button => {
        expect(button.className).toContain('border-2')
        expect(button.className).toContain('border-primary-600')
      })
    })

    it('should use small size for run search buttons', () => {
      renderSavedSearches()

      const buttons = screen.getAllByRole('button', { name: /run search/i })
      buttons.forEach(button => {
        expect(button.className).toContain('px-3')
        expect(button.className).toContain('py-1.5')
        expect(button.className).toContain('text-sm')
      })
    })
  })

  describe('search interaction', () => {
    it('should handle run search button click', () => {
      renderSavedSearches()

      const runButtons = screen.getAllByRole('button', { name: /run search/i })
      fireEvent.click(runButtons[0])

      // Button should be clickable (not disabled)
      expect(runButtons[0]).not.toBeDisabled()
    })

    it('should show hover effect on search cards', () => {
      const { container } = renderSavedSearches()

      const cards = container.querySelectorAll('.hover\\:shadow-lg')
      expect(cards.length).toBeGreaterThan(0)
    })
  })

  describe('save new search button', () => {
    it('should use primary variant', () => {
      renderSavedSearches()

      const button = screen.getByRole('button', { name: /save new search/i })
      expect(button.className).toContain('bg-primary-600')
    })

    it('should handle click', () => {
      renderSavedSearches()

      const button = screen.getByRole('button', { name: /save new search/i })
      fireEvent.click(button)

      expect(button).not.toBeDisabled()
    })
  })

  describe('layout', () => {
    it('should use space-y-6 for main container', () => {
      const { container } = renderSavedSearches()

      const mainDiv = container.querySelector('.space-y-6')
      expect(mainDiv).toBeInTheDocument()
    })

    it('should use space-y-4 for searches list', () => {
      const { container } = renderSavedSearches()

      const listDiv = container.querySelector('.space-y-4')
      expect(listDiv).toBeInTheDocument()
    })

    it('should use flexbox for header', () => {
      const { container } = renderSavedSearches()

      const header = screen.getByText('Saved Searches').closest('div')?.parentElement
      expect(header?.className).toContain('flex')
      expect(header?.className).toContain('items-center')
      expect(header?.className).toContain('justify-between')
    })

    it('should use flexbox for each search card', () => {
      const { container } = renderSavedSearches()

      // The card content uses flex layout
      const flexElements = container.querySelectorAll('.flex.items-start.justify-between')
      expect(flexElements.length).toBeGreaterThan(0)
    })
  })

  describe('data handling', () => {
    it('should handle undefined data gracefully', async () => {
      const api = await import('../../app/api')
      vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as any)

      renderSavedSearches()

      expect(screen.getByText('No saved searches yet')).toBeInTheDocument()
    })

    it('should handle null data gracefully', async () => {
      const api = await import('../../app/api')
      vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as any)

      renderSavedSearches()

      expect(screen.getByText('No saved searches yet')).toBeInTheDocument()
    })

    it('should handle data without data property', async () => {
      const api = await import('../../app/api')
      vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
        data: {},
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as any)

      renderSavedSearches()

      expect(screen.getByText('No saved searches yet')).toBeInTheDocument()
    })

    it('should render single search correctly', async () => {
      const api = await import('../../app/api')
      vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
        data: {
          data: [
            {
              id: '1',
              name: 'Single Search',
              description: 'A single saved search',
              query: {},
              created_by: 'user123',
              created_at: '2024-01-01T12:00:00Z',
              updated_at: '2024-01-01T12:00:00Z',
            },
          ],
        },
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as any)

      renderSavedSearches()

      expect(screen.getByText('Single Search')).toBeInTheDocument()
      expect(screen.getByText('A single saved search')).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('should have proper heading hierarchy', () => {
      renderSavedSearches()

      const h1 = screen.getByRole('heading', { level: 1 })
      expect(h1).toHaveTextContent('Saved Searches')

      const h3Elements = screen.getAllByRole('heading', { level: 3 })
      expect(h3Elements.length).toBeGreaterThan(0)
    })

    it('should have accessible buttons', () => {
      renderSavedSearches()

      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).toBeInTheDocument()
        expect(button.textContent).toBeTruthy()
      })
    })

    it('should use semantic HTML', () => {
      renderSavedSearches()

      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
      expect(screen.getAllByRole('button').length).toBeGreaterThan(0)
    })
  })

  describe('styling', () => {
    it('should apply text-gray-900 to search names', () => {
      renderSavedSearches()

      const name = screen.getByText('High Priority Investigations')
      expect(name.className).toContain('text-gray-900')
    })

    it('should apply text-gray-600 to descriptions', () => {
      renderSavedSearches()

      const description = screen.getByText('All investigations with high or critical priority')
      expect(description.className).toContain('text-gray-600')
    })

    it('should apply text-primary-600 to bookmark icons', () => {
      renderSavedSearches()

      const icons = screen.getAllByTestId('bookmark-icon')
      // Find icons with primary color (not the gray one in empty state)
      const primaryIcons = icons.filter(icon => icon.className?.includes('text-primary-600'))
      expect(primaryIcons.length).toBeGreaterThan(0)
    })

    it('should use appropriate spacing in cards', () => {
      renderSavedSearches()

      const cardContent = screen.getByText('High Priority Investigations').closest('div')?.parentElement
      expect(cardContent?.className).toContain('space-x-4')
    })
  })

  describe('edge cases', () => {
    it('should handle search without description', async () => {
      const api = await import('../../app/api')
      vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
        data: {
          data: [
            {
              id: '1',
              name: 'No Description Search',
              query: {},
              created_by: 'user123',
              created_at: '2024-01-01T12:00:00Z',
              updated_at: '2024-01-01T12:00:00Z',
            },
          ],
        },
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as any)

      renderSavedSearches()

      expect(screen.getByText('No Description Search')).toBeInTheDocument()
    })

    it('should handle very long search names', async () => {
      const api = await import('../../app/api')
      const longName = 'A'.repeat(100)
      vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
        data: {
          data: [
            {
              id: '1',
              name: longName,
              description: 'Test',
              query: {},
              created_by: 'user123',
              created_at: '2024-01-01T12:00:00Z',
              updated_at: '2024-01-01T12:00:00Z',
            },
          ],
        },
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as any)

      renderSavedSearches()

      expect(screen.getByText(longName)).toBeInTheDocument()
    })

    it('should handle many saved searches', async () => {
      const api = await import('../../app/api')
      const manySearches = Array.from({ length: 50 }, (_, i) => ({
        id: `search-${i}`,
        name: `Search ${i}`,
        description: `Description ${i}`,
        query: {},
        created_by: 'user123',
        created_at: '2024-01-01T12:00:00Z',
        updated_at: '2024-01-01T12:00:00Z',
      }))

      vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
        data: { data: manySearches },
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as any)

      renderSavedSearches()

      expect(screen.getByText('Search 0')).toBeInTheDocument()
      expect(screen.getByText('Search 49')).toBeInTheDocument()
    })

    it('should handle special characters in search names', async () => {
      const api = await import('../../app/api')
      vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
        data: {
          data: [
            {
              id: '1',
              name: 'Search with <> & " special chars',
              description: 'Test & validation',
              query: {},
              created_by: 'user123',
              created_at: '2024-01-01T12:00:00Z',
              updated_at: '2024-01-01T12:00:00Z',
            },
          ],
        },
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as any)

      renderSavedSearches()

      expect(screen.getByText('Search with <> & " special chars')).toBeInTheDocument()
    })
  })

  describe('component integration', () => {
    it('should use Card component for each search', () => {
      renderSavedSearches()

      // Cards should have the characteristic Card styling
      const cards = document.querySelectorAll('[class*="hover:shadow-lg"]')
      expect(cards.length).toBeGreaterThan(0)
    })

    it('should use Button component for actions', () => {
      renderSavedSearches()

      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        // Buttons should have characteristic Button component classes
        expect(button.className).toContain('rounded-lg')
        expect(button.className).toContain('font-medium')
      })
    })

    it('should use LoadingSpinner when loading', async () => {
      const api = await import('../../app/api')
      vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
        refetch: mockRefetch,
      } as any)

      renderSavedSearches()

      const spinner = screen.getByTestId('loading-spinner')
      expect(spinner.className).toContain('animate-spin')
      expect(spinner.className).toContain('border-primary-600')
    })
  })

  describe('react key props', () => {
    it('should use unique keys for search items', () => {
      const { container } = renderSavedSearches()

      const searches = container.querySelectorAll('[class*="hover:shadow-lg"]')
      expect(searches.length).toBe(2)
      // React will handle keys internally; we just verify the items are rendered
    })
  })

  describe('conditional rendering', () => {
    it('should not show empty state when searches exist', () => {
      renderSavedSearches()

      expect(screen.queryByText('No saved searches yet')).not.toBeInTheDocument()
    })

    it('should not show loading spinner when not loading', () => {
      renderSavedSearches()

      const containers = document.querySelectorAll('.h-full')
      const loadingContainer = Array.from(containers).find(
        el => el.className.includes('flex') &&
             el.className.includes('items-center') &&
             el.className.includes('justify-center')
      )

      // Should not have the loading container when data is loaded
      if (loadingContainer) {
        expect(loadingContainer.querySelector('.animate-spin')).not.toBeInTheDocument()
      }
    })

    it('should show searches list only when not loading', () => {
      renderSavedSearches()

      expect(screen.getByText('High Priority Investigations')).toBeInTheDocument()
    })
  })

  describe('type safety', () => {
    it('should handle searches with all optional fields', async () => {
      const api = await import('../../app/api')
      vi.mocked(api.useGetSavedSearchesQuery).mockReturnValue({
        data: {
          data: [
            {
              id: '1',
              name: 'Minimal Search',
              query: {},
              created_by: 'user123',
              created_at: '2024-01-01T12:00:00Z',
              updated_at: '2024-01-01T12:00:00Z',
            },
          ],
        },
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as any)

      expect(() => renderSavedSearches()).not.toThrow()
    })
  })
})

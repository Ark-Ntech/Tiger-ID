import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import { BrowserRouter } from 'react-router-dom'
import React from 'react'
import SearchResults from '../SearchResults'

// Mock react-router-dom
const mockNavigate = vi.fn()
const mockSearchParams = new URLSearchParams()
const mockSetSearchParams = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useSearchParams: () => [mockSearchParams, mockSetSearchParams],
  }
})

// Mock heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  MagnifyingGlassIcon: () => <div data-testid="magnifying-glass-icon">MagnifyingGlassIcon</div>,
  FolderIcon: () => <div data-testid="folder-icon">FolderIcon</div>,
  ShieldCheckIcon: () => <div data-testid="shield-check-icon">ShieldCheckIcon</div>,
  BuildingOfficeIcon: () => <div data-testid="building-office-icon">BuildingOfficeIcon</div>,
  DocumentTextIcon: () => <div data-testid="document-text-icon">DocumentTextIcon</div>,
}))

// Mock API hooks
const mockUseGlobalSearchQuery = vi.fn()

vi.mock('../../app/api', () => ({
  useGlobalSearchQuery: (params: any, options: any) => mockUseGlobalSearchQuery(params, options),
}))

// Mock data
const mockInvestigations = [
  {
    id: 'inv-1',
    title: 'Tiger Trafficking Case #1',
    description: 'Investigation into suspected tiger trafficking ring',
    status: 'completed',
    priority: 'high',
  },
  {
    id: 'inv-2',
    title: 'Facility Inspection Report',
    description: 'Follow-up on facility violations',
    status: 'active',
    priority: 'medium',
  },
]

const mockTigers = [
  {
    id: 'tiger-1',
    name: 'Bengal Tiger',
    images: ['img1.jpg', 'img2.jpg'],
  },
  {
    id: 'tiger-2',
    name: null,
    images: ['img3.jpg'],
  },
  {
    id: 'tiger-3',
    name: 'Siberian Tiger',
    images: [],
  },
]

const mockFacilities = [
  {
    id: 'facility-1',
    exhibitor_name: 'Wildlife Sanctuary',
    name: 'Tiger Haven',
    city: 'Austin',
    state: 'TX',
    tiger_count: 12,
  },
  {
    id: 'facility-2',
    exhibitor_name: null,
    name: 'Big Cat Rescue',
    city: null,
    state: 'FL',
    tiger_count: 5,
  },
  {
    id: 'facility-3',
    exhibitor_name: 'Zoo Corp',
    name: null,
    city: 'Denver',
    state: null,
    tiger_count: undefined,
  },
]

const mockEvidence = [
  {
    id: 'evidence-1',
    title: 'Photo Evidence',
    description: 'Tiger photo from social media',
    source_type: 'social_media',
    investigation_id: 'inv-1',
  },
  {
    id: 'evidence-2',
    title: null,
    description: 'Document from facility',
    source_type: null,
    investigation_id: null,
  },
]

const createMockStore = () => {
  return configureStore({
    reducer: {
      api: () => ({}),
    },
  })
}

const renderSearchResults = (store = createMockStore()) => {
  return render(
    <Provider store={store}>
      <BrowserRouter>
        <SearchResults />
      </BrowserRouter>
    </Provider>
  )
}

describe('SearchResults', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSearchParams.delete('q')
  })

  describe('loading state', () => {
    it('should display loading spinner when loading', () => {
      mockSearchParams.set('q', 'tiger')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
      })

      renderSearchResults()

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    })
  })

  describe('error state', () => {
    it('should display error message when search fails', () => {
      mockSearchParams.set('q', 'tiger')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: null,
        isLoading: false,
        error: { message: 'Network error' },
      })

      renderSearchResults()

      expect(screen.getByText('Error performing search. Please try again.')).toBeInTheDocument()
    })

    it('should render error in Card component', () => {
      mockSearchParams.set('q', 'tiger')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: null,
        isLoading: false,
        error: { message: 'Network error' },
      })

      const { container } = renderSearchResults()

      expect(container.querySelector('.text-red-600')).toBeInTheDocument()
    })
  })

  describe('empty state', () => {
    it('should display empty message when no results found', () => {
      mockSearchParams.set('q', 'nonexistent')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: [],
              tigers: [],
              facilities: [],
              evidence: [],
            },
          },
        },
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(screen.getByText(/No results found for "nonexistent"/)).toBeInTheDocument()
      expect(screen.getByText('Try a different search term')).toBeInTheDocument()
      expect(screen.getByTestId('magnifying-glass-icon')).toBeInTheDocument()
    })

    it('should show 0 results in header', () => {
      mockSearchParams.set('q', 'nothing')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: [],
              tigers: [],
              facilities: [],
              evidence: [],
            },
          },
        },
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(screen.getByText('Found 0 results for "nothing"')).toBeInTheDocument()
    })
  })

  describe('query handling', () => {
    it('should skip search when query is empty', () => {
      mockSearchParams.set('q', '')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(mockUseGlobalSearchQuery).toHaveBeenCalledWith(
        { q: '', limit: 50 },
        { skip: true }
      )
    })

    it('should skip search when query is less than 2 characters', () => {
      mockSearchParams.set('q', 'a')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(mockUseGlobalSearchQuery).toHaveBeenCalledWith(
        { q: 'a', limit: 50 },
        { skip: true }
      )
    })

    it('should perform search when query is 2 or more characters', () => {
      mockSearchParams.set('q', 'tiger')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: [],
              tigers: [],
              facilities: [],
              evidence: [],
            },
          },
        },
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(mockUseGlobalSearchQuery).toHaveBeenCalledWith(
        { q: 'tiger', limit: 50 },
        { skip: false }
      )
    })
  })

  describe('search results display', () => {
    it('should display search results header with query', () => {
      mockSearchParams.set('q', 'tiger')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: mockInvestigations,
              tigers: [],
              facilities: [],
              evidence: [],
            },
          },
        },
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(screen.getByText('Search Results')).toBeInTheDocument()
      expect(screen.getByText('Found 2 results for "tiger"')).toBeInTheDocument()
    })

    it('should use singular "result" when count is 1', () => {
      mockSearchParams.set('q', 'test')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: [mockInvestigations[0]],
              tigers: [],
              facilities: [],
              evidence: [],
            },
          },
        },
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(screen.getByText('Found 1 result for "test"')).toBeInTheDocument()
    })

    it('should calculate total results across all categories', () => {
      mockSearchParams.set('q', 'comprehensive')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: mockInvestigations, // 2
              tigers: mockTigers, // 3
              facilities: mockFacilities, // 3
              evidence: mockEvidence, // 2
            },
          },
        },
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(screen.getByText('Found 10 results for "comprehensive"')).toBeInTheDocument()
    })
  })

  describe('investigations section', () => {
    beforeEach(() => {
      mockSearchParams.set('q', 'investigation')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: mockInvestigations,
              tigers: [],
              facilities: [],
              evidence: [],
            },
          },
        },
        isLoading: false,
        error: null,
      })
    })

    it('should render investigations section when investigations exist', () => {
      renderSearchResults()

      expect(screen.getByText('Investigations (2)')).toBeInTheDocument()
      expect(screen.getByTestId('folder-icon')).toBeInTheDocument()
    })

    it('should display all investigation cards', () => {
      renderSearchResults()

      expect(screen.getByText('Tiger Trafficking Case #1')).toBeInTheDocument()
      expect(screen.getByText('Facility Inspection Report')).toBeInTheDocument()
    })

    it('should display investigation descriptions', () => {
      renderSearchResults()

      expect(screen.getByText('Investigation into suspected tiger trafficking ring')).toBeInTheDocument()
      expect(screen.getByText('Follow-up on facility violations')).toBeInTheDocument()
    })

    it('should display status badges', () => {
      renderSearchResults()

      expect(screen.getByText('completed')).toBeInTheDocument()
      expect(screen.getByText('active')).toBeInTheDocument()
    })

    it('should display priority badges', () => {
      renderSearchResults()

      expect(screen.getByText('high')).toBeInTheDocument()
      expect(screen.getByText('medium')).toBeInTheDocument()
    })

    it('should navigate to investigation detail on click', () => {
      renderSearchResults()

      const firstInvestigation = screen.getByText('Tiger Trafficking Case #1').closest('div')
      expect(firstInvestigation).not.toBeNull()

      if (firstInvestigation) {
        fireEvent.click(firstInvestigation)
        expect(mockNavigate).toHaveBeenCalledWith('/investigations/inv-1')
      }
    })

    it('should apply hover styles to investigation cards', () => {
      const { container } = renderSearchResults()

      const cards = container.querySelectorAll('.hover\\:bg-gray-100')
      expect(cards.length).toBeGreaterThan(0)
    })
  })

  describe('tigers section', () => {
    beforeEach(() => {
      mockSearchParams.set('q', 'tiger')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: [],
              tigers: mockTigers,
              facilities: [],
              evidence: [],
            },
          },
        },
        isLoading: false,
        error: null,
      })
    })

    it('should render tigers section when tigers exist', () => {
      renderSearchResults()

      expect(screen.getByText('Tigers (3)')).toBeInTheDocument()
      expect(screen.getByTestId('shield-check-icon')).toBeInTheDocument()
    })

    it('should display tiger names', () => {
      renderSearchResults()

      expect(screen.getByText('Bengal Tiger')).toBeInTheDocument()
      expect(screen.getByText('Siberian Tiger')).toBeInTheDocument()
    })

    it('should display truncated ID when tiger has no name', () => {
      renderSearchResults()

      expect(screen.getByText('Tiger tiger-2')).toBeInTheDocument()
    })

    it('should display image count with plural', () => {
      renderSearchResults()

      expect(screen.getByText('2 images')).toBeInTheDocument()
    })

    it('should display image count with singular', () => {
      renderSearchResults()

      expect(screen.getByText('1 image')).toBeInTheDocument()
    })

    it('should not display image count when no images', () => {
      renderSearchResults()

      const siberianCard = screen.getByText('Siberian Tiger').closest('div')
      expect(siberianCard).not.toBeNull()

      if (siberianCard) {
        expect(within(siberianCard).queryByText(/image/)).not.toBeInTheDocument()
      }
    })

    it('should navigate to tigers page on click', () => {
      renderSearchResults()

      const firstTiger = screen.getByText('Bengal Tiger').closest('div')
      expect(firstTiger).not.toBeNull()

      if (firstTiger) {
        fireEvent.click(firstTiger)
        expect(mockNavigate).toHaveBeenCalledWith('/tigers')
      }
    })

    it('should render tigers in grid layout', () => {
      const { container } = renderSearchResults()

      const gridContainer = container.querySelector('.grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-3')
      expect(gridContainer).toBeInTheDocument()
    })
  })

  describe('facilities section', () => {
    beforeEach(() => {
      mockSearchParams.set('q', 'facility')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: [],
              tigers: [],
              facilities: mockFacilities,
              evidence: [],
            },
          },
        },
        isLoading: false,
        error: null,
      })
    })

    it('should render facilities section when facilities exist', () => {
      renderSearchResults()

      expect(screen.getByText('Facilities (3)')).toBeInTheDocument()
      expect(screen.getByTestId('building-office-icon')).toBeInTheDocument()
    })

    it('should display exhibitor name when available', () => {
      renderSearchResults()

      expect(screen.getByText('Wildlife Sanctuary')).toBeInTheDocument()
    })

    it('should fallback to name when no exhibitor name', () => {
      renderSearchResults()

      expect(screen.getByText('Big Cat Rescue')).toBeInTheDocument()
    })

    it('should display city and state', () => {
      renderSearchResults()

      expect(screen.getByText('Austin, TX')).toBeInTheDocument()
    })

    it('should display state only when no city', () => {
      renderSearchResults()

      expect(screen.getByText('FL')).toBeInTheDocument()
    })

    it('should display city only when no state', () => {
      renderSearchResults()

      expect(screen.getByText('Denver')).toBeInTheDocument()
    })

    it('should display "Location unknown" when no city or state', () => {
      mockSearchParams.set('q', 'unknown')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: [],
              tigers: [],
              facilities: [
                {
                  id: 'fac-unknown',
                  exhibitor_name: 'Unknown Location',
                  name: null,
                  city: null,
                  state: null,
                  tiger_count: 0,
                },
              ],
              evidence: [],
            },
          },
        },
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(screen.getByText('Location unknown')).toBeInTheDocument()
    })

    it('should display tiger count with plural', () => {
      renderSearchResults()

      expect(screen.getByText('12 tigers')).toBeInTheDocument()
    })

    it('should display tiger count with singular', () => {
      renderSearchResults()

      expect(screen.getByText('5 tigers')).toBeInTheDocument()
    })

    it('should not display tiger count when undefined', () => {
      renderSearchResults()

      const zooCard = screen.getByText('Zoo Corp').closest('div')
      expect(zooCard).not.toBeNull()

      if (zooCard) {
        expect(within(zooCard).queryByText(/tiger/)).not.toBeInTheDocument()
      }
    })

    it('should navigate to facility detail on click', () => {
      renderSearchResults()

      const firstFacility = screen.getByText('Wildlife Sanctuary').closest('div')
      expect(firstFacility).not.toBeNull()

      if (firstFacility) {
        fireEvent.click(firstFacility)
        expect(mockNavigate).toHaveBeenCalledWith('/facilities/facility-1')
      }
    })
  })

  describe('evidence section', () => {
    beforeEach(() => {
      mockSearchParams.set('q', 'evidence')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: [],
              tigers: [],
              facilities: [],
              evidence: mockEvidence,
            },
          },
        },
        isLoading: false,
        error: null,
      })
    })

    it('should render evidence section when evidence exists', () => {
      renderSearchResults()

      expect(screen.getByText('Evidence (2)')).toBeInTheDocument()
      expect(screen.getByTestId('document-text-icon')).toBeInTheDocument()
    })

    it('should display evidence title', () => {
      renderSearchResults()

      expect(screen.getByText('Photo Evidence')).toBeInTheDocument()
    })

    it('should fallback to "Evidence" when no title', () => {
      renderSearchResults()

      const evidenceCards = screen.getAllByText('Evidence')
      expect(evidenceCards.length).toBeGreaterThan(0)
    })

    it('should display evidence description', () => {
      renderSearchResults()

      expect(screen.getByText('Tiger photo from social media')).toBeInTheDocument()
      expect(screen.getByText('Document from facility')).toBeInTheDocument()
    })

    it('should display source type badge', () => {
      renderSearchResults()

      expect(screen.getByText('social_media')).toBeInTheDocument()
    })

    it('should display "Unknown" when no source type', () => {
      renderSearchResults()

      expect(screen.getByText('Unknown')).toBeInTheDocument()
    })

    it('should navigate to investigation when investigation_id exists', () => {
      renderSearchResults()

      const firstEvidence = screen.getByText('Photo Evidence').closest('div')
      expect(firstEvidence).not.toBeNull()

      if (firstEvidence) {
        fireEvent.click(firstEvidence)
        expect(mockNavigate).toHaveBeenCalledWith('/investigations/inv-1')
      }
    })

    it('should not navigate when investigation_id is null', () => {
      renderSearchResults()

      const secondEvidence = screen.getByText('Document from facility').closest('div')
      expect(secondEvidence).not.toBeNull()

      if (secondEvidence) {
        mockNavigate.mockClear()
        fireEvent.click(secondEvidence)
        expect(mockNavigate).not.toHaveBeenCalled()
      }
    })
  })

  describe('mixed results', () => {
    it('should render all sections when results exist in all categories', () => {
      mockSearchParams.set('q', 'all')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: mockInvestigations,
              tigers: mockTigers,
              facilities: mockFacilities,
              evidence: mockEvidence,
            },
          },
        },
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(screen.getByText('Investigations (2)')).toBeInTheDocument()
      expect(screen.getByText('Tigers (3)')).toBeInTheDocument()
      expect(screen.getByText('Facilities (3)')).toBeInTheDocument()
      expect(screen.getByText('Evidence (2)')).toBeInTheDocument()
    })

    it('should not render section if results are null', () => {
      mockSearchParams.set('q', 'partial')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: mockInvestigations,
              tigers: null,
              facilities: null,
              evidence: null,
            },
          },
        },
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(screen.getByText('Investigations (2)')).toBeInTheDocument()
      expect(screen.queryByText(/Tigers/)).not.toBeInTheDocument()
      expect(screen.queryByText(/Facilities/)).not.toBeInTheDocument()
      expect(screen.queryByText(/Evidence/)).not.toBeInTheDocument()
    })

    it('should handle missing data gracefully', () => {
      mockSearchParams.set('q', 'test')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: undefined,
          },
        },
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(screen.getByText('Found 0 results for "test"')).toBeInTheDocument()
    })

    it('should handle null data response', () => {
      mockSearchParams.set('q', 'test')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(screen.getByText('Found 0 results for "test"')).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('should have proper heading hierarchy', () => {
      mockSearchParams.set('q', 'accessibility')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: mockInvestigations,
              tigers: [],
              facilities: [],
              evidence: [],
            },
          },
        },
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      const h1 = screen.getByRole('heading', { level: 1, name: 'Search Results' })
      expect(h1).toBeInTheDocument()

      const h2 = screen.getByRole('heading', { level: 2, name: 'Investigations (2)' })
      expect(h2).toBeInTheDocument()
    })

    it('should have proper heading structure for investigation items', () => {
      mockSearchParams.set('q', 'test')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: mockInvestigations,
              tigers: [],
              facilities: [],
              evidence: [],
            },
          },
        },
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      const h3Elements = screen.getAllByRole('heading', { level: 3 })
      expect(h3Elements.length).toBeGreaterThan(0)
    })
  })

  describe('edge cases', () => {
    it('should handle empty query parameter', () => {
      mockSearchParams.delete('q')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(mockUseGlobalSearchQuery).toHaveBeenCalledWith(
        { q: '', limit: 50 },
        { skip: true }
      )
    })

    it('should handle special characters in query', () => {
      mockSearchParams.set('q', 'tiger & "sanctuary"')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: [],
              tigers: [],
              facilities: [],
              evidence: [],
            },
          },
        },
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(screen.getByText(/Found 0 results for "tiger & "sanctuary""/)).toBeInTheDocument()
    })

    it('should handle very long query strings', () => {
      const longQuery = 'a'.repeat(200)
      mockSearchParams.set('q', longQuery)
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: [],
              tigers: [],
              facilities: [],
              evidence: [],
            },
          },
        },
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(screen.getByText(new RegExp(`Found 0 results for "${longQuery}"`))).toBeInTheDocument()
    })

    it('should handle tiger ID substring edge cases', () => {
      mockSearchParams.set('q', 'tiger')
      mockUseGlobalSearchQuery.mockReturnValue({
        data: {
          data: {
            results: {
              investigations: [],
              tigers: [
                {
                  id: 'abc',
                  name: null,
                  images: [],
                },
              ],
              facilities: [],
              evidence: [],
            },
          },
        },
        isLoading: false,
        error: null,
      })

      renderSearchResults()

      expect(screen.getByText('Tiger abc')).toBeInTheDocument()
    })
  })
})

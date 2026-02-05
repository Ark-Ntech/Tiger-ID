import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import FacilityDetail from '../FacilityDetail'

// Mock facility data
const mockFacility = {
  id: 'facility-1',
  name: 'Wildlife Sanctuary',
  exhibitor_name: 'Tiger Conservation Foundation',
  license_number: 'TCF-001',
  usda_license: 'USDA-123-456',
  facility_type: 'sanctuary',
  address: '123 Conservation Way',
  city: 'Tampa',
  state: 'Florida',
  country: 'USA',
  latitude: 27.9506,
  longitude: -82.4572,
  status: 'active' as const,
  verified: true,
  tiger_count: 45,
  tiger_capacity: 60,
  accreditation_status: 'Accredited',
  ir_date: '2023-06-15T10:00:00Z',
  last_inspection_date: '2024-01-15T10:30:00Z',
  website: 'https://wildlifesanctuary.example.com',
  social_media_links: {
    facebook: 'https://facebook.com/wildlifesanctuary',
    instagram: 'https://instagram.com/wildlifesanctuary',
    twitter: 'https://twitter.com/wildlifesanctuary',
  },
  is_reference_facility: true,
  data_source: 'USDA Records',
  reference_metadata: {
    inspection_score: 95,
    compliance_level: 'High',
    last_audit: '2024-01-10',
  },
  created_at: '2023-01-10T08:00:00Z',
  updated_at: '2024-01-20T14:30:00Z',
}

const mockMinimalFacility = {
  id: 'facility-2',
  name: 'Small Rescue Center',
  facility_type: 'rescue',
  address: '',
  city: '',
  state: 'Texas',
  country: 'USA',
  status: 'active' as const,
  verified: false,
  created_at: '2023-05-01T08:00:00Z',
  updated_at: '2023-05-01T08:00:00Z',
}

const mockNonAccreditedFacility = {
  id: 'facility-3',
  name: 'Suspicious Zoo',
  exhibitor_name: 'Unknown Operator',
  facility_type: 'zoo',
  address: '456 Main St',
  city: 'Miami',
  state: 'Florida',
  country: 'USA',
  status: 'active' as const,
  verified: false,
  tiger_count: 12,
  accreditation_status: 'Non-Accredited',
  is_reference_facility: false,
  created_at: '2022-08-15T10:00:00Z',
  updated_at: '2024-01-05T09:00:00Z',
}

const mockTigers = [
  {
    id: 'tiger-1',
    name: 'Raja',
    metadata: {
      origin_facility_id: 'facility-1',
    },
    images: [
      { id: 'img-1', url: '/raja-1.jpg' },
      { id: 'img-2', url: '/raja-2.jpg' },
    ],
  },
  {
    id: 'tiger-2',
    name: 'Sita',
    metadata: {
      origin_facility_id: 'facility-1',
    },
    images: [{ id: 'img-3', url: '/sita-1.jpg' }],
  },
  {
    id: 'tiger-3',
    name: 'Kahn',
    metadata: {
      origin_facility_id: 'facility-2',
    },
    images: [],
  },
]

const mockNavigate = vi.fn()
const mockUseGetFacilityQuery = vi.fn()
const mockUseGetTigersQuery = vi.fn()

vi.mock('../../app/api', () => ({
  useGetFacilityQuery: (id: string) => mockUseGetFacilityQuery(id),
  useGetTigersQuery: (params: any) => mockUseGetTigersQuery(params),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: () => ({ id: 'facility-1' }),
    useNavigate: () => mockNavigate,
  }
})

// Mock heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  BuildingOfficeIcon: () => <svg data-testid="building-icon" />,
  GlobeAltIcon: () => <svg data-testid="globe-icon" />,
  LinkIcon: () => <svg data-testid="link-icon" />,
  ArrowLeftIcon: () => <svg data-testid="arrow-left-icon" />,
  ShieldCheckIcon: () => <svg data-testid="shield-check-icon" />,
  MapPinIcon: () => <svg data-testid="map-pin-icon" />,
  CalendarIcon: () => <svg data-testid="calendar-icon" />,
  InformationCircleIcon: () => <svg data-testid="info-icon" />,
  ExclamationTriangleIcon: () => <svg data-testid="warning-icon" />,
  CheckCircleIcon: () => <svg data-testid="check-icon" />,
  XCircleIcon: () => <svg data-testid="x-circle-icon" />,
}))

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

describe('FacilityDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('loading state', () => {
    it('should show loading spinner when fetching facility', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      const loadingElement = screen.getByRole('status') || screen.getByText(/loading/i)
      expect(loadingElement).toBeInTheDocument()
    })

    it('should center loading spinner', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      const container = screen.getByRole('status').closest('div')
      expect(container).toHaveClass('flex', 'items-center', 'justify-center')
    })
  })

  describe('error state', () => {
    it('should show error alert when fetch fails', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Failed to fetch facility' },
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText(/error loading facility/i)).toBeInTheDocument()
    })

    it('should show back button on error', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Network error' },
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      const backButton = screen.getByText(/back to facilities/i)
      expect(backButton).toBeInTheDocument()
    })

    it('should navigate back when clicking back button on error', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Error' },
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      const backButton = screen.getByText(/back to facilities/i)
      fireEvent.click(backButton)

      expect(mockNavigate).toHaveBeenCalledWith('/facilities')
    })
  })

  describe('not found state', () => {
    it('should show not found alert when facility is null', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: null,
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText(/facility not found/i)).toBeInTheDocument()
    })

    it('should show not found alert when data.data is undefined', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: undefined },
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText(/facility not found/i)).toBeInTheDocument()
    })
  })

  describe('facility header', () => {
    beforeEach(() => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: mockFacility },
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: mockTigers } },
      })
    })

    it('should display facility name from exhibitor_name if available', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Tiger Conservation Foundation')).toBeInTheDocument()
    })

    it('should display facility name from name if exhibitor_name not available', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: { ...mockFacility, exhibitor_name: undefined } },
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Wildlife Sanctuary')).toBeInTheDocument()
    })

    it('should display location with city and state', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Tampa, Florida')).toBeInTheDocument()
    })

    it('should display only state when city is missing', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: { ...mockFacility, city: '' } },
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Florida')).toBeInTheDocument()
    })

    it('should display location unknown when city and state are missing', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: { ...mockFacility, city: '', state: '' } },
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Location unknown')).toBeInTheDocument()
    })

    it('should show reference facility badge when is_reference_facility is true', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText(/⭐ reference facility/i)).toBeInTheDocument()
    })

    it('should not show reference facility badge when is_reference_facility is false', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: { ...mockFacility, is_reference_facility: false } },
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.queryByText(/⭐ reference facility/i)).not.toBeInTheDocument()
    })

    it('should show accreditation status badge', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Accredited')).toBeInTheDocument()
    })

    it('should show warning badge for non-accredited facilities', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: mockNonAccreditedFacility },
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: [] } },
      })

      renderWithRouter(<FacilityDetail />)

      const badge = screen.getByText('Non-Accredited')
      expect(badge).toBeInTheDocument()
    })

    it('should show building icon', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByTestId('building-icon')).toBeInTheDocument()
    })

    it('should show back button', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Back')).toBeInTheDocument()
    })

    it('should navigate back when clicking back button', () => {
      renderWithRouter(<FacilityDetail />)

      const backButton = screen.getByText('Back')
      fireEvent.click(backButton)

      expect(mockNavigate).toHaveBeenCalledWith('/facilities')
    })
  })

  describe('basic information section', () => {
    beforeEach(() => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: mockFacility },
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: mockTigers } },
      })
    })

    it('should display section title', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Basic Information')).toBeInTheDocument()
    })

    it('should display address when available', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Address')).toBeInTheDocument()
      expect(screen.getByText('123 Conservation Way')).toBeInTheDocument()
    })

    it('should not display address section when address is missing', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: mockMinimalFacility },
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: [] } },
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.queryByText('Address')).not.toBeInTheDocument()
    })

    it('should display tiger count when available', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Tiger Count')).toBeInTheDocument()
      expect(screen.getByText('45')).toBeInTheDocument()
    })

    it('should display tiger capacity when available', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Tiger Capacity')).toBeInTheDocument()
      expect(screen.getByText('60')).toBeInTheDocument()
    })

    it('should display IR date when available', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('IR Date')).toBeInTheDocument()
    })

    it('should display last inspection date when available', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Last Inspection')).toBeInTheDocument()
    })

    it('should format dates correctly', () => {
      renderWithRouter(<FacilityDetail />)

      // Check for formatted date (e.g., "January 15, 2024")
      expect(screen.getByText(/january.*2024/i)).toBeInTheDocument()
    })

    it('should show calendar icons for date fields', () => {
      renderWithRouter(<FacilityDetail />)

      const calendarIcons = screen.getAllByTestId('calendar-icon')
      expect(calendarIcons.length).toBeGreaterThan(0)
    })

    it('should show map pin icon for address', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByTestId('map-pin-icon')).toBeInTheDocument()
    })
  })

  describe('links section', () => {
    beforeEach(() => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: mockFacility },
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: mockTigers } },
      })
    })

    it('should display links section when website is available', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Links')).toBeInTheDocument()
    })

    it('should display website link with globe icon', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Website')).toBeInTheDocument()
      expect(screen.getByTestId('globe-icon')).toBeInTheDocument()
    })

    it('should link to website with correct URL', () => {
      renderWithRouter(<FacilityDetail />)

      const websiteLink = screen.getByText('Website').closest('a')
      expect(websiteLink).toHaveAttribute('href', 'https://wildlifesanctuary.example.com')
      expect(websiteLink).toHaveAttribute('target', '_blank')
      expect(websiteLink).toHaveAttribute('rel', 'noopener noreferrer')
    })

    it('should prepend https:// to website URL if missing', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: { ...mockFacility, website: 'wildlifesanctuary.example.com' } },
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      const websiteLink = screen.getByText('Website').closest('a')
      expect(websiteLink).toHaveAttribute('href', 'https://wildlifesanctuary.example.com')
    })

    it('should display social media links', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Facebook')).toBeInTheDocument()
      expect(screen.getByText('Instagram')).toBeInTheDocument()
      expect(screen.getByText('Twitter')).toBeInTheDocument()
    })

    it('should display social media links with link icons', () => {
      renderWithRouter(<FacilityDetail />)

      const linkIcons = screen.getAllByTestId('link-icon')
      expect(linkIcons.length).toBe(3)
    })

    it('should capitalize social media platform names', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Facebook')).toBeInTheDocument()
    })

    it('should link to social media with correct URLs', () => {
      renderWithRouter(<FacilityDetail />)

      const facebookLink = screen.getByText('Facebook').closest('a')
      expect(facebookLink).toHaveAttribute('href', 'https://facebook.com/wildlifesanctuary')
      expect(facebookLink).toHaveAttribute('target', '_blank')
    })

    it('should not display links section when no website or social media', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: { ...mockFacility, website: undefined, social_media_links: {} } },
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.queryByText('Links')).not.toBeInTheDocument()
    })

    it('should not display links section when social_media_links is undefined', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: { ...mockFacility, website: undefined, social_media_links: undefined } },
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.queryByText('Links')).not.toBeInTheDocument()
    })
  })

  describe('associated tigers section', () => {
    beforeEach(() => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: mockFacility },
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: mockTigers } },
      })
    })

    it('should display associated tigers section when tigers exist', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText(/associated tigers/i)).toBeInTheDocument()
    })

    it('should show tiger count in section title', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Associated Tigers (2)')).toBeInTheDocument()
    })

    it('should display shield check icon', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByTestId('shield-check-icon')).toBeInTheDocument()
    })

    it('should display tiger names', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Raja')).toBeInTheDocument()
      expect(screen.getByText('Sita')).toBeInTheDocument()
    })

    it('should display truncated ID when tiger has no name', () => {
      const tigersWithUnnamed = [
        ...mockTigers,
        {
          id: 'tiger-12345678-abcd-efgh',
          name: undefined,
          metadata: { origin_facility_id: 'facility-1' },
          images: [],
        },
      ]

      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: tigersWithUnnamed } },
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText(/tiger tiger-12/i)).toBeInTheDocument()
    })

    it('should display image count for tigers with images', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('2 images')).toBeInTheDocument()
      expect(screen.getByText('1 image')).toBeInTheDocument()
    })

    it('should use singular form for single image', () => {
      renderWithRouter(<FacilityDetail />)

      const sitaCard = screen.getByText('Sita').closest('div')
      expect(sitaCard).toHaveTextContent('1 image')
    })

    it('should navigate to tigers page when clicking tiger card', () => {
      renderWithRouter(<FacilityDetail />)

      const rajaCard = screen.getByText('Raja').closest('div')
      fireEvent.click(rajaCard!)

      expect(mockNavigate).toHaveBeenCalledWith('/tigers')
    })

    it('should not display tigers section when no tigers', () => {
      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: [] } },
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.queryByText(/associated tigers/i)).not.toBeInTheDocument()
    })

    it('should filter tigers by origin_facility_id', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Raja')).toBeInTheDocument()
      expect(screen.getByText('Sita')).toBeInTheDocument()
      expect(screen.queryByText('Kahn')).not.toBeInTheDocument()
    })

    it('should handle missing tigers data gracefully', () => {
      mockUseGetTigersQuery.mockReturnValue({
        data: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.queryByText(/associated tigers/i)).not.toBeInTheDocument()
    })
  })

  describe('metadata section', () => {
    beforeEach(() => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: mockFacility },
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: mockTigers } },
      })
    })

    it('should display metadata section title', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Metadata')).toBeInTheDocument()
    })

    it('should display data source when available', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Data Source')).toBeInTheDocument()
      expect(screen.getByText('USDA Records')).toBeInTheDocument()
    })

    it('should display created date when available', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Created')).toBeInTheDocument()
    })

    it('should display updated date when available', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Last Updated')).toBeInTheDocument()
    })

    it('should format metadata dates correctly', () => {
      renderWithRouter(<FacilityDetail />)

      // Check for formatted dates
      expect(screen.getByText(/january.*2023/i)).toBeInTheDocument()
      expect(screen.getByText(/january.*2024/i)).toBeInTheDocument()
    })
  })

  describe('reference metadata section', () => {
    beforeEach(() => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: mockFacility },
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: mockTigers } },
      })
    })

    it('should display reference data section when reference_metadata exists', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Reference Data')).toBeInTheDocument()
    })

    it('should display reference metadata keys with underscores replaced', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText(/inspection score/i)).toBeInTheDocument()
      expect(screen.getByText(/compliance level/i)).toBeInTheDocument()
      expect(screen.getByText(/last audit/i)).toBeInTheDocument()
    })

    it('should capitalize reference metadata keys', () => {
      renderWithRouter(<FacilityDetail />)

      const inspectionScore = screen.getByText(/inspection score/i)
      expect(inspectionScore).toBeInTheDocument()
    })

    it('should display reference metadata values', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('95')).toBeInTheDocument()
      expect(screen.getByText('High')).toBeInTheDocument()
      expect(screen.getByText('2024-01-10')).toBeInTheDocument()
    })

    it('should not display reference data section when reference_metadata is empty', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: { ...mockFacility, reference_metadata: {} } },
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.queryByText('Reference Data')).not.toBeInTheDocument()
    })

    it('should not display reference data section when reference_metadata is undefined', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: { ...mockFacility, reference_metadata: undefined } },
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.queryByText('Reference Data')).not.toBeInTheDocument()
    })
  })

  describe('date formatting', () => {
    beforeEach(() => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: mockFacility },
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: mockTigers } },
      })
    })

    it('should return null for undefined dates', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: { ...mockFacility, ir_date: undefined } },
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.queryByText('IR Date')).not.toBeInTheDocument()
    })

    it('should return original string for invalid dates', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: { ...mockFacility, ir_date: 'invalid-date' } },
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('invalid-date')).toBeInTheDocument()
    })
  })

  describe('layout and styling', () => {
    beforeEach(() => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: mockFacility },
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: mockTigers } },
      })
    })

    it('should use grid layout for main content', () => {
      renderWithRouter(<FacilityDetail />)

      const mainContent = screen.getByText('Basic Information').closest('.grid')
      expect(mainContent).toBeInTheDocument()
    })

    it('should apply hover effect to tiger cards', () => {
      renderWithRouter(<FacilityDetail />)

      const rajaCard = screen.getByText('Raja').closest('div')
      expect(rajaCard).toHaveClass('hover:bg-gray-100')
    })

    it('should apply cursor pointer to clickable tiger cards', () => {
      renderWithRouter(<FacilityDetail />)

      const rajaCard = screen.getByText('Raja').closest('div')
      expect(rajaCard).toHaveClass('cursor-pointer')
    })

    it('should have consistent spacing between sections', () => {
      renderWithRouter(<FacilityDetail />)

      const container = screen.getByText('Basic Information').closest('.space-y-6')
      expect(container).toBeInTheDocument()
    })
  })

  describe('edge cases', () => {
    it('should handle facility with no tigers data', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: mockFacility },
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: null,
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.queryByText(/associated tigers/i)).not.toBeInTheDocument()
    })

    it('should handle facility with minimal data', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: mockMinimalFacility },
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: [] } },
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Small Rescue Center')).toBeInTheDocument()
      expect(screen.getByText('Texas')).toBeInTheDocument()
    })

    it('should handle tigers with null metadata', () => {
      const tigersWithNullMetadata = [
        {
          id: 'tiger-4',
          name: 'Orphan',
          metadata: null,
          images: [],
        },
      ]

      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: tigersWithNullMetadata } },
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.queryByText('Orphan')).not.toBeInTheDocument()
    })

    it('should handle tigers with undefined origin_facility_id', () => {
      const tigersWithoutFacility = [
        {
          id: 'tiger-5',
          name: 'Unknown Origin',
          metadata: { other_field: 'value' },
          images: [],
        },
      ]

      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: tigersWithoutFacility } },
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.queryByText('Unknown Origin')).not.toBeInTheDocument()
    })

    it('should handle empty social media links object', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: { ...mockFacility, social_media_links: {} } },
        isLoading: false,
        error: undefined,
      })

      renderWithRouter(<FacilityDetail />)

      expect(screen.queryByText('Facebook')).not.toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    beforeEach(() => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: mockFacility },
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: mockTigers } },
      })
    })

    it('should have proper link attributes for external links', () => {
      renderWithRouter(<FacilityDetail />)

      const websiteLink = screen.getByText('Website').closest('a')
      expect(websiteLink).toHaveAttribute('target', '_blank')
      expect(websiteLink).toHaveAttribute('rel', 'noopener noreferrer')
    })

    it('should have descriptive button text', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByText('Back')).toBeInTheDocument()
    })

    it('should have icons with data-testid for testing', () => {
      renderWithRouter(<FacilityDetail />)

      expect(screen.getByTestId('building-icon')).toBeInTheDocument()
      expect(screen.getByTestId('arrow-left-icon')).toBeInTheDocument()
    })
  })

  describe('query parameters', () => {
    it('should call useGetFacilityQuery with facility ID from params', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: mockFacility },
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: [] } },
      })

      renderWithRouter(<FacilityDetail />)

      expect(mockUseGetFacilityQuery).toHaveBeenCalledWith('facility-1')
    })

    it('should call useGetTigersQuery with correct parameters', () => {
      mockUseGetFacilityQuery.mockReturnValue({
        data: { data: mockFacility },
        isLoading: false,
        error: undefined,
      })
      mockUseGetTigersQuery.mockReturnValue({
        data: { data: { data: [] } },
      })

      renderWithRouter(<FacilityDetail />)

      expect(mockUseGetTigersQuery).toHaveBeenCalledWith({ page: 1, page_size: 100 })
    })
  })
})

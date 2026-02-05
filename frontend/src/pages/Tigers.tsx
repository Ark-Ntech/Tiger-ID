import { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  useGetTigersQuery,
  useIdentifyTigerMutation,
  useIdentifyTigersBatchMutation,
  useGetAvailableModelsQuery,
  useCreateInvestigationMutation,
  useLaunchInvestigationMutation,
  useCreateTigerMutation,
  useLaunchInvestigationFromTigerMutation,
  useGetFacilitiesQuery,
} from '../app/api'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Alert from '../components/common/Alert'
import { ShieldCheckIcon, ArrowsRightLeftIcon } from '@heroicons/react/24/outline'

// Import new components
import TigerFilters, { TigerFilterState } from '../components/tigers/TigerFilters'
import TigerCard, { TigerCardData } from '../components/tigers/TigerCard'
import TigerUploadWizard from '../components/tigers/TigerUploadWizard'
import TigerRegistrationWizard, { TigerRegistrationData } from '../components/tigers/TigerRegistrationWizard'

// Default filter state
const DEFAULT_FILTERS: TigerFilterState = {
  search: '',
  facility: '',
  status: 'all',
  minConfidence: 0,
  sortBy: 'created_at',
  sortOrder: 'desc',
}

// Model information helper for upload wizard
const MODEL_INFO: Record<string, { id: string; name: string; description: string }> = {
  wildlife_tools: {
    id: 'wildlife_tools',
    name: 'Wildlife Tools (MegaDescriptor)',
    description: 'Robust general wildlife RE-ID model. Best for most use cases with high accuracy.',
  },
  tiger_reid: {
    id: 'tiger_reid',
    name: 'Tiger ReID',
    description: 'Tiger-specific stripe specialist model. Optimized for tiger stripe patterns.',
  },
  rapid: {
    id: 'rapid',
    name: 'RAPID',
    description: 'Real-time animal pattern re-identification. Fast initial screening model.',
  },
  cvwc2019: {
    id: 'cvwc2019',
    name: 'CVWC2019',
    description: 'Part-pose guided tiger re-identification. Robust to pose variations.',
  },
  transreid: {
    id: 'transreid',
    name: 'TransReID',
    description: 'Transformer-based re-identification. Strong on partial views.',
  },
  megadescriptor_b: {
    id: 'megadescriptor_b',
    name: 'MegaDescriptor B',
    description: 'Advanced descriptor model for fine-grained identification.',
  },
}

const Tigers = () => {
  const navigate = useNavigate()
  const [page, _setPage] = useState(1)
  void _setPage // Reserved for pagination feature

  // Modal states
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showRegistrationModal, setShowRegistrationModal] = useState(false)

  // Filter state
  const [filters, setFilters] = useState<TigerFilterState>(DEFAULT_FILTERS)

  // Selection state for comparison
  const [selectedTigerIds, setSelectedTigerIds] = useState<Set<string>>(new Set())

  // API queries
  const { data, isLoading, error, refetch } = useGetTigersQuery({ page, page_size: 50 })
  const { data: modelsData } = useGetAvailableModelsQuery()
  const { data: facilitiesData } = useGetFacilitiesQuery({ page: 1, page_size: 100 })
  const [identifyTiger] = useIdentifyTigerMutation()
  const [identifyBatch] = useIdentifyTigersBatchMutation()
  const [createInvestigation] = useCreateInvestigationMutation()
  const [_launchInvestigation] = useLaunchInvestigationMutation()
  void _launchInvestigation // Alternative launch method
  const [createTiger] = useCreateTigerMutation()
  const [launchInvestigationFromTiger] = useLaunchInvestigationFromTigerMutation()

  // Derived data
  const availableModels = modelsData?.data?.models || []
  const modelNames = Array.isArray(availableModels) ? availableModels : Object.keys(availableModels)

  // Format models for wizard
  const modelsForWizard = useMemo(() => {
    return modelNames.map((name) => MODEL_INFO[name] || {
      id: name,
      name: name,
      description: 'Custom model configuration',
    })
  }, [modelNames])

  // Format facilities for filters and wizards
  const facilitiesForFilters = useMemo(() => {
    const facilities = facilitiesData?.data?.data || facilitiesData?.data || []
    return Array.isArray(facilities)
      ? facilities.map((f: any) => ({ id: f.id, name: f.name }))
      : []
  }, [facilitiesData])

  // Raw tigers from API
  const rawTigers = useMemo(() => {
    return data?.data?.data || []
  }, [data])

  // Map API tigers to TigerCardData format
  const mappedTigers: TigerCardData[] = useMemo(() => {
    return rawTigers.map((tiger: any) => {
      // Determine status based on verification state
      let status: 'verified' | 'pending' | 'unverified' = 'unverified'
      if (tiger.verification_status === 'verified' || tiger.is_verified) {
        status = 'verified'
      } else if (tiger.verification_status === 'pending') {
        status = 'pending'
      }

      // Get primary image URL
      let imagePath = ''
      if (tiger.images && tiger.images.length > 0) {
        const imgUrl = tiger.images[0].url || tiger.images[0].thumbnail_url
        imagePath = imgUrl?.startsWith('http')
          ? imgUrl
          : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${imgUrl}`
      } else if (tiger.primary_image_url) {
        imagePath = tiger.primary_image_url
      }

      // Find facility info
      const facility = tiger.facility_id
        ? facilitiesForFilters.find((f) => f.id === tiger.facility_id)
        : undefined

      return {
        id: tiger.id,
        name: tiger.name || `Tiger #${tiger.id.substring(0, 8)}`,
        image_path: imagePath,
        confidence_score: tiger.confidence_score || 0.95,
        status,
        facility,
        created_at: tiger.created_at || new Date().toISOString(),
      }
    })
  }, [rawTigers, facilitiesForFilters])

  // Apply filters to tigers
  const filteredTigers = useMemo(() => {
    let result = [...mappedTigers]

    // Filter by search
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      result = result.filter(
        (tiger) =>
          tiger.name.toLowerCase().includes(searchLower) ||
          tiger.id.toLowerCase().includes(searchLower) ||
          tiger.facility?.name.toLowerCase().includes(searchLower)
      )
    }

    // Filter by facility
    if (filters.facility) {
      result = result.filter((tiger) => tiger.facility?.id === filters.facility)
    }

    // Filter by status
    if (filters.status !== 'all') {
      result = result.filter((tiger) => tiger.status === filters.status)
    }

    // Filter by minimum confidence
    if (filters.minConfidence > 0) {
      const threshold = filters.minConfidence / 100
      result = result.filter((tiger) => tiger.confidence_score >= threshold)
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0
      switch (filters.sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name)
          break
        case 'confidence':
          comparison = a.confidence_score - b.confidence_score
          break
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          break
        case 'facility':
          comparison = (a.facility?.name || '').localeCompare(b.facility?.name || '')
          break
      }
      return filters.sortOrder === 'desc' ? -comparison : comparison
    })

    return result
  }, [mappedTigers, filters])

  // Debug logging
  useEffect(() => {
    if (error) {
      console.error('Error loading tigers:', error)
    }
    if (data) {
      console.log('Tigers data loaded:', data)
    }
  }, [error, data])

  // Filter handlers
  const handleFilterChange = useCallback((newFilters: Partial<TigerFilterState>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }))
  }, [])

  const handleFilterReset = useCallback(() => {
    setFilters(DEFAULT_FILTERS)
  }, [])

  // Selection handlers
  const handleTigerSelect = useCallback((tigerId: string) => {
    setSelectedTigerIds((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(tigerId)) {
        newSet.delete(tigerId)
      } else {
        newSet.add(tigerId)
      }
      return newSet
    })
  }, [])

  const handleClearSelection = useCallback(() => {
    setSelectedTigerIds(new Set())
  }, [])

  // Navigation handlers
  const handleTigerClick = useCallback(
    (tigerId: string) => {
      navigate(`/tigers/${tigerId}`)
    },
    [navigate]
  )

  // Reserved for future use - launches investigation from tiger detail view
  const _handleLaunchInvestigation = useCallback(async (tigerId: string, tigerName?: string) => {
    try {
      const result = await launchInvestigationFromTiger({
        tiger_id: tigerId,
        tiger_name: tigerName,
      }).unwrap()

      // Type assertion for the API response
      const resultData = result?.data as { investigation_id?: string } | undefined
      if (resultData?.investigation_id) {
        navigate(`/investigations/${resultData.investigation_id}`)
      } else {
        // Fallback: create investigation manually
        const investigation = await createInvestigation({
          title: `Investigation: ${tigerName || `Tiger ${tigerId.substring(0, 8)}`}`,
          description: `Investigation launched for tiger ${tigerName || tigerId}`,
          priority: 'medium',
          tags: ['tiger-investigation'],
        }).unwrap()

        const investigationData = investigation?.data as { id?: string } | undefined
        if (investigationData?.id) {
          navigate(`/investigations/${investigationData.id}`)
        }
      }
    } catch (error: any) {
      console.error('Error launching investigation:', error)
      alert(`Failed to launch investigation: ${error?.data?.detail || error?.message || 'Unknown error'}`)
    }
  }, [launchInvestigationFromTiger, createInvestigation, navigate])
  void _handleLaunchInvestigation // Available for tiger context menu in future

  // Compare selected tigers
  const handleCompareSelected = useCallback(() => {
    if (selectedTigerIds.size < 2) {
      alert('Please select at least 2 tigers to compare')
      return
    }
    const ids = Array.from(selectedTigerIds).join(',')
    navigate(`/tigers/compare?ids=${ids}`)
  }, [selectedTigerIds, navigate])

  // Upload wizard handlers
  const handleUploadComplete = async (uploadData: {
    images: File[]
    facilityId?: string
    captureDate?: string
    notes?: string
    selectedModels: string[]
  }) => {
    try {
      // Process upload based on number of images
      if (uploadData.images.length === 1) {
        const formData = new FormData()
        formData.append('image', uploadData.images[0])
        if (uploadData.selectedModels.length > 0) {
          formData.append('model_name', uploadData.selectedModels[0])
        }
        if (uploadData.selectedModels.length > 1) {
          formData.append('use_all_models', 'true')
          formData.append('ensemble_mode', 'parallel')
        }
        if (uploadData.facilityId) {
          formData.append('facility_id', uploadData.facilityId)
        }
        if (uploadData.notes) {
          formData.append('notes', uploadData.notes)
        }

        const result = await identifyTiger(formData).unwrap()
        console.log('Identification result:', result)

        // Navigate to results or show notification
        const resultData = result?.data as { tiger_id?: string } | undefined
        if (resultData?.tiger_id) {
          navigate(`/tigers/${resultData.tiger_id}`)
        } else {
          refetch()
        }
      } else {
        // Batch upload
        const formData = new FormData()
        uploadData.images.forEach((file) => {
          formData.append('images', file)
        })
        if (uploadData.selectedModels.length > 0) {
          formData.append('model_name', uploadData.selectedModels[0])
        }
        if (uploadData.facilityId) {
          formData.append('facility_id', uploadData.facilityId)
        }

        const result = await identifyBatch(formData).unwrap()
        console.log('Batch identification result:', result)
        refetch()
      }
    } catch (error: any) {
      console.error('Error during upload:', error)
      throw new Error(error?.data?.detail || error?.message || 'Failed to process images')
    }
  }

  // Registration wizard handlers
  const handleRegistrationComplete = async (registrationData: TigerRegistrationData) => {
    try {
      const formData = new FormData()
      formData.append('name', registrationData.name)
      if (registrationData.estimatedAge) {
        formData.append('estimated_age', registrationData.estimatedAge.toString())
      }
      if (registrationData.sex) {
        formData.append('sex', registrationData.sex)
      }
      if (registrationData.distinctiveMarkings) {
        formData.append('distinctive_markings', registrationData.distinctiveMarkings)
      }
      if (registrationData.notes) {
        formData.append('notes', registrationData.notes)
      }
      formData.append('facility_id', registrationData.facilityId)
      if (registrationData.enclosure) {
        formData.append('enclosure', registrationData.enclosure)
      }
      // Add reference image IDs
      registrationData.referenceImageIds.forEach((id) => {
        formData.append('reference_image_ids', id)
      })

      const result = await createTiger(formData).unwrap()
      const resultData = result?.data as { tiger_id?: string; id?: string } | undefined
      const tigerId = resultData?.tiger_id || resultData?.id

      // Refresh tiger list
      refetch()

      // Navigate to new tiger
      if (tigerId) {
        navigate(`/tigers/${tigerId}`)
      }
    } catch (error: any) {
      console.error('Error registering tiger:', error)
      throw new Error(error?.data?.detail || error?.message || 'Failed to register tiger')
    }
  }

  // Loading state
  if (isLoading) {
    return (
      <div
        data-testid="tigers-loading"
        className="flex items-center justify-center h-full"
      >
        <div className="text-center">
          <LoadingSpinner size="xl" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading tigers...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div
        data-testid="tigers-error"
        className="flex items-center justify-center h-full"
      >
        <Alert type="error">Error loading tigers. Please try again.</Alert>
      </div>
    )
  }

  return (
    <div data-testid="tigers-page" className="space-y-6">
      {/* Header */}
      <div
        data-testid="tigers-header"
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Tiger Database
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            All identified tigers and their profiles
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={() => setShowRegistrationModal(true)}
            data-testid="register-tiger-button"
          >
            Register New Tiger
          </Button>
          <Button
            variant="primary"
            onClick={() => setShowUploadModal(true)}
            data-testid="upload-tiger-button"
          >
            Upload Tiger Image
          </Button>
        </div>
      </div>

      {/* Filters */}
      <TigerFilters
        filters={filters}
        facilities={facilitiesForFilters}
        totalCount={mappedTigers.length}
        filteredCount={filteredTigers.length}
        onFilterChange={handleFilterChange}
        onReset={handleFilterReset}
        data-testid="tigers-filters"
      />

      {/* Selection bar */}
      {selectedTigerIds.size > 0 && (
        <div
          data-testid="tigers-selection-bar"
          className="flex items-center justify-between px-4 py-3 bg-tiger-orange/10 dark:bg-tiger-orange/20 border border-tiger-orange/30 rounded-xl"
        >
          <span className="text-sm font-medium text-tiger-orange dark:text-tiger-orange-light">
            {selectedTigerIds.size} tiger{selectedTigerIds.size !== 1 ? 's' : ''} selected
          </span>
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearSelection}
              data-testid="clear-selection-button"
            >
              Clear Selection
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleCompareSelected}
              disabled={selectedTigerIds.size < 2}
              data-testid="compare-selected-button"
            >
              <ArrowsRightLeftIcon className="w-4 h-4 mr-2" />
              Compare Selected ({selectedTigerIds.size})
            </Button>
          </div>
        </div>
      )}

      {/* Tiger Grid */}
      {filteredTigers.length > 0 ? (
        <div
          data-testid="tigers-grid"
          className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
        >
          {filteredTigers.map((tiger) => (
            <TigerCard
              key={tiger.id}
              tiger={tiger}
              isSelected={selectedTigerIds.has(tiger.id)}
              onSelect={handleTigerSelect}
              onClick={handleTigerClick}
              showCheckbox
              data-testid={`tiger-card-${tiger.id}`}
            />
          ))}
        </div>
      ) : (
        <Card
          data-testid="tigers-empty"
          className="text-center py-12"
        >
          <ShieldCheckIcon className="h-12 w-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">
            {mappedTigers.length === 0
              ? 'No tigers identified yet'
              : 'No tigers match your filters'}
          </p>
          {mappedTigers.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleFilterReset}
              className="mt-4"
              data-testid="clear-filters-button"
            >
              Clear Filters
            </Button>
          )}
        </Card>
      )}

      {/* Compare button (floating) */}
      {selectedTigerIds.size >= 2 && (
        <div
          data-testid="compare-floating-button"
          className="fixed bottom-6 right-6 z-40"
        >
          <Button
            variant="primary"
            size="lg"
            onClick={handleCompareSelected}
            className="shadow-lg"
          >
            <ArrowsRightLeftIcon className="w-5 h-5 mr-2" />
            Compare Selected ({selectedTigerIds.size})
          </Button>
        </div>
      )}

      {/* Upload Wizard */}
      <TigerUploadWizard
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onComplete={handleUploadComplete}
        facilities={facilitiesForFilters}
        models={modelsForWizard}
        data-testid="tiger-upload-wizard"
      />

      {/* Registration Wizard */}
      <TigerRegistrationWizard
        isOpen={showRegistrationModal}
        onClose={() => setShowRegistrationModal(false)}
        onComplete={handleRegistrationComplete}
        facilities={facilitiesForFilters}
        data-testid="tiger-registration-wizard"
      />
    </div>
  )
}

export default Tigers

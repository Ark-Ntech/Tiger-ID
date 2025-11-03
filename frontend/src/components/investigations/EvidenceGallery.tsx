import { useState, useMemo } from 'react'
import { useGetEvidenceQuery } from '../../app/api'
import Card from '../common/Card'
import LoadingSpinner from '../common/LoadingSpinner'
import Badge from '../common/Badge'
import Button from '../common/Button'
import { formatDate } from '../../utils/formatters'
import { Evidence as EvidenceType } from '../../types'

interface EvidenceGalleryProps {
  investigationId: string
}

const EvidenceGallery = ({ investigationId }: EvidenceGalleryProps) => {
  const [filterType, setFilterType] = useState<string>('all')
  const [filterVerified, setFilterVerified] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')

  const { data, isLoading, error } = useGetEvidenceQuery(investigationId)

  const evidence = useMemo(() => {
    if (!data?.data) return []
    return Array.isArray(data.data) ? data.data : data.data.evidence || []
  }, [data])

  const filteredEvidence = useMemo(() => {
    return evidence.filter((item: EvidenceType) => {
      // Type filter
      if (filterType !== 'all' && item.type !== filterType) {
        return false
      }

      // Verified filter
      if (filterVerified === 'verified' && !item.verified) {
        return false
      }
      if (filterVerified === 'unverified' && item.verified) {
        return false
      }

      // Search query
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        const matchesTitle = item.title?.toLowerCase().includes(query)
        const matchesDescription = item.description?.toLowerCase().includes(query)
        const matchesSource = item.source?.toLowerCase().includes(query)
        const matchesTags = item.tags?.some((tag) =>
          tag.toLowerCase().includes(query)
        )
        if (!matchesTitle && !matchesDescription && !matchesSource && !matchesTags) {
          return false
        }
      }

      return true
    })
  }, [evidence, filterType, filterVerified, searchQuery])

  const typeCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    evidence.forEach((item: EvidenceType) => {
      counts[item.type] = (counts[item.type] || 0) + 1
    })
    return counts
  }, [evidence])

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'image':
        return '🖼️'
      case 'document':
        return '📄'
      case 'video':
        return '🎥'
      case 'audio':
        return '🎵'
      case 'url':
        return '🔗'
      case 'text':
        return '📝'
      default:
        return '📎'
    }
  }

  if (isLoading) {
    return (
      <Card>
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner />
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <div className="text-center text-red-600 py-8">
          Failed to load evidence
        </div>
      </Card>
    )
  }

  return (
    <Card>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Evidence Gallery ({filteredEvidence.length} / {evidence.length})
        </h3>
      </div>

      {/* Filters */}
      <div className="mb-6 space-y-4">
        {/* Search */}
        <div>
          <input
            type="text"
            placeholder="Search evidence..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Filter buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-gray-700">Type:</span>
          <Button
            variant={filterType === 'all' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilterType('all')}
          >
            All ({evidence.length})
          </Button>
          {Object.entries(typeCounts).map(([type, count]) => (
            <Button
              key={type}
              variant={filterType === type ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setFilterType(type)}
            >
              {getTypeIcon(type)} {type} ({count})
            </Button>
          ))}

          <span className="ml-4 text-sm font-medium text-gray-700">Status:</span>
          <Button
            variant={filterVerified === 'all' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilterVerified('all')}
          >
            All
          </Button>
          <Button
            variant={filterVerified === 'verified' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilterVerified('verified')}
          >
            ✅ Verified
          </Button>
          <Button
            variant={filterVerified === 'unverified' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilterVerified('unverified')}
          >
            ⏳ Unverified
          </Button>
        </div>
      </div>

      {/* Evidence grid */}
      {filteredEvidence.length === 0 ? (
        <div className="text-center text-gray-500 py-12">
          <p>No evidence found matching your filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredEvidence.map((item: EvidenceType) => (
            <div
              key={item.id}
              className="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:shadow-md transition-shadow cursor-pointer"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">{getTypeIcon(item.type)}</span>
                  <div>
                    <h4 className="font-medium text-gray-900 text-sm line-clamp-1">
                      {item.title || 'Untitled Evidence'}
                    </h4>
                    <p className="text-xs text-gray-500">{item.type}</p>
                  </div>
                </div>
                {item.verified ? (
                  <Badge variant="success" className="text-xs">
                    ✅
                  </Badge>
                ) : (
                  <Badge variant="warning" className="text-xs">
                    ⏳
                  </Badge>
                )}
              </div>

              {item.description && (
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                  {item.description}
                </p>
              )}

              <div className="space-y-1 mb-3">
                {item.source && (
                  <p className="text-xs text-gray-500">
                    Source: <span className="text-gray-700">{item.source}</span>
                  </p>
                )}
                <p className="text-xs text-gray-500">
                  Collected: {formatDate(item.collected_at)}
                </p>
              </div>

              {item.tags && item.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {item.tags.slice(0, 3).map((tag, idx) => (
                    <Badge key={idx} variant="info" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                  {item.tags.length > 3 && (
                    <Badge variant="info" className="text-xs">
                      +{item.tags.length - 3}
                    </Badge>
                  )}
                </div>
              )}

              <div className="mt-3 flex space-x-2">
                {item.file_url && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => window.open(item.file_url, '_blank')}
                  >
                    View
                  </Button>
                )}
                {item.source && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => window.open(item.source, '_blank')}
                  >
                    Source
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

export default EvidenceGallery


import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useGlobalSearchQuery } from '../app/api'
import Card from '../components/common/Card'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import { 
  MagnifyingGlassIcon, 
  FolderIcon, 
  ShieldCheckIcon, 
  BuildingOfficeIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'

const SearchResults = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const query = searchParams.get('q') || ''
  
  const { data, isLoading, error } = useGlobalSearchQuery(
    { q: query, limit: 50 },
    { skip: !query || query.length < 2 }
  )

  const results = data?.data || {
    investigations: [],
    tigers: [],
    facilities: [],
    evidence: []
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Card>
          <div className="text-center py-12">
            <p className="text-red-600">Error performing search. Please try again.</p>
          </div>
        </Card>
      </div>
    )
  }

  const totalResults = 
    (results.investigations?.length || 0) +
    (results.tigers?.length || 0) +
    (results.facilities?.length || 0) +
    (results.evidence?.length || 0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Search Results</h1>
        <p className="text-gray-600 mt-2">
          Found {totalResults} result{totalResults !== 1 ? 's' : ''} for "{query}"
        </p>
      </div>

      {totalResults === 0 ? (
        <Card>
          <div className="text-center py-12">
            <MagnifyingGlassIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No results found for "{query}"</p>
            <p className="text-sm text-gray-500 mt-2">Try a different search term</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Investigations */}
          {results.investigations && results.investigations.length > 0 && (
            <Card>
              <div className="flex items-center space-x-2 mb-4">
                <FolderIcon className="h-5 w-5 text-primary-600" />
                <h2 className="text-xl font-semibold text-gray-900">
                  Investigations ({results.investigations.length})
                </h2>
              </div>
              <div className="space-y-3">
                {results.investigations.map((inv: any) => (
                  <div
                    key={inv.id}
                    className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                    onClick={() => navigate(`/investigations/${inv.id}`)}
                  >
                    <h3 className="font-semibold text-gray-900">{inv.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{inv.description}</p>
                    <div className="flex items-center space-x-2 mt-2">
                      <Badge variant={inv.status === 'completed' ? 'success' : 'info'}>
                        {inv.status}
                      </Badge>
                      <Badge variant={inv.priority === 'high' ? 'error' : 'default'}>
                        {inv.priority}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Tigers */}
          {results.tigers && results.tigers.length > 0 && (
            <Card>
              <div className="flex items-center space-x-2 mb-4">
                <ShieldCheckIcon className="h-5 w-5 text-primary-600" />
                <h2 className="text-xl font-semibold text-gray-900">
                  Tigers ({results.tigers.length})
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {results.tigers.map((tiger: any) => (
                  <div
                    key={tiger.id}
                    className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                    onClick={() => navigate('/tigers')}
                  >
                    <h3 className="font-semibold text-gray-900">
                      {tiger.name || `Tiger ${tiger.id.substring(0, 8)}`}
                    </h3>
                    {tiger.images && tiger.images.length > 0 && (
                      <p className="text-sm text-gray-600 mt-1">
                        {tiger.images.length} image{tiger.images.length !== 1 ? 's' : ''}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Facilities */}
          {results.facilities && results.facilities.length > 0 && (
            <Card>
              <div className="flex items-center space-x-2 mb-4">
                <BuildingOfficeIcon className="h-5 w-5 text-primary-600" />
                <h2 className="text-xl font-semibold text-gray-900">
                  Facilities ({results.facilities.length})
                </h2>
              </div>
              <div className="space-y-3">
                {results.facilities.map((facility: any) => (
                  <div
                    key={facility.id}
                    className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                    onClick={() => navigate(`/facilities/${facility.id}`)}
                  >
                    <h3 className="font-semibold text-gray-900">
                      {facility.exhibitor_name || facility.name}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {facility.city && facility.state ? `${facility.city}, ${facility.state}` : facility.state || facility.city || 'Location unknown'}
                    </p>
                    {facility.tiger_count !== undefined && (
                      <p className="text-xs text-gray-500 mt-1">
                        {facility.tiger_count} tiger{facility.tiger_count !== 1 ? 's' : ''}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Evidence */}
          {results.evidence && results.evidence.length > 0 && (
            <Card>
              <div className="flex items-center space-x-2 mb-4">
                <DocumentTextIcon className="h-5 w-5 text-primary-600" />
                <h2 className="text-xl font-semibold text-gray-900">
                  Evidence ({results.evidence.length})
                </h2>
              </div>
              <div className="space-y-3">
                {results.evidence.map((evidence: any) => (
                  <div
                    key={evidence.id}
                    className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                    onClick={() => evidence.investigation_id && navigate(`/investigations/${evidence.investigation_id}`)}
                  >
                    <h3 className="font-semibold text-gray-900">{evidence.title || 'Evidence'}</h3>
                    <p className="text-sm text-gray-600 mt-1">{evidence.description}</p>
                    <Badge variant="info" className="mt-2">
                      {evidence.source_type || 'Unknown'}
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

export default SearchResults


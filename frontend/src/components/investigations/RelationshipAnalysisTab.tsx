import { useState } from 'react'
import { useRelationshipAnalysisMutation, useGetFacilitiesQuery } from '../../app/api'
import Card from '../common/Card'
import Button from '../common/Button'
import LoadingSpinner from '../common/LoadingSpinner'
import Badge from '../common/Badge'
import { ShareIcon } from '@heroicons/react/24/outline'

const RelationshipAnalysisTab = () => {
  const [selectedFacilityId, setSelectedFacilityId] = useState('')
  const { data: facilitiesData, isLoading: facilitiesLoading } = useGetFacilitiesQuery({
    page: 1,
    page_size: 100,
  })
  const [relationshipAnalysis, { isLoading, data, error }] = useRelationshipAnalysisMutation()

  const facilities = facilitiesData?.data?.data || []

  const handleAnalyze = async () => {
    if (!selectedFacilityId) return
    try {
      await relationshipAnalysis({ facility_id: selectedFacilityId })
    } catch (err) {
      console.error('Relationship analysis error:', err)
    }
  }

  const relationships = data?.data?.relationships
  const connections = relationships?.connections || []
  const tigers = relationships?.tigers || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <ShareIcon className="h-6 w-6 text-primary-600" />
          Relationship Analysis
        </h2>
        <p className="text-gray-600 mt-2">
          Analyze relationships between facilities, tigers, and entities
        </p>
      </div>

      <Card>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Facility to Analyze
            </label>
            {facilitiesLoading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <select
                value={selectedFacilityId}
                onChange={(e) => setSelectedFacilityId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">Select a facility...</option>
                {facilities.map((facility) => (
                  <option key={facility.id} value={facility.id}>
                    {facility.name} ({facility.state || 'Unknown'})
                  </option>
                ))}
              </select>
            )}
          </div>
          <Button
            onClick={handleAnalyze}
            disabled={!selectedFacilityId || isLoading}
            className="w-full"
          >
            {isLoading ? 'Analyzing...' : '🔗 Analyze Relationships'}
          </Button>
        </div>
      </Card>

      {error && (
        <Card>
          <div className="text-red-600">
            Analysis failed: {'data' in error ? JSON.stringify(error.data) : 'Unknown error'}
          </div>
        </Card>
      )}

      {data?.data && (
        <div className="space-y-6">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Found {connections.length} connections
              </h3>
            </div>

            {connections.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No connections found</p>
            ) : (
              <div className="space-y-4">
                {connections.map((conn, idx) => (
                  <div
                    key={idx}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 mb-1">
                          {conn.type?.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()) ||
                            'Unknown'}
                        </h4>
                        {conn.facility_name && (
                          <p className="text-sm text-gray-600 mb-1">
                            <strong>Facility:</strong> {conn.facility_name}
                          </p>
                        )}
                        {conn.facility_id && (
                          <p className="text-xs text-gray-500">Facility ID: {conn.facility_id}</p>
                        )}
                      </div>
                      <Badge variant="info">Strength: {conn.connection_strength.toFixed(2)}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {tigers.length > 0 && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Associated Tigers</h3>
              <div className="space-y-2">
                {tigers.map((tiger, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <span className="font-medium text-gray-900">
                      {tiger.name || 'Unnamed'}
                    </span>
                    <Badge variant={tiger.status === 'active' ? 'success' : 'default'}>
                      {tiger.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      )}
    </div>
  )
}

export default RelationshipAnalysisTab


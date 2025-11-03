import { useState } from 'react'
import { useCompileEvidenceMutation, useGetEvidenceGroupsQuery, useGetInvestigationsQuery } from '../../app/api'
import Card from '../common/Card'
import Button from '../common/Button'
import Textarea from '../common/Textarea'
import LoadingSpinner from '../common/LoadingSpinner'
import Badge from '../common/Badge'
import { DocumentTextIcon } from '@heroicons/react/24/outline'

const EvidenceCompilationTab = () => {
  const [selectedInvestigationId, setSelectedInvestigationId] = useState('')
  const [sourceUrls, setSourceUrls] = useState('')
  const { data: investigationsData } = useGetInvestigationsQuery({ page: 1, page_size: 50 })
  const [compileEvidence, { isLoading, data, error }] = useCompileEvidenceMutation()
  const {
    data: groupsData,
    isLoading: groupsLoading,
    refetch: refetchGroups,
  } = useGetEvidenceGroupsQuery(selectedInvestigationId, {
    skip: !selectedInvestigationId,
  })

  const investigations = investigationsData?.data?.data || []

  const handleCompile = async () => {
    if (!selectedInvestigationId || !sourceUrls.trim()) return
    const urls = sourceUrls
      .split('\n')
      .map((url) => url.trim())
      .filter((url) => url.length > 0)
    if (urls.length === 0) return

    try {
      await compileEvidence({
        investigation_id: selectedInvestigationId,
        source_urls: urls,
      })
      refetchGroups()
    } catch (err) {
      console.error('Evidence compilation error:', err)
    }
  }

  const compilation = data?.data?.compilation
  const compiled = compilation?.compiled || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <DocumentTextIcon className="h-6 w-6 text-primary-600" />
          Evidence Compilation
        </h2>
        <p className="text-gray-600 mt-2">
          Compile evidence from web sources into an investigation
        </p>
      </div>

      <Card>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Investigation
            </label>
            <select
              value={selectedInvestigationId}
              onChange={(e) => setSelectedInvestigationId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Select an investigation...</option>
              {investigations.map((inv) => (
                <option key={inv.id} value={inv.id}>
                  {inv.title} ({inv.status})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Source URLs (one per line)
            </label>
            <Textarea
              value={sourceUrls}
              onChange={(e) => setSourceUrls(e.target.value)}
              placeholder="https://example.com/page1&#10;https://example.com/page2"
              rows={6}
            />
          </div>
          <Button
            onClick={handleCompile}
            disabled={!selectedInvestigationId || !sourceUrls.trim() || isLoading}
            className="w-full"
          >
            {isLoading ? 'Compiling...' : '📋 Compile Evidence'}
          </Button>
        </div>
      </Card>

      {error && (
        <Card>
          <div className="text-red-600">
            Evidence compilation failed: {'data' in error ? JSON.stringify(error.data) : 'Unknown error'}
          </div>
        </Card>
      )}

      {data?.data && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Compiled {compilation?.compiled_count || 0} evidence items
            </h3>
            {compilation?.error_count && compilation.error_count > 0 && (
              <Badge variant="warning">
                ⚠️ {compilation.error_count} errors occurred
              </Badge>
            )}
          </div>

          {compiled.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-semibold text-gray-900 mb-2">Compiled Evidence:</h4>
              {compiled.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 bg-green-50 rounded-lg"
                >
                  <span className="text-sm text-gray-700">
                    ✅ Evidence created: {item.evidence_id?.substring(0, 8)}...
                  </span>
                  <Badge variant="success">Score: {item.score.toFixed(2)}</Badge>
                </div>
              ))}
            </div>
          )}

          {compilation?.errors && compilation.errors.length > 0 && (
            <div className="mt-4 space-y-2">
              <h4 className="font-semibold text-red-900 mb-2">Errors:</h4>
              {compilation.errors.map((error, idx) => (
                <div key={idx} className="p-2 bg-red-50 rounded text-sm text-red-700">
                  {error}
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {selectedInvestigationId && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Evidence Groups</h3>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchGroups()}
              disabled={groupsLoading}
            >
              Refresh
            </Button>
          </div>
          {groupsLoading ? (
            <LoadingSpinner size="sm" />
          ) : groupsData?.data?.groups ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {groupsData.data.groups.by_facility && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">By Facility</h4>
                  {Object.entries(groupsData.data.groups.by_facility).map(([facilityId, items]) => (
                    <div key={facilityId} className="p-2 bg-gray-50 rounded mb-2">
                      <span className="text-sm text-gray-700">
                        <strong>Facility {facilityId.substring(0, 8)}:</strong> {items.length} items
                      </span>
                    </div>
                  ))}
                </div>
              )}
              {groupsData.data.groups.high_relevance && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">High Relevance Evidence</h4>
                  {groupsData.data.groups.high_relevance.slice(0, 10).map((item, idx) => (
                    <div key={idx} className="p-2 bg-gray-50 rounded mb-2">
                      <span className="text-sm text-gray-700">
                        Score: {item.score.toFixed(2)} - {item.source_type}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">No evidence groups found</p>
          )}
        </Card>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      )}
    </div>
  )
}

export default EvidenceCompilationTab


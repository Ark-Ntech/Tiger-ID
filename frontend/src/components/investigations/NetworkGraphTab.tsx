import { useState } from 'react'
import { useGetNetworkGraphQuery } from '../../app/api'
import Card from '../common/Card'
import Button from '../common/Button'
import LoadingSpinner from '../common/LoadingSpinner'
import Badge from '../common/Badge'
import { CubeIcon } from '@heroicons/react/24/outline'

const NetworkGraphTab = () => {
  const [includeReference, setIncludeReference] = useState(true)
  const { data, isLoading, error, refetch } = useGetNetworkGraphQuery({
    include_reference: includeReference,
  })

  const network = data?.data?.network
  const nodes = network?.nodes || []
  const edges = network?.edges || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <CubeIcon className="h-6 w-6 text-primary-600" />
          Network Graph
        </h2>
        <p className="text-gray-600 mt-2">Visualize facility relationship network</p>
      </div>

      <Card>
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeReference}
                onChange={(e) => setIncludeReference(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">Include Reference Facilities Only</span>
            </label>
            <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isLoading}>
              Refresh
            </Button>
          </div>
        </div>
      </Card>

      {error && (
        <Card>
          <div className="text-red-600">
            Network graph generation failed: {'data' in error ? JSON.stringify(error.data) : 'Unknown error'}
          </div>
        </Card>
      )}

      {data?.data && (
        <div className="space-y-6">
          <Card>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-sm text-gray-600">Nodes (Facilities)</p>
                <p className="text-2xl font-bold text-gray-900">{nodes.length}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Edges (Connections)</p>
                <p className="text-2xl font-bold text-gray-900">{edges.length}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Reference Facilities</p>
                <p className="text-2xl font-bold text-primary-600">
                  {nodes.filter((n) => n.is_reference).length}
                </p>
              </div>
            </div>
          </Card>

          {nodes.length > 0 && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Facilities in Network</h3>
              <div className="max-h-96 overflow-y-auto space-y-2">
                {nodes.slice(0, 20).map((node) => (
                  <div
                    key={node.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div>
                      <span className="font-medium text-gray-900">
                        {node.label || 'Unknown'}
                        {node.is_reference && ' ⭐'}
                      </span>
                      <div className="flex gap-2 mt-1">
                        {node.state && (
                          <span className="text-xs text-gray-600">State: {node.state}</span>
                        )}
                        {node.tiger_count !== undefined && (
                          <span className="text-xs text-gray-600">
                            Tigers: {node.tiger_count}
                          </span>
                        )}
                      </div>
                    </div>
                    {node.is_reference && (
                      <Badge variant="success">⭐ Reference Facility</Badge>
                    )}
                  </div>
                ))}
                {nodes.length > 20 && (
                  <p className="text-sm text-gray-500 text-center py-2">
                    Showing first 20 of {nodes.length} facilities
                  </p>
                )}
              </div>
            </Card>
          )}

          {edges.length > 0 && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Connections</h3>
              <div className="max-h-96 overflow-y-auto space-y-2">
                {edges.slice(0, 10).map((edge, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <span className="text-sm text-gray-700">
                        {edge.type}: {edge.from.substring(0, 8)}... → {edge.to.substring(0, 8)}...
                      </span>
                    </div>
                    <Badge variant="info">Strength: {edge.strength.toFixed(2)}</Badge>
                  </div>
                ))}
                {edges.length > 10 && (
                  <p className="text-sm text-gray-500 text-center py-2">
                    Showing first 10 of {edges.length} connections
                  </p>
                )}
              </div>
            </Card>
          )}

          {nodes.length === 0 && (
            <Card>
              <p className="text-gray-500 text-center py-8">
                No network data available. Full interactive graph visualization coming soon.
              </p>
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

export default NetworkGraphTab


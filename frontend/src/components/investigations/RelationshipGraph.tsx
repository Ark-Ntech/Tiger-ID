import { useMemo, useCallback } from 'react'
import { useGetNetworkGraphQuery } from '../../app/api'
import Card from '../common/Card'
import LoadingSpinner from '../common/LoadingSpinner'
import Badge from '../common/Badge'
import { NetworkGraphResponse } from '../../types'
import ForceGraph2D from 'react-force-graph-2d'

interface RelationshipGraphProps {
  investigationId?: string
  facilityId?: string
}

const RelationshipGraph = ({ investigationId, facilityId }: RelationshipGraphProps) => {
  const { data, isLoading, error } = useGetNetworkGraphQuery(
    investigationId || facilityId || '',
    { skip: !investigationId && !facilityId }
  )

  const graphData = useMemo(() => {
    if (!data?.data) return null
    return data.data as NetworkGraphResponse
  }, [data])

  // Transform data for react-force-graph-2d
  const graphNodes = useMemo(() => {
    if (!graphData?.network) return { nodes: [], links: [] }

    const nodes = graphData.network.nodes.map((node) => ({
      ...node,
      id: node.id,
      name: node.label || node.name || node.id.substring(0, 8),
      type: node.type || 'unknown',
    }))

    const links = graphData.network.edges.map((edge) => ({
      source: edge.from,
      target: edge.to,
      type: edge.type,
      strength: edge.strength || 1,
    }))

    return { nodes, links }
  }, [graphData])

  const getNodeColor = useCallback((node: any) => {
    switch (node.type?.toLowerCase()) {
      case 'facility':
        return '#3B82F6' // blue
      case 'tiger':
        return '#EF4444' // red
      case 'investigation':
        return '#10B981' // green
      case 'person':
        return '#8B5CF6' // purple
      default:
        return '#6B7280' // gray
    }
  }, [])

  const getNodeSize = useCallback((node: any) => {
    // Scale node size based on connections or other metrics
    if (node.tiger_count) {
      return 8 + node.tiger_count * 2
    }
    return 8
  }, [])

  if (isLoading) {
    return (
      <Card>
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner />
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <div className="text-center text-red-600 py-8">
          Failed to load relationship graph
        </div>
      </Card>
    )
  }

  const network = graphData?.network
  if (!network || graphNodes.nodes.length === 0) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Relationship Graph</h3>
        <div className="text-center text-gray-500 py-12">
          <p>No relationship data available.</p>
          <p className="text-sm mt-2">Select a facility or investigation to visualize relationships.</p>
        </div>
      </Card>
    )
  }

  return (
    <Card>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Relationship Graph</h3>
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <span>{graphNodes.nodes.length} nodes</span>
          <span>{graphNodes.links.length} connections</span>
        </div>
      </div>

      {/* Interactive Force-Directed Graph */}
      <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
        <ForceGraph2D
          graphData={graphNodes}
          nodeColor={getNodeColor}
          nodeVal={getNodeSize}
          nodeLabel={(node: any) => `${node.name} (${node.type})`}
          linkColor={() => 'rgba(148, 163, 184, 0.6)'}
          linkWidth={(link: any) => link.strength || 1}
          linkDirectionalArrowLength={6}
          linkDirectionalArrowRelPos={1}
          linkCurvature={0.1}
          cooldownTicks={100}
          onNodeDragEnd={(node: any) => {
            node.fx = node.x
            node.fy = node.y
          }}
          onNodeClick={(node: any) => {
            // Pin/unpin node
            node.fx = node.fx === undefined ? node.x : undefined
            node.fy = node.fy === undefined ? node.y : undefined
          }}
          width={800}
          height={600}
        />
      </div>

      {/* Legend */}
      <div className="mt-6 flex flex-wrap gap-4">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-blue-500"></div>
          <span className="text-sm text-gray-600">Facility</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-red-500"></div>
          <span className="text-sm text-gray-600">Tiger</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-green-500"></div>
          <span className="text-sm text-gray-600">Investigation</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-purple-500"></div>
          <span className="text-sm text-gray-600">Person</span>
        </div>
      </div>

      {/* Instructions */}
      <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
        <p className="text-xs text-blue-800">
          <strong>Tip:</strong> Click and drag nodes to reposition them. Click a node to pin/unpin it.
          Nodes automatically arrange themselves based on their relationships.
        </p>
      </div>

      {/* Node Details */}
      {graphNodes.nodes.length > 0 && (
        <div className="mt-6 space-y-2">
          <h4 className="text-sm font-semibold text-gray-900">Nodes ({graphNodes.nodes.length})</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-48 overflow-y-auto">
            {graphNodes.nodes.map((node: any) => (
              <div
                key={node.id}
                className="p-2 bg-gray-50 rounded border border-gray-200 text-xs"
              >
                <div className="flex items-center space-x-1 mb-1">
                  <span>{node.name}</span>
                </div>
                {node.type && (
                  <Badge variant="info" className="text-xs">
                    {node.type}
                  </Badge>
                )}
                {node.state && (
                  <span className="text-gray-500 text-xs block mt-1">{node.state}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}

export default RelationshipGraph

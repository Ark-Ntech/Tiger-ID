import { useMemo } from 'react'
import { useGetInvestigationQuery, useGetTigerQuery } from '../../app/api'
import Card from '../common/Card'
import LoadingSpinner from '../common/LoadingSpinner'
import Badge from '../common/Badge'
import { formatDate } from '../../utils/formatters'
import { Link } from 'react-router-dom'

interface RelationshipsViewProps {
  investigationId: string
}

const RelationshipsView = ({ investigationId }: RelationshipsViewProps) => {
  const { data: investigationData, isLoading: investigationLoading } = useGetInvestigationQuery(investigationId)
  
  const investigation = investigationData?.data
  
  // Get related tigers
  const relatedTigers = useMemo(() => {
    if (!investigation?.related_tigers) return []
    return investigation.related_tigers
  }, [investigation])
  
  // Get related facilities (if any)
  const relatedFacilities = useMemo(() => {
    // This would come from investigation data if available
    return []
  }, [])
  
  if (investigationLoading) {
    return (
      <Card>
        <div className="flex items-center justify-center p-8">
          <LoadingSpinner size="lg" />
        </div>
      </Card>
    )
  }
  
  if (!investigation) {
    return (
      <Card>
        <div className="p-8 text-center text-gray-500">
          Investigation not found
        </div>
      </Card>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Related Tigers */}
      {relatedTigers.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Related Tigers
          </h3>
          <div className="space-y-3">
            {relatedTigers.map((tigerId: string) => (
              <TigerRelationshipCard key={tigerId} tigerId={tigerId} />
            ))}
          </div>
        </Card>
      )}
      
      {/* Related Facilities */}
      {relatedFacilities.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Related Facilities
          </h3>
          <div className="space-y-3">
            {relatedFacilities.map((facilityId: string) => (
              <FacilityRelationshipCard key={facilityId} facilityId={facilityId} />
            ))}
          </div>
        </Card>
      )}
      
      {/* No relationships */}
      {relatedTigers.length === 0 && relatedFacilities.length === 0 && (
        <Card>
          <div className="p-8 text-center text-gray-500">
            <p className="text-lg mb-2">No relationships found</p>
            <p className="text-sm">Relationships will appear here as the investigation progresses.</p>
          </div>
        </Card>
      )}
    </div>
  )
}

const TigerRelationshipCard = ({ tigerId }: { tigerId: string }) => {
  const { data: tigerData, isLoading } = useGetTigerQuery(tigerId, { skip: !tigerId })
  
  if (isLoading) {
    return (
      <div className="p-3 bg-gray-50 rounded-lg">
        <LoadingSpinner size="sm" />
      </div>
    )
  }
  
  if (!tigerData?.data) {
    return (
      <div className="p-3 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-600">Tiger ID: {tigerId}</p>
      </div>
    )
  }
  
  const tiger = tigerData.data
  
  return (
    <Link
      to={`/tigers`}
      className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="font-medium text-gray-900">{tiger.name || 'Unnamed Tiger'}</p>
          <p className="text-sm text-gray-500 mt-1">ID: {tigerId}</p>
          {tiger.status && (
            <Badge variant="info" className="mt-2">
              {tiger.status}
            </Badge>
          )}
        </div>
        <div className="text-right">
          {tiger.last_seen_date && (
            <p className="text-xs text-gray-500">
              Last seen: {formatDate(tiger.last_seen_date)}
            </p>
          )}
          {tiger.last_seen_location && (
            <p className="text-xs text-gray-500 mt-1">
              {tiger.last_seen_location}
            </p>
          )}
        </div>
      </div>
    </Link>
  )
}

const FacilityRelationshipCard = ({ facilityId }: { facilityId: string }) => {
  // This would fetch facility data if available
  return (
    <div className="p-4 bg-gray-50 rounded-lg">
      <p className="text-sm text-gray-600">Facility ID: {facilityId}</p>
    </div>
  )
}

export default RelationshipsView


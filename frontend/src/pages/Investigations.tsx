import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGetInvestigationsQuery } from '../app/api'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import Badge from '../components/common/Badge'
import LoadingSpinner from '../components/common/LoadingSpinner'
import { FolderOpenIcon, PlusIcon } from '@heroicons/react/24/outline'
import { formatDate } from '../utils/formatters'

const Investigations = () => {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined)

  const { data, isLoading, error } = useGetInvestigationsQuery({
    page,
    page_size: 10,
    status: statusFilter,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-red-600">Failed to load investigations</p>
      </div>
    )
  }

  const investigations = data?.data?.data || []
  const pagination = data?.data

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'in_progress':
        return 'info'
      case 'completed':
        return 'success'
      case 'archived':
        return 'default'
      default:
        return 'warning'
    }
  }

  const getPriorityVariant = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'danger'
      case 'high':
        return 'warning'
      case 'medium':
        return 'info'
      default:
        return 'default'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Investigations</h1>
          <p className="text-gray-600 mt-2">Manage and track all investigations</p>
        </div>
        <Button
          variant="primary"
          onClick={() => navigate('/investigations/launch')}
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          New Investigation
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium text-gray-700">Filter by Status:</label>
          <select
            value={statusFilter || ''}
            onChange={(e) => setStatusFilter(e.target.value || undefined)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All</option>
            <option value="draft">Draft</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </Card>

      {/* Investigations List */}
      <div className="space-y-4">
        {investigations.length > 0 ? (
          investigations.map((investigation: any) => (
            <Card
              key={investigation.id}
              className="hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => navigate(`/investigations/${investigation.id}`)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4 flex-1">
                  <div className="p-3 bg-primary-100 rounded-lg">
                    <FolderOpenIcon className="h-6 w-6 text-primary-600" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {investigation.title}
                      </h3>
                      <Badge variant={getStatusVariant(investigation.status)}>
                        {investigation.status?.replace('_', ' ')}
                      </Badge>
                      <Badge variant={getPriorityVariant(investigation.priority)}>
                        {investigation.priority}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 mt-2">
                      {investigation.description}
                    </p>
                    <div className="flex items-center space-x-4 mt-3 text-xs text-gray-500">
                      <span>Created: {formatDate(investigation.created_at)}</span>
                      {investigation.updated_at && (
                        <span>Updated: {formatDate(investigation.updated_at)}</span>
                      )}
                    </div>
                    {investigation.tags && investigation.tags.length > 0 && (
                      <div className="flex items-center space-x-2 mt-2">
                        {investigation.tags.map((tag: string) => (
                          <span
                            key={tag}
                            className={`px-2 py-1 text-gray-700 text-xs rounded ${
                              tag === 'auto-generated' 
                                ? 'bg-blue-100 text-blue-800' 
                                : 'bg-gray-100'
                            }`}
                          >
                            {tag === 'auto-generated' ? '🤖 ' + tag : tag}
                          </span>
                        ))}
                      </div>
                    )}
                    {investigation.related_tigers && investigation.related_tigers.length > 0 && (
                      <div className="flex items-center space-x-2 mt-2">
                        <span className="text-xs text-gray-500">
                          🐅 {investigation.related_tigers.length} related tiger(s)
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          ))
        ) : (
          <Card className="text-center py-12">
            <FolderOpenIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No investigations found</p>
            <Button
              variant="primary"
              className="mt-4"
              onClick={() => navigate('/investigations/launch')}
            >
              Create Your First Investigation
            </Button>
          </Card>
        )}
      </div>

      {/* Pagination */}
      {pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-gray-600">
            Page {page} of {pagination.total_pages}
          </span>
          <Button
            variant="outline"
            disabled={page >= pagination.total_pages}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  )
}

export default Investigations


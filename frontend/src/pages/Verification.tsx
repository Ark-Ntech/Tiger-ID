import { useState } from 'react'
import { useGetVerificationTasksQuery } from '../app/api'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import { CheckCircleIcon } from '@heroicons/react/24/outline'

const Verification = () => {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string | undefined>('pending')

  const { data, isLoading } = useGetVerificationTasksQuery({
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

  const tasks = data?.data?.data || []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Verification Tasks</h1>
        <p className="text-gray-600 mt-2">Review and verify evidence and data</p>
      </div>

      <Card>
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium text-gray-700">Filter by Status:</label>
          <select
            value={statusFilter || ''}
            onChange={(e) => setStatusFilter(e.target.value || undefined)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="verified">Verified</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </Card>

      {tasks.length > 0 ? (
        <div className="space-y-4">
          {tasks.map((task: any) => (
            <Card key={task.id} className="hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <CheckCircleIcon className="h-6 w-6 text-gray-400" />
                    <h3 className="text-lg font-semibold text-gray-900">
                      {task.type} Verification
                    </h3>
                    <Badge
                      variant={
                        task.status === 'verified'
                          ? 'success'
                          : task.status === 'rejected'
                          ? 'danger'
                          : 'warning'
                      }
                    >
                      {task.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600 mt-2">Entity ID: {task.entity_id}</p>
                  {task.notes && (
                    <p className="text-sm text-gray-500 mt-2">{task.notes}</p>
                  )}
                </div>
                {task.status === 'pending' && (
                  <div className="flex items-center space-x-2">
                    <Button variant="outline" size="sm">
                      Review
                    </Button>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="text-center py-12">
          <CheckCircleIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No verification tasks found</p>
        </Card>
      )}
    </div>
  )
}

export default Verification


import { useGetSavedSearchesQuery } from '../app/api'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import { BookmarkIcon } from '@heroicons/react/24/outline'

const SavedSearches = () => {
  const { data, isLoading } = useGetSavedSearchesQuery()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  const searches = data?.data || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Saved Searches</h1>
          <p className="text-gray-600 mt-2">Your saved search queries</p>
        </div>
        <Button variant="primary">Save New Search</Button>
      </div>

      {searches.length > 0 ? (
        <div className="space-y-4">
          {searches.map((search: any) => (
            <Card key={search.id} className="hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4">
                  <BookmarkIcon className="h-6 w-6 text-primary-600" />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{search.name}</h3>
                    <p className="text-sm text-gray-600 mt-1">{search.description}</p>
                  </div>
                </div>
                <Button variant="outline" size="sm">
                  Run Search
                </Button>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="text-center py-12">
          <BookmarkIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No saved searches yet</p>
        </Card>
      )}
    </div>
  )
}

export default SavedSearches


import { useGetTemplatesQuery } from '../app/api'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import { DocumentTextIcon } from '@heroicons/react/24/outline'

const Templates = () => {
  const { data, isLoading } = useGetTemplatesQuery()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  const templates = data?.data || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Investigation Templates</h1>
          <p className="text-gray-600 mt-2">Pre-configured investigation templates</p>
        </div>
        <Button 
          variant="primary"
          onClick={() => {
            // TODO: Implement template creation dialog
            alert('Template creation feature coming soon!')
          }}
        >
          Create Template
        </Button>
      </div>

      {templates.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.map((template: any) => (
            <Card key={template.id} className="hover:shadow-lg transition-shadow">
              <DocumentTextIcon className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-lg font-semibold text-gray-900">{template.name}</h3>
              <p className="text-sm text-gray-600 mt-2">{template.description}</p>
              <div className="mt-4 space-y-2">
                <Button 
                  variant="outline" 
                  className="w-full" 
                  size="sm"
                  onClick={() => {
                    // TODO: Implement template application
                    alert(`Template "${template.name}" application feature coming soon!`)
                  }}
                >
                  Use Template
                </Button>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="text-center py-12">
          <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No templates available</p>
        </Card>
      )}
    </div>
  )
}

export default Templates


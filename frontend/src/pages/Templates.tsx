import { useState } from 'react'
import { useGetTemplatesQuery, useApplyTemplateMutation } from '../app/api'
import { useNavigate } from 'react-router-dom'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import CreateTemplateDialog from '../components/templates/CreateTemplateDialog'
import { DocumentTextIcon } from '@heroicons/react/24/outline'

const Templates = () => {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [_selectedTemplateId, _setSelectedTemplateId] = useState<string | null>(null)
  void _selectedTemplateId; void _setSelectedTemplateId // Reserved for template selection feature
  const navigate = useNavigate()
  const { data, isLoading, refetch } = useGetTemplatesQuery()
  const [applyTemplate, { isLoading: isApplying }] = useApplyTemplateMutation()

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
          onClick={() => setIsCreateDialogOpen(true)}
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
                  onClick={async () => {
                    try {
                      // Create a new investigation first, then apply template
                      // For now, prompt for investigation ID or create new
                      const investigationId = prompt('Enter Investigation ID to apply template to (or leave blank to create new):')

                      if (investigationId === null) {
                        // User cancelled the prompt
                        return
                      }

                      if (investigationId) {
                        await applyTemplate({
                          template_id: template.template_id || template.id,
                          investigation_id: investigationId,
                        }).unwrap()
                        alert(`Template "${template.name}" applied successfully!`)
                        navigate(`/investigations/${investigationId}`)
                      } else {
                        // Navigate to launch investigation with template pre-selected
                        navigate('/investigations/launch', { state: { templateId: template.template_id || template.id } })
                      }
                    } catch (err: any) {
                      alert(`Failed to apply template: ${err?.data?.detail || err?.message || 'Unknown error'}`)
                    }
                  }}
                  disabled={isApplying}
                >
                  {isApplying ? 'Applying...' : 'Use Template'}
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

      <CreateTemplateDialog
        isOpen={isCreateDialogOpen}
        onClose={() => setIsCreateDialogOpen(false)}
        onSuccess={() => {
          refetch()
        }}
      />
    </div>
  )
}

export default Templates


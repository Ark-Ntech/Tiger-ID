import { useState } from 'react'
import { useCreateTemplateMutation } from '../../app/api'
import Button from '../common/Button'
import Alert from '../common/Alert'
import { XMarkIcon } from '@heroicons/react/24/outline'

interface CreateTemplateDialogProps {
  isOpen: boolean
  onClose: () => void
  onSuccess?: () => void
}

const CreateTemplateDialog = ({ isOpen, onClose, onSuccess }: CreateTemplateDialogProps) => {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [createTemplate, { isLoading, error }] = useCreateTemplateMutation()

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!name.trim()) {
      return
    }

    try {
      await createTemplate({
        name: name.trim(),
        description: description.trim() || undefined,
        workflow_steps: [],
        default_agents: [],
      }).unwrap()
      
      setName('')
      setDescription('')
      onSuccess?.()
      onClose()
    } catch (err) {
      console.error('Failed to create template:', err)
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity" onClick={onClose} />
        
        <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Create Template</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert type="error">
                {'data' in error ? JSON.stringify(error.data) : 'Failed to create template'}
              </Alert>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Template Name *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="e.g., Standard Investigation"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="Describe what this template is used for..."
              />
            </div>

            <div className="flex gap-3 justify-end pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={isLoading}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={isLoading || !name.trim()}
              >
                {isLoading ? 'Creating...' : 'Create Template'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default CreateTemplateDialog


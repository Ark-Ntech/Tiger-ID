import { useState } from 'react'
import {
  useGetAnnotationsQuery,
  useCreateAnnotationMutation,
  useUpdateAnnotationMutation,
  useDeleteAnnotationMutation,
} from '../../app/api'
import Card from '../common/Card'
import LoadingSpinner from '../common/LoadingSpinner'
import Button from '../common/Button'
import Badge from '../common/Badge'
import { formatDate } from '../../utils/formatters'
import { Annotation } from '../../types'
import { XMarkIcon, PencilIcon, TrashIcon, PlusIcon } from '@heroicons/react/24/outline'

interface AnnotationPanelProps {
  investigationId: string
}

const AnnotationPanel = ({ investigationId }: AnnotationPanelProps) => {
  const [isCreating, setIsCreating] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    content: '',
    annotation_type: 'note' as 'note' | 'highlight' | 'question' | 'tag',
    target_entity_type: 'investigation' as 'investigation' | 'evidence',
    target_entity_id: investigationId,
    metadata: {},
  })

  const { data, isLoading, error, refetch } = useGetAnnotationsQuery({
    target_entity_type: 'investigation',
    target_entity_id: investigationId,
  })

  const [createAnnotation] = useCreateAnnotationMutation()
  const [updateAnnotation] = useUpdateAnnotationMutation()
  const [deleteAnnotation] = useDeleteAnnotationMutation()

  const annotations = data?.data || []

  const handleCreate = async () => {
    if (!formData.content.trim()) return

    try {
      await createAnnotation({
        content: formData.content,
        annotation_type: formData.annotation_type,
        target_entity_type: formData.target_entity_type,
        target_entity_id: formData.target_entity_id,
        metadata: formData.metadata,
      }).unwrap()
      setIsCreating(false)
      setFormData({
        ...formData,
        content: '',
      })
      refetch()
    } catch (err) {
      console.error('Failed to create annotation:', err)
    }
  }

  const handleUpdate = async (id: string, content: string) => {
    try {
      await updateAnnotation({
        id,
        data: { content },
      }).unwrap()
      setEditingId(null)
      refetch()
    } catch (err) {
      console.error('Failed to update annotation:', err)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this annotation?')) return

    try {
      await deleteAnnotation(id).unwrap()
      refetch()
    } catch (err) {
      console.error('Failed to delete annotation:', err)
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'note':
        return '📝'
      case 'highlight':
        return '💡'
      case 'question':
        return '❓'
      case 'tag':
        return '🏷️'
      default:
        return '📌'
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'note':
        return 'bg-blue-100 text-blue-800'
      case 'highlight':
        return 'bg-yellow-100 text-yellow-800'
      case 'question':
        return 'bg-purple-100 text-purple-800'
      case 'tag':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (isLoading) {
    return (
      <Card>
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner />
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <div className="text-center text-red-600 py-8">
          Failed to load annotations
        </div>
      </Card>
    )
  }

  return (
    <Card>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Annotations ({annotations.length})
        </h3>
        {!isCreating && (
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsCreating(true)}
          >
            <PlusIcon className="h-4 w-4 mr-1" />
            Add Annotation
          </Button>
        )}
      </div>

      {/* Create form */}
      {isCreating && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Type
              </label>
              <select
                value={formData.annotation_type}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    annotation_type: e.target.value as any,
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="note">Note</option>
                <option value="highlight">Highlight</option>
                <option value="question">Question</option>
                <option value="tag">Tag</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Content
              </label>
              <textarea
                value={formData.content}
                onChange={(e) =>
                  setFormData({ ...formData, content: e.target.value })
                }
                placeholder="Enter your annotation..."
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div className="flex space-x-2">
              <Button variant="primary" size="sm" onClick={handleCreate}>
                Create
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setIsCreating(false)
                  setFormData({
                    ...formData,
                    content: '',
                  })
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Annotations list */}
      {annotations.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          <p>No annotations yet. Click "Add Annotation" to create one.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {annotations.map((annotation: Annotation) => (
            <div
              key={annotation.id}
              className="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="text-xl">
                    {getTypeIcon(annotation.annotation_type)}
                  </span>
                  <Badge
                    variant="info"
                    className={getTypeColor(annotation.annotation_type)}
                  >
                    {annotation.annotation_type}
                  </Badge>
                  <span className="text-xs text-gray-500">
                    {formatDate(annotation.created_at)}
                  </span>
                </div>
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() =>
                      setEditingId(
                        editingId === annotation.id ? null : annotation.id
                      )
                    }
                    className="p-1 text-gray-400 hover:text-gray-600"
                  >
                    <PencilIcon className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(annotation.id)}
                    className="p-1 text-gray-400 hover:text-red-600"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {editingId === annotation.id ? (
                <div className="space-y-2">
                  <textarea
                    defaultValue={annotation.content}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    ref={(el) => {
                      if (el) {
                        el.focus()
                        el.select()
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.ctrlKey) {
                        handleUpdate(annotation.id, e.currentTarget.value)
                      }
                      if (e.key === 'Escape') {
                        setEditingId(null)
                      }
                    }}
                  />
                  <div className="flex space-x-2">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() =>
                        handleUpdate(
                          annotation.id,
                          (
                            document.querySelector(
                              `textarea[defaultValue="${annotation.content}"]`
                            ) as HTMLTextAreaElement
                          )?.value || annotation.content
                        )
                      }
                    >
                      Save
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setEditingId(null)}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                  {annotation.content}
                </p>
              )}

              {annotation.metadata && Object.keys(annotation.metadata).length > 0 && (
                <div className="mt-2 text-xs text-gray-400">
                  {JSON.stringify(annotation.metadata)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

export default AnnotationPanel


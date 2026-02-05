import { useRef, useCallback } from 'react'
import Card from '../common/Card'
import { PhotoIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { useInvestigation2 } from '../../context/Investigation2Context'

/**
 * Investigation 2.0 upload component.
 * Uses context for state management instead of props.
 */
const Investigation2Upload = () => {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const {
    uploadedImage,
    imagePreview,
    context,
    investigationId,
    isLaunching,
    setUploadedImage,
    setImagePreview,
    updateContext,
  } = useInvestigation2()

  // Disable interactions when investigation is running
  const disabled = !!investigationId || isLaunching

  const handleImageUpload = useCallback(
    (file: File) => {
      setUploadedImage(file)

      // Create preview
      const reader = new FileReader()
      reader.onloadend = () => {
        setImagePreview(reader.result as string)
      }
      reader.readAsDataURL(file)
    },
    [setUploadedImage, setImagePreview]
  )

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()

      if (disabled) return

      const files = e.dataTransfer.files
      if (files.length > 0) {
        const file = files[0]
        if (file.type.startsWith('image/')) {
          handleImageUpload(file)
        }
      }
    },
    [disabled, handleImageUpload]
  )

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (files && files.length > 0) {
        handleImageUpload(files[0])
      }
    },
    [handleImageUpload]
  )

  const handleRemoveImage = useCallback(() => {
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
    setUploadedImage(null)
    setImagePreview(null)
  }, [setUploadedImage, setImagePreview])

  const handleContextChange = useCallback(
    (field: 'location' | 'date' | 'notes', value: string) => {
      updateContext(field, value)
    },
    [updateContext]
  )

  return (
    <Card>
      <div className="p-6">
        <h2 className="text-xl font-semibold mb-4">Upload Tiger Image</h2>

        {/* Image Upload Area */}
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
            disabled
              ? 'border-gray-300 bg-gray-50 cursor-not-allowed'
              : 'border-gray-400 hover:border-blue-500 cursor-pointer'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => !disabled && fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
            disabled={disabled}
          />

          {imagePreview ? (
            <div className="relative">
              <img
                src={imagePreview}
                alt="Uploaded tiger"
                className="max-h-64 mx-auto rounded-lg"
              />
              {!disabled && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleRemoveImage()
                  }}
                  className="absolute top-2 right-2 p-2 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              )}
              {uploadedImage && (
                <p className="mt-2 text-sm text-gray-600">
                  {uploadedImage.name} ({(uploadedImage.size / 1024).toFixed(1)} KB)
                </p>
              )}
            </div>
          ) : (
            <div className="py-8">
              <PhotoIcon className="w-16 h-16 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600 mb-2">
                Drag and drop a tiger image here, or click to browse
              </p>
              <p className="text-sm text-gray-500">
                Supported formats: JPG, PNG, WEBP (Max 20 MB)
              </p>
            </div>
          )}
        </div>

        {/* Context Fields */}
        <div className="mt-6 space-y-4">
          <h3 className="text-lg font-medium">Investigation Context</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Location
            </label>
            <input
              type="text"
              value={context.location || ''}
              onChange={(e) => handleContextChange('location', e.target.value)}
              placeholder="e.g., Texas, USA"
              disabled={disabled}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Date
            </label>
            <input
              type="date"
              value={context.date || ''}
              onChange={(e) => handleContextChange('date', e.target.value)}
              disabled={disabled}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Additional Notes
            </label>
            <textarea
              value={context.notes || ''}
              onChange={(e) => handleContextChange('notes', e.target.value)}
              placeholder="Add any relevant information about this sighting..."
              rows={4}
              disabled={disabled}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed resize-none"
            />
          </div>
        </div>
      </div>
    </Card>
  )
}

export default Investigation2Upload

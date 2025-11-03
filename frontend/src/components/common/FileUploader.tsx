import { useState, useCallback } from 'react'
import { CloudArrowUpIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { cn } from '../../utils/cn'
import { formatFileSize } from '../../utils/formatters'

interface FileUploaderProps {
  onFilesSelected: (files: File[]) => void
  accept?: string
  multiple?: boolean
  maxSize?: number // in bytes
  maxFiles?: number
}

const FileUploader = ({
  onFilesSelected,
  accept,
  multiple = true,
  maxSize = 10 * 1024 * 1024, // 10MB default
  maxFiles = 10,
}: FileUploaderProps) => {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [error, setError] = useState<string | null>(null)

  const validateFiles = (files: FileList | null): File[] => {
    if (!files || files.length === 0) return []

    const fileArray = Array.from(files)
    const validFiles: File[] = []

    for (const file of fileArray) {
      if (file.size > maxSize) {
        setError(`File ${file.name} exceeds maximum size of ${formatFileSize(maxSize)}`)
        continue
      }

      if (multiple && validFiles.length >= maxFiles) {
        setError(`Maximum ${maxFiles} files allowed`)
        break
      }

      validFiles.push(file)
    }

    return validFiles
  }

  const handleFiles = useCallback(
    (files: FileList | null) => {
      setError(null)
      const validFiles = validateFiles(files)

      if (validFiles.length > 0) {
        const newFiles = multiple
          ? [...selectedFiles, ...validFiles].slice(0, maxFiles)
          : [validFiles[0]]

        setSelectedFiles(newFiles)
        onFilesSelected(newFiles)
      }
    },
    [selectedFiles, multiple, maxFiles, onFilesSelected]
  )

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()

    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setDragActive(false)

      handleFiles(e.dataTransfer.files)
    },
    [handleFiles]
  )

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      handleFiles(e.target.files)
    },
    [handleFiles]
  )

  const removeFile = useCallback(
    (index: number) => {
      const newFiles = selectedFiles.filter((_, i) => i !== index)
      setSelectedFiles(newFiles)
      onFilesSelected(newFiles)
    },
    [selectedFiles, onFilesSelected]
  )

  return (
    <div className="w-full">
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={cn(
          'relative border-2 border-dashed rounded-lg p-8 text-center transition-colors',
          dragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-gray-400'
        )}
      >
        <input
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />

        <CloudArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        
        <p className="text-sm font-medium text-gray-900">
          {dragActive ? 'Drop files here' : 'Drag and drop files here'}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          or click to browse ({formatFileSize(maxSize)} max)
        </p>
      </div>

      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}

      {/* Selected Files */}
      {selectedFiles.length > 0 && (
        <div className="mt-4 space-y-2">
          <p className="text-sm font-medium text-gray-700">Selected Files:</p>
          {selectedFiles.map((file, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{file.name}</p>
                <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
              </div>
              <button
                type="button"
                onClick={() => removeFile(index)}
                className="text-gray-400 hover:text-red-600 transition-colors"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default FileUploader


import { useState } from 'react'
import Button from '../common/Button'
import LoadingSpinner from '../common/LoadingSpinner'
import { DocumentArrowDownIcon, XMarkIcon } from '@heroicons/react/24/outline'

interface ExportDialogProps {
  investigationId: string
  investigationTitle: string
  onClose: () => void
}

const ExportDialog = ({
  investigationId,
  investigationTitle,
  onClose,
}: ExportDialogProps) => {
  const [exporting, setExporting] = useState<string | null>(null)
  const [includeEvidence, setIncludeEvidence] = useState(true)
  const [includeSteps, setIncludeSteps] = useState(true)
  const [includeMetadata, setIncludeMetadata] = useState(true)

  const handleExport = async (format: string) => {
    setExporting(format)
    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      let url: string
      let filename: string

      if (format === 'json') {
        url = `${baseUrl}/api/v1/investigations/${investigationId}/export/json?include_evidence=${includeEvidence}&include_steps=${includeSteps}&include_metadata=${includeMetadata}`
        filename = `${investigationTitle}_${format}.json`
      } else if (format === 'markdown') {
        url = `${baseUrl}/api/v1/investigations/${investigationId}/export/markdown?include_evidence=${includeEvidence}&include_steps=${includeSteps}`
        filename = `${investigationTitle}_${format}.md`
      } else if (format === 'pdf') {
        url = `${baseUrl}/api/v1/investigations/${investigationId}/export/pdf?include_evidence=${includeEvidence}&include_steps=${includeSteps}`
        filename = `${investigationTitle}_${format}.pdf`
      } else if (format === 'csv') {
        url = `${baseUrl}/api/v1/investigations/${investigationId}/export/csv?data_type=evidence`
        filename = `${investigationTitle}_${format}.csv`
      } else {
        return
      }

      // Fetch the file with authentication
      const token = localStorage.getItem('token') || sessionStorage.getItem('token')
      const response = await fetch(url, {
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      })

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`)
      }

      const blob = await response.blob()

      // Create a temporary link to download the file
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = filename.replace(/[^a-z0-9.]/gi, '_').toLowerCase()
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(link.href)
    } catch (error) {
      console.error(`Failed to export as ${format}:`, error)
      alert(`Failed to export as ${format}. Please try again.`)
    } finally {
      setExporting(null)
    }
  }

  const exportFormats = [
    { id: 'json', name: 'JSON', description: 'Machine-readable format', icon: '📄' },
    {
      id: 'markdown',
      name: 'Markdown',
      description: 'Human-readable format',
      icon: '📝',
    },
    {
      id: 'pdf',
      name: 'PDF',
      description: 'Printable document',
      icon: '📕',
    },
    {
      id: 'csv',
      name: 'CSV',
      description: 'Spreadsheet format',
      icon: '📊',
    },
  ]

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Export Investigation</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Options */}
          <div className="space-y-3">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={includeEvidence}
                onChange={(e) => setIncludeEvidence(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">Include Evidence</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={includeSteps}
                onChange={(e) => setIncludeSteps(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">Include Steps</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={includeMetadata}
                onChange={(e) => setIncludeMetadata(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">Include Metadata</span>
            </label>
          </div>

          {/* Export formats */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700 mb-3">
              Choose export format:
            </p>
            {exportFormats.map((format) => (
              <button
                key={format.id}
                onClick={() => handleExport(format.id)}
                disabled={exporting !== null}
                className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 hover:border-primary-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{format.icon}</span>
                  <div className="text-left">
                    <p className="font-medium text-gray-900">{format.name}</p>
                    <p className="text-xs text-gray-500">{format.description}</p>
                  </div>
                </div>
                {exporting === format.id ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <DocumentArrowDownIcon className="h-5 w-5 text-gray-400" />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end p-6 border-t border-gray-200">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  )
}

export default ExportDialog


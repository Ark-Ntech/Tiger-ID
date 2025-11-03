import { useState } from 'react'
import Card from '../common/Card'
import Button from '../common/Button'
import FileUploader from '../common/FileUploader'
import { DocumentArrowUpIcon } from '@heroicons/react/24/outline'

const ReferenceDataTab = () => {
  const [createVerifications, setCreateVerifications] = useState(true)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>(
    'idle'
  )
  const [uploadMessage, setUploadMessage] = useState('')

  const handleFileChange = (file: File | null) => {
    setUploadedFile(file)
    setUploadStatus('idle')
    setUploadMessage('')
  }

  const handleImport = async () => {
    if (!uploadedFile) {
      setUploadMessage('Please upload a reference facility file')
      setUploadStatus('error')
      return
    }

    setUploadStatus('uploading')
    setUploadMessage('Importing reference facilities...')

    try {
      // TODO: Implement actual file upload endpoint
      // For now, this is a placeholder
      await new Promise((resolve) => setTimeout(resolve, 2000))
      setUploadStatus('success')
      setUploadMessage('✅ Reference facilities imported successfully!')
    } catch (err) {
      setUploadStatus('error')
      setUploadMessage('Import failed. Please try again.')
      console.error('Import error:', err)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <DocumentArrowUpIcon className="h-6 w-6 text-primary-600" />
          Reference Data Management
        </h2>
        <p className="text-gray-600 mt-2">Import and manage reference facility dataset</p>
      </div>

      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Import Reference Facilities</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload Reference Facility Excel File
            </label>
            <p className="text-xs text-gray-500 mb-2">
              Upload the TPC Tigers non-accredited facilities spreadsheet
            </p>
            <FileUploader
              accept=".xlsx,.xls"
              onFilesSelected={(files) => handleFileChange(files[0] || null)}
              multiple={false}
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={createVerifications}
              onChange={(e) => setCreateVerifications(e.target.checked)}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <label className="text-sm text-gray-700">Create Verification Requests</label>
          </div>

          <Button
            onClick={handleImport}
            disabled={!uploadedFile || uploadStatus === 'uploading'}
            className="w-full"
          >
            {uploadStatus === 'uploading' ? 'Importing...' : '📥 Import Reference Data'}
          </Button>

          {uploadMessage && (
            <div
              className={`p-3 rounded-lg text-sm ${
                uploadStatus === 'success'
                  ? 'bg-green-50 text-green-700'
                  : uploadStatus === 'error'
                  ? 'bg-red-50 text-red-700'
                  : 'bg-blue-50 text-blue-700'
              }`}
            >
              {uploadMessage}
            </div>
          )}
        </div>
      </Card>

      <Card>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Reference Facilities</h3>
          <Button variant="outline" size="sm">
            Refresh
          </Button>
        </div>
        <div className="text-center py-8">
          <p className="text-gray-500">
            Reference facility list will appear here after import.
          </p>
          <p className="text-sm text-gray-400 mt-2">
            Import reference data to get started.
          </p>
        </div>
      </Card>
    </div>
  )
}

export default ReferenceDataTab


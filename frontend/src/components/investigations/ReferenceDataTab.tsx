import { useState } from 'react'
import Card from '../common/Card'
import Button from '../common/Button'
import FileUploader from '../common/FileUploader'
import Alert from '../common/Alert'
import { useImportFacilitiesExcelMutation } from '../../app/api'
import { DocumentArrowUpIcon } from '@heroicons/react/24/outline'

const ReferenceDataTab = () => {
  const [createVerifications, setCreateVerifications] = useState(true)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploadMessage, setUploadMessage] = useState('')
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [importFacilities, { isLoading: isImporting }] = useImportFacilitiesExcelMutation()

  const handleFileChange = (file: File | null) => {
    setUploadedFile(file)
    setUploadMessage('')
    setUploadStatus('idle')
  }

  const handleImport = async () => {
    if (!uploadedFile) {
      setUploadMessage('Please select a file to upload')
      setUploadStatus('error')
      return
    }

    try {
      const result = await importFacilities({
        file: uploadedFile,
        update_existing: true,
      }).unwrap()

      if (result.success && result.data) {
        const { message, stats } = result.data
        setUploadMessage(message || `Successfully imported ${stats.created} facilities, updated ${stats.updated}`)
        setUploadStatus('success')
        setUploadedFile(null) // Clear file after successful upload
      }
    } catch (err: any) {
      console.error('Import error:', err)
      const errorMsg = err?.data?.detail || err?.message || 'Failed to import facilities. Please try again.'
      setUploadMessage(errorMsg)
      setUploadStatus('error')
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
            disabled={!uploadedFile || isImporting}
            className="w-full"
          >
            {isImporting ? 'Importing...' : '📥 Import Reference Data'}
          </Button>

          {uploadMessage && (
            <Alert 
              type={uploadStatus === 'success' ? 'success' : uploadStatus === 'error' ? 'error' : 'info'} 
              className="mt-4"
            >
              {uploadMessage}
            </Alert>
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


import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Card, { CardHeader, CardTitle, CardDescription } from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Badge from '../components/common/Badge'
import Modal from '../components/common/Modal'
import { cn } from '../utils/cn'
import {
  PhotoIcon,
  ArrowLeftIcon,
  ArrowDownTrayIcon,
  TrashIcon,
  PlusIcon,
  XMarkIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowPathIcon,
  CpuChipIcon,
  ChartBarIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  FolderOpenIcon,
  ArrowUpTrayIcon,
} from '@heroicons/react/24/outline'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ExportFormat = 'zip' | 'coco' | 'yolo' | 'csv'
type ImageQualityFilter = 'all' | 'high' | 'medium' | 'low'

interface DatasetStats {
  totalTigers: number
  totalImages: number
  avgImagesPerTiger: number
  readyForTraining: number
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const DatasetManagement = () => {
  const navigate = useNavigate()

  // Data state
  const [tigers, setTigers] = useState<any[]>([])
  const [tigerImages, setTigerImages] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)

  // Selection state
  const [selectedTiger, setSelectedTiger] = useState<string>('')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])

  // UI state
  const [showAddImagesModal, setShowAddImagesModal] = useState(false)
  const [showExportModal, setShowExportModal] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [qualityFilter, setQualityFilter] = useState<ImageQualityFilter>('all')
  const [exportFormat, setExportFormat] = useState<ExportFormat>('zip')
  const [exportAllTigers, setExportAllTigers] = useState(false)
  const [isExporting, setIsExporting] = useState(false)

  // Derived
  const filteredTigers = tigers.filter(
    (t) =>
      !searchTerm ||
      (t.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (t.id || '').toLowerCase().includes(searchTerm.toLowerCase())
  )

  const stats: DatasetStats = {
    totalTigers: tigers.length,
    totalImages: tigers.reduce((sum: number, t: any) => sum + (t.image_count || 0), 0),
    avgImagesPerTiger: tigers.length > 0
      ? Math.round(tigers.reduce((sum: number, t: any) => sum + (t.image_count || 0), 0) / tigers.length)
      : 0,
    readyForTraining: tigers.filter((t: any) => (t.image_count || 0) >= 5).length,
  }

  // -------------------------------------------------------------------------
  // Data loading
  // -------------------------------------------------------------------------

  useEffect(() => {
    fetchTigers()
  }, [])

  useEffect(() => {
    if (selectedTiger) fetchTigerImages(selectedTiger)
  }, [selectedTiger])

  const fetchTigers = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/v1/tigers?page_size=100', {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      const data = await response.json()
      setTigers(data.data?.data || [])
    } catch (error) {
      console.error('Error fetching tigers:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchTigerImages = async (tigerId: string) => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`/api/v1/tigers/${tigerId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      const data = await response.json()
      setTigerImages(data.data?.images || [])
    } catch (error) {
      console.error('Error fetching tiger images:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------

  const handleAddImages = async () => {
    if (!selectedTiger || selectedFiles.length === 0) {
      alert('Please select a tiger and at least one image')
      return
    }

    setIsLoading(true)
    try {
      const formData = new FormData()
      selectedFiles.forEach((file) => formData.append('images', file))

      const response = await fetch(`/api/v1/tigers/${selectedTiger}/images`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        body: formData,
      })

      if (!response.ok) throw new Error('Failed to add images')

      alert('Images added successfully')
      setShowAddImagesModal(false)
      setSelectedFiles([])
      fetchTigerImages(selectedTiger)
      fetchTigers() // refresh counts
    } catch (error: any) {
      alert(`Failed to add images: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRemoveImage = async (imageId: string) => {
    if (!confirm('Are you sure you want to remove this image from the dataset?')) return

    try {
      const response = await fetch(`/api/v1/tigers/${selectedTiger}/images/${imageId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
      })
      if (!response.ok) throw new Error('Failed to remove image')
      fetchTigerImages(selectedTiger)
      fetchTigers()
    } catch (error: any) {
      alert(`Failed to remove image: ${error.message}`)
    }
  }

  const handleExportDataset = async () => {
    setIsExporting(true)
    try {
      const endpoint = exportAllTigers
        ? `/api/v1/dataset/export?format=${exportFormat}`
        : `/api/v1/tigers/${selectedTiger}/export-dataset?format=${exportFormat}`

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
      })

      if (!response.ok) throw new Error('Failed to export dataset')

      const blob = await response.blob()
      const ext = exportFormat === 'zip' ? 'zip' : exportFormat === 'csv' ? 'csv' : 'zip'
      const filename = exportAllTigers
        ? `tiger_dataset_full.${ext}`
        : `tiger_${selectedTiger}_dataset.${ext}`

      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      setShowExportModal(false)
    } catch (error: any) {
      alert(`Failed to export dataset: ${error.message}`)
    } finally {
      setIsExporting(false)
    }
  }

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/dashboard')} className="flex items-center gap-2">
            <ArrowLeftIcon className="h-5 w-5" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-tactical-900 dark:text-tactical-100">Dataset Management</h1>
            <p className="text-tactical-500 dark:text-tactical-400 mt-1">
              Manage training datasets for the 6-model tiger re-identification ensemble
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {selectedTiger && (
            <Button
              variant="outline"
              onClick={() => setShowAddImagesModal(true)}
              className="flex items-center gap-2"
            >
              <PlusIcon className="h-5 w-5" />
              Add Images
            </Button>
          )}
          <Button
            variant="secondary"
            onClick={() => setShowExportModal(true)}
            className="flex items-center gap-2"
          >
            <ArrowDownTrayIcon className="h-5 w-5" />
            Export
          </Button>
        </div>
      </div>

      {/* Dataset Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card padding="sm">
          <div className="flex items-center gap-2 mb-1">
            <FolderOpenIcon className="h-4 w-4 text-tiger-orange" />
            <p className="text-xs font-medium uppercase tracking-wider text-tactical-500 dark:text-tactical-400">
              Tigers
            </p>
          </div>
          <p className="text-2xl font-bold text-tactical-900 dark:text-tactical-100">{stats.totalTigers}</p>
        </Card>
        <Card padding="sm">
          <div className="flex items-center gap-2 mb-1">
            <PhotoIcon className="h-4 w-4 text-tiger-orange" />
            <p className="text-xs font-medium uppercase tracking-wider text-tactical-500 dark:text-tactical-400">
              Total Images
            </p>
          </div>
          <p className="text-2xl font-bold text-tactical-900 dark:text-tactical-100">{stats.totalImages}</p>
        </Card>
        <Card padding="sm">
          <div className="flex items-center gap-2 mb-1">
            <ChartBarIcon className="h-4 w-4 text-tiger-orange" />
            <p className="text-xs font-medium uppercase tracking-wider text-tactical-500 dark:text-tactical-400">
              Avg / Tiger
            </p>
          </div>
          <p className="text-2xl font-bold text-tactical-900 dark:text-tactical-100">{stats.avgImagesPerTiger}</p>
        </Card>
        <Card padding="sm">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircleIcon className="h-4 w-4 text-emerald-500" />
            <p className="text-xs font-medium uppercase tracking-wider text-tactical-500 dark:text-tactical-400">
              Training Ready
            </p>
          </div>
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{stats.readyForTraining}</p>
          <p className="text-xs text-tactical-400 dark:text-tactical-500">5+ images</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tiger Selection Panel */}
        <Card>
          <CardHeader
            action={
              <Button variant="ghost" size="sm" onClick={fetchTigers} className="flex items-center gap-1">
                <ArrowPathIcon className="h-3.5 w-3.5" />
              </Button>
            }
          >
            <CardTitle as="h2">Tigers</CardTitle>
            <CardDescription>{tigers.length} total</CardDescription>
          </CardHeader>

          {/* Search */}
          <div className="relative mb-4">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-tactical-400" />
            <input
              type="text"
              placeholder="Search tigers..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={cn(
                'w-full pl-9 pr-3 py-2 rounded-lg border text-sm',
                'bg-white dark:bg-tactical-800',
                'border-tactical-300 dark:border-tactical-600',
                'text-tactical-900 dark:text-tactical-100',
                'placeholder:text-tactical-400 dark:placeholder:text-tactical-500',
                'focus:outline-none focus:ring-2 focus:ring-tiger-orange/50 focus:border-tiger-orange'
              )}
            />
          </div>

          {isLoading && !selectedTiger ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner size="sm" />
            </div>
          ) : (
            <div className="space-y-1.5 max-h-[28rem] overflow-y-auto pr-1">
              {filteredTigers.length === 0 ? (
                <p className="text-sm text-tactical-500 dark:text-tactical-400 text-center py-8">
                  {searchTerm ? 'No tigers match your search' : 'No tigers in the database'}
                </p>
              ) : (
                filteredTigers.map((tiger: any) => {
                  const count = tiger.image_count || 0
                  const isSelected = selectedTiger === tiger.id
                  const isReady = count >= 5
                  return (
                    <button
                      key={tiger.id}
                      onClick={() => setSelectedTiger(tiger.id)}
                      className={cn(
                        'w-full text-left p-3 rounded-lg transition-all duration-200',
                        isSelected
                          ? 'bg-tiger-orange/10 border border-tiger-orange/30'
                          : 'hover:bg-tactical-50 dark:hover:bg-tactical-800 border border-transparent'
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div className="min-w-0">
                          <p
                            className={cn(
                              'font-medium text-sm truncate',
                              isSelected
                                ? 'text-tiger-orange'
                                : 'text-tactical-900 dark:text-tactical-100'
                            )}
                          >
                            {tiger.name || `Tiger #${(tiger.id || '').substring(0, 8)}`}
                          </p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-xs text-tactical-500 dark:text-tactical-400">
                              {count} image{count !== 1 ? 's' : ''}
                            </span>
                            {isReady ? (
                              <Badge variant="success" size="xs">Ready</Badge>
                            ) : (
                              <Badge variant="warning" size="xs">Need {5 - count} more</Badge>
                            )}
                          </div>
                        </div>
                        {isSelected && (
                          <div className="w-2 h-2 rounded-full bg-tiger-orange shrink-0" />
                        )}
                      </div>
                    </button>
                  )
                })
              )}
            </div>
          )}
        </Card>

        {/* Images Panel */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader
              action={
                selectedTiger ? (
                  <div className="flex items-center gap-2">
                    <Badge variant="info" size="sm">
                      {tigerImages.length} image{tigerImages.length !== 1 ? 's' : ''}
                    </Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowAddImagesModal(true)}
                      className="flex items-center gap-1"
                    >
                      <PlusIcon className="h-3.5 w-3.5" />
                      Add
                    </Button>
                  </div>
                ) : undefined
              }
            >
              <CardTitle as="h2">
                {selectedTiger ? 'Dataset Images' : 'Select a Tiger'}
              </CardTitle>
              {selectedTiger && (
                <CardDescription>
                  Images used for training and embedding generation across all 6 ensemble models
                </CardDescription>
              )}
            </CardHeader>

            {selectedTiger ? (
              isLoading ? (
                <div className="flex items-center justify-center py-16">
                  <LoadingSpinner size="lg" />
                </div>
              ) : tigerImages.length > 0 ? (
                <>
                  {/* Quality filter */}
                  <div className="flex items-center gap-2 mb-4">
                    <FunnelIcon className="h-4 w-4 text-tactical-400" />
                    <span className="text-xs text-tactical-500 dark:text-tactical-400">Quality:</span>
                    {(['all', 'high', 'medium', 'low'] as ImageQualityFilter[]).map((q) => (
                      <button
                        key={q}
                        onClick={() => setQualityFilter(q)}
                        className={cn(
                          'px-2 py-0.5 rounded-full text-xs font-medium transition-colors capitalize',
                          qualityFilter === q
                            ? 'bg-tiger-orange text-white'
                            : 'bg-tactical-100 dark:bg-tactical-800 text-tactical-600 dark:text-tactical-400 hover:bg-tactical-200 dark:hover:bg-tactical-700'
                        )}
                      >
                        {q}
                      </button>
                    ))}
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {tigerImages.map((image: any) => (
                      <div
                        key={image.id}
                        className={cn(
                          'relative aspect-square rounded-lg overflow-hidden group',
                          'bg-tactical-100 dark:bg-tactical-800',
                          'border border-tactical-200 dark:border-tactical-700'
                        )}
                      >
                        <img
                          src={
                            image.url?.startsWith('http')
                              ? image.url
                              : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${image.url || ''}`
                          }
                          alt={`Image ${image.id}`}
                          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                        />
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all duration-300 flex items-center justify-center gap-2">
                          <button
                            onClick={() => handleRemoveImage(image.id)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity p-2 bg-red-600 text-white rounded-lg hover:bg-red-700 shadow-lg"
                            title="Remove from dataset"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                        {/* Image quality indicator */}
                        {image.quality_score != null && (
                          <div className="absolute top-1.5 right-1.5">
                            <Badge
                              variant={
                                image.quality_score >= 0.8
                                  ? 'success'
                                  : image.quality_score >= 0.5
                                  ? 'warning'
                                  : 'danger'
                              }
                              size="xs"
                            >
                              {Math.round(image.quality_score * 100)}%
                            </Badge>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="text-center py-16">
                  <PhotoIcon className="h-12 w-12 mx-auto mb-4 text-tactical-300 dark:text-tactical-600" />
                  <p className="text-tactical-500 dark:text-tactical-400 font-medium">No images in dataset</p>
                  <p className="text-sm text-tactical-400 dark:text-tactical-500 mt-1">
                    Add images to use this tiger for ensemble training
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAddImagesModal(true)}
                    className="mt-4 flex items-center gap-2 mx-auto"
                  >
                    <ArrowUpTrayIcon className="h-4 w-4" />
                    Add Images
                  </Button>
                </div>
              )
            ) : (
              <div className="text-center py-16">
                <CpuChipIcon className="h-12 w-12 mx-auto mb-4 text-tactical-300 dark:text-tactical-600" />
                <p className="text-tactical-500 dark:text-tactical-400 font-medium">Select a tiger to manage its dataset</p>
                <p className="text-sm text-tactical-400 dark:text-tactical-500 mt-1">
                  Choose a tiger from the panel on the left to view and manage its training images
                </p>
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Ensemble training info */}
      <Card>
        <CardHeader>
          <CardTitle as="h2">
            <InformationCircleIcon className="h-5 w-5 inline-block mr-2 text-tiger-orange" />
            Dataset Requirements
          </CardTitle>
          <CardDescription>Requirements for training the 6-model ensemble</CardDescription>
        </CardHeader>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-tactical-50 dark:bg-tactical-800/50 rounded-lg p-4">
            <h3 className="font-semibold text-sm text-tactical-900 dark:text-tactical-100 mb-2">Minimum Requirements</h3>
            <ul className="space-y-1.5 text-xs text-tactical-600 dark:text-tactical-400">
              <li className="flex items-start gap-2">
                <CheckCircleIcon className="h-3.5 w-3.5 text-emerald-500 shrink-0 mt-0.5" />
                5+ images per tiger identity
              </li>
              <li className="flex items-start gap-2">
                <CheckCircleIcon className="h-3.5 w-3.5 text-emerald-500 shrink-0 mt-0.5" />
                Clear stripe pattern visibility
              </li>
              <li className="flex items-start gap-2">
                <CheckCircleIcon className="h-3.5 w-3.5 text-emerald-500 shrink-0 mt-0.5" />
                Resolution 640x640 or higher
              </li>
              <li className="flex items-start gap-2">
                <CheckCircleIcon className="h-3.5 w-3.5 text-emerald-500 shrink-0 mt-0.5" />
                Multiple angles recommended
              </li>
            </ul>
          </div>
          <div className="bg-tactical-50 dark:bg-tactical-800/50 rounded-lg p-4">
            <h3 className="font-semibold text-sm text-tactical-900 dark:text-tactical-100 mb-2">Supported Formats</h3>
            <div className="flex flex-wrap gap-1.5">
              {['JPEG', 'PNG', 'WEBP', 'TIFF', 'BMP'].map((fmt) => (
                <Badge key={fmt} variant="outline" size="xs">{fmt}</Badge>
              ))}
            </div>
            <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-3">
              Images are automatically deduplicated via SHA256 hashing before ML processing.
            </p>
          </div>
          <div className="bg-tactical-50 dark:bg-tactical-800/50 rounded-lg p-4">
            <h3 className="font-semibold text-sm text-tactical-900 dark:text-tactical-100 mb-2">Export Formats</h3>
            <div className="space-y-1.5 text-xs text-tactical-600 dark:text-tactical-400">
              <div className="flex items-center gap-2">
                <Badge variant="info" size="xs">ZIP</Badge>
                <span>Raw images in folders</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="purple" size="xs">COCO</Badge>
                <span>COCO JSON annotations</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="success" size="xs">YOLO</Badge>
                <span>YOLO label format</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="default" size="xs">CSV</Badge>
                <span>Metadata and paths</span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Add Images Modal */}
      <Modal
        isOpen={showAddImagesModal}
        onClose={() => {
          setShowAddImagesModal(false)
          setSelectedFiles([])
        }}
        title="Add Images to Dataset"
        size="lg"
      >
        <div className="space-y-4">
          <div
            className={cn(
              'border-2 border-dashed rounded-xl p-8 text-center transition-colors',
              selectedFiles.length > 0
                ? 'border-tiger-orange/50 bg-tiger-orange/5'
                : 'border-tactical-300 dark:border-tactical-600 hover:border-tiger-orange/30'
            )}
          >
            <ArrowUpTrayIcon className="h-10 w-10 mx-auto mb-3 text-tactical-400 dark:text-tactical-500" />
            <label className="cursor-pointer">
              <span className="text-sm font-medium text-tiger-orange hover:text-tiger-orange-dark">
                Choose files
              </span>
              <span className="text-sm text-tactical-500 dark:text-tactical-400"> or drag and drop</span>
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={(e) => setSelectedFiles(Array.from(e.target.files || []))}
                className="hidden"
              />
            </label>
            <p className="text-xs text-tactical-400 dark:text-tactical-500 mt-1">
              JPEG, PNG, WEBP, TIFF up to 50MB each
            </p>
          </div>

          {selectedFiles.length > 0 && (
            <div className="space-y-1.5 max-h-48 overflow-y-auto">
              {selectedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-2 rounded-lg bg-tactical-50 dark:bg-tactical-800"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <PhotoIcon className="h-4 w-4 text-tactical-400 shrink-0" />
                    <span className="text-sm text-tactical-700 dark:text-tactical-300 truncate">{file.name}</span>
                    <span className="text-xs text-tactical-400 dark:text-tactical-500 shrink-0">
                      {(file.size / 1024 / 1024).toFixed(1)} MB
                    </span>
                  </div>
                  <button
                    onClick={() => setSelectedFiles((prev) => prev.filter((_, i) => i !== index))}
                    className="text-red-500 hover:text-red-700 dark:hover:text-red-400 shrink-0 ml-2"
                  >
                    <XMarkIcon className="h-4 w-4" />
                  </button>
                </div>
              ))}
              <p className="text-xs text-tactical-500 dark:text-tactical-400 pt-1">
                {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''} selected (
                {(selectedFiles.reduce((s, f) => s + f.size, 0) / 1024 / 1024).toFixed(1)} MB total)
              </p>
            </div>
          )}

          <div className="flex gap-2 justify-end pt-2">
            <Button
              variant="secondary"
              onClick={() => {
                setShowAddImagesModal(false)
                setSelectedFiles([])
              }}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleAddImages}
              disabled={selectedFiles.length === 0 || isLoading}
              isLoading={isLoading}
              className="flex items-center gap-2"
            >
              <ArrowUpTrayIcon className="h-4 w-4" />
              Add {selectedFiles.length} Image{selectedFiles.length !== 1 ? 's' : ''}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Export Modal */}
      <Modal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        title="Export Dataset"
        size="md"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-tactical-700 dark:text-tactical-300 mb-2">
              Export Scope
            </label>
            <div className="flex gap-3">
              <button
                onClick={() => setExportAllTigers(false)}
                disabled={!selectedTiger}
                className={cn(
                  'flex-1 p-3 rounded-lg border-2 text-left transition-all text-sm',
                  !exportAllTigers && selectedTiger
                    ? 'border-tiger-orange bg-tiger-orange/5'
                    : 'border-tactical-200 dark:border-tactical-700',
                  !selectedTiger && 'opacity-40 cursor-not-allowed'
                )}
              >
                <p className="font-medium text-tactical-900 dark:text-tactical-100">Selected Tiger</p>
                <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-0.5">
                  {selectedTiger ? `Export images for current tiger` : 'Select a tiger first'}
                </p>
              </button>
              <button
                onClick={() => setExportAllTigers(true)}
                className={cn(
                  'flex-1 p-3 rounded-lg border-2 text-left transition-all text-sm',
                  exportAllTigers
                    ? 'border-tiger-orange bg-tiger-orange/5'
                    : 'border-tactical-200 dark:border-tactical-700'
                )}
              >
                <p className="font-medium text-tactical-900 dark:text-tactical-100">All Tigers</p>
                <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-0.5">
                  Full dataset export ({stats.totalImages} images)
                </p>
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-tactical-700 dark:text-tactical-300 mb-2">
              Export Format
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(
                [
                  { id: 'zip' as const, name: 'ZIP Archive', desc: 'Raw images in identity folders' },
                  { id: 'coco' as const, name: 'COCO Format', desc: 'JSON annotations + images' },
                  { id: 'yolo' as const, name: 'YOLO Format', desc: 'YOLO labels + images' },
                  { id: 'csv' as const, name: 'CSV Metadata', desc: 'Paths, labels, and metadata' },
                ] as const
              ).map((fmt) => (
                <button
                  key={fmt.id}
                  onClick={() => setExportFormat(fmt.id)}
                  className={cn(
                    'p-3 rounded-lg border-2 text-left transition-all text-sm',
                    exportFormat === fmt.id
                      ? 'border-tiger-orange bg-tiger-orange/5'
                      : 'border-tactical-200 dark:border-tactical-700 hover:border-tactical-300 dark:hover:border-tactical-600'
                  )}
                >
                  <p className="font-medium text-tactical-900 dark:text-tactical-100">{fmt.name}</p>
                  <p className="text-xs text-tactical-500 dark:text-tactical-400 mt-0.5">{fmt.desc}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-2 justify-end pt-2">
            <Button variant="secondary" onClick={() => setShowExportModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleExportDataset}
              disabled={isExporting || (!exportAllTigers && !selectedTiger)}
              isLoading={isExporting}
              className="flex items-center gap-2"
            >
              <ArrowDownTrayIcon className="h-4 w-4" />
              Export Dataset
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default DatasetManagement

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import Alert from '../components/common/Alert'
import { ArrowLeftIcon } from '@heroicons/react/24/outline'
import Investigation2Upload from '../components/investigations/Investigation2Upload'
import Investigation2Progress from '../components/investigations/Investigation2Progress'
import Investigation2Results from '../components/investigations/Investigation2Results'
import { useLaunchInvestigation2Mutation, useGetInvestigation2Query } from '../app/api'

interface ProgressStep {
  phase: string
  status: 'pending' | 'running' | 'completed' | 'error'
  timestamp?: string
  data?: any
}

const Investigation2 = () => {
  const navigate = useNavigate()
  const [investigationId, setInvestigationId] = useState<string | null>(null)
  const [uploadedImage, setUploadedImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [context, setContext] = useState({
    location: '',
    date: '',
    notes: ''
  })
  const [progressSteps, setProgressSteps] = useState<ProgressStep[]>([])
  const [error, setError] = useState<string | null>(null)
  const [websocket, setWebsocket] = useState<WebSocket | null>(null)

  const [launchInvestigation, { isLoading: isLaunching }] = useLaunchInvestigation2Mutation()
  const { data: investigationData, isLoading: isLoadingData } = useGetInvestigation2Query(
    investigationId || '',
    { skip: !investigationId, pollingInterval: 5000 }
  )

  // Initialize progress steps
  const initializeProgress = () => {
    setProgressSteps([
      { phase: 'upload_and_parse', status: 'pending' },
      { phase: 'reverse_image_search', status: 'pending' },
      { phase: 'tiger_detection', status: 'pending' },
      { phase: 'stripe_analysis', status: 'pending' },
      { phase: 'omnivinci_comparison', status: 'pending' },
      { phase: 'report_generation', status: 'pending' },
      { phase: 'complete', status: 'pending' }
    ])
  }

  // WebSocket connection
  useEffect(() => {
    if (!investigationId) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/v1/investigations2/ws/${investigationId}`
    
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        console.log('WebSocket message:', message)

        if (message.event === 'phase_started') {
          updateProgressStep(message.data.phase, 'running', message.data)
        } else if (message.event === 'phase_completed') {
          updateProgressStep(message.data.phase, 'completed', message.data)
        } else if (message.event === 'investigation_completed') {
          updateProgressStep('complete', 'completed', message.data)
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
    }

    setWebsocket(ws)

    // Ping interval to keep connection alive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping')
      }
    }, 30000)

    return () => {
      clearInterval(pingInterval)
      ws.close()
    }
  }, [investigationId])

  const updateProgressStep = (phase: string, status: ProgressStep['status'], data?: any) => {
    setProgressSteps(prev => 
      prev.map(step => 
        step.phase === phase 
          ? { ...step, status, timestamp: new Date().toISOString(), data }
          : step
      )
    )
  }

  const handleImageUpload = (file: File) => {
    setUploadedImage(file)
    
    // Create preview
    const reader = new FileReader()
    reader.onloadend = () => {
      setImagePreview(reader.result as string)
    }
    reader.readAsDataURL(file)
  }

  const handleContextChange = (field: string, value: string) => {
    setContext(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleLaunch = async () => {
    if (!uploadedImage) {
      setError('Please upload a tiger image')
      return
    }

    setError(null)
    initializeProgress()

    try {
      const formData = new FormData()
      formData.append('image', uploadedImage)
      if (context.location) formData.append('location', context.location)
      if (context.date) formData.append('date', context.date)
      if (context.notes) formData.append('notes', context.notes)

      const result = await launchInvestigation(formData).unwrap()
      
      if (result.success) {
        setInvestigationId(result.investigation_id)
      } else {
        setError('Failed to launch investigation')
      }
    } catch (err: any) {
      setError(err.data?.detail || 'Failed to launch investigation')
      console.error('Launch error:', err)
    }
  }

  const handleReset = () => {
    setInvestigationId(null)
    setUploadedImage(null)
    setImagePreview(null)
    setContext({ location: '', date: '', notes: '' })
    setProgressSteps([])
    setError(null)
    if (websocket) {
      websocket.close()
    }
  }

  const isInProgress = investigationId && !investigationData?.status?.includes('complete')
  const isCompleted = investigationData?.status === 'completed'

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => navigate('/investigations')}
          >
            <ArrowLeftIcon className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Investigation 2.0
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Advanced tiger identification workflow
            </p>
          </div>
        </div>
        {investigationId && (
          <Button variant="secondary" size="sm" onClick={handleReset}>
            New Investigation
          </Button>
        )}
      </div>

      {/* Error Alert */}
      {error && (
        <Alert type="error" message={error} className="mb-6" />
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Upload & Context */}
        <div>
          <Investigation2Upload
            image={uploadedImage}
            imagePreview={imagePreview}
            context={context}
            onImageUpload={handleImageUpload}
            onContextChange={handleContextChange}
            disabled={!!investigationId || isLaunching}
          />

          {!investigationId && (
            <div className="mt-6">
              <Button
                variant="primary"
                size="lg"
                onClick={handleLaunch}
                disabled={!uploadedImage || isLaunching}
                className="w-full"
              >
                {isLaunching ? 'Launching...' : 'Launch Investigation'}
              </Button>
            </div>
          )}
        </div>

        {/* Right Column - Progress & Results */}
        <div>
          {(investigationId || progressSteps.length > 0) && (
            <Investigation2Progress
              steps={progressSteps}
              investigationId={investigationId}
            />
          )}

          {isCompleted && investigationData && (
            <div className="mt-6">
              <Investigation2Results
                investigation={investigationData}
              />
            </div>
          )}
        </div>
      </div>

      {/* Full Width Results */}
      {isCompleted && investigationData && (
        <div className="mt-8">
          <Card>
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">Investigation Report</h2>
              <Investigation2Results
                investigation={investigationData}
                fullWidth
              />
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}

export default Investigation2


import Card from '../common/Card'
import LoadingSpinner from '../common/LoadingSpinner'
import { CheckCircleIcon, XCircleIcon, ClockIcon } from '@heroicons/react/24/outline'

interface ProgressStep {
  phase: string
  status: 'pending' | 'running' | 'completed' | 'error'
  timestamp?: string
  data?: any
}

interface Investigation2ProgressProps {
  steps: ProgressStep[]
  investigationId: string | null
}

const phaseLabels: Record<string, string> = {
  upload_and_parse: 'Upload & Parse',
  reverse_image_search: 'Reverse Image Search',
  tiger_detection: 'Tiger Detection',
  stripe_analysis: 'Stripe Analysis',
  omnivinci_comparison: 'Omnivinci Comparison',
  report_generation: 'Report Generation',
  complete: 'Complete'
}

const phaseDescriptions: Record<string, string> = {
  upload_and_parse: 'Processing uploaded image and context',
  reverse_image_search: 'Searching web for related tiger images',
  tiger_detection: 'Detecting tigers using MegaDetector',
  stripe_analysis: 'Running 4 stripe detection models in parallel',
  omnivinci_comparison: 'Comparing tigers using multi-modal AI',
  report_generation: 'Generating comprehensive report with GPT-5-mini',
  complete: 'Investigation complete'
}

const Investigation2Progress = ({ steps, investigationId }: Investigation2ProgressProps) => {
  const getStatusIcon = (status: ProgressStep['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-6 h-6 text-green-500" />
      case 'running':
        return <LoadingSpinner size="sm" />
      case 'error':
        return <XCircleIcon className="w-6 h-6 text-red-500" />
      default:
        return <ClockIcon className="w-6 h-6 text-gray-400" />
    }
  }

  const getStatusColor = (status: ProgressStep['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 border-green-300'
      case 'running':
        return 'bg-blue-100 border-blue-300 animate-pulse'
      case 'error':
        return 'bg-red-100 border-red-300'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  const currentStep = steps.findIndex(s => s.status === 'running')
  const completedSteps = steps.filter(s => s.status === 'completed').length
  const totalSteps = steps.length

  return (
    <Card>
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Investigation Progress</h2>
          {investigationId && (
            <span className="text-sm text-gray-500">
              ID: {investigationId.substring(0, 8)}...
            </span>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">
              {completedSteps} of {totalSteps} steps completed
            </span>
            <span className="text-sm text-gray-500">
              {Math.round((completedSteps / totalSteps) * 100)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${(completedSteps / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        {/* Steps List */}
        <div className="space-y-3">
          {steps.map((step, index) => (
            <div
              key={step.phase}
              className={`border rounded-lg p-4 transition-all ${getStatusColor(step.status)}`}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  {getStatusIcon(step.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-900">
                      {index + 1}. {phaseLabels[step.phase] || step.phase}
                    </h3>
                    {step.timestamp && (
                      <span className="text-xs text-gray-500">
                        {new Date(step.timestamp).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    {phaseDescriptions[step.phase] || 'Processing...'}
                  </p>

                  {/* Step Data */}
                  {step.data && step.status === 'completed' && (
                    <div className="mt-2 text-xs text-gray-700 bg-white/50 rounded px-2 py-1">
                      {step.phase === 'tiger_detection' && step.data.tigers_detected !== undefined && (
                        <span>✓ Detected {step.data.tigers_detected} tiger(s)</span>
                      )}
                      {step.phase === 'stripe_analysis' && step.data.models_run !== undefined && (
                        <span>✓ Ran {step.data.models_run} models successfully</span>
                      )}
                      {step.phase === 'reverse_image_search' && step.data.results_count !== undefined && (
                        <span>✓ Found {step.data.results_count} related images</span>
                      )}
                      {step.phase === 'omnivinci_comparison' && step.data.matches_analyzed !== undefined && (
                        <span>✓ Analyzed {step.data.matches_analyzed} potential matches</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Status Message */}
        {currentStep >= 0 && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              Currently running: <strong>{phaseLabels[steps[currentStep].phase]}</strong>
            </p>
          </div>
        )}
      </div>
    </Card>
  )
}

export default Investigation2Progress


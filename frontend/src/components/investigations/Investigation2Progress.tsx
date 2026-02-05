import { useCallback, useMemo } from 'react'
import Card from '../common/Card'
import LoadingSpinner from '../common/LoadingSpinner'
import { AnimatedNumber } from '../common/AnimatedNumber'
import { CheckCircleIcon, XCircleIcon, ClockIcon, WifiIcon } from '@heroicons/react/24/outline'
import { useInvestigation2 } from '../../context/Investigation2Context'
import { ModelProgressGrid } from './progress/ModelProgressGrid'
import type { StepStatus } from '../../types/investigation2'
import type { ModelProgress } from './progress/ModelProgressGrid'

const phaseLabels: Record<string, string> = {
  upload_and_parse: 'Upload & Parse',
  reverse_image_search: 'Reverse Image Search',
  tiger_detection: 'Tiger Detection',
  stripe_analysis: 'Stripe Analysis',
  report_generation: 'Report Generation',
  complete: 'Complete'
}

const phaseDescriptions: Record<string, string> = {
  upload_and_parse: 'Processing uploaded image and context',
  reverse_image_search: 'Searching web for related tiger images',
  tiger_detection: 'Detecting tigers using MegaDetector',
  stripe_analysis: 'Running 6-model ReID ensemble in parallel',
  report_generation: 'Generating comprehensive report with Claude',
  complete: 'Investigation complete'
}

/**
 * Investigation 2.0 progress component.
 * Uses context for state management instead of props.
 * Integrates ModelProgressGrid for real-time stripe analysis visualization.
 */
const Investigation2Progress = () => {
  const {
    progressSteps,
    investigationId,
    modelProgress: contextModelProgress,
    isStripeAnalysisRunning,
    wsConnected,
    completedModelsCount,
    totalModelsCount,
  } = useInvestigation2()

  /**
   * Transform context model progress to ModelProgressGrid format.
   * The context stores modelProgress as ModelProgressInfo[] which is compatible
   * with ModelProgress from ModelProgressGrid with minor mapping.
   */
  const modelProgressArray: ModelProgress[] = useMemo(() => {
    return contextModelProgress.map((mp) => ({
      model: mp.model,
      progress: mp.progress,
      status: mp.status,
      embeddings: undefined, // Not tracked in context currently
      processingTime: mp.completedAt && mp.startedAt
        ? new Date(mp.completedAt).getTime() - new Date(mp.startedAt).getTime()
        : undefined,
      errorMessage: undefined, // Not tracked in context currently
    }))
  }, [contextModelProgress])

  /**
   * Handle retry request for a failed model.
   * This would trigger a re-run of the specific model.
   */
  const handleModelRetry = useCallback((model: string) => {
    console.log(`[Investigation2Progress] Retry requested for model: ${model}`)
    // TODO: Implement retry via WebSocket or API call
    // For now, log the retry request
    // In production, this would send a message to restart the model:
    // ws.send(JSON.stringify({ type: 'retry_model', model, investigation_id: investigationId }))
  }, [])

  const getStatusIcon = (status: StepStatus) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-6 h-6 text-green-500" data-testid="status-icon-completed" />
      case 'running':
        return <LoadingSpinner size="sm" data-testid="status-icon-running" />
      case 'error':
        return <XCircleIcon className="w-6 h-6 text-red-500" data-testid="status-icon-error" />
      default:
        return <ClockIcon className="w-6 h-6 text-gray-400" data-testid="status-icon-pending" />
    }
  }

  const getStatusColor = (status: StepStatus) => {
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

  const currentStep = progressSteps.findIndex(s => s.status === 'running')
  const completedSteps = progressSteps.filter(s => s.status === 'completed').length
  const totalSteps = progressSteps.length
  const currentPhase = currentStep >= 0 ? progressSteps[currentStep].phase : null

  return (
    <Card data-testid="investigation-progress-card">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold" data-testid="progress-title">
            Investigation Progress
          </h2>
          <div className="flex items-center gap-3">
            {/* WebSocket connection indicator */}
            <div
              className="flex items-center gap-1.5"
              data-testid="ws-connection-indicator"
              title={wsConnected ? 'Connected to real-time updates' : 'Disconnected from real-time updates'}
            >
              <WifiIcon
                className={`w-4 h-4 ${wsConnected ? 'text-green-500' : 'text-gray-400'}`}
                data-testid="ws-connection-icon"
              />
              <span className={`text-xs ${wsConnected ? 'text-green-600' : 'text-gray-500'}`}>
                {wsConnected ? 'Live' : 'Offline'}
              </span>
            </div>
            {investigationId && (
              <span className="text-sm text-gray-500" data-testid="investigation-id">
                ID: {investigationId.substring(0, 8)}...
              </span>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-6" data-testid="overall-progress-section">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700" data-testid="progress-steps-label">
              {completedSteps} of {totalSteps} steps completed
            </span>
            <span className="text-sm text-gray-500" data-testid="progress-percentage">
              <AnimatedNumber
                value={totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0}
                duration={800}
                suffix="%"
                easing="easeOut"
              />
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2" data-testid="progress-bar-track">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0}%` }}
              data-testid="progress-bar-fill"
            />
          </div>
        </div>

        {/* Model Progress Grid - Show during stripe_analysis phase */}
        {(isStripeAnalysisRunning || currentPhase === 'stripe_analysis') && modelProgressArray.length > 0 && (
          <div className="mb-6" data-testid="model-progress-section">
            <ModelProgressGrid
              models={modelProgressArray}
              title="Stripe Analysis - 6-Model Ensemble"
              onRetry={handleModelRetry}
              data-testid="stripe-analysis-model-grid"
            />
            {/* Additional stripe analysis info */}
            <div
              className="mt-3 text-sm text-gray-600 flex items-center gap-2"
              data-testid="stripe-analysis-summary"
            >
              <span>
                {completedModelsCount} of {totalModelsCount} models completed
              </span>
              {wsConnected && (
                <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded">
                  Real-time updates
                </span>
              )}
            </div>
          </div>
        )}

        {/* Steps List */}
        <div className="space-y-3" data-testid="progress-steps-list">
          {progressSteps.map((step, index) => (
            <div
              key={step.phase}
              className={`border rounded-lg p-4 transition-all ${getStatusColor(step.status)}`}
              data-testid={`progress-step-${step.phase}`}
              data-status={step.status}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5" data-testid={`step-icon-${step.phase}`}>
                  {getStatusIcon(step.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h3
                      className="text-sm font-semibold text-gray-900"
                      data-testid={`step-label-${step.phase}`}
                    >
                      {index + 1}. {phaseLabels[step.phase] || step.phase}
                    </h3>
                    {step.timestamp && (
                      <span
                        className="text-xs text-gray-500"
                        data-testid={`step-timestamp-${step.phase}`}
                      >
                        {new Date(step.timestamp).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                  <p
                    className="text-sm text-gray-600 mt-1"
                    data-testid={`step-description-${step.phase}`}
                  >
                    {phaseDescriptions[step.phase] || 'Processing...'}
                  </p>

                  {/* Step Data */}
                  {step.data && step.status === 'completed' && (
                    <div
                      className="mt-2 text-xs text-gray-700 bg-white/50 rounded px-2 py-1"
                      data-testid={`step-data-${step.phase}`}
                    >
                      {step.phase === 'tiger_detection' && 'tigers_detected' in step.data && step.data.tigers_detected !== undefined && (
                        <span>Detected {step.data.tigers_detected} tiger(s)</span>
                      )}
                      {step.phase === 'stripe_analysis' && 'models_run' in step.data && step.data.models_run !== undefined && (
                        <span>Ran {step.data.models_run} models successfully</span>
                      )}
                      {step.phase === 'reverse_image_search' && 'results_count' in step.data && step.data.results_count !== undefined && (
                        <span>Found {step.data.results_count} related images</span>
                      )}
                    </div>
                  )}

                  {/* Inline model progress for stripe_analysis when collapsed */}
                  {step.phase === 'stripe_analysis' &&
                   step.status === 'running' &&
                   totalModelsCount > 0 &&
                   !isStripeAnalysisRunning && (
                    <div
                      className="mt-2 text-xs text-gray-700"
                      data-testid="step-model-progress-inline"
                    >
                      <span>
                        Models: {completedModelsCount}/{totalModelsCount} completed
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Status Message */}
        {currentStep >= 0 && (
          <div
            className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg"
            data-testid="current-phase-indicator"
          >
            <p className="text-sm text-blue-800">
              Currently running: <strong data-testid="current-phase-name">{phaseLabels[progressSteps[currentStep].phase]}</strong>
            </p>
          </div>
        )}
      </div>
    </Card>
  )
}

export default Investigation2Progress

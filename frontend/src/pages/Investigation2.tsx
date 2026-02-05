import { useNavigate } from 'react-router-dom'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import Badge from '../components/common/Badge'
import Alert from '../components/common/Alert'
import { ArrowLeftIcon } from '@heroicons/react/24/outline'
import Investigation2Upload from '../components/investigations/Investigation2Upload'
import Investigation2Progress from '../components/investigations/Investigation2Progress'
import Investigation2ResultsEnhanced from '../components/investigations/Investigation2ResultsEnhanced'
import { InvestigationLayout } from '../components/investigations/layout'
import { Investigation2Provider, useInvestigation2 } from '../context/Investigation2Context'

/**
 * Inner component that uses the Investigation2 context.
 * This allows the component to access all state through context instead of props.
 */
const Investigation2Content = () => {
  const navigate = useNavigate()

  const {
    investigationId,
    investigation,
    progressSteps,
    isLaunching,
    uploadedImage,
    error,
    isCompleted,
    wsConnected,
    launchInvestigation,
    resetInvestigation,
    regenerateReport,
  } = useInvestigation2()

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
        <div className="flex items-center gap-3">
          {/* WebSocket Status Indicator */}
          {investigationId && (
            <div className="flex items-center gap-2 text-sm">
              <span
                className={`w-2 h-2 rounded-full ${
                  wsConnected ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className="text-gray-500">
                {wsConnected ? 'Live' : 'Connecting...'}
              </span>
            </div>
          )}
          {investigationId && (
            <Button variant="secondary" size="sm" onClick={resetInvestigation}>
              New Investigation
            </Button>
          )}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert type="error" message={error} className="mb-6" />
      )}

      {/* Main Content - Responsive Layout */}
      <InvestigationLayout
        hasImage={!!uploadedImage}
        isComplete={isCompleted}
        uploadPanel={
          <div data-testid="upload-panel">
            <Investigation2Upload />

            {!investigationId && (
              <div className="mt-6">
                <Button
                  variant="primary"
                  size="lg"
                  onClick={launchInvestigation}
                  disabled={!uploadedImage || isLaunching}
                  className="w-full"
                  data-testid="launch-investigation-btn"
                >
                  {isLaunching ? 'Launching...' : 'Launch Investigation'}
                </Button>
              </div>
            )}
          </div>
        }
        progressPanel={
          (investigationId || progressSteps.length > 0) ? (
            <Investigation2Progress />
          ) : (
            <div
              className="flex items-center justify-center h-64 rounded-xl border-2 border-dashed border-tactical-200 dark:border-tactical-700"
              data-testid="progress-placeholder"
            >
              <p className="text-tactical-500 dark:text-tactical-400 text-center px-4">
                Upload an image and launch the investigation to see progress
              </p>
            </div>
          )
        }
        resultsPanel={
          isCompleted && investigation ? (
            <Investigation2ResultsEnhanced
              investigation={investigation}
              onRegenerateReport={regenerateReport}
            />
          ) : undefined
        }
      />

      {/* Full Width Results */}
      {isCompleted && investigation && (
        <div className="mt-8">
          <Card>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Investigation Report</h2>
                <Badge color="green">Completed</Badge>
              </div>
              <Investigation2ResultsEnhanced
                investigation={investigation}
                fullWidth
                onRegenerateReport={regenerateReport}
              />
            </div>
          </Card>
        </div>
      )}

      {/* Debug Info (development only) */}
      {import.meta.env.DEV && investigation && (
        <div className="mt-4 text-xs text-gray-500">
          <details>
            <summary className="cursor-pointer hover:text-gray-700">Debug Info</summary>
            <pre className="mt-2 p-2 bg-gray-100 rounded overflow-auto max-h-40">
              {JSON.stringify({
                status: investigation.status,
                steps: investigation.steps?.length || 0,
                hasSteps: !!investigation.steps,
                hasSummary: !!investigation.summary,
                isCompleted: isCompleted,
                wsConnected: wsConnected,
              }, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  )
}

/**
 * Investigation 2.0 page component.
 * Wraps the content in the Investigation2Provider for state management.
 */
const Investigation2 = () => {
  return (
    <Investigation2Provider>
      <Investigation2Content />
    </Investigation2Provider>
  )
}

export default Investigation2

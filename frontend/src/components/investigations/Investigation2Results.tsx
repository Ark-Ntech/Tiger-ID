import Card from '../common/Card'
import Badge from '../common/Badge'
import { CheckCircleIcon, ExclamationTriangleIcon, InformationCircleIcon } from '@heroicons/react/24/outline'

interface Investigation2ResultsProps {
  investigation: any
  fullWidth?: boolean
}

const Investigation2Results = ({ investigation, fullWidth = false }: Investigation2ResultsProps) => {
  const summary = investigation.summary || {}
  const report = summary.report || summary
  const topMatches = report.top_matches || []
  const modelsUsed = report.models_used || []
  const detectionCount = report.detection_count || 0
  const totalMatches = report.total_matches || 0
  const confidence = report.confidence || 'medium'

  const getConfidenceBadge = (conf: string) => {
    switch (conf.toLowerCase()) {
      case 'high':
        return <Badge color="green">High Confidence</Badge>
      case 'medium':
        return <Badge color="yellow">Medium Confidence</Badge>
      case 'low':
        return <Badge color="red">Low Confidence</Badge>
      default:
        return <Badge color="gray">{conf}</Badge>
    }
  }

  const getConfidenceIcon = (conf: string) => {
    switch (conf.toLowerCase()) {
      case 'high':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />
      case 'medium':
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />
      case 'low':
        return <InformationCircleIcon className="w-5 h-5 text-red-500" />
      default:
        return <InformationCircleIcon className="w-5 h-5 text-gray-500" />
    }
  }

  return (
    <div className={fullWidth ? 'space-y-6' : ''}>
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <div className="p-4">
            <div className="text-sm text-gray-600 mb-1">Tigers Detected</div>
            <div className="text-2xl font-bold">{detectionCount}</div>
          </div>
        </Card>
        <Card>
          <div className="p-4">
            <div className="text-sm text-gray-600 mb-1">Models Used</div>
            <div className="text-2xl font-bold">{modelsUsed.length}</div>
          </div>
        </Card>
        <Card>
          <div className="p-4">
            <div className="text-sm text-gray-600 mb-1">Total Matches</div>
            <div className="text-2xl font-bold">{totalMatches}</div>
          </div>
        </Card>
        <Card>
          <div className="p-4">
            <div className="text-sm text-gray-600 mb-1">Confidence</div>
            <div className="mt-1">{getConfidenceBadge(confidence)}</div>
          </div>
        </Card>
      </div>

      {/* Top Matches */}
      {topMatches.length > 0 && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              {getConfidenceIcon(confidence)}
              Top Tiger Matches
            </h3>
            <div className="space-y-3">
              {topMatches.slice(0, 10).map((match: any, index: number) => (
                <div
                  key={`${match.tiger_id}-${index}`}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-semibold text-gray-900">
                          {index + 1}.
                        </span>
                        <span className="font-medium text-gray-900">
                          {match.tiger_name || `Tiger ${match.tiger_id}`}
                        </span>
                        <Badge color="blue" size="sm">
                          {match.model}
                        </Badge>
                      </div>
                      <div className="mt-1 text-sm text-gray-600">
                        ID: {match.tiger_id}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-blue-600">
                        {(match.similarity * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500">similarity</div>
                    </div>
                  </div>

                  {/* Similarity Bar */}
                  <div className="mt-3">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          match.similarity > 0.9
                            ? 'bg-green-500'
                            : match.similarity > 0.8
                            ? 'bg-blue-500'
                            : 'bg-yellow-500'
                        }`}
                        style={{ width: `${match.similarity * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Generated Report */}
      {report.summary && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">Investigation Report</h3>
            <div className="prose max-w-none">
              <div className="whitespace-pre-wrap text-gray-700">
                {report.summary}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Models Used */}
      {modelsUsed.length > 0 && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">Models Used</h3>
            <div className="flex flex-wrap gap-2">
              {modelsUsed.map((model: string) => (
                <Badge key={model} color="purple">
                  {model}
                </Badge>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* No Matches */}
      {topMatches.length === 0 && (
        <Card>
          <div className="p-6 text-center">
            <InformationCircleIcon className="w-12 h-12 mx-auto text-gray-400 mb-3" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Matches Found</h3>
            <p className="text-gray-600">
              No matching tigers were found in the database. This could be a new tiger or the image quality may need improvement.
            </p>
          </div>
        </Card>
      )}
    </div>
  )
}

export default Investigation2Results


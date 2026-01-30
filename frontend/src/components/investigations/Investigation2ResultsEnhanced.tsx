import { useState } from 'react'
import Card from '../common/Card'
import Badge from '../common/Badge'
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  GlobeAltIcon,
  BeakerIcon,
  EyeIcon,
  DocumentTextIcon,
  MapIcon,
  LinkIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline'
import { Investigation2Citations } from './Investigation2Citations'
import { Investigation2Map } from './Investigation2Map'
import { Investigation2MatchCard } from './Investigation2MatchCard'
import { Investigation2Methodology } from './Investigation2Methodology'
import { MarkdownContent } from '../common/MarkdownContent'

interface Investigation2ResultsEnhancedProps {
  investigation: any
  fullWidth?: boolean
}

const Investigation2ResultsEnhanced = ({ investigation, fullWidth: _fullWidth = false }: Investigation2ResultsEnhancedProps) => {
  const [activeTab, setActiveTab] = useState('overview')

  // Suppress unused variable warning - fullWidth reserved for future layout enhancements
  void _fullWidth

  const summary = investigation.summary || {}
  const report = summary.report || summary
  const topMatches = report.top_matches || []
  const modelsUsed = report.models_used || []
  const detectionCount = report.detection_count || 0
  const totalMatches = report.total_matches || 0
  const confidence = report.confidence || 'medium'

  // Extract phase-specific data
  const reverseSearchResults = summary.reverse_search_results || {}
  const omnivinci = summary.omnivinci_comparison || {}
  const detectedTigers = summary.detected_tigers || []

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

  const tabs = [
    { id: 'overview', label: 'Overview', icon: InformationCircleIcon },
    { id: 'detection', label: 'Detection', icon: EyeIcon, count: detectionCount },
    { id: 'matching', label: 'Matches', icon: BeakerIcon, count: totalMatches },
    { id: 'location', label: 'Location', icon: MapIcon },
    { id: 'citations', label: 'Citations', icon: LinkIcon },
    { id: 'methodology', label: 'Methodology', icon: LightBulbIcon },
    { id: 'external', label: 'External Intel', icon: GlobeAltIcon, count: reverseSearchResults.total_results },
    { id: 'report', label: 'Full Report', icon: DocumentTextIcon }
  ]

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-4">
          {tabs.map(tab => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-5 h-5" />
                {tab.label}
                {tab.count !== undefined && tab.count !== null && (
                  <Badge color={tab.count > 0 ? 'blue' : 'gray'} size="sm">
                    {tab.count}
                  </Badge>
                )}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <div className="p-4">
                  <div className="text-sm text-gray-600 mb-1">Tigers Detected</div>
                  <div className="text-3xl font-bold text-blue-600">{detectionCount}</div>
                </div>
              </Card>
              <Card>
                <div className="p-4">
                  <div className="text-sm text-gray-600 mb-1">Models Used</div>
                  <div className="text-3xl font-bold text-purple-600">{modelsUsed.length}</div>
                </div>
              </Card>
              <Card>
                <div className="p-4">
                  <div className="text-sm text-gray-600 mb-1">Total Matches</div>
                  <div className="text-3xl font-bold text-green-600">{totalMatches}</div>
                </div>
              </Card>
              <Card>
                <div className="p-4">
                  <div className="text-sm text-gray-600 mb-1">Confidence</div>
                  <div className="mt-2">{getConfidenceBadge(confidence)}</div>
                </div>
              </Card>
            </div>

            {/* Top Matches Preview */}
            {topMatches.length > 0 && (
              <Card>
                <div className="p-6">
                  <h3 className="text-lg font-semibold mb-4">Top 5 Matches</h3>
                  <div className="space-y-3">
                    {topMatches.slice(0, 5).map((match: any, index: number) => (
                      <div
                        key={`${match.tiger_id}-${index}`}
                        className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-lg font-semibold text-gray-900">#{index + 1}</span>
                              <span className="font-medium text-gray-900">
                                {match.tiger_name || `Tiger ${match.tiger_id}`}
                              </span>
                              <Badge color="blue" size="sm">{match.model}</Badge>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold text-blue-600">
                              {(match.similarity * 100).toFixed(1)}%
                            </div>
                            <div className="text-xs text-gray-500">similarity</div>
                          </div>
                        </div>
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
          </div>
        )}

        {/* Detection Tab */}
        {activeTab === 'detection' && (
          <div className="space-y-6">
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-semibold mb-4">Tiger Detection Results</h3>
                {detectedTigers.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {detectedTigers.map((tiger: any, index: number) => (
                      <div key={index} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <Badge color="blue">Tiger #{index + 1}</Badge>
                          <Badge color={tiger.confidence > 0.9 ? 'green' : 'yellow'}>
                            {(tiger.confidence * 100).toFixed(1)}% confidence
                          </Badge>
                        </div>
                        {tiger.bbox && (
                          <div className="text-sm text-gray-600 mt-2">
                            <div>Bounding Box:</div>
                            <div className="font-mono text-xs bg-gray-100 p-2 rounded mt-1">
                              [{tiger.bbox.map((v: number) => v.toFixed(0)).join(', ')}]
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    No tigers detected
                  </div>
                )}
              </div>
            </Card>
          </div>
        )}

        {/* Matching Tab - Now using Investigation2MatchCard */}
        {activeTab === 'matching' && (
          <div className="space-y-6">
            {topMatches.length > 0 ? (
              <div>
                <h3 className="text-lg font-semibold mb-4">Top Matches</h3>
                {topMatches.map((match: any, index: number) => (
                  <Investigation2MatchCard
                    key={`${match.tiger_id}-${index}`}
                    match={{
                      tiger_id: match.tiger_id,
                      tiger_name: match.tiger_name || `Tiger ${match.tiger_id}`,
                      similarity: match.similarity * 100,
                      model: match.model,
                      database_image: match.image_path || '/placeholder-tiger.png',
                      facility: {
                        name: match.facility_name || 'Unknown Facility',
                        location: match.facility_location || 'Unknown Location',
                        coordinates: match.facility_coordinates
                      }
                    }}
                  />
                ))}
              </div>
            ) : (
              <Card>
                <div className="p-6 text-center text-gray-500">
                  No matches available
                </div>
              </Card>
            )}
          </div>
        )}

        {/* Location Tab */}
        {activeTab === 'location' && (
          <div className="space-y-6">
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-semibold mb-4">Tiger Location Analysis</h3>
                <Investigation2Map locations={[]} />
              </div>
            </Card>
          </div>
        )}

        {/* Citations Tab */}
        {activeTab === 'citations' && (
          <div className="space-y-6">
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-semibold mb-4">Web Search Citations</h3>
                <Investigation2Citations citations={reverseSearchResults.citations || []} />
              </div>
            </Card>
          </div>
        )}

        {/* Methodology Tab */}
        {activeTab === 'methodology' && (
          <div className="space-y-6">
            <Card>
              <div className="p-6">
                <Investigation2Methodology steps={report.methodology_steps || []} />
              </div>
            </Card>
          </div>
        )}

        {/* External Intel Tab */}
        {activeTab === 'external' && (
          <div className="space-y-6">
            {reverseSearchResults.providers && (
              <>
                {/* Tavily Results */}
                {reverseSearchResults.providers.tavily && (
                  <Card>
                    <div className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold">Tavily Search Results</h3>
                        <Badge color="green">
                          {reverseSearchResults.providers.tavily.count || 0} results
                        </Badge>
                      </div>
                      
                      {reverseSearchResults.providers.tavily.results && reverseSearchResults.providers.tavily.results.length > 0 ? (
                        <div className="space-y-3">
                          {reverseSearchResults.providers.tavily.results.map((result: any, idx: number) => (
                            <a
                              key={idx}
                              href={result.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block border rounded-lg p-4 hover:bg-gray-50 hover:border-blue-300 transition-all"
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <h4 className="font-medium text-blue-600 hover:text-blue-700">
                                    {result.title}
                                  </h4>
                                  <p className="text-sm text-gray-600 mt-1">
                                    {result.content}
                                  </p>
                                  <div className="text-xs text-gray-500 mt-2">
                                    {result.url}
                                  </div>
                                </div>
                                {result.score && (
                                  <Badge color="blue" size="sm">
                                    {(result.score * 100).toFixed(0)}% relevance
                                  </Badge>
                                )}
                              </div>
                            </a>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center text-gray-500 py-8">
                          No Tavily results available
                        </div>
                      )}
                      
                      {/* Tavily Images */}
                      {reverseSearchResults.providers.tavily.images && reverseSearchResults.providers.tavily.images.length > 0 && (
                        <div className="mt-6">
                          <h4 className="font-medium mb-3">Related Images</h4>
                          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                            {reverseSearchResults.providers.tavily.images.map((imgUrl: string, idx: number) => (
                              <a
                                key={idx}
                                href={imgUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="block aspect-square rounded-lg overflow-hidden border hover:ring-2 hover:ring-blue-400 transition-all"
                              >
                                <img
                                  src={imgUrl}
                                  alt={`Related tiger ${idx + 1}`}
                                  className="w-full h-full object-cover"
                                />
                              </a>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </Card>
                )}

                {/* Facility Crawl Results */}
                {reverseSearchResults.providers.facilities && (
                  <Card>
                    <div className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold">Facility Website Crawls</h3>
                        <Badge color="purple">
                          {reverseSearchResults.providers.facilities.crawled || 0} crawled
                        </Badge>
                      </div>
                      
                      {reverseSearchResults.providers.facilities.results && reverseSearchResults.providers.facilities.results.length > 0 ? (
                        <div className="space-y-3">
                          {reverseSearchResults.providers.facilities.results.map((facility: any, idx: number) => (
                            <div
                              key={idx}
                              className={`border rounded-lg p-4 ${
                                facility.success ? 'border-gray-200' : 'border-red-200 bg-red-50'
                              }`}
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <h4 className="font-medium text-gray-900">
                                      {facility.facility}
                                    </h4>
                                    {facility.has_tiger_content && (
                                      <Badge color="green" size="sm">Tiger Content Found</Badge>
                                    )}
                                    {facility.success ? (
                                      <CheckCircleIcon className="w-5 h-5 text-green-500" />
                                    ) : (
                                      <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
                                    )}
                                  </div>
                                  <a
                                    href={facility.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-sm text-blue-600 hover:underline mt-1 block"
                                  >
                                    {facility.url}
                                  </a>
                                  {facility.content_preview && (
                                    <p className="text-sm text-gray-600 mt-2">
                                      {facility.content_preview}
                                    </p>
                                  )}
                                  {facility.links_found > 0 && (
                                    <div className="text-xs text-gray-500 mt-2">
                                      Found {facility.links_found} links
                                    </div>
                                  )}
                                  {facility.error && (
                                    <div className="text-xs text-red-600 mt-2">
                                      Error: {facility.error}
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center text-gray-500 py-8">
                          No facilities crawled
                        </div>
                      )}
                    </div>
                  </Card>
                )}

                {/* Google/SerpApi Results */}
                {reverseSearchResults.providers.google && (
                  <Card>
                    <div className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold">Google Lens / SerpApi</h3>
                        <Badge color="blue">
                          {reverseSearchResults.providers.google.count || 0} results
                        </Badge>
                      </div>
                      
                      {reverseSearchResults.providers.google.error ? (
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                          <div className="flex items-start gap-2">
                            <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                            <div>
                              <div className="font-medium text-yellow-900">Service Unavailable</div>
                              <div className="text-sm text-yellow-700 mt-1">
                                {reverseSearchResults.providers.google.note || reverseSearchResults.providers.google.error}
                              </div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center text-gray-500 py-8">
                          No Google Lens results
                        </div>
                      )}
                    </div>
                  </Card>
                )}
              </>
            )}
          </div>
        )}

        {/* Detection Tab */}
        {activeTab === 'detection' && (
          <div className="space-y-6">
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-semibold mb-4">Tiger Detection (MegaDetector GPU)</h3>
                {detectedTigers.length > 0 ? (
                  <div className="space-y-4">
                    {detectedTigers.map((tiger: any, index: number) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <h4 className="font-semibold text-gray-900">
                              Detected Tiger #{index + 1}
                            </h4>
                            <div className="text-sm text-gray-600 mt-1">
                              Category: {tiger.category || 'animal'}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold text-green-600">
                              {(tiger.confidence * 100).toFixed(1)}%
                            </div>
                            <div className="text-xs text-gray-500">confidence</div>
                          </div>
                        </div>
                        
                        {tiger.bbox && Array.isArray(tiger.bbox) && (
                          <div className="bg-gray-50 rounded p-3">
                            <div className="text-xs text-gray-600 mb-1">Bounding Box Coordinates:</div>
                            <div className="grid grid-cols-4 gap-2 text-sm font-mono">
                              <div><span className="text-gray-500">X1:</span> {tiger.bbox[0]?.toFixed(0)}</div>
                              <div><span className="text-gray-500">Y1:</span> {tiger.bbox[1]?.toFixed(0)}</div>
                              <div><span className="text-gray-500">X2:</span> {tiger.bbox[2]?.toFixed(0)}</div>
                              <div><span className="text-gray-500">Y2:</span> {tiger.bbox[3]?.toFixed(0)}</div>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-12">
                    <InformationCircleIcon className="w-16 h-16 mx-auto text-gray-300 mb-3" />
                    <div>No tigers detected in this image</div>
                  </div>
                )}
              </div>
            </Card>
          </div>
        )}

        {/* Report Tab */}
        {activeTab === 'report' && (
          <div className="space-y-6">
            <Card>
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-2xl font-bold text-gray-900">Investigation Report</h3>
                  <div className="flex gap-2">
                    <Badge color="purple">Claude AI Generated</Badge>
                    {getConfidenceBadge(confidence)}
                  </div>
                </div>
                
                {report.summary ? (
                  <MarkdownContent content={report.summary} />
                ) : (
                  <div className="text-center text-gray-500 py-12">
                    <DocumentTextIcon className="w-16 h-16 mx-auto text-gray-300 mb-3" />
                    <div>Report not yet generated</div>
                  </div>
                )}
              </div>
            </Card>
            
            {/* OmniVinci Analysis */}
            {omnivinci.visual_analysis && (
              <Card>
                <div className="p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <h3 className="text-lg font-semibold">OmniVinci Visual Analysis</h3>
                    <Badge color="purple">Omni-Modal LLM</Badge>
                    {omnivinci.omnivinci_available && (
                      <Badge color="green" size="sm">Active</Badge>
                    )}
                  </div>
                  
                  <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6">
                    <MarkdownContent content={omnivinci.visual_analysis} />
                  </div>
                  
                  <div className="mt-4 flex gap-2">
                    <Badge color="gray" size="sm">
                      Analysis Type: {omnivinci.analysis_type}
                    </Badge>
                    <Badge color="gray" size="sm">
                      Model Consensus: {omnivinci.models_consensus || 0} models
                    </Badge>
                  </div>
                </div>
              </Card>
            )}
          </div>
        )}
      </div>

      {/* No Results Message */}
      {topMatches.length === 0 && totalMatches === 0 && (
        <Card>
          <div className="p-8 text-center">
            <InformationCircleIcon className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Matches Found</h3>
            <p className="text-gray-600 max-w-md mx-auto">
              No matching tigers were found in the reference database. This could indicate:
            </p>
            <ul className="text-sm text-gray-600 mt-3 space-y-1 max-w-md mx-auto text-left">
              <li>• This is a new/unrecorded individual</li>
              <li>• The reference database needs expansion</li>
              <li>• Image quality or angle affects matching</li>
              <li>• Stripe patterns are not clearly visible</li>
            </ul>
          </div>
        </Card>
      )}
    </div>
  )
}

export default Investigation2ResultsEnhanced


import { useState } from 'react'
import { useWebSearchMutation } from '../../app/api'
import Card from '../common/Card'
import Button from '../common/Button'
import Input from '../common/Input'
import LoadingSpinner from '../common/LoadingSpinner'
import Badge from '../common/Badge'
import { GlobeAltIcon } from '@heroicons/react/24/outline'

const WebSearchTab = () => {
  const [query, setQuery] = useState('')
  const [limit, setLimit] = useState(10)
  const [provider, setProvider] = useState<'firecrawl' | 'serper' | 'tavily' | 'perplexity'>('serper')
  const [location, setLocation] = useState('')
  const [gl, setGl] = useState('')
  const [hl, setHl] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [webSearch, { isLoading, data, error }] = useWebSearchMutation()

  const handleSearch = async () => {
    if (!query.trim()) return
    try {
      const searchParams: any = { query, limit, provider }
      if (provider === 'serper') {
        if (location) searchParams.location = location
        if (gl) searchParams.gl = gl
        if (hl) searchParams.hl = hl
      }
      await webSearch(searchParams)
    } catch (err) {
      console.error('Search error:', err)
    }
  }

  const results = data?.data?.results || []
  const answerBox = data?.data?.answer_box
  const knowledgeGraph = data?.data?.knowledge_graph
  const peopleAlsoAsk = data?.data?.people_also_ask || []
  const relatedQuestions = data?.data?.related_questions || []
  const totalResults = data?.data?.total_results

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <GlobeAltIcon className="h-6 w-6 text-primary-600" />
          Web Search
        </h2>
        <p className="text-gray-600 mt-2">Search the web for information related to your investigation</p>
      </div>

      <Card>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-2">
              <Input
                type="text"
                placeholder="e.g., 'tiger facility Texas USDA violations'"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Results Limit
              </label>
              <Input
                type="number"
                min={1}
                max={50}
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value) || 10)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Provider
              </label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="firecrawl">Firecrawl</option>
                <option value="serper">Serper</option>
                <option value="tavily">Tavily</option>
                <option value="perplexity">Perplexity</option>
              </select>
            </div>
          </div>
          
          {provider === 'serper' && (
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                {showAdvanced ? '▼' : '▶'} Advanced Options (Location, Country, Language)
              </button>
              {showAdvanced && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Location
                    </label>
                    <Input
                      type="text"
                      placeholder="e.g., Austin, Texas"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Country Code (gl)
                    </label>
                    <Input
                      type="text"
                      placeholder="e.g., us, uk"
                      value={gl}
                      onChange={(e) => setGl(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Language Code (hl)
                    </label>
                    <Input
                      type="text"
                      placeholder="e.g., en, es"
                      value={hl}
                      onChange={(e) => setHl(e.target.value)}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
          
          <Button onClick={handleSearch} disabled={!query.trim() || isLoading} className="w-full">
            {isLoading ? 'Searching...' : '🔍 Search'}
          </Button>
        </div>
      </Card>

      {error && (
        <Card>
          <div className="text-red-600">
            Search failed: {'data' in error ? JSON.stringify(error.data) : 'Unknown error'}
          </div>
        </Card>
      )}

      {data?.data && (
        <div className="space-y-6">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Found {data.data.count} results
                </h3>
                {totalResults && (
                  <p className="text-sm text-gray-500">Total: {totalResults} results available</p>
                )}
              </div>
              <Badge variant="info">Provider: {data.data.provider}</Badge>
            </div>

            {/* Answer Box (Serper) */}
            {answerBox && (
              <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-semibold text-blue-900 mb-2">Featured Answer</h4>
                {answerBox.answer && (
                  <p className="text-blue-800 mb-2">{answerBox.answer}</p>
                )}
                {answerBox.title && (
                  <p className="text-sm text-blue-700 font-medium">{answerBox.title}</p>
                )}
                {answerBox.link && (
                  <a
                    href={answerBox.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline"
                  >
                    {answerBox.link}
                  </a>
                )}
              </div>
            )}

            {/* Knowledge Graph (Serper) */}
            {knowledgeGraph && (
              <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                <h4 className="font-semibold text-green-900 mb-2">Knowledge Graph</h4>
                {knowledgeGraph.title && (
                  <p className="text-green-800 font-medium mb-1">{knowledgeGraph.title}</p>
                )}
                {knowledgeGraph.description && (
                  <p className="text-green-700 text-sm mb-2">{knowledgeGraph.description}</p>
                )}
                {knowledgeGraph.website && (
                  <a
                    href={knowledgeGraph.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-green-600 hover:underline"
                  >
                    {knowledgeGraph.website}
                  </a>
                )}
              </div>
            )}

            {/* Organic Results */}
            <div className="space-y-4">
              {results.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No results found</p>
              ) : (
                results.map((result, idx) => (
                  <div
                    key={idx}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 mb-1">{result.title || 'No title'}</h4>
                        {result.url && (
                          <a
                            href={result.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary-600 hover:text-primary-700 text-sm mb-2 block"
                          >
                            {result.url}
                          </a>
                        )}
                        {result.snippet && (
                          <p className="text-gray-600 text-sm">{result.snippet}</p>
                        )}
                      </div>
                      <div className="flex flex-col gap-2 items-end">
                        {result.position && (
                          <Badge variant="default">Position: {result.position}</Badge>
                        )}
                        {result.score && (
                          <Badge variant="info">Score: {result.score.toFixed(2)}</Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* People Also Ask (Serper) */}
            {peopleAlsoAsk.length > 0 && (
              <div className="mt-6 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                <h4 className="font-semibold text-purple-900 mb-3">People Also Ask</h4>
                <div className="space-y-2">
                  {peopleAlsoAsk.map((item: any, idx: number) => (
                    <div key={idx} className="text-sm text-purple-800">
                      • {item.question || item}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Related Questions (Serper) */}
            {relatedQuestions.length > 0 && (
              <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <h4 className="font-semibold text-yellow-900 mb-3">Related Questions</h4>
                <div className="space-y-2">
                  {relatedQuestions.map((item: any, idx: number) => (
                    <div key={idx} className="text-sm text-yellow-800">
                      • {item.question || item}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      )}
    </div>
  )
}

export default WebSearchTab


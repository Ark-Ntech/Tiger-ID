import { useState } from 'react'
import { useNewsSearchMutation } from '../../app/api'
import Card from '../common/Card'
import Button from '../common/Button'
import Input from '../common/Input'
import LoadingSpinner from '../common/LoadingSpinner'
import Badge from '../common/Badge'
import { NewspaperIcon } from '@heroicons/react/24/outline'

const NewsMonitorTab = () => {
  const [query, setQuery] = useState('')
  const [days, setDays] = useState(7)
  const [limit, setLimit] = useState(20)
  const [newsSearch, { isLoading, data, error }] = useNewsSearchMutation()

  const handleSearch = async () => {
    try {
      await newsSearch({ query: query.trim() || undefined, days, limit })
    } catch (err) {
      console.error('News search error:', err)
    }
  }

  const articles = data?.data?.articles || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <NewspaperIcon className="h-6 w-6 text-primary-600" />
          News Monitor
        </h2>
        <p className="text-gray-600 mt-2">Monitor news articles for tiger trafficking keywords</p>
      </div>

      <Card>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Input
                type="text"
                label="Custom Query (optional)"
                placeholder="Leave empty to use default keywords"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Days Back
              </label>
              <Input
                type="number"
                min={1}
                max={365}
                value={days}
                onChange={(e) => setDays(parseInt(e.target.value) || 7)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Results Limit
              </label>
              <Input
                type="number"
                min={1}
                max={100}
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value) || 20)}
              />
            </div>
          </div>
          <Button onClick={handleSearch} disabled={isLoading} className="w-full">
            {isLoading ? 'Searching...' : '📰 Search News'}
          </Button>
        </div>
      </Card>

      {error && (
        <Card>
          <div className="text-red-600">
            News search failed: {'data' in error ? JSON.stringify(error.data) : 'Unknown error'}
          </div>
        </Card>
      )}

      {data?.data && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Found {articles.length} news articles
            </h3>
            <Badge variant="info">Days: {data.data.days}</Badge>
          </div>

          <div className="space-y-4">
            {articles.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No news articles found</p>
            ) : (
              articles.map((article, idx) => (
                <div
                  key={idx}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-1">
                        {article.title || 'No title'}
                      </h4>
                      {article.url && (
                        <a
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-600 hover:text-primary-700 text-sm mb-2 block"
                        >
                          {article.url}
                        </a>
                      )}
                      {article.source && (
                        <p className="text-sm text-gray-600 mb-1">
                          <strong>Source:</strong> {article.source}
                        </p>
                      )}
                      {article.snippet && (
                        <p className="text-gray-600 text-sm mb-2">{article.snippet}</p>
                      )}
                      {article.date && (
                        <p className="text-xs text-gray-500">Date: {article.date}</p>
                      )}
                    </div>
                    <div>
                      {article.facility_name && (
                        <Badge variant="warning">Facility: {article.facility_name}</Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      )}
    </div>
  )
}

export default NewsMonitorTab


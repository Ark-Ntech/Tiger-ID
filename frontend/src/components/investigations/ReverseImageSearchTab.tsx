import { useState } from 'react'
import { useReverseImageSearchMutation } from '../../app/api'
import Card from '../common/Card'
import Button from '../common/Button'
import Input from '../common/Input'
import LoadingSpinner from '../common/LoadingSpinner'
import Badge from '../common/Badge'
import { PhotoIcon } from '@heroicons/react/24/outline'

const ReverseImageSearchTab = () => {
  const [imageUrl, setImageUrl] = useState('')
  const [provider, setProvider] = useState<'google' | 'tineye' | 'yandex'>('google')
  const [reverseImageSearch, { isLoading, data, error }] = useReverseImageSearchMutation()

  const handleSearch = async () => {
    if (!imageUrl.trim()) return
    try {
      await reverseImageSearch({ image_url: imageUrl, provider })
    } catch (err) {
      console.error('Image search error:', err)
    }
  }

  const results = data?.data?.results || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <PhotoIcon className="h-6 w-6 text-primary-600" />
          Reverse Image Search
        </h2>
        <p className="text-gray-600 mt-2">Search the web for similar images using reverse image search</p>
      </div>

      <Card>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-3">
              <Input
                type="text"
                label="Image URL"
                placeholder="https://example.com/tiger-image.jpg"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
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
                <option value="google">Google</option>
                <option value="tineye">TinEye</option>
                <option value="yandex">Yandex</option>
              </select>
            </div>
          </div>
          <div className="text-sm text-gray-500">
            Note: File upload support coming soon. Currently supports image URLs only.
          </div>
          <Button onClick={handleSearch} disabled={!imageUrl.trim() || isLoading} className="w-full">
            {isLoading ? 'Searching...' : '🖼️ Search Image'}
          </Button>
        </div>
      </Card>

      {error && (
        <Card>
          <div className="text-red-600">
            Image search failed: {'data' in error ? JSON.stringify(error.data) : 'Unknown error'}
          </div>
        </Card>
      )}

      {data?.data && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Found {data.data.count} similar images
            </h3>
            <Badge variant="info">Provider: {data.data.provider}</Badge>
          </div>

          <div className="space-y-4">
            {results.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No similar images found</p>
            ) : (
              results.map((result, idx) => (
                <div
                  key={idx}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      {result.title && (
                        <h4 className="font-semibold text-gray-900 mb-1">{result.title}</h4>
                      )}
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
                    {result.score && (
                      <Badge variant="info">Similarity: {result.score.toFixed(2)}</Badge>
                    )}
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

export default ReverseImageSearchTab


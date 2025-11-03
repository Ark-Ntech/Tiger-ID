import { useState } from 'react'
import { useGenerateLeadsMutation } from '../../app/api'
import Card from '../common/Card'
import Button from '../common/Button'
import Input from '../common/Input'
import LoadingSpinner from '../common/LoadingSpinner'
import Badge from '../common/Badge'
import { LightBulbIcon } from '@heroicons/react/24/outline'

const LeadGenerationTab = () => {
  const [location, setLocation] = useState('')
  const [includeListings, setIncludeListings] = useState(true)
  const [includeSocial, setIncludeSocial] = useState(true)
  const [generateLeads, { isLoading, data, error }] = useGenerateLeadsMutation()

  const handleGenerate = async () => {
    try {
      await generateLeads({
        location: location.trim() || undefined,
        include_listings: includeListings,
        include_social_media: includeSocial,
      })
    } catch (err) {
      console.error('Lead generation error:', err)
    }
  }

  const leadsData = data?.data?.leads
  const listings = leadsData?.listings || []
  const socialPosts = leadsData?.social_media_posts || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <LightBulbIcon className="h-6 w-6 text-primary-600" />
          Lead Generation
        </h2>
        <p className="text-gray-600 mt-2">
          Generate investigation leads from suspicious listings and social media posts
        </p>
      </div>

      <Card>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Input
                type="text"
                label="Location Filter (optional)"
                placeholder="e.g., Texas, California"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">Include:</label>
              <div className="flex flex-col gap-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={includeListings}
                    onChange={(e) => setIncludeListings(e.target.checked)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700">Include Listings</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={includeSocial}
                    onChange={(e) => setIncludeSocial(e.target.checked)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700">Include Social Media</span>
                </label>
              </div>
            </div>
          </div>
          <Button onClick={handleGenerate} disabled={isLoading} className="w-full">
            {isLoading ? 'Generating...' : '🎯 Generate Leads'}
          </Button>
        </div>
      </Card>

      {error && (
        <Card>
          <div className="text-red-600">
            Lead generation failed: {'data' in error ? JSON.stringify(error.data) : 'Unknown error'}
          </div>
        </Card>
      )}

      {data?.data && (
        <div className="space-y-6">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Generated {leadsData?.total_leads || 0} leads
                {leadsData?.summary?.high_priority_leads && (
                  <span className="ml-2 text-red-600">
                    ({leadsData.summary.high_priority_leads} high priority)
                  </span>
                )}
              </h3>
            </div>
          </Card>

          {listings.length > 0 && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">📋 Suspicious Listings</h3>
              <div className="space-y-4">
                {listings.map((listing, idx) => (
                  <div
                    key={idx}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 mb-1">
                          {listing.title || 'No title'}
                        </h4>
                        {listing.url && (
                          <a
                            href={listing.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary-600 hover:text-primary-700 text-sm mb-2 block"
                          >
                            {listing.url}
                          </a>
                        )}
                        {listing.snippet && (
                          <p className="text-gray-600 text-sm mb-2">{listing.snippet}</p>
                        )}
                        {listing.matched_facilities && listing.matched_facilities.length > 0 && (
                          <Badge variant="warning" className="mt-2">
                            ⚠️ Matched to {listing.matched_facilities.length} reference
                            {listing.matched_facilities.length > 1 ? ' facilities' : ' facility'}
                          </Badge>
                        )}
                      </div>
                      <div>
                        <Badge variant="danger">
                          Suspicious: {listing.suspicious_score.toFixed(2)}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {socialPosts.length > 0 && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                📱 Suspicious Social Media Posts
              </h3>
              <div className="space-y-4">
                {socialPosts.map((post, idx) => (
                  <div
                    key={idx}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        {post.url && (
                          <a
                            href={post.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary-600 hover:text-primary-700 text-sm mb-2 block"
                          >
                            {post.url}
                          </a>
                        )}
                        {post.snippet && (
                          <p className="text-gray-600 text-sm">{post.snippet}</p>
                        )}
                      </div>
                      <div className="flex flex-col gap-2 items-end">
                        <Badge variant="danger">
                          Suspicious: {post.suspicious_score.toFixed(2)}
                        </Badge>
                        <Badge variant="info">Platform: {post.platform || 'Unknown'}</Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {listings.length === 0 && socialPosts.length === 0 && (
            <Card>
              <p className="text-gray-500 text-center py-8">No leads found</p>
            </Card>
          )}
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

export default LeadGenerationTab


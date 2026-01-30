import React, { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';

interface Match {
  tiger_id: string;
  tiger_name: string;
  similarity: number;
  model: string;
  uploaded_image_crop?: string;
  database_image: string;
  facility: {
    name: string;
    location: string;
    coordinates?: { lat: number; lon: number };
  };
  confidence_breakdown?: {
    stripe_similarity: number;
    visual_features: number;
    historical_context: number;
  };
}

interface Investigation2MatchCardProps {
  match: Match;
}

const ProgressBar: React.FC<{ label: string; value: number }> = ({ label, value }) => {
  return (
    <div className="mb-2">
      <div className="flex justify-between text-sm mb-1">
        <span>{label}</span>
        <span className="font-medium">{value.toFixed(1)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        ></div>
      </div>
    </div>
  );
};

export const Investigation2MatchCard: React.FC<Investigation2MatchCardProps> = ({ match }) => {
  const [expanded, setExpanded] = useState(false);

  const getSimilarityColor = (similarity: number) => {
    if (similarity >= 80) return 'bg-green-100 text-green-800';
    if (similarity >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <div className="match-card border border-gray-300 rounded-lg p-4 mb-4 bg-white shadow-sm hover:shadow-md transition-shadow duration-200">
      {/* Summary */}
      <div
        className="flex items-center gap-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <img
          src={match.database_image}
          alt={match.tiger_name}
          className="w-20 h-20 object-cover rounded border border-gray-200"
          onError={(e) => {
            (e.target as HTMLImageElement).src = '/placeholder-tiger.png';
          }}
        />

        <div className="flex-1">
          <h4 className="font-semibold text-lg">{match.tiger_name || 'Unknown Tiger'}</h4>
          <div className="flex flex-wrap gap-2 mt-1">
            <span className={`inline-block px-2 py-1 text-xs font-medium rounded ${getSimilarityColor(match.similarity)}`}>
              {match.similarity.toFixed(1)}% match
            </span>
            <span className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
              {match.model}
            </span>
          </div>
          <p className="text-sm text-gray-600 mt-1">{match.facility.name}</p>
        </div>

        <div className="text-gray-400 hover:text-gray-600 transition-colors">
          {expanded ? <ChevronUpIcon className="w-6 h-6" /> : <ChevronDownIcon className="w-6 h-6" />}
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="mt-4 border-t border-gray-200 pt-4">
          {/* Image Comparison */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            {match.uploaded_image_crop && (
              <div>
                <h5 className="font-medium text-sm mb-2 text-gray-700">Uploaded Image</h5>
                <img
                  src={match.uploaded_image_crop}
                  alt="Uploaded"
                  className="w-full rounded border border-gray-200"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/placeholder-tiger.png';
                  }}
                />
              </div>
            )}
            <div>
              <h5 className="font-medium text-sm mb-2 text-gray-700">Database Match</h5>
              <img
                src={match.database_image}
                alt="Database"
                className="w-full rounded border border-gray-200"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = '/placeholder-tiger.png';
                }}
              />
            </div>
          </div>

          {/* Confidence Breakdown */}
          {match.confidence_breakdown && (
            <div className="mb-4 bg-gray-50 rounded p-4">
              <h5 className="font-medium text-sm mb-3 text-gray-700">Confidence Breakdown</h5>
              <ProgressBar
                label="Stripe Similarity"
                value={match.confidence_breakdown.stripe_similarity}
              />
              <ProgressBar
                label="Visual Features"
                value={match.confidence_breakdown.visual_features}
              />
              <ProgressBar
                label="Historical Context"
                value={match.confidence_breakdown.historical_context}
              />
            </div>
          )}

          {/* Facility Information */}
          <div className="mb-4 bg-gray-50 rounded p-4">
            <h5 className="font-medium text-sm mb-2 text-gray-700">Facility Information</h5>
            <p className="text-sm font-medium">{match.facility.name}</p>
            <p className="text-sm text-gray-600">{match.facility.location}</p>
            {match.facility.coordinates && (
              <p className="text-xs text-gray-400 mt-1">
                Coordinates: {match.facility.coordinates.lat.toFixed(4)}, {match.facility.coordinates.lon.toFixed(4)}
              </p>
            )}
          </div>

          {/* Tiger ID */}
          <div className="text-xs text-gray-400">
            Tiger ID: {match.tiger_id}
          </div>
        </div>
      )}
    </div>
  );
};

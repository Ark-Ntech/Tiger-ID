import React from 'react';
import type { Citation } from '../../types/investigation2';

interface Investigation2CitationsProps {
  citations: Citation[];
}

export const Investigation2Citations: React.FC<Investigation2CitationsProps> = ({ citations }) => {
  if (!citations || citations.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No citations available</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
      {citations.map((citation, idx) => (
        <div
          key={idx}
          className="citation-card border border-gray-300 rounded-lg p-4 hover:shadow-lg transition-shadow duration-200 bg-white"
        >
          <a
            href={citation.uri}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline block mb-2"
          >
            <h4 className="font-semibold text-lg line-clamp-2">{citation.title}</h4>
          </a>

          <p className="text-sm text-gray-600 mt-2 line-clamp-3">{citation.snippet}</p>

          <div className="mt-3 flex flex-wrap gap-2 items-center">
            {citation.relevance_score && (
              <span className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                {citation.relevance_score}% relevant
              </span>
            )}

            {citation.location_mentions && citation.location_mentions.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {citation.location_mentions.slice(0, 3).map((location, locIdx) => (
                  <span
                    key={locIdx}
                    className="inline-block px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded"
                  >
                    {location}
                  </span>
                ))}
                {citation.location_mentions.length > 3 && (
                  <span className="inline-block px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded">
                    +{citation.location_mentions.length - 3} more
                  </span>
                )}
              </div>
            )}
          </div>

          <div className="mt-2 text-xs text-gray-400 truncate">
            {new URL(citation.uri).hostname}
          </div>
        </div>
      ))}
    </div>
  );
};

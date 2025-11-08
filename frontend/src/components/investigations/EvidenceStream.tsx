import { useState } from 'react'
import Card from '../common/Card'
import Badge from '../common/Badge'
import Button from '../common/Button'
import {
  DocumentTextIcon,
  NewspaperIcon,
  GlobeAltIcon,
  PhotoIcon,
  CheckCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'

interface Evidence {
  id: string
  type: string
  title: string
  source: string
  date?: string
  preview: string
  confidence: 'high' | 'medium' | 'low'
  timestamp: string
}

interface EvidenceStreamProps {
  evidence: Evidence[]
  onRemove?: (id: string) => void
  onView?: (id: string) => void
}

const EvidenceStream = ({ evidence, onRemove, onView }: EvidenceStreamProps) => {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const getTypeIcon = (type: string) => {
    if (type === 'document') return DocumentTextIcon
    if (type === 'article' || type === 'news') return NewspaperIcon
    if (type === 'webpage') return GlobeAltIcon
    if (type === 'image') return PhotoIcon
    return DocumentTextIcon
  }

  const getConfidenceColor = (confidence: string) => {
    if (confidence === 'high') return 'success'
    if (confidence === 'medium') return 'warning'
    return 'default'
  }

  if (evidence.length === 0) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Evidence Stream</h3>
        <p className="text-sm text-gray-500 text-center py-4">
          No evidence collected yet. Evidence will appear here as it's discovered.
        </p>
      </Card>
    )
  }

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Evidence Stream</h3>
        <Badge variant="primary">{evidence.length} items</Badge>
      </div>
      
      <div className="space-y-3 max-h-[500px] overflow-y-auto">
        {evidence.map((item) => {
          const Icon = getTypeIcon(item.type)
          const isExpanded = expandedId === item.id
          
          return (
            <div 
              key={item.id}
              className="border border-gray-200 rounded-lg p-3 hover:border-gray-300 transition-colors"
            >
              <div className="flex items-start gap-3">
                <div className="text-gray-600 mt-0.5">
                  <Icon className="h-5 w-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <h4 className="text-sm font-medium text-gray-900">
                      {item.title}
                    </h4>
                    <Badge variant={getConfidenceColor(item.confidence)} className="text-xs">
                      {item.confidence}
                    </Badge>
                  </div>
                  
                  <p className="text-xs text-gray-600 mb-2">
                    Source: {item.source}
                    {item.date && ` • ${item.date}`}
                  </p>
                  
                  <p className={`text-xs text-gray-700 ${isExpanded ? '' : 'line-clamp-2'}`}>
                    {item.preview}
                  </p>
                  
                  {item.preview.length > 100 && (
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : item.id)}
                      className="text-xs text-primary-600 hover:text-primary-700 mt-1"
                    >
                      {isExpanded ? 'Show less' : 'Show more'}
                    </button>
                  )}
                  
                  <div className="flex items-center gap-2 mt-2">
                    {onView && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onView(item.id)}
                        className="text-xs"
                      >
                        View Full
                      </Button>
                    )}
                    {onRemove && (
                      <button
                        onClick={() => onRemove(item.id)}
                        className="text-xs text-red-600 hover:text-red-700 flex items-center gap-1"
                      >
                        <XMarkIcon className="h-3 w-3" />
                        Remove
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </Card>
  )
}

export default EvidenceStream


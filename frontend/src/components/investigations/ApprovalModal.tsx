import { useState } from 'react'
import Modal from '../common/Modal'
import Button from '../common/Button'
import Badge from '../common/Badge'
import { 
  ClockIcon, 
  CurrencyDollarIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline'

interface ApprovalModalProps {
  isOpen: boolean
  onClose: () => void
  approvalId: string
  approvalType: 'plan' | 'evidence_review' | 'findings' | 'final'
  data: any
  onApprove: (modifications?: any) => void
  onReject: (reason?: string) => void
}

const ApprovalModal = ({
  isOpen,
  onClose,
  approvalId,
  approvalType,
  data,
  onApprove,
  onReject
}: ApprovalModalProps) => {
  const [rejectionReason, setRejectionReason] = useState('')
  const [showRejectInput, setShowRejectInput] = useState(false)

  const getTitle = () => {
    switch (approvalType) {
      case 'plan':
        return 'Approve Investigation Plan'
      case 'evidence_review':
        return 'Review Collected Evidence'
      case 'findings':
        return 'Review Preliminary Findings'
      case 'final':
        return 'Final Approval - Generate Report'
      default:
        return 'Approval Required'
    }
  }

  const handleApprove = () => {
    onApprove()
    onClose()
  }

  const handleReject = () => {
    onReject(rejectionReason || undefined)
    onClose()
    setShowRejectInput(false)
    setRejectionReason('')
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={getTitle()} size="lg">
      <div className="space-y-4">
        {/* Approval Type Specific Content */}
        {approvalType === 'plan' && data && (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-900 mb-2">
                Investigation Request
              </h4>
              <p className="text-sm text-blue-800">{data.request}</p>
            </div>

            {data.entities && data.entities.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-2">Target Entities</h4>
                <div className="flex flex-wrap gap-2">
                  {data.entities.map((entity: string, idx: number) => (
                    <Badge key={idx} variant="primary">{entity}</Badge>
                  ))}
                </div>
              </div>
            )}

            {data.goals && data.goals.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-2">Investigation Goals</h4>
                <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                  {data.goals.map((goal: string, idx: number) => (
                    <li key={idx}>{goal}</li>
                  ))}
                </ul>
              </div>
            )}

            {data.tools && data.tools.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-2">
                  Tools to Use ({data.tools.length})
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  {data.tools.map((tool: any, idx: number) => (
                    <div key={idx} className="text-xs bg-gray-50 p-2 rounded">
                      {tool.name || tool}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center gap-4 pt-2 border-t">
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <ClockIcon className="h-4 w-4" />
                <span>~{Math.round(data.duration_estimate_seconds || 60)} seconds</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <CurrencyDollarIcon className="h-4 w-4" />
                <span>${(data.cost_estimate_usd || 0).toFixed(2)}</span>
              </div>
            </div>
          </div>
        )}

        {approvalType === 'evidence_review' && data && (
          <div className="space-y-4">
            <div className="text-sm text-gray-700">
              Research phase complete. Collected {data.evidence_count || 0} pieces of evidence.
            </div>
            {data.summary && (
              <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-800">
                {data.summary}
              </div>
            )}
          </div>
        )}

        {approvalType === 'findings' && data && (
          <div className="space-y-4">
            <div className="text-sm text-gray-700">
              Analysis complete. Found {data.findings_count || 0} key findings.
            </div>
            {data.key_findings && (
              <ul className="list-disc list-inside text-sm text-gray-800 space-y-1">
                {data.key_findings.map((finding: string, idx: number) => (
                  <li key={idx}>{finding}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {approvalType === 'final' && data && (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-green-900 mb-2">
                Investigation Complete
              </h4>
              <p className="text-sm text-green-800">
                All phases completed successfully. Ready to generate formal report.
              </p>
            </div>
            {data.summary && (
              <div className="text-sm text-gray-700">
                {data.summary}
              </div>
            )}
          </div>
        )}

        {/* Warning Message */}
        {!showRejectInput && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 flex items-start gap-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 mt-0.5" />
            <p className="text-xs text-yellow-800">
              This approval is required to proceed with the investigation. 
              Rejecting will pause the investigation.
            </p>
          </div>
        )}

        {/* Rejection Input */}
        {showRejectInput && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reason for rejection (optional)
            </label>
            <textarea
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Explain why you're rejecting this..."
            />
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t">
          {showRejectInput ? (
            <>
              <Button
                variant="outline"
                onClick={() => {
                  setShowRejectInput(false)
                  setRejectionReason('')
                }}
              >
                Cancel
              </Button>
              <Button variant="danger" onClick={handleReject}>
                Confirm Rejection
              </Button>
            </>
          ) : (
            <>
              <Button
                variant="outline"
                onClick={() => setShowRejectInput(true)}
              >
                Reject
              </Button>
              <Button variant="primary" onClick={handleApprove}>
                Approve & Continue
              </Button>
            </>
          )}
        </div>
      </div>
    </Modal>
  )
}

export default ApprovalModal


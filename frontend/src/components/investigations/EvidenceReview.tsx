import ApprovalModal from './ApprovalModal'

interface EvidenceReviewProps {
  isOpen: boolean
  onClose: () => void
  data: any
  onApprove: () => void
  onReject: (reason?: string) => void
}

const EvidenceReview = (props: EvidenceReviewProps) => {
  return (
    <ApprovalModal
      {...props}
      approvalId={props.data?.investigation_id || 'evidence'}
      approvalType="evidence_review"
    />
  )
}

export default EvidenceReview


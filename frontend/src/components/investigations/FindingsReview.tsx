import ApprovalModal from './ApprovalModal'

interface FindingsReviewProps {
  isOpen: boolean
  onClose: () => void
  findings: any
  onApprove: () => void
  onReject: (reason?: string) => void
}

const FindingsReview = (props: FindingsReviewProps) => {
  return (
    <ApprovalModal
      {...props}
      approvalId={props.findings?.investigation_id || 'findings'}
      approvalType="findings"
      data={props.findings}
    />
  )
}

export default FindingsReview


import ApprovalModal from './ApprovalModal'

interface InvestigationPlanReviewProps {
  isOpen: boolean
  onClose: () => void
  plan: any
  onApprove: () => void
  onReject: (reason?: string) => void
}

const InvestigationPlanReview = (props: InvestigationPlanReviewProps) => {
  return (
    <ApprovalModal
      {...props}
      approvalId={props.plan?.investigation_id || 'plan'}
      approvalType="plan"
      data={props.plan}
    />
  )
}

export default InvestigationPlanReview


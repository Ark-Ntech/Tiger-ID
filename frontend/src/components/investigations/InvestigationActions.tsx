import Button from '../common/Button'
import {
  PlayIcon,
  PauseIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  CheckCircleIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline'

interface InvestigationActionsProps {
  investigation: any
  extended?: any
  onResume?: () => void
  onPause?: () => void
  onView?: () => void
  onApprove?: () => void
  onExport?: () => void
  onEdit?: () => void
  onDelete?: () => void
}

const InvestigationActions = ({
  investigation,
  extended,
  onResume,
  onPause,
  onView,
  onApprove,
  onExport,
  onEdit,
  onDelete
}: InvestigationActionsProps) => {
  const status = investigation.status

  return (
    <div className="flex items-center gap-2">
      {/* Pending Approval */}
      {extended?.pending_approval && onApprove && (
        <Button
          variant="warning"
          size="sm"
          onClick={(e) => {
            e.stopPropagation()
            onApprove()
          }}
        >
          <CheckCircleIcon className="h-4 w-4 mr-1" />
          Review & Approve
        </Button>
      )}

      {/* Paused - Resume */}
      {status === 'paused' && onResume && (
        <Button
          variant="primary"
          size="sm"
          onClick={(e) => {
            e.stopPropagation()
            onResume()
          }}
        >
          <PlayIcon className="h-4 w-4 mr-1" />
          Resume
        </Button>
      )}

      {/* Active - Pause */}
      {(status === 'active' || status === 'in_progress') && onPause && (
        <Button
          variant="outline"
          size="sm"
          onClick={(e) => {
            e.stopPropagation()
            onPause()
          }}
        >
          <PauseIcon className="h-4 w-4 mr-1" />
          Pause
        </Button>
      )}

      {/* Draft - Edit */}
      {status === 'draft' && onEdit && (
        <Button
          variant="outline"
          size="sm"
          onClick={(e) => {
            e.stopPropagation()
            onEdit()
          }}
        >
          <PencilIcon className="h-4 w-4 mr-1" />
          Edit
        </Button>
      )}

      {/* Completed - Export */}
      {status === 'completed' && onExport && (
        <Button
          variant="outline"
          size="sm"
          onClick={(e) => {
            e.stopPropagation()
            onExport()
          }}
        >
          <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
          Export
        </Button>
      )}

      {/* Always Show View */}
      {onView && (
        <Button
          variant={status === 'active' || status === 'in_progress' ? 'primary' : 'outline'}
          size="sm"
          onClick={(e) => {
            e.stopPropagation()
            onView()
          }}
        >
          <EyeIcon className="h-4 w-4 mr-1" />
          {status === 'active' || status === 'in_progress' ? 'View Live' : 'View'}
        </Button>
      )}

      {/* Draft - Delete */}
      {status === 'draft' && onDelete && (
        <Button
          variant="danger"
          size="sm"
          onClick={(e) => {
            e.stopPropagation()
            if (confirm('Delete this draft investigation?')) {
              onDelete()
            }
          }}
        >
          <TrashIcon className="h-4 w-4" />
        </Button>
      )}
    </div>
  )
}

export default InvestigationActions


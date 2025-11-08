import Button from '../common/Button'
import { PauseIcon, ArchiveBoxIcon, TrashIcon } from '@heroicons/react/24/outline'

interface BulkActionsProps {
  selectedIds: Set<string>
  onPause: (ids: string[]) => void
  onArchive: (ids: string[]) => void
  onDelete: (ids: string[]) => void
  onClearSelection: () => void
}

const BulkActions = ({
  selectedIds,
  onPause,
  onArchive,
  onDelete,
  onClearSelection
}: BulkActionsProps) => {
  const selectedArray = Array.from(selectedIds)

  if (selectedIds.size === 0) return null

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <span className="text-sm font-medium text-blue-900">
          {selectedIds.size} investigation{selectedIds.size > 1 ? 's' : ''} selected
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={onClearSelection}
        >
          Clear Selection
        </Button>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            if (confirm(`Pause ${selectedIds.size} investigation(s)?`)) {
              onPause(selectedArray)
            }
          }}
        >
          <PauseIcon className="h-4 w-4 mr-1" />
          Pause All
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            if (confirm(`Archive ${selectedIds.size} investigation(s)?`)) {
              onArchive(selectedArray)
            }
          }}
        >
          <ArchiveBoxIcon className="h-4 w-4 mr-1" />
          Archive All
        </Button>

        <Button
          variant="danger"
          size="sm"
          onClick={() => {
            if (confirm(`Delete ${selectedIds.size} investigation(s)? This action cannot be undone.`)) {
              onDelete(selectedArray)
            }
          }}
        >
          <TrashIcon className="h-4 w-4 mr-1" />
          Delete All
        </Button>
      </div>
    </div>
  )
}

export default BulkActions


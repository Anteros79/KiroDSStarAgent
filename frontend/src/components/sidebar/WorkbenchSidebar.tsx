import { ActiveDatasetPanel } from './ActiveDatasetPanel'
import { ResearchGoalPanel } from './ResearchGoalPanel'
import { DatasetInfo } from '../../types'

interface WorkbenchSidebarProps {
  dataset?: DatasetInfo
  onStartAnalysis: (goal: string) => void
  onExploreNew?: () => void
  onUploadDataset?: () => void
  isAnalyzing: boolean
}

export function WorkbenchSidebar({
  dataset,
  onStartAnalysis,
  onExploreNew,
  onUploadDataset,
  isAnalyzing,
}: WorkbenchSidebarProps) {
  return (
    <div className="flex flex-col h-full">
      <ActiveDatasetPanel dataset={dataset} onUpload={onUploadDataset} />
      <div className="flex-1" />
      <ResearchGoalPanel
        onStartAnalysis={onStartAnalysis}
        onExploreNew={onExploreNew}
        isAnalyzing={isAnalyzing}
        disabled={!dataset}
      />
    </div>
  )
}

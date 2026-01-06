import { AdviceFromFieldTile } from './AdviceFromFieldTile'
import { IndustryFactorsTile } from './IndustryFactorsTile'
import { InvestigationRecord } from '../techops/types'

interface ThingsToConsiderSectionProps {
  investigation: InvestigationRecord | null
  kpiId: string
  station: string
  window: 'weekly' | 'daily'
  onExecuteQuery: (query: string) => void
  isProcessing?: boolean
}

export function ThingsToConsiderSection({
  investigation,
  kpiId,
  station,
  window,
  onExecuteQuery,
  isProcessing = false,
}: ThingsToConsiderSectionProps) {
  const diagnostics = investigation?.diagnostics || []

  return (
    <div className="space-y-4 md:space-y-6">
      {/* Section Header */}
      <div>
        <h2 className="text-lg md:text-xl font-semibold text-slate-900">Things to Consider</h2>
      </div>

      {/* Tiles stacked vertically - single column on all screen sizes */}
      <div className="space-y-3 md:space-y-4">
        <AdviceFromFieldTile
          diagnostics={diagnostics}
          kpiId={kpiId}
          station={station}
          window={window}
          onSelectPrompt={onExecuteQuery}
          isProcessing={isProcessing}
        />
        
        <IndustryFactorsTile
          kpiId={kpiId}
          station={station}
          window={window}
          onSelectFactor={onExecuteQuery}
          isProcessing={isProcessing}
        />
      </div>
    </div>
  )
}
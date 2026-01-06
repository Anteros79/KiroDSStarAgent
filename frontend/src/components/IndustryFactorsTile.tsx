import { ClipboardList } from 'lucide-react'
import { SuggestionChip } from './SuggestionChip'
import { getRelevantFactors } from '../config/industryFactorsConfig'

interface IndustryFactorsTileProps {
  kpiId: string
  station: string
  window: 'weekly' | 'daily'
  onSelectFactor: (query: string) => void
  isProcessing?: boolean
}

export function IndustryFactorsTile({
  kpiId,
  station,
  window,
  onSelectFactor,
  isProcessing = false,
}: IndustryFactorsTileProps) {
  const relevantFactors = getRelevantFactors(kpiId)

  // Generate queries from factor templates with context interpolation
  const factorChips = relevantFactors.map((factor) => {
    const query = factor.queryTemplate
      .replace(/{kpi}/g, kpiId)
      .replace(/{station}/g, station)
      .replace(/{window}/g, window)

    return {
      id: factor.id,
      label: factor.label,
      query,
      description: factor.description,
    }
  })

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 md:p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-start gap-3 mb-3 md:mb-4">
        <div className="flex items-center justify-center w-8 h-8 md:w-10 md:h-10 bg-blue-100 rounded-lg flex-shrink-0">
          <ClipboardList className="w-4 h-4 md:w-5 md:h-5 text-blue-600" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-base md:text-lg font-semibold text-slate-900">Common Industry Causal Factors</h3>
          <p className="text-xs md:text-sm text-slate-600 mt-1">
            Standard factors to check during root cause analysis
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="space-y-3">
        {factorChips.length > 0 ? (
          <div className="flex flex-wrap gap-1.5 md:gap-2">
            {factorChips.map((chip) => (
              <SuggestionChip
                key={chip.id}
                label={chip.label}
                query={chip.query}
                onClick={onSelectFactor}
                isLoading={isProcessing}
                disabled={isProcessing}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-6 md:py-8">
            <div className="flex items-center justify-center w-10 h-10 md:w-12 md:h-12 bg-slate-100 rounded-lg mx-auto mb-2 md:mb-3">
              <ClipboardList className="w-5 h-5 md:w-6 md:h-6 text-slate-400" />
            </div>
            <p className="text-xs md:text-sm text-slate-500 px-4">
              No industry factors available for this KPI.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
import { Lightbulb } from 'lucide-react'
import { SuggestionChip } from './SuggestionChip'
import { generateFieldAdvice } from '../services/fieldAdviceGenerator'
import { InvestigationDiagnostic } from '../techops/types'

interface AdviceFromFieldTileProps {
  diagnostics: InvestigationDiagnostic[]
  kpiId: string
  station: string
  window: 'weekly' | 'daily'
  onSelectPrompt: (query: string) => void
  isProcessing?: boolean
}

export function AdviceFromFieldTile({
  diagnostics,
  kpiId,
  station,
  window,
  onSelectPrompt,
  isProcessing = false,
}: AdviceFromFieldTileProps) {
  const suggestions = generateFieldAdvice(diagnostics, kpiId, station, window)

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 md:p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-start gap-3 mb-3 md:mb-4">
        <div className="flex items-center justify-center w-8 h-8 md:w-10 md:h-10 bg-yellow-100 rounded-lg flex-shrink-0">
          <Lightbulb className="w-4 h-4 md:w-5 md:h-5 text-yellow-600" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-base md:text-lg font-semibold text-slate-900">Advice from the Field</h3>
          <p className="text-xs md:text-sm text-slate-600 mt-1">
            Suggestions based on similar conditions from other stations
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="space-y-3">
        {suggestions.length > 0 ? (
          <div className="flex flex-wrap gap-1.5 md:gap-2">
            {suggestions.map((suggestion) => (
              <SuggestionChip
                key={suggestion.id}
                label={suggestion.label}
                query={suggestion.query}
                onClick={onSelectPrompt}
                isLoading={isProcessing}
                disabled={isProcessing}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-6 md:py-8">
            <div className="flex items-center justify-center w-10 h-10 md:w-12 md:h-12 bg-slate-100 rounded-lg mx-auto mb-2 md:mb-3">
              <Lightbulb className="w-5 h-5 md:w-6 md:h-6 text-slate-400" />
            </div>
            <p className="text-xs md:text-sm text-slate-500 px-4">
              No field suggestions available yet. Run an analysis to generate suggestions.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
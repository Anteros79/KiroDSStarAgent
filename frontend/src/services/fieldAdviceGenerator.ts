import { FieldAdviceSuggestion } from '../types/thingsToConsider'
import { InvestigationDiagnostic } from '../techops/types'

/**
 * Generates field advice suggestions based on investigation diagnostics
 * @param diagnostics Array of investigation diagnostics
 * @param kpiId The KPI identifier
 * @param station The station identifier
 * @param window The time window (weekly or daily)
 * @returns Array of field advice suggestions
 */
export function generateFieldAdvice(
  diagnostics: InvestigationDiagnostic[],
  kpiId: string,
  station: string,
  _window: 'weekly' | 'daily'
): FieldAdviceSuggestion[] {
  const suggestions: FieldAdviceSuggestion[] = []
  
  for (const diag of diagnostics) {
    // Stage change suggestions
    if (diag.stage_change) {
      suggestions.push({
        id: `stage_${diag.name}`,
        label: `What changed when the stage shifted?`,
        query: `The SPC chart shows a stage change around ${diag.selected_t}. What operational changes occurred at ${station} at that time that could explain the ${kpiId} shift?`,
        source: 'stage_change',
        confidence: diag.confidence,
      })
    }
    
    // YoY delta suggestions
    if (diag.yoy_delta !== undefined && diag.yoy_delta !== null && Math.abs(diag.yoy_delta) > 0.05) {
      const direction = diag.yoy_delta > 0 ? 'increase' : 'decrease'
      suggestions.push({
        id: `yoy_${diag.name}`,
        label: `Why the ${Math.abs(diag.yoy_delta * 100).toFixed(0)}% YoY ${direction}?`,
        query: `${kpiId} shows a ${Math.abs(diag.yoy_delta * 100).toFixed(1)}% year-over-year ${direction} at ${station}. What factors explain this change compared to last year?`,
        source: 'yoy_delta',
        confidence: diag.confidence,
      })
    }
    
    // Peer comparison suggestions
    if (diag.peer_mean !== undefined && diag.peer_mean !== null && diag.selected_value !== undefined && diag.selected_value !== null) {
      const diff = diag.selected_value - diag.peer_mean
      if (Math.abs(diff) > 0.02) {
        const comparison = diff > 0 ? 'above' : 'below'
        suggestions.push({
          id: `peer_${diag.name}`,
          label: `Why different from peer stations?`,
          query: `${station} is performing ${comparison} peer average for ${kpiId}. What factors at ${station} differ from peer stations that could explain this?`,
          source: 'peer_comparison',
          confidence: diag.confidence,
        })
      }
    }
    
    // Signal pattern suggestions for other diagnostic findings
    if (diag.finding && !diag.stage_change && (diag.yoy_delta === undefined || Math.abs(diag.yoy_delta) <= 0.05)) {
      suggestions.push({
        id: `signal_${diag.name}`,
        label: `Investigate ${diag.name} finding`,
        query: `The analysis shows: ${diag.finding}. What could be causing this pattern in ${kpiId} at ${station}?`,
        source: 'signal_pattern',
        confidence: diag.confidence,
      })
    }
  }
  
  // Remove duplicates and sort by confidence (highest first)
  const uniqueSuggestions = suggestions.filter((suggestion, index, self) => 
    index === self.findIndex(s => s.query === suggestion.query)
  )
  
  return uniqueSuggestions.sort((a, b) => (b.confidence || 0) - (a.confidence || 0))
}
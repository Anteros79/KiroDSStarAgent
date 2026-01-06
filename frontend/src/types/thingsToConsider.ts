// Types for Things to Consider feature

export interface FieldAdviceSuggestion {
  id: string
  label: string
  query: string
  source: 'stage_change' | 'yoy_delta' | 'peer_comparison' | 'signal_pattern'
  confidence?: number
  relatedStation?: string
}

export interface IndustryFactor {
  id: string
  category: string
  label: string
  description: string
  queryTemplate: string
  relevantKpis: string[]
  priority: number
}
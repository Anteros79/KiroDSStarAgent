export type SignalState = 'none' | 'warning' | 'critical'

export interface DemoIdentity {
  id: string
  name: string
  role: string
  station: string
}

export interface TechOpsKPI {
  id: string
  label: string
  unit: string
  goal: number
  ul: number
  ll: number
  decimals: number
}

export interface TechOpsMetricPoint {
  t: string // ISO date or week start
  value: number
  yoy_value?: number | null
  yoy_delta?: number | null
  signal_state: SignalState
}

export interface TechOpsKPISeries {
  kpi: TechOpsKPI
  points: TechOpsMetricPoint[]
  mean: number
  past_value: number
  past_delta: number
  signal_state: SignalState
}

export interface TechOpsDashboardResponse {
  station: string
  window: 'weekly' | 'daily'
  kpis: TechOpsKPISeries[]
}

export interface ActiveSignalsResponse {
  station: string
  signals: Array<{
    signal_id: string
    kpi_id: string
    station: string
    status: SignalState
    detected_at: string
    latest_value: number
  }>
}

export interface CreateInvestigationRequest {
  kpi_id: string
  station: string
  window: 'weekly' | 'daily'
  point_t?: string
}

export interface CreateInvestigationResponse {
  investigation_id: string
  prompt_mode: 'cause' | 'yoy'
  prompt: string
}

export interface InvestigationRecord {
  investigation_id: string
  kpi_id: string
  station: string
  window: 'weekly' | 'daily'
  created_by: DemoIdentity
  created_at: string
  status: string
  prompt_mode: 'cause' | 'yoy'
  prompt: string
  selected_point_t?: string | null
}



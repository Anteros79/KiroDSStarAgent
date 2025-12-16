import {
  ActiveSignalsResponse,
  CreateInvestigationRequest,
  CreateInvestigationResponse,
  DemoIdentity,
  FinalizeInvestigationRequest,
  InvestigationRecord,
  TechOpsDashboardResponse,
  TechOpsKPI,
} from './types'

const API_BASE = '/api'

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }))
    throw new Error(error.message || `HTTP ${response.status}`)
  }

  return response.json()
}

export const techOpsApi = {
  // Identity
  getMe(): Promise<DemoIdentity> {
    return request<DemoIdentity>('/me')
  },

  selectMe(identity_id: string): Promise<DemoIdentity> {
    return request<DemoIdentity>('/me/select', {
      method: 'POST',
      body: JSON.stringify({ identity_id }),
    })
  },

  // Data
  getKPIs(): Promise<TechOpsKPI[]> {
    return request<TechOpsKPI[]>('/techops/kpis')
  },

  getDashboardWeekly(station: string): Promise<TechOpsDashboardResponse> {
    return request<TechOpsDashboardResponse>(`/techops/dashboard/weekly?station=${encodeURIComponent(station)}`)
  },

  getDashboardDaily(station: string): Promise<TechOpsDashboardResponse> {
    return request<TechOpsDashboardResponse>(`/techops/dashboard/daily?station=${encodeURIComponent(station)}`)
  },

  getActiveSignals(station: string): Promise<ActiveSignalsResponse> {
    return request<ActiveSignalsResponse>(`/techops/signals/active?station=${encodeURIComponent(station)}`)
  },

  // Investigations
  createInvestigation(payload: CreateInvestigationRequest): Promise<CreateInvestigationResponse> {
    return request<CreateInvestigationResponse>('/techops/investigations', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  listInvestigations(station?: string): Promise<InvestigationRecord[]> {
    const qs = station ? `?station=${encodeURIComponent(station)}` : ''
    return request<InvestigationRecord[]>(`/techops/investigations${qs}`)
  },

  getInvestigation(investigation_id: string): Promise<InvestigationRecord> {
    return request<InvestigationRecord>(`/techops/investigations/${encodeURIComponent(investigation_id)}`)
  },

  finalizeInvestigation(investigation_id: string, payload: FinalizeInvestigationRequest): Promise<InvestigationRecord> {
    return request<InvestigationRecord>(`/techops/investigations/${encodeURIComponent(investigation_id)}/finalize`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}



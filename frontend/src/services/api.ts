import { SystemStatus, AnalysisState } from '../types'

const API_BASE = '/api'

class APIService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
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

  async getStatus(): Promise<SystemStatus> {
    return this.request<SystemStatus>('/status')
  }

  async startAnalysis(researchGoal: string, datasetPath?: string): Promise<{ analysis_id: string }> {
    return this.request('/analyze', {
      method: 'POST',
      body: JSON.stringify({
        research_goal: researchGoal,
        dataset_path: datasetPath,
      }),
    })
  }

  async getAnalysis(analysisId: string): Promise<AnalysisState> {
    return this.request<AnalysisState>(`/analysis/${analysisId}`)
  }

  async approveStep(analysisId: string, stepId: string, iterationId: string): Promise<void> {
    return this.request(`/analysis/${analysisId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ step_id: stepId, iteration_id: iterationId }),
    })
  }

  async refineStep(
    analysisId: string, 
    stepId: string, 
    iterationId: string, 
    feedback: string
  ): Promise<void> {
    return this.request(`/analysis/${analysisId}/refine`, {
      method: 'POST',
      body: JSON.stringify({ step_id: stepId, iteration_id: iterationId, feedback }),
    })
  }
}

export const apiService = new APIService()

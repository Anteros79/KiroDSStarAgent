// Investigation workflow types

export interface Investigation {
  id: string
  measureName: string
  hypothesis: string
  createdAt: Date
  updatedAt: Date
  status: 'active' | 'completed' | 'archived'
  steps: InvestigationStep[]
  notes: string
  finalAnalysis?: string
  conclusion?: string
}

export interface InvestigationStep {
  id: string
  stepNumber: number
  query: string
  iterations: StepIteration[]
  status: 'pending' | 'running' | 'approved' | 'declined'
  approvedIterationId?: string
  notes: string
  createdAt: Date
}

export interface StepIteration {
  id: string
  iterationNumber: number
  timestamp: Date
  description: string
  generatedCode: string
  response: string
  visualization?: ChartData
  verification: VerificationResult
  status: 'pending' | 'generating' | 'executing' | 'verifying' | 'verified' | 'failed'
  feedback?: string
}

export interface ChartData {
  chart_type: string
  title: string
  plotly_json: any
}

export interface VerificationResult {
  passed: boolean
  assessment: string
  suggestions?: string[]
}

// Actions for investigation workflow
export type InvestigationAction =
  | { type: 'START_INVESTIGATION'; measureName: string }
  | { type: 'ADD_STEP'; query: string }
  | { type: 'START_ITERATION'; stepId: string }
  | { type: 'UPDATE_ITERATION'; stepId: string; iterationId: string; updates: Partial<StepIteration> }
  | { type: 'APPROVE_STEP'; stepId: string; iterationId: string }
  | { type: 'DECLINE_STEP'; stepId: string; iterationId: string; feedback: string }
  | { type: 'UPDATE_NOTES'; notes: string }
  | { type: 'SET_FINAL_ANALYSIS'; analysis: string; conclusion: string }
  | { type: 'COMPLETE_INVESTIGATION' }
  | { type: 'LOAD_INVESTIGATION'; investigation: Investigation }

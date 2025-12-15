// Model provider options
export type ModelProvider = 'ollama' | 'bedrock'

export interface ModelConfig {
  provider: ModelProvider
  model_id: string
  host?: string  // For Ollama
  region?: string  // For Bedrock
}

// System status
export interface SystemStatus {
  status: 'ready' | 'initializing' | 'error'
  model: string
  region: string
  specialists: string[]
  data_loaded: boolean
  dataset_info?: DatasetInfo
}

// Dataset information
export interface DatasetInfo {
  filename: string
  description: string
  columns: ColumnInfo[]
  rowCount: number
}

export interface ColumnInfo {
  name: string
  dtype: string
}

// Analysis state
export interface AnalysisState {
  id: string
  researchGoal: string
  dataset: DatasetInfo
  steps: AnalysisStep[]
  status: 'idle' | 'running' | 'completed' | 'error'
  startedAt: Date
  completedAt?: Date
}

export interface AnalysisStep {
  id: string
  stepNumber: number
  iterations: Iteration[]
  status: 'pending' | 'running' | 'completed'
}

export interface Iteration {
  id: string
  iterationNumber: number
  timestamp: Date
  description: string
  generatedCode: string
  executionOutput: ExecutionResult
  visualization?: ChartSpec
  verification: VerificationResult
  status: 'pending' | 'generating' | 'executing' | 'verifying' | 'verified' | 'failed'
}

export interface ExecutionResult {
  success: boolean
  output: string
  error?: string
  duration_ms: number
}

export interface ChartSpec {
  chart_type: string
  title: string
  plotly_json: any
}

export interface VerificationResult {
  passed: boolean
  assessment: string
  suggestions?: string[]
}

// Legacy types for backward compatibility
export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  routing?: string[]
  execution_time_ms?: number
  charts?: ChartData[]
  events?: StreamEvent[]
}

export interface StreamEvent {
  type: 'agent_start' | 'routing' | 'tool_start' | 'tool_end' | 'agent_end' | 'query_start' | 'response' | 'error'
  data: any
  timestamp: string
}

export interface ChartData {
  chart_type: string
  title: string
  data: any[]
  x_axis?: AxisConfig
  y_axis?: AxisConfig
  styling?: any
  plotly_json?: any
  matplotlib_code?: string
}

export interface AxisConfig {
  label: string
  type?: string
}

// WebSocket events
export interface WSEvent {
  type: string
  data: any
}

export interface CodeGeneratedEvent {
  type: 'code_generated'
  step_id: string
  iteration_id: string
  code: string
}

export interface ExecutionCompleteEvent {
  type: 'execution_complete'
  step_id: string
  iteration_id: string
  output: ExecutionResult
}

export interface VisualizationReadyEvent {
  type: 'visualization_ready'
  step_id: string
  iteration_id: string
  chart: ChartSpec
}

export interface VerificationCompleteEvent {
  type: 'verification_complete'
  step_id: string
  iteration_id: string
  result: VerificationResult
}

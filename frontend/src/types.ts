export interface SystemStatus {
  status: string
  model: string
  region: string
  specialists: string[]
  data_loaded: boolean
}

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

export interface QueryRequest {
  query: string
  context?: Record<string, any>
}

export interface QueryResponse {
  response: string
  routing: string[]
  execution_time_ms: number
  charts?: ChartData[]
}

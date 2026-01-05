import { useState } from 'react'
import { ChevronDown, ChevronUp, AlertTriangle, CheckCircle2, XCircle, HelpCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react'

export interface DiagnosticResult {
  name: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | string
  confidence?: number
  detail?: string
  finding?: string
  selected_t?: string
  selected_value?: number
  ucl?: number
  lcl?: number
  cl?: number
  yoy_delta?: number
  peer_mean?: number
  pre_mean?: number
  post_mean?: number
  delta?: number
  known_demo_root_cause?: string
  stage_change?: boolean
  mr_signal?: boolean
}

interface DiagnosticPillsProps {
  diagnostics: DiagnosticResult[]
  title?: string
}

export function DiagnosticPills({ diagnostics, title = 'DS‑STAR Diagnostics' }: DiagnosticPillsProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  if (!diagnostics || diagnostics.length === 0) {
    return null
  }

  // Deduplicate by name
  const uniqueDiagnostics = Array.from(
    new Map(diagnostics.map((d) => [d.name, d])).values()
  )

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="text-sm font-extrabold text-slate-900">{title}</div>
        <div className="text-xs text-slate-500">
          {uniqueDiagnostics.filter(d => d.status === 'completed').length}/{uniqueDiagnostics.length} completed
        </div>
      </div>
      <div className="text-xs text-slate-500">Automated diagnostic tests for this investigation</div>
      
      <div className="space-y-1.5 mt-3">
        {uniqueDiagnostics.map((diagnostic) => (
          <DiagnosticPill
            key={diagnostic.name}
            diagnostic={diagnostic}
            isExpanded={expandedId === diagnostic.name}
            onToggle={() => setExpandedId(expandedId === diagnostic.name ? null : diagnostic.name)}
          />
        ))}
      </div>
    </div>
  )
}

function getConfidenceConfig(confidence?: number) {
  if (confidence === undefined || confidence === null) {
    return { color: 'slate', bg: 'bg-slate-100', border: 'border-slate-200', text: 'text-slate-600', label: 'Pending' }
  }
  
  const pct = confidence * 100
  
  if (pct >= 85) {
    return { color: 'emerald', bg: 'bg-emerald-50', border: 'border-emerald-300', text: 'text-emerald-700', label: 'High' }
  }
  if (pct >= 65) {
    return { color: 'blue', bg: 'bg-blue-50', border: 'border-blue-300', text: 'text-blue-700', label: 'Medium' }
  }
  if (pct >= 40) {
    return { color: 'amber', bg: 'bg-amber-50', border: 'border-amber-300', text: 'text-amber-700', label: 'Low' }
  }
  return { color: 'rose', bg: 'bg-rose-50', border: 'border-rose-300', text: 'text-rose-700', label: 'Very Low' }
}

function getStatusIcon(status: string, confidence?: number) {
  if (status === 'pending' || status === 'in_progress') {
    return <HelpCircle className="w-4 h-4 text-slate-400" />
  }
  if (status === 'failed') {
    return <XCircle className="w-4 h-4 text-rose-500" />
  }
  
  // Completed - use confidence-based icon
  const pct = (confidence ?? 0) * 100
  if (pct >= 65) {
    return <CheckCircle2 className="w-4 h-4 text-emerald-500" />
  }
  if (pct >= 40) {
    return <AlertTriangle className="w-4 h-4 text-amber-500" />
  }
  return <XCircle className="w-4 h-4 text-rose-500" />
}

function formatTestName(name: string): string {
  return name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function DiagnosticPill({
  diagnostic,
  isExpanded,
  onToggle,
}: {
  diagnostic: DiagnosticResult
  isExpanded: boolean
  onToggle: () => void
}) {
  const config = getConfidenceConfig(diagnostic.confidence)
  const confidencePct = diagnostic.confidence !== undefined ? Math.round(diagnostic.confidence * 100) : null

  return (
    <div className={`rounded-lg border ${config.border} ${config.bg} overflow-hidden transition-all`}>
      {/* Collapsed Pill */}
      <div
        className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-white/50 transition-colors"
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          onToggle()
        }}
      >
        {getStatusIcon(diagnostic.status, diagnostic.confidence)}
        
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-slate-900 truncate">
            {formatTestName(diagnostic.name)}
          </div>
        </div>

        {/* Confidence Badge */}
        {confidencePct !== null && (
          <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${config.bg} ${config.text} border ${config.border}`}>
            {confidencePct}% {config.label}
          </span>
        )}

        {diagnostic.status === 'in_progress' && (
          <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-700 border border-blue-200 animate-pulse">
            Running...
          </span>
        )}

        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-slate-400 flex-shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0" />
        )}
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <ExpandedContent diagnostic={diagnostic} />
      )}
    </div>
  )
}

function ExpandedContent({ diagnostic }: { diagnostic: DiagnosticResult }) {
  try {
    return (
      <div className="px-3 pb-3 pt-1 border-t border-slate-200/50 bg-white/80 space-y-2">
        {/* Finding */}
        {diagnostic.finding && (
          <div>
            <div className="text-xs font-bold text-slate-500 uppercase mb-1">Finding</div>
            <p className="text-sm text-slate-800">{diagnostic.finding}</p>
          </div>
        )}

        {/* Detail */}
        {diagnostic.detail && (
          <div>
            <div className="text-xs font-bold text-slate-500 uppercase mb-1">Detail</div>
            <p className="text-sm text-slate-700">{diagnostic.detail}</p>
          </div>
        )}

        {/* Known Root Cause (Demo) */}
        {diagnostic.known_demo_root_cause && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-2">
            <div className="text-xs font-bold text-amber-700 uppercase mb-1">Identified Root Cause</div>
            <p className="text-sm font-semibold text-amber-900">{diagnostic.known_demo_root_cause}</p>
          </div>
        )}

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2">
          {diagnostic.selected_value !== undefined && diagnostic.selected_value !== null && !isNaN(Number(diagnostic.selected_value)) && (
            <MetricBox label="Selected Value" value={Number(diagnostic.selected_value).toFixed(2)} />
          )}
          {diagnostic.cl !== undefined && diagnostic.cl !== null && !isNaN(Number(diagnostic.cl)) && (
            <MetricBox label="Center Line" value={Number(diagnostic.cl).toFixed(2)} />
          )}
          {diagnostic.ucl !== undefined && diagnostic.ucl !== null && !isNaN(Number(diagnostic.ucl)) && (
            <MetricBox label="UCL" value={Number(diagnostic.ucl).toFixed(2)} trend="up" />
          )}
          {diagnostic.lcl !== undefined && diagnostic.lcl !== null && !isNaN(Number(diagnostic.lcl)) && (
            <MetricBox label="LCL" value={Number(diagnostic.lcl).toFixed(2)} trend="down" />
          )}
          {diagnostic.yoy_delta !== undefined && diagnostic.yoy_delta !== null && !isNaN(Number(diagnostic.yoy_delta)) && (
            <MetricBox 
              label="YoY Delta" 
              value={`${Number(diagnostic.yoy_delta) >= 0 ? '+' : ''}${Number(diagnostic.yoy_delta).toFixed(2)}`}
              trend={Number(diagnostic.yoy_delta) > 0 ? 'up' : Number(diagnostic.yoy_delta) < 0 ? 'down' : 'neutral'}
            />
          )}
          {diagnostic.peer_mean !== undefined && diagnostic.peer_mean !== null && !isNaN(Number(diagnostic.peer_mean)) && (
            <MetricBox label="Peer Mean" value={Number(diagnostic.peer_mean).toFixed(2)} />
          )}
          {diagnostic.delta !== undefined && diagnostic.delta !== null && !isNaN(Number(diagnostic.delta)) && (
            <MetricBox 
              label="Pre/Post Delta" 
              value={`${Number(diagnostic.delta) >= 0 ? '+' : ''}${Number(diagnostic.delta).toFixed(2)}`}
              trend={Number(diagnostic.delta) > 0 ? 'up' : Number(diagnostic.delta) < 0 ? 'down' : 'neutral'}
            />
          )}
        </div>

        {/* Flags */}
        <div className="flex flex-wrap gap-2 mt-2">
          {diagnostic.stage_change && (
            <span className="px-2 py-1 rounded-full text-xs font-bold bg-purple-100 text-purple-700 border border-purple-200">
              Stage Change Detected
            </span>
          )}
          {diagnostic.mr_signal && (
            <span className="px-2 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-700 border border-rose-200">
              MR Signal (Volatility)
            </span>
          )}
        </div>
      </div>
    )
  } catch (error) {
    console.error('Error rendering diagnostic expanded content:', error)
    return (
      <div className="px-3 pb-3 pt-1 border-t border-slate-200/50 bg-white/80">
        <p className="text-sm text-red-600">Error displaying diagnostic details</p>
      </div>
    )
  }
}

function MetricBox({ 
  label, 
  value, 
  trend 
}: { 
  label: string
  value: string
  trend?: 'up' | 'down' | 'neutral'
}) {
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus
  const trendColor = trend === 'up' ? 'text-rose-500' : trend === 'down' ? 'text-emerald-500' : 'text-slate-400'

  return (
    <div className="bg-slate-50 rounded-lg p-2">
      <div className="text-xs text-slate-500 font-medium">{label}</div>
      <div className="flex items-center gap-1">
        <span className="text-sm font-bold text-slate-900">{value}</span>
        {trend && <TrendIcon className={`w-3 h-3 ${trendColor}`} />}
      </div>
    </div>
  )
}

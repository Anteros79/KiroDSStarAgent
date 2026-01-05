import { useState } from 'react'
import { ChevronDown, ChevronUp, CheckCircle2, XCircle, Clock, BarChart3, Code2, FileText } from 'lucide-react'
import { ChartDisplay } from '../../components/content/ChartDisplay'
import { CodeDisplay } from '../../components/content/CodeDisplay'

export interface StepPillData {
  id: string
  stepNumber: number
  hypothesis: string
  status: 'pending' | 'running' | 'approved' | 'declined' | 'completed'
  includeInReport: boolean
  iterations: Array<{
    id: string
    iterationNumber: number
    response?: string
    generatedCode?: string
    visualization?: any
    status: string
  }>
}

interface StepPillsProps {
  steps: StepPillData[]
  onToggleInclude: (stepId: string, include: boolean) => void
  onStepClick?: (stepId: string) => void
}

export function StepPills({ steps, onToggleInclude, onStepClick }: StepPillsProps) {
  const [expandedStepId, setExpandedStepId] = useState<string | null>(null)

  if (steps.length === 0) {
    return null
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          Research Steps ({steps.length})
        </div>
        <div className="text-xs text-slate-500">
          {steps.filter(s => s.includeInReport).length} included in report
        </div>
      </div>
      
      <div className="space-y-1.5">
        {steps.map((step) => (
          <StepPill
            key={step.id}
            step={step}
            isExpanded={expandedStepId === step.id}
            onToggleExpand={() => setExpandedStepId(expandedStepId === step.id ? null : step.id)}
            onToggleInclude={(include) => onToggleInclude(step.id, include)}
            onClick={() => onStepClick?.(step.id)}
          />
        ))}
      </div>
    </div>
  )
}

function StepPill({
  step,
  isExpanded,
  onToggleExpand,
  onToggleInclude,
  onClick: _onClick,
}: {
  step: StepPillData
  isExpanded: boolean
  onToggleExpand: () => void
  onToggleInclude: (include: boolean) => void
  onClick?: () => void
}) {
  // Note: onClick is available for future use
  void _onClick
  const statusConfig = {
    pending: { icon: Clock, color: 'text-slate-400', bg: 'bg-slate-100', border: 'border-slate-200' },
    running: { icon: Clock, color: 'text-blue-500', bg: 'bg-blue-50', border: 'border-blue-200' },
    approved: { icon: CheckCircle2, color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' },
    declined: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-50', border: 'border-red-200' },
    completed: { icon: CheckCircle2, color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' },
  }

  const config = statusConfig[step.status] || statusConfig.pending
  const StatusIcon = config.icon
  const latestIteration = step.iterations[step.iterations.length - 1]
  const hasChart = latestIteration?.visualization
  const hasCode = latestIteration?.generatedCode

  return (
    <div className={`rounded-lg border ${config.border} ${config.bg} overflow-hidden transition-all`}>
      {/* Collapsed Pill View */}
      <div
        className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-white/50 transition-colors"
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          onToggleExpand()
        }}
      >
        <StatusIcon className={`w-4 h-4 ${config.color} flex-shrink-0`} />
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-500">STEP {step.stepNumber}</span>
            {hasChart && <BarChart3 className="w-3 h-3 text-purple-500" aria-label="Has visualization" />}
            {hasCode && <Code2 className="w-3 h-3 text-blue-500" aria-label="Has code" />}
          </div>
          <p className="text-sm text-slate-900 truncate">{step.hypothesis}</p>
        </div>

        {/* Include Toggle */}
        <label
          className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-white border border-slate-200 cursor-pointer hover:border-slate-300"
          onClick={(e) => e.stopPropagation()}
        >
          <input
            type="checkbox"
            checked={step.includeInReport}
            onChange={(e) => onToggleInclude(e.target.checked)}
            className="w-3.5 h-3.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-xs font-medium text-slate-600">Include</span>
        </label>

        {/* Expand/Collapse */}
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-slate-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-slate-400" />
        )}
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-3 pb-3 pt-1 border-t border-slate-200/50 bg-white/80 space-y-3">
          {/* Hypothesis */}
          <div>
            <div className="text-xs font-bold text-slate-500 uppercase mb-1">Hypothesis Tested</div>
            <p className="text-sm text-slate-800">{step.hypothesis}</p>
          </div>

          {/* Iterations */}
          {step.iterations.map((iteration) => (
            <div key={iteration.id} className="space-y-2">
              {/* Response */}
              {iteration.response && (
                <div>
                  <div className="flex items-center gap-1.5 mb-1">
                    <FileText className="w-3 h-3 text-slate-400" />
                    <span className="text-xs font-bold text-slate-500">FINDINGS</span>
                  </div>
                  <div className="text-sm text-slate-700 bg-slate-50 rounded-lg p-2 max-h-32 overflow-y-auto">
                    {iteration.response}
                  </div>
                </div>
              )}

              {/* Code */}
              {iteration.generatedCode && (
                <div>
                  <div className="flex items-center gap-1.5 mb-1">
                    <Code2 className="w-3 h-3 text-blue-500" />
                    <span className="text-xs font-bold text-slate-500">ANALYSIS CODE</span>
                  </div>
                  <div className="max-h-40 overflow-hidden rounded-lg">
                    <CodeDisplay code={iteration.generatedCode} language="python" />
                  </div>
                </div>
              )}

              {/* Visualization */}
              {iteration.visualization && (
                <div>
                  <div className="flex items-center gap-1.5 mb-1">
                    <BarChart3 className="w-3 h-3 text-purple-500" />
                    <span className="text-xs font-bold text-slate-500">VISUALIZATION</span>
                  </div>
                  <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
                    <ChartDisplay chart={iteration.visualization} />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

import { AnalysisStep } from '../../types'
import { StepCard } from './StepCard'
import { FileSearch } from 'lucide-react'

interface AnalysisTimelineProps {
  steps: AnalysisStep[]
  onApprove: (stepId: string, iterationId: string) => void
  onDecline: (stepId: string, iterationId: string, feedback: string) => void
}

export function AnalysisTimeline({ steps, onApprove, onDecline }: AnalysisTimelineProps) {
  if (steps.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-400">
        <FileSearch className="w-16 h-16 mb-4 opacity-50" />
        <h3 className="text-lg font-medium text-slate-600 mb-2">No Analysis Yet</h3>
        <p className="text-sm text-center max-w-md">
          Enter a research goal in the sidebar and click "Start Analysis" to begin your iterative data science workflow.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Timeline header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-slate-900">Analysis Timeline</h2>
        <span className="text-sm text-slate-500 bg-slate-100 px-3 py-1 rounded-full">
          {steps.length} {steps.length === 1 ? 'Step' : 'Steps'}
        </span>
      </div>

      {/* Steps */}
      <div className="space-y-4">
        {steps.map((step) => (
          <StepCard
            key={step.id}
            step={step}
            onApprove={onApprove}
            onDecline={onDecline}
          />
        ))}
      </div>
    </div>
  )
}

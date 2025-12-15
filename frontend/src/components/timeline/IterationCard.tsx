import { Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { Iteration } from '../../types'
import { CodeDisplay } from '../content/CodeDisplay'
import { AgentResponse } from '../content/AgentResponse'
import { ChartDisplay } from '../content/ChartDisplay'
import { VerifierAssessment } from '../content/VerifierAssessment'

interface IterationCardProps {
  iteration: Iteration
  onApprove: () => void
  onDecline: (feedback: string) => void
}

export function IterationCard({ iteration, onApprove, onDecline }: IterationCardProps) {
  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    })
  }

  const statusBadge = {
    verified: (
      <span className="pill-success flex items-center gap-1">
        <CheckCircle className="w-3 h-3" />
        Verified
      </span>
    ),
    failed: (
      <span className="pill-error flex items-center gap-1">
        <XCircle className="w-3 h-3" />
        Failed
      </span>
    ),
    pending: null,
    generating: (
      <span className="pill flex items-center gap-1">
        <Loader2 className="w-3 h-3 animate-spin" />
        Generating...
      </span>
    ),
    executing: (
      <span className="pill flex items-center gap-1">
        <Loader2 className="w-3 h-3 animate-spin" />
        Executing...
      </span>
    ),
    verifying: (
      <span className="pill flex items-center gap-1">
        <Loader2 className="w-3 h-3 animate-spin" />
        Verifying...
      </span>
    ),
  }

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden bg-white">
      {/* Iteration header */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-slate-700">
            ITERATION {iteration.iterationNumber}
          </span>
          <span className="flex items-center gap-1 text-xs text-slate-500">
            <Clock className="w-3 h-3" />
            {formatTime(iteration.timestamp)}
          </span>
        </div>
        {statusBadge[iteration.status]}
      </div>

      {/* Iteration content */}
      <div className="p-4 space-y-4">
        {/* Description */}
        <p className="text-slate-700 font-medium">{iteration.description}</p>

        {/* Generated code */}
        {iteration.generatedCode && (
          <div>
            <h4 className="text-sm font-semibold text-slate-600 mb-2">Generated Python Code</h4>
            <CodeDisplay code={iteration.generatedCode} language="python" />
          </div>
        )}

        {/* Agent Response with formatted output and auto-charts */}
        {iteration.executionOutput && (
          <div>
            <h4 className="text-sm font-semibold text-slate-600 mb-2">Agent Response</h4>
            <AgentResponse 
              output={iteration.executionOutput.output}
              success={iteration.executionOutput.success}
              duration_ms={iteration.executionOutput.duration_ms}
              error={iteration.executionOutput.error}
            />
          </div>
        )}

        {/* Visualization */}
        {iteration.visualization && (
          <div>
            <h4 className="text-sm font-semibold text-slate-600 mb-2">
              {iteration.visualization.title}
            </h4>
            <ChartDisplay chart={iteration.visualization} />
          </div>
        )}

        {/* Verifier assessment */}
        {iteration.verification && (
          <VerifierAssessment
            verification={iteration.verification}
            onApprove={onApprove}
            onDecline={onDecline}
            showActions={iteration.status === 'verifying' || iteration.status === 'verified' || iteration.status === 'failed'}
          />
        )}
      </div>
    </div>
  )
}

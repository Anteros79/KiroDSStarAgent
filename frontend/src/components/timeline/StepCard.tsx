import { useState } from 'react'
import { ChevronDown, ChevronRight, Loader2, CheckCircle2, Circle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { AnalysisStep } from '../../types'
import { IterationCard } from './IterationCard'
import clsx from 'clsx'

interface StepCardProps {
  step: AnalysisStep
  onApprove: (stepId: string, iterationId: string) => void
  onDecline: (stepId: string, iterationId: string, feedback: string) => void
}

export function StepCard({ step, onApprove, onDecline }: StepCardProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  const statusIcon = {
    pending: <Circle className="w-5 h-5 text-slate-400" />,
    running: <Loader2 className="w-5 h-5 text-primary animate-spin" />,
    completed: <CheckCircle2 className="w-5 h-5 text-success" />,
  }

  return (
    <div className="card-elevated">
      {/* Step header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-2 -m-2 rounded-lg hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          {statusIcon[step.status]}
          <span className="font-semibold text-slate-900">
            STEP {step.stepNumber} DETAILS
          </span>
          <span className={clsx(
            'text-xs px-2 py-0.5 rounded-full',
            step.status === 'completed' && 'bg-success/10 text-success',
            step.status === 'running' && 'bg-primary/10 text-primary',
            step.status === 'pending' && 'bg-slate-100 text-slate-500'
          )}>
            {step.status}
          </span>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-5 h-5 text-slate-400" />
        ) : (
          <ChevronRight className="w-5 h-5 text-slate-400" />
        )}
      </button>

      {/* Iterations */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-4 space-y-4">
              {step.iterations.map((iteration) => (
                <IterationCard
                  key={iteration.id}
                  iteration={iteration}
                  onApprove={() => onApprove(step.id, iteration.id)}
                  onDecline={(feedback) => onDecline(step.id, iteration.id, feedback)}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

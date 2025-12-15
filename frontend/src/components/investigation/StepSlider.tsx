import { Check, Circle, ChevronLeft, ChevronRight } from 'lucide-react'
import { InvestigationStep } from '../../types/investigation'
import clsx from 'clsx'

interface StepSliderProps {
  steps: InvestigationStep[]
  currentIndex: number
  onStepChange: (index: number) => void
}

export function StepSlider({ steps, currentIndex, onStepChange }: StepSliderProps) {
  const canGoBack = currentIndex > 0
  const canGoForward = currentIndex < steps.length

  return (
    <div className="bg-white border-b border-slate-200 px-6 py-3">
      <div className="flex items-center justify-between">
        {/* Navigation buttons */}
        <button
          onClick={() => onStepChange(currentIndex - 1)}
          disabled={!canGoBack}
          className="p-2 rounded-lg hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronLeft className="w-5 h-5 text-slate-600" />
        </button>

        {/* Step indicators */}
        <div className="flex-1 flex items-center justify-center gap-2 px-4 overflow-x-auto">
          {steps.map((step, index) => (
            <button
              key={step.id}
              onClick={() => onStepChange(index)}
              className={clsx(
                'flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all',
                index === currentIndex
                  ? 'bg-primary text-white shadow-md'
                  : step.status === 'approved'
                  ? 'bg-success/10 text-success hover:bg-success/20'
                  : step.status === 'declined'
                  ? 'bg-error/10 text-error hover:bg-error/20'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              )}
            >
              {step.status === 'approved' ? (
                <Check className="w-3.5 h-3.5" />
              ) : (
                <Circle className="w-3.5 h-3.5" />
              )}
              <span>Step {step.stepNumber}</span>
            </button>
          ))}

          {/* New step indicator */}
          {currentIndex === steps.length && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium bg-primary/10 text-primary border-2 border-dashed border-primary/30">
              <Circle className="w-3.5 h-3.5" />
              <span>New Step</span>
            </div>
          )}
        </div>

        {/* Forward button */}
        <button
          onClick={() => onStepChange(currentIndex + 1)}
          disabled={!canGoForward}
          className="p-2 rounded-lg hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronRight className="w-5 h-5 text-slate-600" />
        </button>
      </div>

      {/* Progress bar */}
      <div className="mt-3 h-1 bg-slate-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-primary to-success transition-all duration-300"
          style={{
            width: `${steps.length > 0 ? ((steps.filter(s => s.status === 'approved').length / steps.length) * 100) : 0}%`,
          }}
        />
      </div>
    </div>
  )
}

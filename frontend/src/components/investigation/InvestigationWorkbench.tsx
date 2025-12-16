import { useState, useEffect, useRef } from 'react'
import { useInvestigation } from '../../hooks/useInvestigation'
import { StepSlider } from './StepSlider'
import { NotesPanel } from './NotesPanel'
import { ChartDisplay } from '../content/ChartDisplay'
import { CodeDisplay } from '../content/CodeDisplay'
import { AgentResponse } from '../content/AgentResponse'
import { Play, Loader2, HelpCircle, CheckCircle2, Database } from 'lucide-react'

interface InvestigationWorkbenchProps {
  measureName?: string
  datasetName?: string
  initialQuery?: string
  autoRunInitialQuery?: boolean
}

export function InvestigationWorkbench({ 
  measureName = 'On-Time Performance', 
  datasetName = 'airline_operations.csv',
  initialQuery,
  autoRunInitialQuery = false,
}: InvestigationWorkbenchProps) {
  // Show dataset name in header
  const _datasetName = datasetName
  const {
    investigation,
    currentStepIndex,
    isProcessing,
    startInvestigation,
    runAnalysis,
    approveAndContinue,
    declineAndRefine,
    goToStep,
    updateNotes,
    saveFinalAnalysis,
    completeInvestigation,
    setIterationIncluded,
  } = useInvestigation()

  const [query, setQuery] = useState('')
  const autoRanRef = useRef(false)

  // Start investigation on mount
  useEffect(() => {
    if (!investigation) {
      startInvestigation(measureName)
    }
  }, [investigation, measureName, startInvestigation])

  // Set initial query based on hypothesis
  useEffect(() => {
    if (investigation && !query && investigation.steps.length === 0) {
      setQuery(initialQuery || `Why is "${measureName}" signaling? What factors are driving this metric?`)
    }
  }, [investigation, measureName, query, initialQuery])

  // Optionally auto-run the initial query (demo flow for Tech Ops)
  useEffect(() => {
    if (!autoRunInitialQuery) return
    if (!investigation) return
    if (investigation.steps.length > 0) return
    if (isProcessing) return
    if (autoRanRef.current) return

    const q = (initialQuery || query).trim()
    if (!q) return

    autoRanRef.current = true
    runAnalysis(q)
    setQuery('')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoRunInitialQuery, investigation, isProcessing, initialQuery, query, runAnalysis])

  const handleRunAnalysis = () => {
    if (query.trim() && !isProcessing) {
      runAnalysis(query.trim())
      setQuery('')
    }
  }

  const handleApprove = (stepId: string, iterationId: string) => {
    approveAndContinue(stepId, iterationId)
    // Suggest next question
    setQuery('')
  }

  const handleDecline = (stepId: string, iterationId: string, feedback: string) => {
    declineAndRefine(stepId, iterationId, feedback)
  }

  const currentStep = investigation?.steps[currentStepIndex]
  const isNewStep = currentStepIndex === (investigation?.steps.length || 0)
  const allStepsApproved = investigation?.steps.every(s => s.status === 'approved')

  if (!investigation) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with hypothesis */}
      <div className="bg-gradient-to-r from-blue-600/10 to-purple-600/10 px-6 py-4 border-b border-slate-200">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <HelpCircle className="w-6 h-6 text-blue-600 mt-0.5" />
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                Investigating: {investigation.measureName}
              </h2>
              <p className="text-sm text-slate-600 mt-1">
                {investigation.hypothesis}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-white/80 rounded-lg border border-slate-200">
            <Database className="w-4 h-4 text-slate-500" />
            <span className="text-sm text-slate-600">{_datasetName}</span>
          </div>
        </div>
      </div>

      {/* Step slider */}
      {investigation.steps.length > 0 && (
        <StepSlider
          steps={investigation.steps}
          currentIndex={currentStepIndex}
          onStepChange={goToStep}
        />
      )}

      {/* Main content area */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Show current or selected step */}
          {currentStep && !isNewStep && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
                Step {currentStep.stepNumber}: {currentStep.query}
              </h3>
              
              {currentStep.iterations.map((iteration) => (
                <div key={iteration.id} className="card-elevated">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className="font-semibold text-slate-700">
                        Iteration {iteration.iterationNumber}
                      </span>
                      <label className="flex items-center gap-2 text-xs text-slate-600">
                        <input
                          type="checkbox"
                          className="h-4 w-4 rounded border-slate-300"
                          checked={iteration.includeInFinal !== false}
                          onChange={(e) => setIterationIncluded(currentStep.id, iteration.id, e.target.checked)}
                        />
                        Include in final
                      </label>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      iteration.status === 'verified' ? 'bg-green-100 text-green-700' : 
                      iteration.status === 'failed' ? 'bg-red-100 text-red-700' :
                      iteration.status === 'executing' ? 'bg-blue-100 text-blue-700' :
                      iteration.status === 'generating' ? 'bg-purple-100 text-purple-700' :
                      'bg-slate-100 text-slate-700'
                    }`}>
                      {iteration.status}
                    </span>
                  </div>

                  {/* Generated Code */}
                  {iteration.generatedCode && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-slate-600 mb-2">Generated Analysis Code</h4>
                      <CodeDisplay 
                        code={iteration.generatedCode} 
                        language="python"
                      />
                    </div>
                  )}

                  {/* Response */}
                  {iteration.response && (
                    <div className="mb-4">
                      <AgentResponse 
                        output={iteration.response} 
                        success={iteration.status !== 'failed'}
                        duration_ms={0}
                      />
                    </div>
                  )}

                  {/* Visualization */}
                  {iteration.visualization && (
                    <div className="mb-4">
                      <ChartDisplay chart={iteration.visualization} />
                    </div>
                  )}

                  {/* Verification Assessment */}
                  {iteration.verification && iteration.verification.assessment && (
                    <div className={`mb-4 p-4 rounded-lg border ${
                      iteration.verification.passed 
                        ? 'bg-green-50 border-green-200' 
                        : 'bg-amber-50 border-amber-200'
                    }`}>
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle2 className={`w-5 h-5 ${
                          iteration.verification.passed ? 'text-green-600' : 'text-amber-600'
                        }`} />
                        <span className="font-medium text-slate-700">
                          {iteration.verification.passed ? 'Verification Passed' : 'Needs Review'}
                        </span>
                      </div>
                      <p className="text-sm text-slate-600">{iteration.verification.assessment}</p>
                    </div>
                  )}

                  {/* Actions for latest iteration */}
                  {iteration.status === 'verified' && currentStep.status !== 'approved' && (
                    <div className="flex gap-3 pt-4 border-t border-slate-200">
                      <button
                        onClick={() => handleApprove(currentStep.id, iteration.id)}
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors"
                      >
                        <CheckCircle2 className="w-5 h-5" />
                        Approve & Continue
                      </button>
                      <button
                        onClick={() => {
                          const feedback = prompt('What should be refined?')
                          if (feedback) handleDecline(currentStep.id, iteration.id, feedback)
                        }}
                        className="flex-1 px-4 py-3 border border-red-500 text-red-600 hover:bg-red-500 hover:text-white font-medium rounded-lg transition-colors"
                      >
                        Decline & Refine
                      </button>
                    </div>
                  )}

                  {currentStep.status === 'approved' && currentStep.approvedIterationId === iteration.id && (
                    <div className="flex items-center gap-2 pt-4 border-t border-slate-200 text-green-600">
                      <CheckCircle2 className="w-5 h-5" />
                      <span className="font-medium">Approved - Linked to next step</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* New step input */}
          {isNewStep && (
            <div className="card-elevated">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">
                {investigation.steps.length === 0 ? 'Start Your Investigation' : 'Continue Investigation'}
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-600 mb-2">
                    What would you like to explore?
                  </label>
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Enter your analysis question..."
                    className="w-full h-24 p-3 border border-slate-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.ctrlKey) {
                        handleRunAnalysis()
                      }
                    }}
                  />
                  <p className="text-xs text-slate-500 mt-1">Press Ctrl+Enter to run</p>
                </div>

                <button
                  onClick={handleRunAnalysis}
                  disabled={!query.trim() || isProcessing}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary hover:bg-primary-dark text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Play className="w-5 h-5" />
                      Run Analysis
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Notes panel */}
          <NotesPanel
            notes={investigation.notes}
            onNotesChange={updateNotes}
            finalAnalysis={investigation.finalAnalysis}
            conclusion={investigation.conclusion}
            onSaveFinal={saveFinalAnalysis}
            isComplete={allStepsApproved && investigation.steps.length > 0}
          />

          {/* Complete investigation button */}
          {allStepsApproved && investigation.steps.length > 0 && investigation.finalAnalysis && (
            <button
              onClick={completeInvestigation}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-primary to-purple-600 text-white font-medium rounded-lg transition-all hover:shadow-lg"
            >
              <CheckCircle2 className="w-5 h-5" />
              Complete Investigation & Save
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

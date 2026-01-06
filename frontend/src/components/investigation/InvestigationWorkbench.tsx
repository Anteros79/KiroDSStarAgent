import { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react'
import { useInvestigation } from '../../hooks/useInvestigation'
import { StepSlider } from './StepSlider'
import { NotesPanel } from './NotesPanel'
import { ChartDisplay } from '../content/ChartDisplay'
import { CodeDisplay } from '../content/CodeDisplay'
import { AgentResponse } from '../content/AgentResponse'
import { MeasureAnalysisPanel } from '../../techops/components/MeasureAnalysisPanel'
import { StepPills, StepPillData } from '../../techops/components/StepPills'
import { getMeasureConfig, generateInvestigationPrompt } from '../../techops/measureConfig'
import { Play, Loader2, HelpCircle, CheckCircle2, Database, MessageSquare, ChevronDown, ChevronUp } from 'lucide-react'

interface InvestigationWorkbenchProps {
  measureName?: string
  datasetName?: string
  initialQuery?: string
  autoRunInitialQuery?: boolean
  wsContext?: {
    investigation_id?: string
    kpi_id?: string
    station?: string
    window?: 'weekly' | 'daily'
    point_t?: string
    max_iterations?: number
    summary_level?: 'station' | 'region' | 'company'
  }
}

export interface InvestigationWorkbenchRef {
  executeQuery: (query: string) => void
}

export const InvestigationWorkbench = forwardRef<InvestigationWorkbenchRef, InvestigationWorkbenchProps>(({ 
  measureName = 'On-Time Performance', 
  datasetName = 'airline_operations.csv',
  initialQuery,
  autoRunInitialQuery = false,
  wsContext,
}, ref) => {
  const measureId = wsContext?.kpi_id || measureName.toLowerCase().replace(/[\s-]/g, '_')
  const measureConfig = getMeasureConfig(measureId)
  const station = wsContext?.station || 'DAL'
  const window = wsContext?.window || 'weekly'

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
  const [showAnalysisPanel, setShowAnalysisPanel] = useState(true)
  const autoRanRef = useRef(false)

  // Expose methods to parent component
  useImperativeHandle(ref, () => ({
    executeQuery: (externalQuery: string) => {
      setQuery(externalQuery)
      if (externalQuery.trim() && !isProcessing) {
        runAnalysis(externalQuery.trim(), wsContext)
        setQuery('')
      }
    }
  }), [isProcessing, runAnalysis, wsContext])

  // Start investigation on mount
  useEffect(() => {
    if (!investigation) {
      startInvestigation(measureConfig.label)
    }
  }, [investigation, measureConfig.label, startInvestigation])

  // Set initial query based on measure config
  useEffect(() => {
    if (investigation && !query && investigation.steps.length === 0) {
      const contextualPrompt = initialQuery || generateInvestigationPrompt(
        measureId,
        station,
        window,
        wsContext?.point_t
      )
      setQuery(contextualPrompt)
    }
  }, [investigation, measureId, station, window, wsContext?.point_t, query, initialQuery])

  // Optionally auto-run the initial query
  useEffect(() => {
    if (!autoRunInitialQuery) return
    if (!investigation) return
    if (investigation.steps.length > 0) return
    if (isProcessing) return
    if (autoRanRef.current) return

    const q = (initialQuery || query).trim()
    if (!q) return

    autoRanRef.current = true
    runAnalysis(q, wsContext)
    setQuery('')
  }, [autoRunInitialQuery, investigation, isProcessing, initialQuery, query, runAnalysis, wsContext])

  const handleRunAnalysis = () => {
    if (query.trim() && !isProcessing) {
      runAnalysis(query.trim(), wsContext)
      setQuery('')
    }
  }

  const handleSelectAnalysis = (suggestedQuery: string) => {
    setQuery(suggestedQuery)
  }

  const handleApprove = (stepId: string, iterationId: string) => {
    approveAndContinue(stepId, iterationId)
    setQuery('')
  }

  const handleDecline = (stepId: string, iterationId: string, feedback: string) => {
    declineAndRefine(stepId, iterationId, feedback)
  }

  const handleToggleStepInclude = (stepId: string, include: boolean) => {
    const step = investigation?.steps.find(s => s.id === stepId)
    if (step && step.iterations.length > 0) {
      const latestIteration = step.iterations[step.iterations.length - 1]
      setIterationIncluded(stepId, latestIteration.id, include)
    }
  }

  const currentStep = investigation?.steps[currentStepIndex]
  const isNewStep = currentStepIndex === (investigation?.steps.length || 0)
  const allStepsApproved = investigation?.steps.every(s => s.status === 'approved')

  // Convert steps to pill format
  const stepPillData: StepPillData[] = (investigation?.steps || []).map(step => ({
    id: step.id,
    stepNumber: step.stepNumber,
    hypothesis: step.query,
    status: step.status as StepPillData['status'],
    includeInReport: step.iterations.some(i => i.includeInFinal !== false),
    iterations: step.iterations.map(i => ({
      id: i.id,
      iterationNumber: i.iterationNumber,
      response: i.response,
      generatedCode: i.generatedCode,
      visualization: i.visualization,
      status: i.status,
    })),
  }))

  if (!investigation) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 h-full">
      {/* Main Content Area */}
      <div className="lg:col-span-2 flex flex-col h-full">
        {/* Compact Header */}
        <div className="bg-gradient-to-r from-blue-600/10 to-purple-600/10 px-4 py-3 border-b border-slate-200">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 min-w-0">
              <HelpCircle className="w-5 h-5 text-blue-600 flex-shrink-0" />
              <div className="min-w-0">
                <h2 className="text-base font-bold text-slate-900 truncate">
                  {measureConfig.label}
                </h2>
                <p className="text-xs text-slate-600 truncate">
                  {measureConfig.signalMeaning.slice(0, 80)}...
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <div className="flex items-center gap-1.5 px-2 py-1 bg-white/80 rounded-lg border border-slate-200">
                <Database className="w-3.5 h-3.5 text-slate-500" />
                <span className="text-xs text-slate-600">{datasetName}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Step slider - more compact */}
        {investigation.steps.length > 0 && (
          <StepSlider
            steps={investigation.steps}
            currentIndex={currentStepIndex}
            onStepChange={goToStep}
          />
        )}

        {/* Main content - reduced padding */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-4xl mx-auto space-y-4">
            {/* Measure Analysis Panel - Collapsible */}
            {investigation.steps.length === 0 && (
              <div className="space-y-2">
                <button
                  onClick={() => setShowAnalysisPanel(!showAnalysisPanel)}
                  className="flex items-center gap-2 text-sm font-semibold text-slate-700 hover:text-slate-900"
                >
                  {showAnalysisPanel ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  Analysis Options for {measureConfig.label}
                </button>
                {showAnalysisPanel && (
                  <MeasureAnalysisPanel
                    measureId={measureId}
                    station={station}
                    window={window}
                    onSelectAnalysis={handleSelectAnalysis}
                  />
                )}
              </div>
            )}

            {/* Step Pills - Minimized format for completed steps */}
            {investigation.steps.length > 0 && (
              <StepPills
                steps={stepPillData}
                onToggleInclude={handleToggleStepInclude}
                onStepClick={(stepId) => {
                  const idx = investigation.steps.findIndex(s => s.id === stepId)
                  if (idx >= 0) goToStep(idx)
                }}
              />
            )}

            {/* Current Step Detail - Only show if viewing a specific step */}
            {currentStep && !isNewStep && (
              <div className="space-y-3 mt-4 pt-4 border-t border-slate-200">
                <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider">
                  Step {currentStep.stepNumber} Detail
                </h3>
                
                {currentStep.iterations.map((iteration) => (
                  <div key={iteration.id} className="card-elevated p-3">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-slate-700">
                          Iteration {iteration.iterationNumber}
                        </span>
                      </div>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        iteration.status === 'verified' ? 'bg-green-100 text-green-700' : 
                        iteration.status === 'failed' ? 'bg-red-100 text-red-700' :
                        iteration.status === 'executing' ? 'bg-blue-100 text-blue-700' :
                        iteration.status === 'generating' ? 'bg-purple-100 text-purple-700' :
                        'bg-slate-100 text-slate-700'
                      }`}>
                        {iteration.status}
                      </span>
                    </div>

                    {iteration.generatedCode && (
                      <div className="mb-3">
                        <h4 className="text-xs font-medium text-slate-600 mb-1">Generated Code</h4>
                        <CodeDisplay code={iteration.generatedCode} language="python" />
                      </div>
                    )}

                    {iteration.response && (
                      <div className="mb-3">
                        <AgentResponse 
                          output={iteration.response} 
                          success={iteration.status !== 'failed'}
                          duration_ms={iteration.duration_ms ?? 0}
                        />
                      </div>
                    )}

                    {iteration.visualization && (
                      <div className="mb-3">
                        <ChartDisplay chart={iteration.visualization} />
                      </div>
                    )}

                    {iteration.verification && iteration.verification.assessment && (
                      <div className={`mb-3 p-3 rounded-lg border ${
                        iteration.verification.passed 
                          ? 'bg-green-50 border-green-200' 
                          : 'bg-amber-50 border-amber-200'
                      }`}>
                        <div className="flex items-center gap-2 mb-1">
                          <CheckCircle2 className={`w-4 h-4 ${
                            iteration.verification.passed ? 'text-green-600' : 'text-amber-600'
                          }`} />
                          <span className="font-medium text-sm text-slate-700">
                            {iteration.verification.passed ? 'Verified' : 'Needs Review'}
                          </span>
                        </div>
                        <p className="text-sm text-slate-600">{iteration.verification.assessment}</p>
                      </div>
                    )}

                    {iteration.status === 'verified' && currentStep.status !== 'approved' && (
                      <div className="flex gap-2 pt-3 border-t border-slate-200">
                        <button
                          onClick={() => handleApprove(currentStep.id, iteration.id)}
                          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors"
                        >
                          <CheckCircle2 className="w-4 h-4" />
                          Approve
                        </button>
                        <button
                          onClick={() => {
                            const feedback = prompt('What should be refined?')
                            if (feedback) handleDecline(currentStep.id, iteration.id, feedback)
                          }}
                          className="flex-1 px-3 py-2 border border-red-500 text-red-600 hover:bg-red-500 hover:text-white text-sm font-medium rounded-lg transition-colors"
                        >
                          Decline
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Notes panel - more compact */}
            <NotesPanel
              notes={investigation.notes}
              onNotesChange={updateNotes}
              finalAnalysis={investigation.finalAnalysis}
              conclusion={investigation.conclusion}
              onSaveFinal={saveFinalAnalysis}
              isComplete={allStepsApproved && investigation.steps.length > 0}
            />

            {/* Complete button */}
            {allStepsApproved && investigation.steps.length > 0 && investigation.finalAnalysis && (
              <button
                onClick={completeInvestigation}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-primary to-purple-600 text-white font-medium rounded-lg transition-all hover:shadow-lg"
              >
                <CheckCircle2 className="w-4 h-4" />
                Complete Investigation
              </button>
            )}
          </div>
        </div>
      </div>

      {/* DS-STAR Assistant Rail - Tighter */}
      <aside className="lg:col-span-1 border-t lg:border-t-0 lg:border-l border-slate-200 bg-white flex flex-col min-h-[400px]">
        <div className="px-3 py-2 border-b border-slate-200 flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-slate-600" />
          <span className="text-sm font-bold text-slate-900">DS‑STAR</span>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {/* Quick Analysis Buttons */}
          {investigation.steps.length === 0 && (
            <MeasureAnalysisPanel
              measureId={measureId}
              station={station}
              window={window}
              onSelectAnalysis={handleSelectAnalysis}
              compact
            />
          )}

          {/* Chat Items */}
          {investigation.steps.flatMap((step) =>
            step.iterations.map((iteration) => (
              <div key={iteration.id} className="rounded-lg border border-slate-200 bg-slate-50 p-2">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-slate-500">
                    S{step.stepNumber}.{iteration.iterationNumber}
                  </span>
                  <label className="flex items-center gap-1">
                    <input
                      type="checkbox"
                      className="h-3 w-3 rounded border-slate-300"
                      checked={iteration.includeInFinal !== false}
                      onChange={(e) => setIterationIncluded(step.id, iteration.id, e.target.checked)}
                    />
                    <span className="text-xs text-slate-500">Inc</span>
                  </label>
                </div>
                {iteration.response ? (
                  <p className="text-xs text-slate-700 line-clamp-3">{iteration.response}</p>
                ) : (
                  <p className="text-xs text-slate-400">Processing...</p>
                )}
                {iteration.visualization && (
                  <div className="mt-2 -mx-2 -mb-2">
                    <ChartDisplay chart={iteration.visualization} />
                  </div>
                )}
              </div>
            ))
          )}

          {investigation.steps.length === 0 && (
            <p className="text-xs text-slate-500">
              Select an analysis option above or type a custom query below.
            </p>
          )}
        </div>

        {/* Query Input - Compact */}
        <div className="p-3 border-t border-slate-200 bg-slate-50">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask DS‑STAR..."
            className="w-full h-16 p-2 border border-slate-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.ctrlKey) {
                handleRunAnalysis()
              }
            }}
          />
          <div className="mt-2 flex items-center gap-2">
            <button
              onClick={handleRunAnalysis}
              disabled={!query.trim() || isProcessing}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-primary hover:bg-primary-dark text-white text-sm font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Running
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" />
                  Run
                </>
              )}
            </button>
            <span className="text-xs text-slate-400">Ctrl+↵</span>
          </div>
        </div>
      </aside>
    </div>
  )
})

InvestigationWorkbench.displayName = 'InvestigationWorkbench'

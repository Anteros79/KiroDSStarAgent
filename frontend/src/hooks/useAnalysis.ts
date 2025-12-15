import { useState, useCallback, useEffect } from 'react'
import { AnalysisState, AnalysisStep, Iteration, WSEvent } from '../types'
import { wsService } from '../services/websocket'

export function useAnalysis() {
  const [analysis, setAnalysis] = useState<AnalysisState | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Handle WebSocket events
  useEffect(() => {
    const unsubscribe = wsService.subscribe((event: WSEvent) => {
      switch (event.type) {
        case 'analysis_started':
          setAnalysis({
            id: event.data.analysis_id,
            researchGoal: event.data.research_goal,
            dataset: event.data.dataset,
            steps: [],
            status: 'running',
            startedAt: new Date(),
          })
          setIsLoading(false)
          break

        case 'step_started':
          setAnalysis((prev) => {
            if (!prev) return prev
            const newStep: AnalysisStep = {
              id: event.data.step_id,
              stepNumber: event.data.step_number,
              iterations: [],
              status: 'running',
            }
            return { ...prev, steps: [...prev.steps, newStep] }
          })
          break

        case 'iteration_started':
          setAnalysis((prev) => {
            if (!prev) return prev
            const newIteration: Iteration = {
              id: event.data.iteration_id,
              iterationNumber: event.data.iteration_number,
              timestamp: new Date(),
              description: event.data.description || '',
              generatedCode: '',
              executionOutput: { success: false, output: '', duration_ms: 0 },
              verification: { passed: false, assessment: '' },
              status: 'generating',
            }
            return updateIteration(prev, event.data.step_id, newIteration)
          })
          break

        case 'code_generated':
          setAnalysis((prev) => {
            if (!prev) return prev
            return updateIterationField(
              prev,
              event.data.step_id,
              event.data.iteration_id,
              { generatedCode: event.data.code, status: 'executing' }
            )
          })
          break

        case 'execution_complete':
          setAnalysis((prev) => {
            if (!prev) return prev
            return updateIterationField(
              prev,
              event.data.step_id,
              event.data.iteration_id,
              { executionOutput: event.data.output, status: 'verifying' }
            )
          })
          break

        case 'visualization_ready':
          setAnalysis((prev) => {
            if (!prev) return prev
            return updateIterationField(
              prev,
              event.data.step_id,
              event.data.iteration_id,
              { visualization: event.data.chart }
            )
          })
          break

        case 'verification_complete':
          setAnalysis((prev) => {
            if (!prev) return prev
            const status = event.data.result.passed ? 'verified' : 'failed'
            return updateIterationField(
              prev,
              event.data.step_id,
              event.data.iteration_id,
              { verification: event.data.result, status }
            )
          })
          break

        case 'step_completed':
          setAnalysis((prev) => {
            if (!prev) return prev
            return {
              ...prev,
              steps: prev.steps.map((s) =>
                s.id === event.data.step_id ? { ...s, status: 'completed' } : s
              ),
            }
          })
          break

        case 'analysis_completed':
          setAnalysis((prev) => {
            if (!prev) return prev
            return { ...prev, status: 'completed', completedAt: new Date() }
          })
          break

        case 'error':
          setError(event.data.message)
          setIsLoading(false)
          break
      }
    })

    return unsubscribe
  }, [])

  const startAnalysis = useCallback(async (researchGoal: string) => {
    setIsLoading(true)
    setError(null)
    try {
      wsService.startAnalysis(researchGoal)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start analysis')
      setIsLoading(false)
    }
  }, [])

  const approveStep = useCallback((stepId: string, iterationId: string) => {
    wsService.approveStep(stepId, iterationId)
  }, [])

  const refineStep = useCallback((stepId: string, iterationId: string, feedback: string) => {
    wsService.refineStep(stepId, iterationId, feedback)
  }, [])

  const reset = useCallback(() => {
    setAnalysis(null)
    setError(null)
  }, [])

  return {
    analysis,
    isLoading,
    error,
    startAnalysis,
    approveStep,
    refineStep,
    reset,
  }
}

// Helper functions
function updateIteration(
  state: AnalysisState,
  stepId: string,
  newIteration: Iteration
): AnalysisState {
  return {
    ...state,
    steps: state.steps.map((step) =>
      step.id === stepId
        ? { ...step, iterations: [...step.iterations, newIteration] }
        : step
    ),
  }
}

function updateIterationField(
  state: AnalysisState,
  stepId: string,
  iterationId: string,
  updates: Partial<Iteration>
): AnalysisState {
  return {
    ...state,
    steps: state.steps.map((step) =>
      step.id === stepId
        ? {
            ...step,
            iterations: step.iterations.map((iter) =>
              iter.id === iterationId ? { ...iter, ...updates } : iter
            ),
          }
        : step
    ),
  }
}

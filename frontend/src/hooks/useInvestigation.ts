import { useState, useCallback, useEffect, useReducer, useRef } from 'react'
import { Investigation, InvestigationStep, StepIteration, InvestigationAction } from '../types/investigation'
import { wsService } from '../services/websocket'
import { WSEvent } from '../types'

// Generate unique IDs
const generateId = () => Math.random().toString(36).substring(2, 10)

// Initial state
const createInitialInvestigation = (measureName: string): Investigation => ({
  id: generateId(),
  measureName,
  hypothesis: `Why is "${measureName}" signaling? What factors are driving this metric?`,
  createdAt: new Date(),
  updatedAt: new Date(),
  status: 'active',
  steps: [],
  notes: '',
})

// Extended action type to include step ID for ADD_STEP
type ExtendedInvestigationAction =
  | InvestigationAction
  | { type: 'ADD_STEP_WITH_ID'; query: string; stepId: string }
  | {
      type: 'START_ITERATION_WITH_ID'
      stepId: string
      iterationId: string
      iterationNumber?: number
      description?: string
    }

// Reducer for investigation state
function investigationReducer(state: Investigation | null, action: ExtendedInvestigationAction): Investigation | null {
  switch (action.type) {
    case 'START_INVESTIGATION':
      return createInitialInvestigation(action.measureName)

    case 'ADD_STEP': {
      if (!state) return state
      const newStep: InvestigationStep = {
        id: generateId(),
        stepNumber: state.steps.length + 1,
        query: action.query,
        iterations: [],
        status: 'pending',
        notes: '',
        createdAt: new Date(),
      }
      return {
        ...state,
        steps: [...state.steps, newStep],
        updatedAt: new Date(),
      }
    }

    case 'ADD_STEP_WITH_ID': {
      if (!state) return state
      const newStep: InvestigationStep = {
        id: action.stepId,
        stepNumber: state.steps.length + 1,
        query: action.query,
        iterations: [],
        status: 'pending',
        notes: '',
        createdAt: new Date(),
      }
      return {
        ...state,
        steps: [...state.steps, newStep],
        updatedAt: new Date(),
      }
    }

    case 'START_ITERATION': {
      if (!state) return state
      const stepIndex = state.steps.findIndex(s => s.id === action.stepId)
      if (stepIndex === -1) return state

      const step = state.steps[stepIndex]
      const newIteration: StepIteration = {
        id: generateId(),
        iterationNumber: step.iterations.length + 1,
        timestamp: new Date(),
        description: step.query,
        generatedCode: '',
        response: '',
        verification: { passed: false, assessment: '' },
        status: 'generating',
        includeInFinal: true,
      }

      const updatedSteps = [...state.steps]
      updatedSteps[stepIndex] = {
        ...step,
        iterations: [...step.iterations, newIteration],
        status: 'running',
      }

      return { ...state, steps: updatedSteps, updatedAt: new Date() }
    }

    case 'START_ITERATION_WITH_ID': {
      if (!state) return state
      const stepIndex = state.steps.findIndex(s => s.id === action.stepId)
      if (stepIndex === -1) return state

      const step = state.steps[stepIndex]
      const newIteration: StepIteration = {
        id: action.iterationId,
        iterationNumber: action.iterationNumber ?? (step.iterations.length + 1),
        timestamp: new Date(),
        description: action.description ?? step.query,
        generatedCode: '',
        response: '',
        verification: { passed: false, assessment: '' },
        status: 'generating',
        includeInFinal: true,
      }

      const updatedSteps = [...state.steps]
      updatedSteps[stepIndex] = {
        ...step,
        iterations: [...step.iterations, newIteration],
        status: 'running',
      }

      return { ...state, steps: updatedSteps, updatedAt: new Date() }
    }

    case 'UPDATE_ITERATION': {
      if (!state) return state
      const stepIndex = state.steps.findIndex(s => s.id === action.stepId)
      if (stepIndex === -1) return state

      const step = state.steps[stepIndex]
      const iterIndex = step.iterations.findIndex(i => i.id === action.iterationId)
      if (iterIndex === -1) return state

      const updatedIterations = [...step.iterations]
      updatedIterations[iterIndex] = { ...updatedIterations[iterIndex], ...action.updates }

      const updatedSteps = [...state.steps]
      updatedSteps[stepIndex] = { ...step, iterations: updatedIterations }

      return { ...state, steps: updatedSteps, updatedAt: new Date() }
    }

    case 'APPROVE_STEP': {
      if (!state) return state
      const stepIndex = state.steps.findIndex(s => s.id === action.stepId)
      if (stepIndex === -1) return state

      const updatedSteps = [...state.steps]
      updatedSteps[stepIndex] = {
        ...updatedSteps[stepIndex],
        status: 'approved',
        approvedIterationId: action.iterationId,
      }

      return { ...state, steps: updatedSteps, updatedAt: new Date() }
    }

    case 'DECLINE_STEP': {
      if (!state) return state
      const stepIndex = state.steps.findIndex(s => s.id === action.stepId)
      if (stepIndex === -1) return state

      const step = state.steps[stepIndex]
      const iterIndex = step.iterations.findIndex(i => i.id === action.iterationId)
      if (iterIndex === -1) return state

      const updatedIterations = [...step.iterations]
      updatedIterations[iterIndex] = {
        ...updatedIterations[iterIndex],
        status: 'failed',
        feedback: action.feedback,
      }

      const updatedSteps = [...state.steps]
      updatedSteps[stepIndex] = {
        ...step,
        iterations: updatedIterations,
        status: 'declined',
      }

      return { ...state, steps: updatedSteps, updatedAt: new Date() }
    }

    case 'UPDATE_NOTES':
      if (!state) return state
      return { ...state, notes: action.notes, updatedAt: new Date() }

    case 'SET_FINAL_ANALYSIS':
      if (!state) return state
      return {
        ...state,
        finalAnalysis: action.analysis,
        conclusion: action.conclusion,
        updatedAt: new Date(),
      }

    case 'COMPLETE_INVESTIGATION':
      if (!state) return state
      return { ...state, status: 'completed', updatedAt: new Date() }

    case 'LOAD_INVESTIGATION':
      return action.investigation

    default:
      return state
  }
}

export function useInvestigation() {
  const [investigation, dispatch] = useReducer(investigationReducer, null)
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [isProcessing, setIsProcessing] = useState(false)
  
  // Track pending query so we can attach it to the server-generated step_id
  const pendingQueryRef = useRef<string | null>(null)
  const stepsLenRef = useRef(0)

  useEffect(() => {
    stepsLenRef.current = investigation?.steps?.length ?? 0
  }, [investigation?.steps?.length])

  // Handle WebSocket events
  useEffect(() => {
    const unsubscribe = wsService.subscribe((event: WSEvent) => {
      switch (event.type) {
        case 'step_started': {
          const stepId = event.data.step_id as string | undefined
          if (!stepId) break
          const query = pendingQueryRef.current || 'Investigation step'
          pendingQueryRef.current = null

          dispatch({ type: 'ADD_STEP_WITH_ID', query, stepId } as ExtendedInvestigationAction)
          // jump to the newly created step (index = previous length)
          setCurrentStepIndex(stepsLenRef.current)
          break
        }

        case 'iteration_started':
          dispatch({
            type: 'START_ITERATION_WITH_ID',
            stepId: event.data.step_id,
            iterationId: event.data.iteration_id,
            iterationNumber: event.data.iteration_number,
            description: event.data.description,
          } as ExtendedInvestigationAction)
          break

        case 'code_generated':
          dispatch({
            type: 'UPDATE_ITERATION',
            stepId: event.data.step_id,
            iterationId: event.data.iteration_id,
            updates: { generatedCode: event.data.code, status: 'executing' },
          })
          break

        case 'execution_complete':
          dispatch({
            type: 'UPDATE_ITERATION',
            stepId: event.data.step_id,
            iterationId: event.data.iteration_id,
            updates: {
              response: event.data.output?.output || '',
              status: 'verifying',
            },
          })
          break

        case 'visualization_ready':
          dispatch({
            type: 'UPDATE_ITERATION',
            stepId: event.data.step_id,
            iterationId: event.data.iteration_id,
            updates: { visualization: event.data.chart },
          })
          break

        case 'verification_complete':
          dispatch({
            type: 'UPDATE_ITERATION',
            stepId: event.data.step_id,
            iterationId: event.data.iteration_id,
            updates: {
              verification: event.data.result,
              status: event.data.result.passed ? 'verified' : 'failed',
            },
          })
          setIsProcessing(false)
          break

        case 'step_completed':
          setIsProcessing(false)
          break

        case 'error':
          setIsProcessing(false)
          break
      }
    })

    return unsubscribe
  }, [])

  // Start a new investigation
  const startInvestigation = useCallback((measureName: string) => {
    dispatch({ type: 'START_INVESTIGATION', measureName })
    setCurrentStepIndex(0)
    pendingQueryRef.current = null
  }, [])

  // Run analysis for current step
  const runAnalysis = useCallback((query: string, options?: Parameters<typeof wsService.startAnalysis>[1]) => {
    if (!investigation || isProcessing) return

    pendingQueryRef.current = query
    setIsProcessing(true)
    wsService.startAnalysis(query, options)
  }, [investigation, isProcessing])

  const setIterationIncluded = useCallback((stepId: string, iterationId: string, includeInFinal: boolean) => {
    dispatch({
      type: 'UPDATE_ITERATION',
      stepId,
      iterationId,
      updates: { includeInFinal },
    })
  }, [])

  // Approve current step and continue
  const approveAndContinue = useCallback((stepId: string, iterationId: string) => {
    dispatch({ type: 'APPROVE_STEP', stepId, iterationId })
    
    // Send approval to backend
    wsService.approveStep(stepId, iterationId)
    
    // Move to next step slot (new step input)
    if (investigation) {
      setCurrentStepIndex(investigation.steps.length)
    }
    
    pendingQueryRef.current = null
  }, [investigation])

  // Decline and refine
  const declineAndRefine = useCallback((stepId: string, iterationId: string, feedback: string) => {
    dispatch({ type: 'DECLINE_STEP', stepId, iterationId, feedback })
    
    // Trigger new iteration with feedback
    setIsProcessing(true)
    wsService.refineStep(stepId, iterationId, feedback)
  }, [])

  // Navigate to specific step
  const goToStep = useCallback((index: number) => {
    if (investigation && index >= 0 && index <= investigation.steps.length) {
      setCurrentStepIndex(index)
    }
  }, [investigation])

  // Update notes
  const updateNotes = useCallback((notes: string) => {
    dispatch({ type: 'UPDATE_NOTES', notes })
  }, [])

  // Save final analysis
  const saveFinalAnalysis = useCallback((analysis: string, conclusion: string) => {
    dispatch({ type: 'SET_FINAL_ANALYSIS', analysis, conclusion })
  }, [])

  // Complete investigation
  const completeInvestigation = useCallback(() => {
    dispatch({ type: 'COMPLETE_INVESTIGATION' })
    // TODO: Save to local DB
  }, [])

  return {
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
  }
}

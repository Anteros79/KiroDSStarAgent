import { useState } from 'react'
import { Sparkles, Check, X, MessageSquare } from 'lucide-react'
import * as Dialog from '@radix-ui/react-dialog'
import { VerificationResult } from '../../types'

interface VerifierAssessmentProps {
  verification: VerificationResult
  onApprove: () => void
  onDecline: (feedback: string) => void
  showActions?: boolean
}

export function VerifierAssessment({ 
  verification, 
  onApprove, 
  onDecline,
  showActions = true 
}: VerifierAssessmentProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [feedback, setFeedback] = useState('')

  const handleDecline = () => {
    if (feedback.trim()) {
      onDecline(feedback.trim())
      setIsDialogOpen(false)
      setFeedback('')
    }
  }

  return (
    <div className="rounded-lg border border-slate-200 overflow-hidden">
      {/* Assessment header */}
      <div className="flex items-center gap-2 px-4 py-3 bg-gradient-to-r from-primary/10 to-purple-500/10 border-b border-slate-200">
        <Sparkles className="w-5 h-5 text-primary" />
        <span className="font-semibold text-slate-700">Verifier Assessment</span>
      </div>

      {/* Assessment content */}
      <div className="p-4">
        <p className="text-slate-700 mb-4">{verification.assessment}</p>

        {/* Suggestions if any */}
        {verification.suggestions && verification.suggestions.length > 0 && (
          <div className="mb-4">
            <h5 className="text-sm font-medium text-slate-600 mb-2">Suggestions:</h5>
            <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
              {verification.suggestions.map((suggestion, i) => (
                <li key={i}>{suggestion}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Action buttons */}
        {showActions && (
          <div className="flex gap-3 pt-2">
            <button
              onClick={onApprove}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-success hover:bg-success-dark text-white font-medium rounded-lg transition-colors"
            >
              <Check className="w-5 h-5" />
              Approve & Continue
            </button>

            <Dialog.Root open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <Dialog.Trigger asChild>
                <button className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-transparent border border-error text-error hover:bg-error hover:text-white font-medium rounded-lg transition-colors">
                  <X className="w-5 h-5" />
                  Decline & Refine
                </button>
              </Dialog.Trigger>

              <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
                <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-xl p-6 w-full max-w-md z-50">
                  <Dialog.Title className="text-lg font-semibold text-slate-900 mb-2">
                    Provide Refinement Feedback
                  </Dialog.Title>
                  <Dialog.Description className="text-sm text-slate-600 mb-4">
                    Describe what should be changed or improved in the analysis.
                  </Dialog.Description>

                  <textarea
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="e.g., Use a different chart type, filter outliers, add trend line..."
                    className="w-full h-32 p-3 border border-slate-300 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    autoFocus
                  />

                  <div className="flex gap-3 mt-4">
                    <Dialog.Close asChild>
                      <button className="flex-1 px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
                        Cancel
                      </button>
                    </Dialog.Close>
                    <button
                      onClick={handleDecline}
                      disabled={!feedback.trim()}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <MessageSquare className="w-4 h-4" />
                      Submit Refinement
                    </button>
                  </div>
                </Dialog.Content>
              </Dialog.Portal>
            </Dialog.Root>
          </div>
        )}
      </div>
    </div>
  )
}

import { useState } from 'react'
import { FileText, Save, CheckCircle } from 'lucide-react'

interface NotesPanelProps {
  notes: string
  onNotesChange: (notes: string) => void
  finalAnalysis?: string
  conclusion?: string
  onSaveFinal?: (analysis: string, conclusion: string) => void
  isComplete?: boolean
}

export function NotesPanel({
  notes,
  onNotesChange,
  finalAnalysis,
  conclusion,
  onSaveFinal,
  isComplete,
}: NotesPanelProps) {
  const [localAnalysis, setLocalAnalysis] = useState(finalAnalysis || '')
  const [localConclusion, setLocalConclusion] = useState(conclusion || '')
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    if (onSaveFinal) {
      onSaveFinal(localAnalysis, localConclusion)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    }
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 bg-slate-50 border-b border-slate-200">
        <FileText className="w-4 h-4 text-primary" />
        <span className="font-semibold text-slate-700">Investigation Notes</span>
      </div>

      <div className="p-4 space-y-4">
        {/* Running notes */}
        <div>
          <label className="block text-sm font-medium text-slate-600 mb-2">
            Running Notes
          </label>
          <textarea
            value={notes}
            onChange={(e) => onNotesChange(e.target.value)}
            placeholder="Add observations, hypotheses, and findings as you investigate..."
            className="w-full h-32 p-3 border border-slate-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>

        {/* Final analysis section */}
        {isComplete !== false && (
          <>
            <div className="border-t border-slate-200 pt-4">
              <label className="block text-sm font-medium text-slate-600 mb-2">
                Final Analysis
              </label>
              <textarea
                value={localAnalysis}
                onChange={(e) => setLocalAnalysis(e.target.value)}
                placeholder="Summarize your findings and analysis..."
                className="w-full h-24 p-3 border border-slate-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-600 mb-2">
                Conclusion & Recommendation
              </label>
              <textarea
                value={localConclusion}
                onChange={(e) => setLocalConclusion(e.target.value)}
                placeholder="What action should be taken based on this investigation?"
                className="w-full h-20 p-3 border border-slate-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>

            <button
              onClick={handleSave}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary hover:bg-primary-dark text-white font-medium rounded-lg transition-colors"
            >
              {saved ? (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Saved!
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Save Analysis
                </>
              )}
            </button>
          </>
        )}
      </div>
    </div>
  )
}

import { useState } from 'react'
import { Play, Sparkles, Loader2 } from 'lucide-react'

interface ResearchGoalPanelProps {
  onStartAnalysis: (goal: string) => void
  onExploreNew?: () => void
  isAnalyzing: boolean
  disabled?: boolean
}

export function ResearchGoalPanel({ 
  onStartAnalysis, 
  onExploreNew,
  isAnalyzing,
  disabled 
}: ResearchGoalPanelProps) {
  const [goal, setGoal] = useState('')

  const handleSubmit = () => {
    if (goal.trim() && !isAnalyzing && !disabled) {
      onStartAnalysis(goal.trim())
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleSubmit()
    }
  }

  return (
    <div className="p-4 border-t border-white/10">
      <h2 className="text-sm font-semibold text-white/70 uppercase tracking-wider mb-3">
        Research Goal
      </h2>
      
      {/* Goal textarea */}
      <textarea
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Describe what you want to analyze..."
        disabled={isAnalyzing || disabled}
        className="w-full h-32 bg-white/10 border border-white/20 rounded-lg p-3 text-white placeholder-white/40 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
      />
      
      <p className="text-xs text-white/40 mt-1 mb-4">
        Press Ctrl+Enter to start
      </p>
      
      {/* Action buttons */}
      <div className="space-y-2">
        <button
          onClick={handleSubmit}
          disabled={!goal.trim() || isAnalyzing || disabled}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-success hover:bg-success-dark text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isAnalyzing ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              Start Analysis
            </>
          )}
        </button>
        
        {onExploreNew && (
          <button
            onClick={onExploreNew}
            disabled={isAnalyzing || disabled}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-transparent border border-white/30 text-white/80 hover:bg-white/10 font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Sparkles className="w-4 h-4" />
            Explore New Measure
          </button>
        )}
      </div>
    </div>
  )
}

import { useState } from 'react'
import { getMeasureConfig, MeasureConfig, MeasureAnalysisOption } from '../measureConfig'
import { ChevronDown, ChevronRight, Lightbulb, TrendingUp, AlertTriangle, Link2 } from 'lucide-react'

interface MeasureAnalysisPanelProps {
  measureId: string
  station: string
  window: 'weekly' | 'daily'
  onSelectAnalysis: (query: string) => void
  compact?: boolean
}

export function MeasureAnalysisPanel({
  measureId,
  station: _station,
  window: _window,
  onSelectAnalysis,
  compact = false,
}: MeasureAnalysisPanelProps) {
  // Note: station and window are available for future use in context-aware analysis
  void _station
  void _window
  const config = getMeasureConfig(measureId)
  const [expandedSection, setExpandedSection] = useState<string | null>('options')

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section)
  }

  if (compact) {
    return (
      <CompactAnalysisPanel
        config={config}
        onSelectAnalysis={onSelectAnalysis}
      />
    )
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-blue-600" />
          <h3 className="font-bold text-slate-900">{config.label}</h3>
          {config.unit && (
            <span className="text-xs text-slate-500 bg-white px-2 py-0.5 rounded-full border border-slate-200">
              {config.unit}
            </span>
          )}
        </div>
        <p className="text-sm text-slate-600 mt-1">{config.description}</p>
      </div>

      {/* Signal Meaning */}
      <div className="px-4 py-3 border-b border-slate-100 bg-amber-50/50">
        <div className="flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <div className="text-xs font-bold text-amber-800 uppercase">What This Signal Means</div>
            <p className="text-sm text-amber-900 mt-0.5">{config.signalMeaning}</p>
          </div>
        </div>
      </div>

      {/* Analysis Options */}
      <div className="border-b border-slate-100">
        <button
          onClick={() => toggleSection('options')}
          className="w-full px-4 py-2.5 flex items-center justify-between hover:bg-slate-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-bold text-slate-900">Analysis Options</span>
            <span className="text-xs text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
              {config.analysisOptions.length}
            </span>
          </div>
          {expandedSection === 'options' ? (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-slate-400" />
          )}
        </button>
        
        {expandedSection === 'options' && (
          <div className="px-4 pb-3 space-y-2">
            {config.analysisOptions.map((option) => (
              <AnalysisOptionButton
                key={option.id}
                option={option}
                onClick={() => onSelectAnalysis(option.suggestedQuery)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Typical Causes */}
      <div className="border-b border-slate-100">
        <button
          onClick={() => toggleSection('causes')}
          className="w-full px-4 py-2.5 flex items-center justify-between hover:bg-slate-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-500" />
            <span className="text-sm font-bold text-slate-900">Common Root Causes</span>
            <span className="text-xs text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
              {config.typicalCauses.length}
            </span>
          </div>
          {expandedSection === 'causes' ? (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-slate-400" />
          )}
        </button>
        
        {expandedSection === 'causes' && (
          <div className="px-4 pb-3">
            <ul className="space-y-1.5">
              {config.typicalCauses.map((cause, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                  <span className="text-orange-400 mt-1">•</span>
                  {cause}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Related Measures */}
      {config.relatedMeasures.length > 0 && (
        <div>
          <button
            onClick={() => toggleSection('related')}
            className="w-full px-4 py-2.5 flex items-center justify-between hover:bg-slate-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Link2 className="w-4 h-4 text-purple-500" />
              <span className="text-sm font-bold text-slate-900">Related Measures</span>
              <span className="text-xs text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                {config.relatedMeasures.length}
              </span>
            </div>
            {expandedSection === 'related' ? (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-400" />
            )}
          </button>
          
          {expandedSection === 'related' && (
            <div className="px-4 pb-3">
              <div className="flex flex-wrap gap-2">
                {config.relatedMeasures.map((measure) => (
                  <span
                    key={measure}
                    className="px-2.5 py-1 text-xs font-medium bg-purple-50 text-purple-700 rounded-full border border-purple-200"
                  >
                    {measure.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                  </span>
                ))}
              </div>
              <p className="text-xs text-slate-500 mt-2">{config.benchmarkContext}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function AnalysisOptionButton({
  option,
  onClick,
}: {
  option: MeasureAnalysisOption
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-3 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50/50 transition-all group"
    >
      <div className="flex items-center justify-between">
        <span className="font-semibold text-sm text-slate-900 group-hover:text-blue-700">
          {option.label}
        </span>
        <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-blue-500 group-hover:translate-x-0.5 transition-transform" />
      </div>
      <p className="text-xs text-slate-600 mt-1">{option.description}</p>
    </button>
  )
}

function CompactAnalysisPanel({
  config,
  onSelectAnalysis,
}: {
  config: MeasureConfig
  onSelectAnalysis: (query: string) => void
}) {
  return (
    <div className="space-y-2">
      <div className="text-xs font-bold text-slate-500 uppercase">Quick Analysis</div>
      <div className="flex flex-wrap gap-2">
        {config.analysisOptions.slice(0, 4).map((option) => (
          <button
            key={option.id}
            onClick={() => onSelectAnalysis(option.suggestedQuery)}
            className="px-3 py-1.5 text-xs font-medium bg-blue-50 text-blue-700 rounded-full border border-blue-200 hover:bg-blue-100 transition-colors"
            title={option.description}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  )
}

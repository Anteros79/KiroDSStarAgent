import { Database, Upload } from 'lucide-react'
import { DatasetInfo } from '../../types'
import * as Tooltip from '@radix-ui/react-tooltip'

interface ActiveDatasetPanelProps {
  dataset?: DatasetInfo
  onUpload?: () => void
}

export function ActiveDatasetPanel({ dataset, onUpload }: ActiveDatasetPanelProps) {
  if (!dataset) {
    return (
      <div className="p-4">
        <h2 className="text-sm font-semibold text-white/70 uppercase tracking-wider mb-3">
          Active Dataset
        </h2>
        <button
          onClick={onUpload}
          className="w-full flex flex-col items-center justify-center gap-2 p-6 border-2 border-dashed border-white/20 rounded-lg hover:border-white/40 hover:bg-white/5 transition-colors"
        >
          <Upload className="w-8 h-8 text-white/50" />
          <span className="text-sm text-white/70">Upload a dataset</span>
        </button>
      </div>
    )
  }

  return (
    <div className="p-4">
      <h2 className="text-sm font-semibold text-white/70 uppercase tracking-wider mb-3">
        Active Dataset
      </h2>
      
      <div className="bg-white/10 rounded-lg p-4">
        {/* Dataset name */}
        <div className="flex items-center gap-2 mb-2">
          <Database className="w-4 h-4 text-primary-light" />
          <span className="font-medium text-white">{dataset.filename}</span>
        </div>
        
        {/* Description */}
        <p className="text-sm text-white/70 mb-4">{dataset.description}</p>
        
        {/* Row count */}
        <div className="text-xs text-white/50 mb-3">
          {dataset.rowCount.toLocaleString()} rows
        </div>
        
        {/* Column pills */}
        <div className="flex flex-wrap gap-2">
          <Tooltip.Provider delayDuration={200}>
            {dataset.columns.map((col) => (
              <Tooltip.Root key={col.name}>
                <Tooltip.Trigger asChild>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-white/10 text-white/80 hover:bg-white/20 cursor-default transition-colors">
                    {col.name}
                  </span>
                </Tooltip.Trigger>
                <Tooltip.Portal>
                  <Tooltip.Content
                    className="bg-slate-900 text-white text-xs px-2 py-1 rounded shadow-lg"
                    sideOffset={5}
                  >
                    {col.dtype}
                    <Tooltip.Arrow className="fill-slate-900" />
                  </Tooltip.Content>
                </Tooltip.Portal>
              </Tooltip.Root>
            ))}
          </Tooltip.Provider>
        </div>
      </div>
    </div>
  )
}

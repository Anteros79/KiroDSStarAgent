import { Sparkles, Wifi, WifiOff, Settings, Cpu } from 'lucide-react'
import { SystemStatus } from '../../types'

interface HeaderProps {
  status: SystemStatus | null
}

export function Header({ status }: HeaderProps) {
  const isConnected = status?.status === 'ready'
  
  // Parse model info (format: "provider:model_id")
  const parseModel = (model: string) => {
    const [provider, ...rest] = model.split(':')
    const modelId = rest.join(':')
    return { provider, modelId }
  }
  
  const modelInfo = status?.model ? parseModel(status.model) : null

  return (
    <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6 flex-shrink-0">
      {/* Logo and title */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-semibold text-slate-900">DS-STAR Workbench</h1>
          <p className="text-xs text-slate-500">Iterative Agentic Data Science Workflow</p>
        </div>
      </div>

      {/* Right side - status and settings */}
      <div className="flex items-center gap-4">
        {/* Connection status */}
        <div className="flex items-center gap-2 text-sm">
          {isConnected ? (
            <>
              <div className="status-dot-success" />
              <Wifi className="w-4 h-4 text-success" />
              <span className="text-slate-600">Connected</span>
            </>
          ) : (
            <>
              <div className="status-dot-error" />
              <WifiOff className="w-4 h-4 text-error" />
              <span className="text-slate-600">Disconnected</span>
            </>
          )}
        </div>

        {/* Model info */}
        {modelInfo && (
          <div className="flex items-center gap-2 text-xs bg-slate-100 px-3 py-1.5 rounded-full">
            <Cpu className="w-3.5 h-3.5 text-primary" />
            <span className="font-medium text-primary">{modelInfo.provider}</span>
            <span className="text-slate-400">|</span>
            <span className="text-slate-600">{modelInfo.modelId}</span>
          </div>
        )}

        {/* Settings button */}
        <button className="btn-ghost p-2 rounded-lg" title="Settings">
          <Settings className="w-5 h-5" />
        </button>
      </div>
    </header>
  )
}

import { ExecutionResult } from '../../types'
import { AlertCircle, CheckCircle, Clock } from 'lucide-react'
import clsx from 'clsx'

interface ExecutionOutputProps {
  result: ExecutionResult
}

export function ExecutionOutput({ result }: ExecutionOutputProps) {
  const formatOutput = (output: string) => {
    // Split into lines and format
    return output.split('\n').map((line, i) => {
      // Highlight error lines
      const isError = line.toLowerCase().includes('error') || line.toLowerCase().includes('traceback')
      const isWarning = line.toLowerCase().includes('warning')
      
      return (
        <div
          key={i}
          className={clsx(
            'whitespace-pre',
            isError && 'text-error',
            isWarning && 'text-warning'
          )}
        >
          {line || '\u00A0'}
        </div>
      )
    })
  }

  return (
    <div className="rounded-lg overflow-hidden border border-slate-200">
      {/* Header */}
      <div className={clsx(
        'flex items-center justify-between px-3 py-2 text-sm',
        result.success ? 'bg-success/10' : 'bg-error/10'
      )}>
        <div className="flex items-center gap-2">
          {result.success ? (
            <CheckCircle className="w-4 h-4 text-success" />
          ) : (
            <AlertCircle className="w-4 h-4 text-error" />
          )}
          <span className={result.success ? 'text-success' : 'text-error'}>
            {result.success ? 'Execution Successful' : 'Execution Failed'}
          </span>
        </div>
        <div className="flex items-center gap-1 text-slate-500">
          <Clock className="w-3 h-3" />
          {result.duration_ms}ms
        </div>
      </div>

      {/* Output content */}
      <div className="bg-slate-900 p-4 font-mono text-sm text-slate-300 overflow-x-auto max-h-64 overflow-y-auto scrollbar-thin">
        {result.error ? (
          <div className="text-error">{result.error}</div>
        ) : (
          formatOutput(result.output)
        )}
      </div>
    </div>
  )
}

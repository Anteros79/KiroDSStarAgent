import ReactMarkdown from 'react-markdown'
import { AlertCircle, CheckCircle, Clock } from 'lucide-react'
import clsx from 'clsx'

interface AgentResponseProps {
  output: string
  success: boolean
  duration_ms: number
  error?: string
}

export function AgentResponse({ output, success, duration_ms, error }: AgentResponseProps) {
  // Format the output for better display
  const formatOutput = (text: string) => {
    // Convert ** to markdown bold if not already
    let formatted = text
    
    // Convert "Key: Value" patterns to bold keys
    formatted = formatted.replace(/^(\*\*[^*]+\*\*:)/gm, '$1')
    
    // Ensure proper line breaks
    formatted = formatted.replace(/\n{3,}/g, '\n\n')
    
    return formatted
  }

  return (
    <div className="rounded-lg overflow-hidden border border-slate-200">
      {/* Header */}
      <div className={clsx(
        'flex items-center justify-between px-4 py-2 text-sm',
        success ? 'bg-success/10' : 'bg-error/10'
      )}>
        <div className="flex items-center gap-2">
          {success ? (
            <CheckCircle className="w-4 h-4 text-success" />
          ) : (
            <AlertCircle className="w-4 h-4 text-error" />
          )}
          <span className={clsx('font-medium', success ? 'text-success' : 'text-error')}>
            {success ? 'Analysis Complete' : 'Analysis Failed'}
          </span>
        </div>
        <div className="flex items-center gap-1 text-slate-500">
          <Clock className="w-3 h-3" />
          <span>{duration_ms}ms</span>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="bg-error/5 p-4 border-b border-error/20">
          <pre className="text-error text-sm font-mono whitespace-pre-wrap">{error}</pre>
        </div>
      )}

      {/* Formatted response */}
      <div className="bg-white p-4">
        <div className="prose prose-slate prose-sm max-w-none">
          <ReactMarkdown
            components={{
              h1: ({ children }) => (
                <h1 className="text-xl font-bold text-slate-900 mt-4 mb-3 first:mt-0 border-b border-slate-200 pb-2">
                  {children}
                </h1>
              ),
              h2: ({ children }) => (
                <h2 className="text-lg font-semibold text-slate-800 mt-4 mb-2">
                  {children}
                </h2>
              ),
              h3: ({ children }) => (
                <h3 className="text-base font-semibold text-slate-700 mt-3 mb-2">
                  {children}
                </h3>
              ),
              p: ({ children }) => (
                <p className="text-slate-700 mb-3 leading-relaxed">
                  {children}
                </p>
              ),
              ul: ({ children }) => (
                <ul className="list-disc list-outside ml-5 mb-4 text-slate-700 space-y-2">
                  {children}
                </ul>
              ),
              ol: ({ children }) => (
                <ol className="list-decimal list-outside ml-5 mb-4 text-slate-700 space-y-2">
                  {children}
                </ol>
              ),
              li: ({ children }) => (
                <li className="text-slate-700 pl-1">
                  {children}
                </li>
              ),
              strong: ({ children }) => (
                <strong className="font-semibold text-slate-900">
                  {children}
                </strong>
              ),
              em: ({ children }) => (
                <em className="italic text-slate-600">
                  {children}
                </em>
              ),
              code: ({ className, children }) => {
                const isBlock = className?.includes('language-')
                if (isBlock) {
                  return (
                    <code className="block bg-slate-900 text-slate-100 p-4 rounded-lg text-sm font-mono overflow-x-auto my-3">
                      {children}
                    </code>
                  )
                }
                return (
                  <code className="bg-slate-100 text-primary px-1.5 py-0.5 rounded text-sm font-mono">
                    {children}
                  </code>
                )
              },
              pre: ({ children }) => (
                <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg text-sm font-mono overflow-x-auto my-3">
                  {children}
                </pre>
              ),
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 border-primary/30 pl-4 py-1 my-3 text-slate-600 italic">
                  {children}
                </blockquote>
              ),
              table: ({ children }) => (
                <div className="overflow-x-auto my-4">
                  <table className="min-w-full border border-slate-200 rounded-lg overflow-hidden">
                    {children}
                  </table>
                </div>
              ),
              thead: ({ children }) => (
                <thead className="bg-slate-100">{children}</thead>
              ),
              th: ({ children }) => (
                <th className="px-4 py-2 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider border-b border-slate-200">
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td className="px-4 py-2 text-sm text-slate-700 border-b border-slate-100">
                  {children}
                </td>
              ),
              tr: ({ children }) => (
                <tr className="hover:bg-slate-50 transition-colors">{children}</tr>
              ),
            }}
          >
            {formatOutput(output)}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  )
}

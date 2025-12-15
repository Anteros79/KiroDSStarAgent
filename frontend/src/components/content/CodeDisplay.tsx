import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Copy, Check, ChevronDown, ChevronUp } from 'lucide-react'
import clsx from 'clsx'

interface CodeDisplayProps {
  code: string
  language?: string
  maxLines?: number
}

export function CodeDisplay({ code, language = 'python', maxLines = 15 }: CodeDisplayProps) {
  const [copied, setCopied] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)

  const lines = code.split('\n')
  const shouldCollapse = lines.length > maxLines
  const displayCode = shouldCollapse && !isExpanded 
    ? lines.slice(0, maxLines).join('\n') 
    : code

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative group rounded-lg overflow-hidden">
      {/* Copy button */}
      <button
        onClick={handleCopy}
        className={clsx(
          'absolute top-2 right-2 z-10 p-2 rounded-md transition-all',
          'bg-slate-700 hover:bg-slate-600',
          'opacity-0 group-hover:opacity-100',
          copied && 'opacity-100'
        )}
        title="Copy code"
      >
        {copied ? (
          <Check className="w-4 h-4 text-success" />
        ) : (
          <Copy className="w-4 h-4 text-slate-300" />
        )}
      </button>

      {/* Code block */}
      <SyntaxHighlighter
        language={language}
        style={oneDark}
        showLineNumbers
        customStyle={{
          margin: 0,
          borderRadius: '0.5rem',
          fontSize: '0.875rem',
        }}
        lineNumberStyle={{
          minWidth: '2.5em',
          paddingRight: '1em',
          color: '#6b7280',
          userSelect: 'none',
        }}
      >
        {displayCode}
      </SyntaxHighlighter>

      {/* Show more/less toggle */}
      {shouldCollapse && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-center gap-1 py-2 bg-slate-800 text-slate-400 hover:text-slate-200 text-sm transition-colors"
        >
          {isExpanded ? (
            <>
              <ChevronUp className="w-4 h-4" />
              Show less
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4" />
              Show {lines.length - maxLines} more lines
            </>
          )}
        </button>
      )}
    </div>
  )
}

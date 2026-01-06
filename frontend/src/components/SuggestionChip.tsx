import React from 'react'
import { Loader2 } from 'lucide-react'

interface SuggestionChipProps {
  label: string
  query: string
  icon?: React.ReactNode
  onClick: (query: string) => void
  isLoading?: boolean
  disabled?: boolean
}

export function SuggestionChip({
  label,
  query,
  icon,
  onClick,
  isLoading = false,
  disabled = false,
}: SuggestionChipProps) {
  const handleClick = () => {
    if (!disabled && !isLoading) {
      onClick(query)
    }
  }

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      handleClick()
    }
  }

  return (
    <button
      type="button"
      className={`
        inline-flex items-center gap-1.5 md:gap-2 px-2.5 md:px-3 py-1.5 md:py-2 rounded-lg text-xs md:text-sm font-medium
        transition-all duration-200 border min-w-0 flex-shrink-0
        ${
          disabled || isLoading
            ? 'bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed'
            : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50 hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 cursor-pointer'
        }
      `}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      disabled={disabled || isLoading}
      aria-label={`Run query: ${query}`}
      tabIndex={0}
    >
      {isLoading ? (
        <Loader2 className="w-3 h-3 md:w-4 md:h-4 animate-spin text-slate-400 flex-shrink-0" />
      ) : (
        icon && <span className="flex-shrink-0">{icon}</span>
      )}
      
      <span className={`${isLoading ? 'text-slate-400' : ''} truncate`}>
        {label}
      </span>
    </button>
  )
}
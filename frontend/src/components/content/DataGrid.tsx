import { useMemo, useState } from 'react'
import { ChevronUp, ChevronDown, Table2 } from 'lucide-react'

interface DataGridProps {
  data: Record<string, any>[]
  title?: string
}

export function DataGrid({ data, title }: DataGridProps) {
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

  const columns = useMemo(() => {
    if (data.length === 0) return []
    return Object.keys(data[0])
  }, [data])

  const sortedData = useMemo(() => {
    if (!sortColumn) return data
    return [...data].sort((a, b) => {
      const aVal = a[sortColumn]
      const bVal = b[sortColumn]
      
      // Handle numeric sorting
      const aNum = parseFloat(aVal)
      const bNum = parseFloat(bVal)
      
      if (!isNaN(aNum) && !isNaN(bNum)) {
        return sortDirection === 'asc' ? aNum - bNum : bNum - aNum
      }
      
      // String sorting
      const aStr = String(aVal || '')
      const bStr = String(bVal || '')
      return sortDirection === 'asc' 
        ? aStr.localeCompare(bStr) 
        : bStr.localeCompare(aStr)
    })
  }, [data, sortColumn, sortDirection])

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column)
      setSortDirection('asc')
    }
  }

  const formatValue = (value: any) => {
    if (value === null || value === undefined) return '-'
    if (typeof value === 'number') {
      // Format percentages
      if (value >= 0 && value <= 1) {
        return `${(value * 100).toFixed(1)}%`
      }
      // Format large numbers
      if (value >= 1000) {
        return value.toLocaleString()
      }
      // Format decimals
      if (!Number.isInteger(value)) {
        return value.toFixed(2)
      }
    }
    return String(value)
  }

  if (data.length === 0) return null

  return (
    <div className="rounded-lg border border-slate-200 overflow-hidden">
      {title && (
        <div className="flex items-center gap-2 px-4 py-2 bg-slate-50 border-b border-slate-200">
          <Table2 className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium text-slate-700">{title}</span>
          <span className="text-xs text-slate-500">({data.length} rows)</span>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-slate-100">
              {columns.map(col => (
                <th
                  key={col}
                  onClick={() => handleSort(col)}
                  className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider cursor-pointer hover:bg-slate-200 transition-colors select-none"
                >
                  <div className="flex items-center gap-1">
                    {col.replace(/_/g, ' ')}
                    {sortColumn === col && (
                      sortDirection === 'asc' 
                        ? <ChevronUp className="w-3 h-3" />
                        : <ChevronDown className="w-3 h-3" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {sortedData.map((row, i) => (
              <tr key={i} className="hover:bg-slate-50 transition-colors">
                {columns.map(col => (
                  <td key={col} className="px-4 py-3 text-sm text-slate-700 whitespace-nowrap">
                    {formatValue(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

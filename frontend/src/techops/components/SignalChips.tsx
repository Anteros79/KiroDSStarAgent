import { ActiveSignalsResponse } from '../types'

function badgeClasses(status: string) {
  if (status === 'critical') return 'bg-rose-50 text-rose-700 border-rose-200'
  if (status === 'warning') return 'bg-amber-50 text-amber-800 border-amber-200'
  return 'bg-slate-50 text-slate-700 border-slate-200'
}

export function SignalChips({
  signals,
  onClickSignal,
}: {
  signals: ActiveSignalsResponse | null
  onClickSignal?: (args: { kpi_id: string; window?: 'weekly' | 'daily'; point_t?: string }) => void
}) {
  const list = signals?.signals ?? []

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="text-xs font-semibold text-slate-500 tracking-wide mr-2">ACTIVE SIGNALS:</div>
      {list.length === 0 ? (
        <span className="px-3 py-1 rounded-full text-xs border bg-white text-slate-600">
          None detected
        </span>
      ) : (
        list.map((s) => (
          <button
            key={s.signal_id}
            className={[
              'inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold border',
              badgeClasses(s.status),
              onClickSignal ? 'hover:opacity-90 cursor-pointer' : 'cursor-default',
            ].join(' ')}
            title={`${s.signal_id} (${s.kpi_id})`}
            type="button"
            onClick={() => {
              if (!onClickSignal) return
              onClickSignal({ kpi_id: s.kpi_id, window: s.window, point_t: s.latest_point_t || undefined })
            }}
          >
            <span className="inline-block h-2 w-2 rounded-full bg-current opacity-60" />
            {s.kpi_id.split('_').join(' ')}
          </button>
        ))
      )}
    </div>
  )
}

import Plot from 'react-plotly.js'
import { TechOpsKPISeries } from '../types'

function statusPill(status: string) {
  if (status === 'critical') return 'bg-rose-50 text-rose-700 border-rose-200'
  if (status === 'warning') return 'bg-amber-50 text-amber-800 border-amber-200'
  return 'bg-emerald-50 text-emerald-700 border-emerald-200'
}

function formatValue(v: number, unit: string, decimals: number) {
  const n = v.toFixed(decimals)
  if (unit === '%') return `${n}%`
  if (unit === 'count') return `${Math.round(v)}`
  return n
}

export function KpiTrendCard({
  series,
  window,
  onClick,
}: {
  series: TechOpsKPISeries
  window: 'weekly' | 'daily'
  onClick: (pointT?: string) => void
}) {
  const { kpi, points } = series
  const x = points.map((p) => p.t)
  const y = points.map((p) => p.value)

  const ul = kpi.ul
  const ll = kpi.ll

  const last = series.past_value
  const delta = series.past_delta

  const deltaColor =
    delta > 0 ? 'text-emerald-700' : delta < 0 ? 'text-slate-600' : 'text-slate-500'

  return (
    <button
      type="button"
      className="w-full text-left bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition-shadow cursor-pointer overflow-hidden focus:outline-none focus:ring-2 focus:ring-[#0B2A55]/40"
      onClick={() => onClick(undefined)}
      aria-label={`${kpi.label} KPI card`}
    >
      <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
        <div className="font-semibold text-slate-900">{kpi.label}</div>
        <span className={['px-2.5 py-1 rounded-full text-xs font-semibold border', statusPill(series.signal_state)].join(' ')}>
          {series.signal_state.toUpperCase()}
        </span>
      </div>

      <div className="px-4 py-3 grid grid-cols-12 gap-4 items-center">
        <div className="col-span-4">
          <div className="text-xs text-slate-500">Mean</div>
          <div className="text-sm font-semibold text-slate-800">
            {formatValue(series.mean, kpi.unit, kpi.decimals)}
          </div>
          <div className="mt-2 text-[11px] text-slate-500 leading-tight">
            <div>UL/LL: {formatValue(ul, kpi.unit, kpi.decimals)} / {formatValue(ll, kpi.unit, kpi.decimals)}</div>
            <div>Goal: {formatValue(kpi.goal, kpi.unit, kpi.decimals)}</div>
          </div>
        </div>

        <div className="col-span-6">
          <Plot
            data={[
              {
                type: 'scatter',
                mode: 'lines',
                x,
                y,
                line: { color: '#1E3A8A', width: 2 },
                hovertemplate: `${window === 'weekly' ? 'Week' : 'Day'}: %{x}<br>Value: %{y}<extra></extra>`,
              } as any,
            ]}
            layout={{
              height: 90,
              margin: { l: 10, r: 10, t: 10, b: 20 },
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(0,0,0,0)',
              xaxis: { showgrid: false, zeroline: false, showticklabels: false },
              yaxis: { showgrid: false, zeroline: false, showticklabels: false },
              shapes: [
                {
                  type: 'line',
                  xref: 'paper',
                  x0: 0,
                  x1: 1,
                  yref: 'y',
                  y0: ul,
                  y1: ul,
                  line: { color: '#DC2626', width: 1, dash: 'dot' },
                },
                {
                  type: 'line',
                  xref: 'paper',
                  x0: 0,
                  x1: 1,
                  yref: 'y',
                  y0: ll,
                  y1: ll,
                  line: { color: '#7C3AED', width: 1, dash: 'dot' },
                },
              ],
            }}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: '100%' }}
            onClick={(ev) => {
              const pt = (ev?.points?.[0] as any)?.x as string | undefined
              onClick(pt)
            }}
          />
        </div>

        <div className="col-span-2 text-right">
          <div className="text-xs text-slate-500">Past {window === 'weekly' ? 'Week' : 'Day'}</div>
          <div className="text-xl font-extrabold text-slate-900">
            {formatValue(last, kpi.unit, kpi.decimals)}
          </div>
          <div className={['text-xs font-semibold', deltaColor].join(' ')}>
            {delta > 0 ? '▲' : delta < 0 ? '▼' : '→'} {formatValue(Math.abs(delta), kpi.unit, kpi.decimals)}
          </div>
        </div>
      </div>
    </button>
  )
}



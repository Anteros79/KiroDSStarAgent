import Plot from 'react-plotly.js'
import { TechOpsKPISeries } from '../types'

const SW_BLUE = '#304CB2'
const SW_RED = '#C4122F'
const SW_GOLD = '#FFB612'
const SW_CHARCOAL = '#111827'
const SW_SLATE = '#475569'

function clamp(n: number, min: number, max: number) {
  return Math.min(max, Math.max(min, n))
}

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
  dailyDaysToShow,
  weeklyStagesToShow,
}: {
  series: TechOpsKPISeries
  window: 'weekly' | 'daily'
  onClick: (pointT?: string) => void
  dailyDaysToShow?: number
  weeklyStagesToShow?: number
}) {
  const PlotAny: any = Plot
  const { kpi, points } = series

  const lastPoint = points[points.length - 1]
  const ucl = lastPoint?.ucl ?? series.npl_ucl ?? kpi.ul
  const lcl = lastPoint?.lcl ?? series.npl_lcl ?? kpi.ll
  const cl = lastPoint?.cl ?? series.npl_cl ?? series.mean

  const maxPhase = Math.max(1, ...points.map((p) => p.phase_number ?? 1))
  const stagesToShow = clamp(weeklyStagesToShow ?? 2, 1, maxPhase)
  const minPhaseToKeep = Math.max(1, maxPhase - stagesToShow + 1)
  const phaseStartIdx = Math.max(
    0,
    points.findIndex((p) => (p.phase_number ?? 1) >= minPhaseToKeep),
  )

  const daysMax = Math.min(30, points.length)
  const daysToShow = clamp(dailyDaysToShow ?? 7, Math.min(7, daysMax), daysMax)

  const visiblePoints =
    window === 'daily' ? points.slice(-daysToShow) : points.slice(phaseStartIdx)

  const x = visiblePoints.map((p) => p.t)
  const y = visiblePoints.map((p) => p.value)
  const clSeries = visiblePoints.map((p) => p.cl ?? cl)
  const uclSeries = visiblePoints.map((p) => p.ucl ?? ucl)
  const lclSeries = visiblePoints.map((p) => p.lcl ?? lcl)

  const stageChangeTs: string[] = []
  for (let i = 1; i < visiblePoints.length; i++) {
    const prev = visiblePoints[i - 1].phase_number ?? 1
    const cur = visiblePoints[i].phase_number ?? 1
    if (cur !== prev) stageChangeTs.push(visiblePoints[i].t)
  }

  const weeklyTickVals = x.length >= 3 ? [x[0], x[Math.floor(x.length / 2)], x[x.length - 1]] : x
  const weeklyTickText = weeklyTickVals.map((t) => {
    const d = new Date(t)
    const md = d.toLocaleDateString(undefined, { month: '2-digit', day: '2-digit' })
    return `Wk<br>${md}`
  })

  const last = series.past_value
  const delta = series.past_delta

  const deltaColor =
    delta > 0 ? 'text-emerald-700' : delta < 0 ? 'text-slate-600' : 'text-slate-500'

  const dailyTickVals = (() => {
    if (x.length <= 10) return x
    const last7 = x.slice(-7)
    const first = x[0]
    return first === last7[0] ? last7 : [first, ...last7]
  })()

  const dailyTickText = dailyTickVals.map((t, idx) => {
    const d = new Date(t)
    const md = d.toLocaleDateString(undefined, { month: '2-digit', day: '2-digit' })
    const lastWeekStart = Math.max(0, dailyTickVals.length - 7)
    const isLastWeek = idx >= lastWeekStart
    if (!isLastWeek && x.length > 10) return md
    const dow = d.toLocaleDateString(undefined, { weekday: 'short' })
    const weekend = d.getDay() === 0 || d.getDay() === 6
    const color = weekend ? SW_RED : SW_BLUE
    return `<span style="color:${color}"><b>${dow}</b></span><br>${md}`
  })

  return (
    <button
      type="button"
      className="w-full text-left bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition-shadow cursor-pointer overflow-hidden focus:outline-none focus:ring-2 focus:ring-[#0B2A55]/40"
      onClick={() => onClick(undefined)}
      aria-label={`${kpi.label} KPI card`}
    >
      <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
        <div className="font-semibold text-slate-900">{kpi.label}</div>
        <span
          className={[
            'px-2.5 py-1 rounded-full text-xs font-semibold border',
            statusPill(series.signal_state),
          ].join(' ')}
        >
          {series.signal_state.toUpperCase()}
        </span>
      </div>

      <div className="px-4 py-3 grid grid-cols-12 gap-3 items-center">
        <div className="col-span-2">
          <div className="text-xs text-slate-500">Mean</div>
          <div className="text-sm font-semibold text-slate-800">
            {formatValue(series.mean, kpi.unit, kpi.decimals)}
          </div>
          <div className="mt-2 text-[11px] text-slate-500 leading-tight">
            <div>
              UCL/LCL: {formatValue(ucl, kpi.unit, kpi.decimals)} / {formatValue(lcl, kpi.unit, kpi.decimals)}
            </div>
            <div>CL: {formatValue(cl, kpi.unit, kpi.decimals)}</div>
          </div>
        </div>

        <div className="col-span-9">
          <PlotAny
            data={[
              window === 'daily'
                ? ({
                    type: 'bar',
                    x,
                    y,
                    marker: { color: visiblePoints.map((p) => (p.signal_state === 'critical' ? SW_RED : SW_BLUE)) },
                    hovertemplate: 'Day: %{x}<br>Value: %{y}<extra></extra>',
                  } as any)
                : ({
                    type: 'scatter',
                    mode: 'lines+markers',
                    x,
                    y,
                    marker: {
                      size: 6,
                      color: visiblePoints.map((p) => (p.signal_state === 'critical' ? SW_RED : SW_BLUE)),
                    },
                    line: { color: SW_BLUE, width: 2 },
                    hovertemplate: 'Week: %{x}<br>Value: %{y}<extra></extra>',
                  } as any),
              { type: 'scatter', mode: 'lines', x, y: uclSeries, line: { color: SW_RED, width: 1, dash: 'dot' }, hoverinfo: 'skip' } as any,
              { type: 'scatter', mode: 'lines', x, y: lclSeries, line: { color: SW_GOLD, width: 1, dash: 'dot' }, hoverinfo: 'skip' } as any,
              { type: 'scatter', mode: 'lines', x, y: clSeries, line: { color: SW_CHARCOAL, width: 1, dash: 'dash' }, hoverinfo: 'skip' } as any,
            ]}
            layout={{
              height: 140,
              margin: { l: 12, r: 12, t: 10, b: window === 'daily' ? 44 : 26 },
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(0,0,0,0)',
              dragmode: 'zoom',
              xaxis:
                window === 'daily'
                  ? {
                      showgrid: false,
                      zeroline: false,
                      showticklabels: true,
                      tickmode: 'array',
                      tickvals: dailyTickVals,
                      ticktext: dailyTickText,
                      tickfont: { size: 10, color: SW_CHARCOAL },
                      automargin: true,
                    }
                  : {
                      showgrid: false,
                      zeroline: false,
                      showticklabels: true,
                      tickmode: 'array',
                      tickvals: weeklyTickVals,
                      ticktext: weeklyTickText,
                      tickfont: { size: 10, color: SW_CHARCOAL },
                      automargin: true,
                    },
              yaxis: {
                showgrid: false,
                zeroline: false,
                showticklabels: true,
                nticks: 3,
                tickfont: { size: 9, color: SW_CHARCOAL },
              },
              shapes: stageChangeTs.map((t) => ({
                type: 'line',
                xref: 'x',
                x0: t,
                x1: t,
                yref: 'paper',
                y0: 0,
                y1: 1,
                line: { color: SW_SLATE, width: 1, dash: 'dot' },
              })),
            }}
            config={{ displayModeBar: false, responsive: true, scrollZoom: true }}
            style={{ width: '100%' }}
            onClick={(ev: any) => {
              ev?.event?.stopPropagation?.()
              const pt = (ev?.points?.[0] as any)?.x as string | undefined
              onClick(pt)
            }}
          />
        </div>

        <div className="col-span-1 text-right">
          <div className="text-xs text-slate-500">Past {window === 'weekly' ? 'Week' : 'Day'}</div>
          <div className="text-xl font-extrabold text-slate-900">{formatValue(last, kpi.unit, kpi.decimals)}</div>
          <div className={['text-xs font-semibold', deltaColor].join(' ')}>
            {delta > 0 ? '+' : delta < 0 ? '-' : '0'} {formatValue(Math.abs(delta), kpi.unit, kpi.decimals)}
          </div>
        </div>
      </div>
    </button>
  )
}

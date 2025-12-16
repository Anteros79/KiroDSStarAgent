import { useEffect, useMemo, useState } from 'react'
import { techOpsApi } from '../api'
import { ActiveSignalsResponse, InvestigationRecord, TechOpsDashboardResponse } from '../types'
import { SignalChips } from '../components/SignalChips'
import { KpiTrendCard } from '../components/KpiTrendCard'

export function DashboardPage({
  station,
  onOpenInvestigation,
  onSelectInvestigation,
}: {
  station: string
  onOpenInvestigation: (args: { kpi_id: string; window: 'weekly' | 'daily'; point_t?: string }) => void
  onSelectInvestigation?: (investigation_id: string) => void
}) {
  const [window, setWindow] = useState<'weekly' | 'daily'>('weekly')
  const [weekly, setWeekly] = useState<TechOpsDashboardResponse | null>(null)
  const [daily, setDaily] = useState<TechOpsDashboardResponse | null>(null)
  const [signals, setSignals] = useState<ActiveSignalsResponse | null>(null)
  const [investigations, setInvestigations] = useState<InvestigationRecord[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    Promise.all([
      techOpsApi.getDashboardWeekly(station),
      techOpsApi.getDashboardDaily(station),
      techOpsApi.getActiveSignals(station),
      techOpsApi.listInvestigations(station),
    ])
      .then(([w, d, s, invs]) => {
        if (cancelled) return
        setWeekly(w)
        setDaily(d)
        setSignals(s)
        setInvestigations(invs)
        setLoading(false)
      })
      .catch((e) => {
        if (cancelled) return
        setError(e instanceof Error ? e.message : 'Failed to load dashboard')
        setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [station])

  const data = useMemo(() => (window === 'weekly' ? weekly : daily), [window, weekly, daily])
  const signalByKpi = useMemo(() => {
    const m = new Map<string, string>()
    for (const s of signals?.signals || []) m.set(s.kpi_id, s.status)
    return m
  }, [signals])

  const invGrid = (investigations || []).slice().sort((a, b) => (a.created_at < b.created_at ? 1 : -1))

  return (
    <div className="px-6 py-6">
      <div className="max-w-7xl mx-auto space-y-5">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <h2 className="text-2xl font-extrabold text-slate-900">Operational Metrics Dashboard</h2>
            <p className="text-sm text-slate-600 mt-1">
              Station <span className="font-semibold">{station}</span> · Toggle weekly vs daily views and click any KPI to investigate.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="bg-white border border-slate-200 rounded-xl p-1 flex">
              <button
                className={[
                  'px-3 py-2 rounded-lg text-sm font-semibold transition-colors',
                  window === 'weekly' ? 'bg-[#0B2A55] text-white' : 'text-slate-700 hover:bg-slate-50',
                ].join(' ')}
                onClick={() => setWindow('weekly')}
              >
                Weekly Trend
              </button>
              <button
                className={[
                  'px-3 py-2 rounded-lg text-sm font-semibold transition-colors',
                  window === 'daily' ? 'bg-[#0B2A55] text-white' : 'text-slate-700 hover:bg-slate-50',
                ].join(' ')}
                onClick={() => setWindow('daily')}
              >
                Daily (30d)
              </button>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl px-4 py-2 text-sm text-slate-700">
              Date Range: <span className="font-semibold">{window === 'weekly' ? 'Rolling 53 Weeks' : 'Last 30 Days'}</span>
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <SignalChips signals={signals} />
        </div>

        {loading && (
          <div className="bg-white border border-slate-200 rounded-xl p-6 text-slate-600">
            Loading dashboard…
          </div>
        )}

        {error && (
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-rose-800">
            {error}
          </div>
        )}

        {!loading && !error && data && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {data.kpis.map((series) => (
              <KpiTrendCard
                key={series.kpi.id}
                series={series}
                window={data.window}
                onClick={(pointT) => onOpenInvestigation({ kpi_id: series.kpi.id, window: data.window, point_t: pointT })}
              />
            ))}
          </div>
        )}

        {!loading && !error && investigations && (
          <div className="bg-white border border-slate-200 rounded-xl p-5">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-lg font-extrabold text-slate-900">Station Signal Monitor</div>
                <div className="text-sm text-slate-600 mt-1">
                  Investigations for <span className="font-semibold">{station}</span>. Click a card to review details.
                </div>
              </div>
              <div className="text-sm text-slate-600">
                Total: <span className="font-bold text-slate-900">{invGrid.length}</span>
              </div>
            </div>

            {invGrid.length === 0 ? (
              <div className="mt-4 text-slate-600">No investigations yet. Click any KPI above to start one.</div>
            ) : (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {invGrid.map((inv) => {
                  const sig = (signalByKpi.get(inv.kpi_id) || 'none') as 'none' | 'warning' | 'critical'
                  const sigStyle =
                    sig === 'critical'
                      ? 'bg-rose-50 border-rose-200 text-rose-800'
                      : sig === 'warning'
                        ? 'bg-amber-50 border-amber-200 text-amber-800'
                        : 'bg-slate-50 border-slate-200 text-slate-700'

                  return (
                    <button
                      key={inv.investigation_id}
                      onClick={() => onSelectInvestigation?.(inv.investigation_id)}
                      className="text-left rounded-xl border border-slate-200 bg-white hover:bg-slate-50 transition-colors p-4"
                      title="Open investigation"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-xs text-slate-500 font-semibold">INVESTIGATION</div>
                          <div className="text-sm font-extrabold text-slate-900">#{inv.investigation_id}</div>
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-extrabold border ${sigStyle}`}>
                          {sig.toUpperCase()}
                        </span>
                      </div>

                      <div className="mt-3">
                        <div className="text-xs text-slate-500 font-semibold">KPI</div>
                        <div className="text-sm font-bold text-slate-900">{inv.kpi_id.split('_').join(' ')}</div>
                      </div>

                      <div className="mt-3 grid grid-cols-2 gap-3">
                        <div>
                          <div className="text-xs text-slate-500 font-semibold">STATUS</div>
                        <div className="text-sm font-bold text-slate-900">{String(inv.status || '').toUpperCase()}</div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-500 font-semibold">WINDOW</div>
                          <div className="text-sm font-bold text-slate-900">{String(inv.window || '').toUpperCase()}</div>
                        </div>
                      </div>

                      <div className="mt-3">
                        <div className="text-xs text-slate-500 font-semibold">FINAL ROOT CAUSE</div>
                        <div className="text-sm font-bold text-slate-900">
                          {inv.final_root_cause ? inv.final_root_cause : '—'}
                        </div>
                      </div>

                      <div className="mt-3 flex items-center justify-between text-xs text-slate-600">
                        <span>
                          Actions: <span className="font-bold text-slate-900">{inv.final_actions?.length || 0}</span>
                        </span>
                        <span>
                          Evidence: <span className="font-bold text-slate-900">{inv.final_evidence?.length || 0}</span>
                        </span>
                      </div>
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}



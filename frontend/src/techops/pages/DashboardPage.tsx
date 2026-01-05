import { useEffect, useMemo, useState } from 'react'
import { techOpsApi } from '../api'
import { ActiveSignalsResponse, InvestigationRecord, TechOpsDashboardResponse } from '../types'
import { SignalChips } from '../components/SignalChips'
import { KpiTrendCard } from '../components/KpiTrendCard'
import { Clock, CheckCircle2, AlertTriangle, FileSearch } from 'lucide-react'

export function DashboardPage({
  station,
  summaryLevel = 'station',
  onOpenInvestigation,
  onSelectInvestigation,
}: {
  station: string
  summaryLevel?: 'station' | 'region' | 'company'
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
  const [dailyDaysToShow, setDailyDaysToShow] = useState(7)
  const [weeklyStagesToShow, setWeeklyStagesToShow] = useState(99)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    Promise.all([
      techOpsApi.getDashboardWeekly(station, summaryLevel),
      techOpsApi.getDashboardDaily(station, summaryLevel),
      techOpsApi.getActiveSignals(station, summaryLevel),
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
  }, [station, summaryLevel])

  const maxWeeklyPhases = useMemo(() => {
    const w = weekly
    if (!w?.kpis?.length) return 1
    let max = 1
    for (const series of w.kpis) {
      for (const p of series.points) max = Math.max(max, p.phase_number ?? 1)
    }
    return max
  }, [weekly])

  // Initialize stages to show at max when data loads
  useEffect(() => {
    if (maxWeeklyPhases > 1) {
      setWeeklyStagesToShow(maxWeeklyPhases)
    }
  }, [maxWeeklyPhases])

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
              Station <span className="font-semibold">{station}</span> - Toggle weekly vs daily views and click any KPI
              to investigate.
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
              Date Range:{' '}
              <span className="font-semibold">{window === 'weekly' ? 'Rolling 53 Weeks' : 'Last 30 Days'}</span>
            </div>

            {window === 'daily' ? (
              <div className="bg-white border border-slate-200 rounded-xl px-4 py-2 text-sm text-slate-700 flex items-center gap-3">
                <span className="font-semibold">Zoom:</span>
                <input
                  type="range"
                  min={7}
                  max={30}
                  step={1}
                  value={dailyDaysToShow}
                  onChange={(e) => setDailyDaysToShow(Number(e.target.value))}
                  className="w-40"
                  aria-label="Daily zoom slider (days)"
                />
                <span className="tabular-nums">{dailyDaysToShow}d</span>
              </div>
            ) : (
              <div className="bg-white border border-slate-200 rounded-xl px-4 py-2 text-sm text-slate-700 flex items-center gap-3">
                <span className="font-semibold">Stages:</span>
                <input
                  type="range"
                  min={1}
                  max={maxWeeklyPhases}
                  step={1}
                  value={weeklyStagesToShow}
                  onChange={(e) => setWeeklyStagesToShow(Number(e.target.value))}
                  className="w-40"
                  aria-label="Weekly stage zoom slider"
                />
                <span className="tabular-nums">
                  {weeklyStagesToShow}/{maxWeeklyPhases}
                </span>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <SignalChips
            signals={signals}
            onClickSignal={({ kpi_id, window: w, point_t }) => onOpenInvestigation({ kpi_id, window: w || 'weekly', point_t })}
          />
        </div>

        {loading && <div className="bg-white border border-slate-200 rounded-xl p-6 text-slate-600">Loading dashboard...</div>}

        {error && <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-rose-800">{error}</div>}

        {!loading && !error && data && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {data.kpis.map((series) => (
              <KpiTrendCard
                key={series.kpi.id}
                series={series}
                window={data.window}
                dailyDaysToShow={data.window === 'daily' ? dailyDaysToShow : undefined}
                weeklyStagesToShow={data.window === 'weekly' ? weeklyStagesToShow : undefined}
                onClick={(pointT) => onOpenInvestigation({ kpi_id: series.kpi.id, window: data.window, point_t: pointT })}
              />
            ))}
          </div>
        )}

        {!loading && !error && investigations && (
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            {/* Header with status summary */}
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="text-lg font-extrabold text-slate-900">Investigation Monitor</div>
                <div className="text-sm text-slate-600">
                  Station <span className="font-semibold">{station}</span> - Click to review details
                </div>
              </div>
              
              {/* Status Summary Pills */}
              <div className="flex items-center gap-2">
                <StatusPill 
                  icon={Clock} 
                  label="In Progress" 
                  count={invGrid.filter(i => i.status === 'in_progress' || i.status === 'open').length}
                  color="blue"
                />
                <StatusPill 
                  icon={CheckCircle2} 
                  label="Completed" 
                  count={invGrid.filter(i => i.status === 'completed' || i.status === 'finalized').length}
                  color="emerald"
                />
                <StatusPill 
                  icon={AlertTriangle} 
                  label="Critical" 
                  count={invGrid.filter(i => signalByKpi.get(i.kpi_id) === 'critical').length}
                  color="rose"
                />
              </div>
            </div>

            {invGrid.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-slate-500">
                <FileSearch className="w-12 h-12 mb-3 text-slate-300" />
                <div className="text-sm font-medium">No investigations yet</div>
                <div className="text-xs mt-1">Click any KPI card above to start an investigation</div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                {invGrid.map((inv) => {
                  const sig = (signalByKpi.get(inv.kpi_id) || 'none') as 'none' | 'warning' | 'critical'
                  const isCompleted = inv.status === 'completed' || inv.status === 'finalized'
                  const hasRootCause = !!inv.final_root_cause
                  const diagnosticCount = inv.diagnostics?.length || 0
                  const completedDiagnostics = inv.diagnostics?.filter(d => d.status === 'completed').length || 0

                  return (
                    <button
                      key={inv.investigation_id}
                      onClick={() => onSelectInvestigation?.(inv.investigation_id)}
                      className={`text-left rounded-lg border transition-all p-3 ${
                        sig === 'critical' 
                          ? 'border-rose-200 bg-rose-50/50 hover:bg-rose-50' 
                          : sig === 'warning'
                            ? 'border-amber-200 bg-amber-50/50 hover:bg-amber-50'
                            : 'border-slate-200 bg-white hover:bg-slate-50'
                      }`}
                      type="button"
                    >
                      {/* Header Row */}
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2">
                          {isCompleted ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                          ) : (
                            <Clock className="w-4 h-4 text-blue-500 flex-shrink-0 animate-pulse" />
                          )}
                          <span className="text-xs font-bold text-slate-500">#{inv.investigation_id}</span>
                        </div>
                        <SignalBadge signal={sig} />
                      </div>

                      {/* KPI Name */}
                      <div className="mt-2">
                        <div className="text-sm font-bold text-slate-900">
                          {inv.kpi_id.split('_').join(' ')}
                        </div>
                        <div className="text-xs text-slate-500 mt-0.5">
                          {inv.window.toUpperCase()} • {inv.created_at ? new Date(inv.created_at).toLocaleDateString() : 'Recent'}
                        </div>
                      </div>

                      {/* Progress/Results */}
                      <div className="mt-2 pt-2 border-t border-slate-100">
                        {hasRootCause ? (
                          <div>
                            <div className="text-xs font-semibold text-slate-500">ROOT CAUSE</div>
                            <div className="text-xs text-slate-700 mt-0.5 line-clamp-2">{inv.final_root_cause}</div>
                          </div>
                        ) : diagnosticCount > 0 ? (
                          <div className="flex items-center justify-between">
                            <div className="text-xs text-slate-600">
                              Diagnostics: <span className="font-bold">{completedDiagnostics}/{diagnosticCount}</span>
                            </div>
                            <div className="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-blue-500 rounded-full transition-all"
                                style={{ width: `${(completedDiagnostics / diagnosticCount) * 100}%` }}
                              />
                            </div>
                          </div>
                        ) : (
                          <div className="text-xs text-slate-500 italic">Analysis pending...</div>
                        )}
                      </div>

                      {/* Footer Stats */}
                      {(inv.final_actions?.length || inv.final_evidence?.length) ? (
                        <div className="mt-2 flex items-center gap-3 text-xs text-slate-500">
                          {inv.final_actions?.length ? (
                            <span>{inv.final_actions.length} action{inv.final_actions.length !== 1 ? 's' : ''}</span>
                          ) : null}
                          {inv.final_evidence?.length ? (
                            <span>{inv.final_evidence.length} evidence</span>
                          ) : null}
                        </div>
                      ) : null}
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


// Helper components for the investigation monitor
function StatusPill({ 
  icon: Icon, 
  label, 
  count, 
  color 
}: { 
  icon: React.ComponentType<{ className?: string }>
  label: string
  count: number
  color: 'blue' | 'emerald' | 'rose' | 'amber'
}) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    rose: 'bg-rose-50 text-rose-700 border-rose-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
  }

  return (
    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold ${colorClasses[color]}`}>
      <Icon className="w-3.5 h-3.5" />
      <span>{count}</span>
      <span className="hidden sm:inline">{label}</span>
    </div>
  )
}

function SignalBadge({ signal }: { signal: 'none' | 'warning' | 'critical' }) {
  if (signal === 'critical') {
    return (
      <span className="px-1.5 py-0.5 rounded text-xs font-bold bg-rose-100 text-rose-700 border border-rose-200">
        CRITICAL
      </span>
    )
  }
  if (signal === 'warning') {
    return (
      <span className="px-1.5 py-0.5 rounded text-xs font-bold bg-amber-100 text-amber-700 border border-amber-200">
        WARNING
      </span>
    )
  }
  return (
    <span className="px-1.5 py-0.5 rounded text-xs font-bold bg-slate-100 text-slate-600 border border-slate-200">
      STABLE
    </span>
  )
}

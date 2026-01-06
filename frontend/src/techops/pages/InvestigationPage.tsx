import { useEffect, useState, useRef } from 'react'
import { techOpsApi } from '../api'
import { InvestigationRecord, TechOpsKPI } from '../types'
import { InvestigationWorkbench, InvestigationWorkbenchRef } from '../../components/investigation/InvestigationWorkbench'
import { ThingsToConsiderSection } from '../../components/ThingsToConsiderSection'
import { ArrowLeft, Share2, FileDown, CheckCircle2 } from 'lucide-react'
import ChartDisplay from '../../components/ChartDisplay'
import { DiagnosticPills } from '../components/DiagnosticPills'

export function InvestigationPage({
  investigationId,
  onBack,
  onFinalize,
}: {
  investigationId: string
  onBack: () => void
  onFinalize: () => void
}) {
  const [inv, setInv] = useState<InvestigationRecord | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [kpis, setKpis] = useState<TechOpsKPI[] | null>(null)
  const [isProcessingQuery, setIsProcessingQuery] = useState(false)
  const workbenchRef = useRef<InvestigationWorkbenchRef | null>(null)

  useEffect(() => {
    let cancelled = false
    setError(null)
    techOpsApi
      .getInvestigation(investigationId)
      .then((data) => {
        if (cancelled) return
        setInv(data)
      })
      .catch((e) => {
        if (cancelled) return
        setError(e instanceof Error ? e.message : 'Failed to load investigation')
      })
    return () => {
      cancelled = true
    }
  }, [investigationId])

  useEffect(() => {
    let cancelled = false
    techOpsApi
      .getKPIs()
      .then((ks) => {
        if (cancelled) return
        setKpis(ks)
      })
      .catch(() => {
        if (cancelled) return
        setKpis(null)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const title = inv ? `Investigation #${inv.investigation_id}` : 'Investigation'

  const handleExecuteQuery = (query: string) => {
    try {
      if (workbenchRef.current && workbenchRef.current.executeQuery) {
        setIsProcessingQuery(true)
        workbenchRef.current.executeQuery(query)
        // Reset processing state after a delay to allow for query execution
        setTimeout(() => setIsProcessingQuery(false), 1000)
      }
    } catch (error) {
      console.error('Failed to execute query:', error)
      setIsProcessingQuery(false)
      // You could add a toast notification here for user feedback
    }
  }

  return (
    <div className="px-6 py-6">
      <div className="max-w-7xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onBack}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <div>
              <div className="text-xs text-slate-500">Operations &gt; Signal Monitor</div>
              <div className="flex items-center gap-3">
                <h2 className="text-2xl font-extrabold text-slate-900">{title}</h2>
                {inv && (
                  <span className="px-2.5 py-1 rounded-full text-xs font-bold border bg-slate-50 text-slate-700 border-slate-200">
                    {inv.status.toUpperCase()}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700">
              <Share2 className="w-4 h-4" />
              Share
            </button>
            <button
              onClick={onFinalize}
              disabled={!inv}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold disabled:opacity-50"
              title="Go to Final Conclusions"
            >
              <CheckCircle2 className="w-4 h-4" />
              Final Conclusions
            </button>
            <button
              type="button"
              onClick={() => setTimeout(() => window.print(), 150)}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-[#0B2A55] hover:bg-[#082043] text-white font-semibold no-print"
              title="Export via browser print-to-PDF"
            >
              <FileDown className="w-4 h-4" />
              Export PDF
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-rose-800">
            {error}
          </div>
        )}

        {inv && (
          <div className="bg-white border border-slate-200 rounded-xl px-5 py-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <div className="text-xs text-slate-500 font-semibold">STATION</div>
                <div className="text-sm font-bold text-slate-900">{inv.station}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 font-semibold">KPI</div>
                <div className="text-sm font-bold text-slate-900">{inv.kpi_id.split('_').join(' ')}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 font-semibold">WINDOW</div>
                <div className="text-sm font-bold text-slate-900">{inv.window.toUpperCase()}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 font-semibold">CREATED BY</div>
                <div className="text-sm font-bold text-slate-900">{inv.created_by.name}</div>
              </div>
            </div>

            {kpis && kpis.length > 0 && (
              <div className="mt-4 border-t border-slate-200 pt-4">
                <div className="text-xs text-slate-500 font-semibold">AVAILABLE MEASURES</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {kpis.map((k) => (
                    <span
                      key={k.id}
                      className="px-2.5 py-1 rounded-full text-xs font-semibold border bg-slate-50 text-slate-700 border-slate-200"
                      title={k.label}
                    >
                      {k.label}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {inv && (inv.diagnostics?.length || inv.telemetry) && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-1 bg-white border border-slate-200 rounded-xl p-4">
              <DiagnosticPills 
                diagnostics={(inv.diagnostics || []).map(d => ({
                  ...d,
                  confidence: d.confidence ?? 0.75,
                }))} 
              />
            </div>

            <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl overflow-hidden">
              {inv.telemetry ? (
                <div className="p-4">
                  <ChartDisplay chart={inv.telemetry as any} />
                  {Array.isArray((inv.telemetry as any)?.plotly_json?.layout?.meta?.phases) && (
                    <div className="mt-4 border-t border-slate-200 pt-4">
                      <div className="text-sm font-extrabold text-slate-900">SPC Stages (Wheeler Phases)</div>
                      <div className="text-xs text-slate-500 mt-1">Limits recalc at detected shifts; latest phase drives current NPL.</div>
                      <div className="mt-3 overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="text-slate-500">
                              <th className="text-left font-semibold py-1 pr-3">Phase</th>
                              <th className="text-left font-semibold py-1 pr-3">Start</th>
                              <th className="text-left font-semibold py-1 pr-3">End</th>
                              <th className="text-right font-semibold py-1 pr-3">CL</th>
                              <th className="text-right font-semibold py-1 pr-3">UCL</th>
                              <th className="text-right font-semibold py-1">LCL</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(inv.telemetry as any).plotly_json.layout.meta.phases.map((p: any) => (
                              <tr key={String(p.phase)} className="border-t border-slate-100">
                                <td className="py-1 pr-3 font-bold text-slate-900">{p.phase}</td>
                                <td className="py-1 pr-3 text-slate-700">{String(p.start)}</td>
                                <td className="py-1 pr-3 text-slate-700">{String(p.end)}</td>
                                <td className="py-1 pr-3 text-right text-slate-700">{Number(p.cl).toFixed(3)}</td>
                                <td className="py-1 pr-3 text-right text-slate-700">{Number(p.ucl).toFixed(3)}</td>
                                <td className="py-1 text-right text-slate-700">{Number(p.lcl).toFixed(3)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-6 text-slate-600">No telemetry available.</div>
              )}
            </div>
          </div>
        )}

        {/* Things to Consider Section */}
        {inv && (
          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <ThingsToConsiderSection
              investigation={inv}
              kpiId={inv.kpi_id}
              station={inv.station}
              window={inv.window}
              onExecuteQuery={handleExecuteQuery}
              isProcessing={isProcessingQuery}
            />
          </div>
        )}

        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <InvestigationWorkbench
            ref={workbenchRef}
            measureName={inv?.kpi_id.split('_').join(' ') || 'Tech Ops KPI'}
            datasetName="techops_demo_metrics"
            initialQuery={inv?.prompt}
            autoRunInitialQuery={true}
            wsContext={{
              investigation_id: inv?.investigation_id,
              kpi_id: inv?.kpi_id,
              station: inv?.station,
              window: inv?.window,
              point_t: inv?.selected_point_t || undefined,
              summary_level: inv?.summary_level || 'station',
              max_iterations: 20,
            }}
          />
        </div>
      </div>
    </div>
  )
}

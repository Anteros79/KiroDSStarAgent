import { useEffect, useState } from 'react'
import { techOpsApi } from '../api'
import { InvestigationRecord } from '../types'
import { InvestigationWorkbench } from '../../components/investigation/InvestigationWorkbench'
import { ArrowLeft, Share2, FileDown, CheckCircle2 } from 'lucide-react'
import ChartDisplay from '../../components/ChartDisplay'

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

  const title = inv ? `Investigation #${inv.investigation_id}` : 'Investigation'

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
            <button className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-[#0B2A55] hover:bg-[#082043] text-white font-semibold">
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
                <div className="text-sm font-bold text-slate-900">{inv.kpi_id.replaceAll('_', ' ')}</div>
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
          </div>
        )}

        {inv && (inv.diagnostics?.length || inv.telemetry) && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-1 bg-white border border-slate-200 rounded-xl p-5">
              <div className="text-sm font-extrabold text-slate-900">DS‑STAR Diagnostics</div>
              <div className="text-xs text-slate-500 mt-1">Automated tests run for this investigation</div>
              <div className="mt-4 space-y-3">
                {(inv.diagnostics || []).map((t, idx) => (
                  <div key={idx} className="rounded-lg border border-slate-200 p-3 bg-slate-50">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-bold text-slate-900">{t.name}</div>
                      <span className="text-xs font-bold px-2 py-0.5 rounded-full border border-slate-200 bg-white text-slate-700">
                        {String(t.status).replaceAll('_', ' ').toUpperCase()}
                      </span>
                    </div>
                    {typeof t.confidence === 'number' && (
                      <div className="mt-2 text-xs text-slate-600">
                        Confidence: <span className="font-bold">{Math.round(t.confidence * 100)}%</span>
                      </div>
                    )}
                    {t.detail && <div className="mt-1 text-xs text-slate-600">{t.detail}</div>}
                  </div>
                ))}
              </div>
            </div>

            <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl overflow-hidden">
              {inv.telemetry ? (
                <div className="p-4">
                  <ChartDisplay chart={inv.telemetry as any} />
                </div>
              ) : (
                <div className="p-6 text-slate-600">No telemetry available.</div>
              )}
            </div>
          </div>
        )}

        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <InvestigationWorkbench
            measureName={inv?.kpi_id.replaceAll('_', ' ') || 'Tech Ops KPI'}
            datasetName="techops_demo_metrics"
            initialQuery={inv?.prompt}
            autoRunInitialQuery={true}
            wsContext={{
              investigation_id: inv?.investigation_id,
              kpi_id: inv?.kpi_id,
              station: inv?.station,
              window: inv?.window,
              point_t: inv?.selected_point_t || undefined,
              max_iterations: 20,
            }}
          />
        </div>
      </div>
    </div>
  )
}


